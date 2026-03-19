"""
认证蓝图 - 处理用户登录和认证相关的路由
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from app.models import db, User
from app.utils import WechatService, JWTHandler, ApiResponse

logger = logging.getLogger(__name__)

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    微信小程序登录接口
    
    请求体:
    {
        "code": "微信小程序授权返回的 code"
    }
    
    返回:
    {
        "code": 200,
        "message": "Login successful",
        "data": {
            "user_id": 1,
            "token": "jwt-token",
            "user": {
                "id": 1,
                "openid": "...",
                "nickname": "...",
                ...
            }
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        code = data.get('code')
        
        # 验证参数
        if not code:
            logger.warning('Login request missing code parameter')
            return jsonify(ApiResponse.bad_request('Missing code parameter')), 400
        
        # 初始化微信服务
        wechat_service = WechatService(
            appid=current_app.config['WECHAT_APPID'],
            secret=current_app.config['WECHAT_SECRET'],
            login_url=current_app.config['WECHAT_LOGIN_URL']
        )
        
        # 调用微信接口获取 openid 和 session_key
        logger.info(f'Exchanging code for WeChat session')
        session_data = wechat_service.code2session(code)
        
        if not session_data:
            logger.error('Failed to exchange code from WeChat API')
            return jsonify(ApiResponse.error(
                'Failed to get WeChat session',
                code=500
            )), 500
        
        openid = session_data.get('openid')
        
        # 查找或创建用户
        user = User.query.filter_by(openid=openid).first()
        
        if user:
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            logger.info(f'Existing user login: {openid}')
        else:
            # 创建新用户
            user = User(
                openid=openid,
                nickname=f'User_{openid[-8:]}',  # 默认昵称
                credit_score=100,
                status=1,
                last_login=datetime.utcnow()
            )
            db.session.add(user)
            logger.info(f'New user created: {openid}')
        
        # 保存用户信息到数据库
        db.session.commit()
        
        # 初始化 JWT 处理器
        jwt_handler = JWTHandler(
            secret_key=current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM'],
            expiration_seconds=current_app.config['JWT_EXPIRATION']
        )
        
        # 生成 JWT Token
        token = jwt_handler.generate_token(
            user_id=user.id,
            openid=user.openid,
            extra_data={
                'credit_score': user.credit_score
            }
        )
        
        return jsonify(ApiResponse.success(
            data={
                'user_id': user.id,
                'token': token,
                'user': user.to_dict()
            },
            message='Login successful',
            code=200
        )), 200
        
    except Exception as e:
        logger.error(f'Error in login endpoint: {str(e)}', exc_info=True)
        return jsonify(ApiResponse.server_error('Internal server error')), 500


@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """
    验证 token 有效性接口
    
    请求体:
    {
        "token": "jwt-token-string"
    }
    
    返回:
    {
        "code": 200,
        "message": "Token is valid",
        "data": {
            "user_id": 1,
            "openid": "...",
            "valid": true
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        token = data.get('token')
        
        if not token:
            return jsonify(ApiResponse.bad_request('Missing token parameter')), 400
        
        # 初始化 JWT 处理器
        jwt_handler = JWTHandler(
            secret_key=current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM'],
            expiration_seconds=current_app.config['JWT_EXPIRATION']
        )
        
        # 验证 token
        payload = jwt_handler.verify_token(token)
        
        if not payload:
            return jsonify(ApiResponse.error(
                'Token is invalid or expired',
                code=401
            )), 401
        
        return jsonify(ApiResponse.success(
            data={
                'user_id': payload.get('user_id'),
                'openid': payload.get('openid'),
                'valid': True
            },
            message='Token is valid'
        )), 200
        
    except Exception as e:
        logger.error(f'Error in verify_token endpoint: {str(e)}')
        return jsonify(ApiResponse.server_error('Internal server error')), 500


@auth_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    """
    刷新 token 接口
    
    请求体:
    {
        "token": "old-jwt-token-string"
    }
    
    返回:
    {
        "code": 200,
        "message": "Token refreshed successfully",
        "data": {
            "token": "new-jwt-token"
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        token = data.get('token')
        
        if not token:
            return jsonify(ApiResponse.bad_request('Missing token parameter')), 400
        
        # 初始化 JWT 处理器
        jwt_handler = JWTHandler(
            secret_key=current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM'],
            expiration_seconds=current_app.config['JWT_EXPIRATION']
        )
        
        # 验证旧 token（即使过期也能解码）
        payload = jwt_handler.decode_token(token)
        
        if not payload:
            return jsonify(ApiResponse.error(
                'Invalid token',
                code=401
            )), 401
        
        # 获取用户ID和openid
        user_id = payload.get('user_id')
        openid = payload.get('openid')
        
        if not user_id or not openid:
            return jsonify(ApiResponse.error(
                'Invalid token payload',
                code=401
            )), 401
        
        # 获取用户信息
        user = User.query.get(user_id)
        
        if not user or user.openid != openid:
            return jsonify(ApiResponse.error(
                'User not found or token mismatch',
                code=401
            )), 401
        
        # 生成新 token
        new_token = jwt_handler.generate_token(
            user_id=user.id,
            openid=user.openid,
            extra_data={
                'credit_score': user.credit_score
            }
        )
        
        return jsonify(ApiResponse.success(
            data={'token': new_token},
            message='Token refreshed successfully'
        )), 200
        
    except Exception as e:
        logger.error(f'Error in refresh_token endpoint: {str(e)}')
        return jsonify(ApiResponse.server_error('Internal server error')), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口 - 基于手机号和密码
    
    请求体:
    {
        "phone_number": "13812345678",
        "password": "password123",
        "real_name": "张三",
        "student_id": "2022001234"
    }
    
    返回:
    {
        "code": 201,
        "message": "User registered successfully",
        "data": {
            "user_id": 1,
            "access_token": "jwt-token",
            "user": {...}
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        phone_number = data.get('phone_number', '').strip()
        password = data.get('password', '').strip()
        real_name = data.get('real_name', '').strip()
        student_id = data.get('student_id', '').strip()
        
        # 参数验证
        if not phone_number or not password or not real_name or not student_id:
            logger.warning('Register request missing required parameters')
            return jsonify(ApiResponse.bad_request('Missing required parameters')), 400
        
        # 验证手机号格式
        if not _validate_phone(phone_number):
            return jsonify(ApiResponse.bad_request('Invalid phone number format')), 400
        
        # 验证密码强度
        if len(password) < 6:
            return jsonify(ApiResponse.bad_request('Password must be at least 6 characters')), 400
        
        # 检查手机号是否已注册
        existing_user = User.query.filter_by(phone=phone_number).first()
        if existing_user:
            logger.warning(f'Register attempt with existing phone: {phone_number}')
            return jsonify(ApiResponse.error('Phone number already registered', code=400)), 400
        
        # 检查学号是否已存在
        existing_student = User.query.filter_by(student_id=student_id).first()
        if existing_student:
            logger.warning(f'Register attempt with existing student_id: {student_id}')
            return jsonify(ApiResponse.error('Student ID already registered', code=400)), 400
        
        # 创建新用户
        user = User(
            phone=phone_number,
            real_name=real_name,
            student_id=student_id,
            nickname=real_name,  # 默认使用真实姓名作为昵称
            credit_score=100,
            status=1,
            last_login=datetime.utcnow(),
            openid=f'miniapp_{phone_number}'  # 生成虚拟openid
        )
        
        # 设置密码
        user.set_password(password)
        
        # 保存到数据库
        db.session.add(user)
        db.session.commit()
        
        logger.info(f'New user registered: {phone_number}')
        
        # 生成JWT Token
        jwt_handler = JWTHandler(
            secret_key=current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM'],
            expiration_seconds=current_app.config['JWT_EXPIRATION']
        )
        
        token = jwt_handler.generate_token(
            user_id=user.id,
            openid=user.openid,
            extra_data={
                'phone': phone_number,
                'credit_score': user.credit_score
            }
        )
        
        return jsonify(ApiResponse.success(
            data={
                'user_id': user.id,
                'access_token': token,
                'user': user.to_dict(include_private=True)
            },
            message='User registered successfully',
            code=201
        )), 201
        
    except Exception as e:
        logger.error(f'Error in register endpoint: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify(ApiResponse.server_error('Internal server error')), 500


@auth_bp.route('/login-with-password', methods=['POST'])
def login_with_password():
    """
    用户登录接口 - 基于手机号和密码
    
    请求体:
    {
        "phone_number": "13812345678",
        "password": "password123"
    }
    
    返回:
    {
        "code": 200,
        "message": "Login successful",
        "data": {
            "user_id": 1,
            "access_token": "jwt-token",
            "user": {...}
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        phone_number = data.get('phone_number', '').strip()
        password = data.get('password', '').strip()
        
        # 参数验证
        if not phone_number or not password:
            logger.warning('Login request missing required parameters')
            return jsonify(ApiResponse.bad_request('Missing required parameters')), 400
        
        # 查找用户
        user = User.query.filter_by(phone=phone_number).first()
        
        if not user:
            logger.warning(f'Login attempt with non-existent phone: {phone_number}')
            return jsonify(ApiResponse.error('Invalid phone number or password', code=401)), 401
        
        # 检查用户状态
        if user.status != 1:
            logger.warning(f'Login attempt for disabled user: {phone_number}')
            return jsonify(ApiResponse.error('User account is disabled', code=403)), 403
        
        # 验证密码
        if not user.check_password(password):
            logger.warning(f'Login attempt with wrong password for: {phone_number}')
            return jsonify(ApiResponse.error('Invalid phone number or password', code=401)), 401
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'User login successful: {phone_number}')
        
        # 生成JWT Token
        jwt_handler = JWTHandler(
            secret_key=current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM'],
            expiration_seconds=current_app.config['JWT_EXPIRATION']
        )
        
        token = jwt_handler.generate_token(
            user_id=user.id,
            openid=user.openid,
            extra_data={
                'phone': phone_number,
                'credit_score': user.credit_score
            }
        )
        
        return jsonify(ApiResponse.success(
            data={
                'user_id': user.id,
                'access_token': token,
                'user': user.to_dict(include_private=True)
            },
            message='Login successful'
        )), 200
        
    except Exception as e:
        logger.error(f'Error in login_with_password endpoint: {str(e)}', exc_info=True)
        return jsonify(ApiResponse.server_error('Internal server error')), 500


def _validate_phone(phone):
    """验证手机号格式"""
    import re
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


"""
简化认证蓝图 - 兼容前端调用的非版本化路由
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from app.models import db, User
from app.utils import JWTHandler, ApiResponse

logger = logging.getLogger(__name__)

# 创建简化认证蓝图（不带版本号）
simple_auth_bp = Blueprint('simple_auth', __name__, url_prefix='/api/auth')


@simple_auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口 - 基于手机号和密码
    简化版（兼容前端调用）
    
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
                'user': {
                    'id': user.id,
                    'phone': user.phone,
                    'nickname': user.nickname,
                    'real_name': user.real_name,
                    'student_id': user.student_id,
                    'credit_score': user.credit_score,
                    'avatar_url': user.avatar_url
                }
            }
        )), 200
        
    except Exception as e:
        logger.error(f'Error in login endpoint: {str(e)}', exc_info=True)
        return jsonify(ApiResponse.server_error('Internal server error')), 500


@simple_auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口 - 基于手机号
    简化版（兼容前端调用）
    
    请求体:
    {
        "phone_number": "13812345678",
        "password": "password123",
        "real_name": "张三",
        "student_id": "2022001111"
    }
    
    返回:
    {
        "code": 201,
        "message": "Registration successful",
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
        
        # 检查用户是否已存在 (手机号)
        existing_user = User.query.filter_by(phone=phone_number).first()
        if existing_user:
            logger.warning(f'Register attempt with existing phone: {phone_number}')
            return jsonify(ApiResponse.error('该手机号已被注册', code=409)), 409
            
        # 检查学号是否已存在
        existing_student = User.query.filter_by(student_id=student_id).first()
        if existing_student:
            logger.warning(f'Register attempt with existing student_id: {student_id}')
            return jsonify(ApiResponse.error('该学号已被注册', code=409)), 409
        
        # 创建新用户
        new_user = User(
            phone=phone_number,
            real_name=real_name,
            student_id=student_id,
            credit_score=100,
            status=1,
            nickname=real_name,
            openid=f'miniapp_{phone_number}'  # 生成虚拟openid
        )
        new_user.set_password(password)
        new_user.last_login = datetime.utcnow()
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f'New user registered: {phone_number}')
        
        # 生成JWT Token
        jwt_handler = JWTHandler(
            secret_key=current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM'],
            expiration_seconds=current_app.config['JWT_EXPIRATION']
        )
        
        token = jwt_handler.generate_token(
            user_id=new_user.id,
            openid=new_user.openid,
            extra_data={
                'phone': phone_number,
                'credit_score': new_user.credit_score
            }
        )
        
        return jsonify(ApiResponse.success(
            data={
                'user_id': new_user.id,
                'access_token': token,
                'user': {
                    'id': new_user.id,
                    'phone': new_user.phone,
                    'real_name': new_user.real_name,
                    'student_id': new_user.student_id,
                    'credit_score': new_user.credit_score
                }
            }
        )), 201
        
    except Exception as e:
        logger.error(f'Error in register endpoint: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify(ApiResponse.server_error('Internal server error')), 500


def _validate_phone(phone_number: str) -> bool:
    """
    验证手机号格式
    
    Args:
        phone_number: 手机号
    
    Returns:
        是否有效
    """
    import re
    # 简单的手机号验证：11位，以1开头
    return bool(re.match(r'^1[3-9]\d{9}$', phone_number))

"""
小程序认证蓝图 - 处理小程序的注册和登录
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import re
from app.models import db, User
from app.utils import JWTHandler, ApiResponse

logger = logging.getLogger(__name__)

# 创建小程序认证蓝图
mini_program_auth_bp = Blueprint('mini_program_auth', __name__, url_prefix='/api/auth')


@mini_program_auth_bp.route('/register', methods=['POST'])
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
            return jsonify({
                'code': 400,
                'message': 'Missing required parameters',
                'error': 'phone_number, password, real_name, and student_id are required'
            }), 400
        
        # 验证手机号格式
        if not _validate_phone(phone_number):
            return jsonify({
                'code': 400,
                'message': 'Invalid phone number format',
                'error': 'Phone number must be 11 digits starting with 1'
            }), 400
        
        # 验证密码强度
        if len(password) < 6:
            return jsonify({
                'code': 400,
                'message': 'Password must be at least 6 characters',
                'error': 'Password too short'
            }), 400
        
        # 检查手机号是否已注册
        existing_user = User.query.filter_by(phone=phone_number).first()
        if existing_user:
            logger.warning(f'Register attempt with existing phone: {phone_number}')
            return jsonify({
                'code': 400,
                'message': 'Phone number already registered',
                'error': 'This phone number already has an account'
            }), 400
        
        # 检查学号是否已存在
        existing_student = User.query.filter_by(student_id=student_id).first()
        if existing_student:
            logger.warning(f'Register attempt with existing student_id: {student_id}')
            return jsonify({
                'code': 400,
                'message': 'Student ID already registered',
                'error': 'This student ID is already in use'
            }), 400
        
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
        
        return jsonify({
            'code': 201,
            'message': 'User registered successfully',
            'data': {
                'user_id': user.id,
                'access_token': token,
                'user': {
                    'id': user.id,
                    'phone': phone_number,
                    'real_name': real_name,
                    'student_id': student_id,
                    'credit_score': user.credit_score
                }
            }
        }), 201
        
    except Exception as e:
        logger.error(f'Error in register endpoint: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': 'Internal server error',
            'error': str(e)
        }), 500


@mini_program_auth_bp.route('/login', methods=['POST'])
def login():
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
            return jsonify({
                'code': 400,
                'message': 'Missing required parameters',
                'error': 'phone_number and password are required'
            }), 400
        
        # 查找用户
        user = User.query.filter_by(phone=phone_number).first()
        
        if not user:
            logger.warning(f'Login attempt with non-existent phone: {phone_number}')
            return jsonify({
                'code': 401,
                'message': 'Invalid phone number or password',
                'error': 'Authentication failed'
            }), 401
        
        # 检查用户状态
        if user.status != 1:
            logger.warning(f'Login attempt for disabled user: {phone_number}')
            return jsonify({
                'code': 403,
                'message': 'User account is disabled',
                'error': 'Your account has been disabled'
            }), 403
        
        # 验证密码
        if not user.check_password(password):
            logger.warning(f'Login attempt with wrong password for: {phone_number}')
            return jsonify({
                'code': 401,
                'message': 'Invalid phone number or password',
                'error': 'Authentication failed'
            }), 401
        
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
        
        return jsonify({
            'code': 200,
            'message': 'Login successful',
            'data': {
                'user_id': user.id,
                'access_token': token,
                'user': {
                    'id': user.id,
                    'phone': phone_number,
                    'real_name': user.real_name,
                    'student_id': user.student_id,
                    'credit_score': user.credit_score
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error in login endpoint: {str(e)}', exc_info=True)
        return jsonify({
            'code': 500,
            'message': 'Internal server error',
            'error': str(e)
        }), 500


def _validate_phone(phone):
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

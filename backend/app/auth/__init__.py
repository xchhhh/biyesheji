"""
认证模块
"""
from functools import wraps
from flask import request, jsonify
from app.utils import JWTHandler, ApiResponse
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""
    
    def __init__(self, jwt_handler: JWTHandler):
        """
        初始化认证服务
        
        Args:
            jwt_handler: JWT 处理器实例
        """
        self.jwt_handler = jwt_handler
    
    def login_required(self, f):
        """
        登录验证装饰器
        
        使用方法：
            @auth_instance.login_required
            def protected_route():
                pass
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 从请求头获取 token
            token = self._extract_token_from_request()
            
            if not token:
                logger.warning('Missing token in request')
                return jsonify(ApiResponse.unauthorized('Missing authorization token')), 401
            
            # 验证 token
            payload = self.jwt_handler.verify_token(token)
            
            if not payload:
                logger.warning(f'Invalid or expired token')
                return jsonify(ApiResponse.unauthorized('Invalid or expired token')), 401
            
            # 将用户信息存储在 request 对象中
            request.user_id = payload.get('user_id')
            request.openid = payload.get('openid')
            request.token_payload = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def _extract_token_from_request(self) -> str:
        """
        从请求中提取 token
        
        支持两种方式：
        1. Authorization header: "Authorization: Bearer <token>"
        2. 请求参数: ?token=<token>
        
        Returns:
            Token 字符串，未找到返回空字符串
        """
        # 从 Authorization header 获取
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # 移除 "Bearer " 前缀
        
        # 从请求参数获取
        token = request.args.get('token')
        if token:
            return token
        
        # 从 JSON body 获取
        if request.is_json:
            token = request.json.get('token')
            if token:
                return token
        
        return ''

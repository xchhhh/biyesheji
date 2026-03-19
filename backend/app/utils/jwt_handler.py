"""
JWT (JSON Web Token) 处理工具
"""
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class JWTHandler:
    """JWT Token 处理器"""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256', expiration_seconds: int = 7200):
        """
        初始化 JWT 处理器
        
        Args:
            secret_key: JWT 密钥
            algorithm: 加密算法，默认为 HS256
            expiration_seconds: token 过期时间（秒），默认 7200（2小时）
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_seconds = expiration_seconds
    
    def generate_token(self, user_id: int, openid: str, extra_data: Optional[Dict[str, Any]] = None) -> str:
        """
        生成 JWT Token
        
        Args:
            user_id: 用户ID
            openid: 微信 openid
            extra_data: 额外的声明数据
        
        Returns:
            JWT Token 字符串
        """
        try:
            payload = {
                'user_id': user_id,
                'openid': openid,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(seconds=self.expiration_seconds)
            }
            
            # 添加额外数据
            if extra_data:
                payload.update(extra_data)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f'Generated JWT token for user_id: {user_id}')
            return token
            
        except Exception as e:
            logger.error(f'Error generating JWT token: {str(e)}')
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证 JWT Token 的有效性
        
        Args:
            token: JWT Token 字符串
        
        Returns:
            包含 token 声明的字典，验证失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.debug(f'JWT token verified for user_id: {payload.get("user_id")}')
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning(f'JWT token expired')
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f'Invalid JWT token: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Error verifying JWT token: {str(e)}')
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码 JWT Token（不验证过期时间）
        
        Args:
            token: JWT Token 字符串
        
        Returns:
            包含 token 声明的字典，解码失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={'verify_exp': False})
            return payload
            
        except Exception as e:
            logger.error(f'Error decoding JWT token: {str(e)}')
            return None

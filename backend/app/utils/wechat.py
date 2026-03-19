"""
微信小程序接口工具
"""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WechatService:
    """微信登录服务"""
    
    def __init__(self, appid: str, secret: str, login_url: str):
        """
        初始化微信服务
        
        Args:
            appid: 微信小程序应用ID
            secret: 微信小程序应用密钥
            login_url: 微信登录接口地址
        """
        self.appid = appid
        self.secret = secret
        self.login_url = login_url
    
    def code2session(self, code: str) -> Optional[Dict[str, Any]]:
        """
        将授权码 code 转换为 session，获取 openid 和 session_key
        
        Args:
            code: 授权码，从微信小程序客户端获取
        
        Returns:
            字典包含 openid 和 session_key，失败返回 None
        """
        try:
            params = {
                'appid': self.appid,
                'secret': self.secret,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            
            logger.info(f'Calling WeChat API to exchange code for session: {self.login_url}')
            
            response = requests.get(
                self.login_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 检查是否有错误
            if 'errcode' in data:
                error_msg = data.get('errmsg', 'Unknown error')
                logger.error(f'WeChat API error: {error_msg}')
                return None
            
            # 返回包含 openid 和 session_key 的数据
            return {
                'openid': data.get('openid'),
                'session_key': data.get('session_key')
            }
            
        except requests.RequestException as e:
            logger.error(f'Request error when calling WeChat API: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error in code2session: {str(e)}')
            return None

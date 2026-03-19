"""
统一 API 响应工具
"""
from typing import Any, Dict, Optional


class ApiResponse:
    """API 统一响应格式"""
    
    @staticmethod
    def success(data: Any = None, message: str = 'Success', code: int = 200) -> Dict[str, Any]:
        """
        成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            code: HTTP 状态码
        
        Returns:
            响应字典
        """
        return {
            'code': code,
            'message': message,
            'data': data,
            'success': True
        }
    
    @staticmethod
    def error(message: str, code: int = 400, data: Any = None) -> Dict[str, Any]:
        """
        错误响应
        
        Args:
            message: 错误消息
            code: 错误代码
            data: 额外数据
        
        Returns:
            响应字典
        """
        return {
            'code': code,
            'message': message,
            'data': data,
            'success': False
        }
    
    # 常用错误响应快捷方法
    @staticmethod
    def unauthorized(message: str = 'Unauthorized') -> Dict[str, Any]:
        return ApiResponse.error(message, code=401)
    
    @staticmethod
    def forbidden(message: str = 'Forbidden') -> Dict[str, Any]:
        return ApiResponse.error(message, code=403)
    
    @staticmethod
    def not_found(message: str = 'Not Found') -> Dict[str, Any]:
        return ApiResponse.error(message, code=404)
    
    @staticmethod
    def bad_request(message: str = 'Bad Request') -> Dict[str, Any]:
        return ApiResponse.error(message, code=400)
    
    @staticmethod
    def server_error(message: str = 'Internal Server Error') -> Dict[str, Any]:
        return ApiResponse.error(message, code=500)

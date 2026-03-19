"""
API 模块 - 预留用于后续扩展

此模块用于组织所有 API 接口，支持版本管理（v1, v2, 等）
"""
from app.api.reservation import reservation_bp
from app.api.user import user_bp
from app.api.admin import admin_bp
from app.api.management import management_bp

__all__ = ['reservation_bp', 'user_bp', 'admin_bp', 'management_bp']

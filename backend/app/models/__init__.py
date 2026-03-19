"""
数据模型模块
"""
from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例
db = SQLAlchemy()

# 导入所有模型
from app.models.user import User
from app.models.seat import Seat
from app.models.reading_room import ReadingRoom
from app.models.reservation import Reservation
from app.models.credit_flow import CreditFlow
from app.models.announcement import Announcement
from app.models.audit_log import AuditLog
from app.models.seat_maintenance import SeatMaintenance

__all__ = [
    'db', 
    'User', 
    'Seat', 
    'ReadingRoom', 
    'Reservation', 
    'CreditFlow',
    'Announcement',
    'AuditLog',
    'SeatMaintenance'
]

"""
座位模型
"""
from datetime import datetime
from app.models import db


class Seat(db.Model):
    """座位表"""
    __tablename__ = 'seats'
    
    id = db.Column(db.Integer, primary_key=True, comment='座位ID')
    room_id = db.Column(db.Integer, db.ForeignKey('reading_rooms.id'), nullable=False, comment='阅览室ID')
    seat_number = db.Column(db.String(20), nullable=False, comment='座位编号 (如: A-001)')
    status = db.Column(db.Integer, default=0, comment='座位状态 (0-空闲, 1-已占用, 2-维修)')
    last_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='最后使用者ID')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最后更新时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    room = db.relationship('ReadingRoom', backref='seats', lazy='joined')
    last_user = db.relationship('User', lazy='joined')
    
    # 添加唯一约束
    __table_args__ = (
        db.UniqueConstraint('room_id', 'seat_number', name='uq_room_seat_number'),
    )
    
    def __repr__(self):
        return f'<Seat {self.seat_number}>'
    
    def to_dict(self):
        """将座位对象转换为字典"""
        return {
            'id': self.id,
            'room_id': self.room_id,
            'seat_number': self.seat_number,
            'status': self.status,
            'last_user_id': self.last_user_id,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }

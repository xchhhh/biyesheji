"""
预约记录模型
"""
from datetime import datetime
from app.models import db


class Reservation(db.Model):
    """预约记录表"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True, comment='预约ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False, comment='座位ID')
    room_id = db.Column(db.Integer, db.ForeignKey('reading_rooms.id'), nullable=False, comment='阅览室ID')
    reservation_date = db.Column(db.Date, nullable=False, comment='预约日期')
    reservation_time = db.Column(db.String(20), nullable=False, comment='预约时间段 (如: 08:00-10:00)')
    status = db.Column(db.Integer, default=0, comment='状态 (0-预约中, 1-已签到, 2-已结束, 3-已取消, 4-已迟到)')
    check_in_time = db.Column(db.DateTime, nullable=True, comment='签到时间')
    check_out_time = db.Column(db.DateTime, nullable=True, comment='签出时间')
    no_show_times = db.Column(db.Integer, default=0, comment='缺座次数')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    # user 关系由 User.reservations backref='user' 提供
    seat = db.relationship('Seat', lazy='joined')
    # room 关系需要定义（Seat 中没有backref），但改变 backref 名称以避免冲突
    room = db.relationship('ReadingRoom')
    
    # 添加索引
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'reservation_date'),
        db.Index('idx_seat_date', 'seat_id', 'reservation_date'),
        db.Index('idx_room_date', 'room_id', 'reservation_date'),
    )
    
    def __repr__(self):
        return f'<Reservation {self.id}>'
    
    def to_dict(self):
        """将预约记录对象转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'seat_id': self.seat_id,
            'room_id': self.room_id,
            'reservation_date': self.reservation_date.isoformat(),
            'reservation_time': self.reservation_time,
            'status': self.status,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'no_show_times': self.no_show_times,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

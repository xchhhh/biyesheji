"""
阅览室模型
"""
from datetime import datetime
from app.models import db


class ReadingRoom(db.Model):
    """阅览室表"""
    __tablename__ = 'reading_rooms'
    
    id = db.Column(db.Integer, primary_key=True, comment='阅览室ID')
    name = db.Column(db.String(100), nullable=False, comment='阅览室名称')
    building = db.Column(db.String(50), nullable=False, comment='所在建筑')
    floor = db.Column(db.Integer, nullable=False, comment='所在楼层')
    total_seats = db.Column(db.Integer, nullable=False, comment='总座位数')
    available_seats = db.Column(db.Integer, nullable=False, comment='可用座位数')
    open_time = db.Column(db.String(10), nullable=False, default='08:00', comment='开放时间')
    close_time = db.Column(db.String(10), nullable=False, default='22:00', comment='关闭时间')
    description = db.Column(db.Text, nullable=True, comment='阅览室描述')
    status = db.Column(db.Integer, default=1, comment='状态 (1-开放, 0-关闭)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    reservations = db.relationship('Reservation', backref='reading_room', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ReadingRoom {self.name}>'
    
    def to_dict(self):
        """将阅览室对象转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'building': self.building,
            'floor': self.floor,
            'total_seats': self.total_seats,
            'available_seats': self.available_seats,
            'open_time': self.open_time,
            'close_time': self.close_time,
            'description': self.description,
            'status': self.status,
        }

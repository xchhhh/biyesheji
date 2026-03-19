"""
座位维护记录模型
"""
from datetime import datetime
from app.models import db


class SeatMaintenance(db.Model):
    """座位维护记录表 - 追踪座位的维护和修复"""
    __tablename__ = 'seat_maintenance'
    
    id = db.Column(db.Integer, primary_key=True, comment='维护记录ID')
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False, comment='座位ID')
    issue_type = db.Column(db.String(50), nullable=False, comment='问题类型 (broken-损坏, dirty-脏污, furniture-家具问题, electrical-电气问题, other-其他)')
    severity = db.Column(db.String(20), default='medium', comment='严重程度 (low-低, medium-中, high-高, critical-严重)')
    description = db.Column(db.Text, nullable=False, comment='问题描述')
    reported_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='报告人ID')
    reporter_phone = db.Column(db.String(20), nullable=True, comment='报告人电话')
    status = db.Column(db.String(20), default='pending', comment='状态 (pending-待处理, in_progress-处理中, completed-已完成, cancelled-已取消)')
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='分配给的维修人员ID')
    maintenance_date = db.Column(db.DateTime, nullable=True, comment='实际维护日期')
    completion_date = db.Column(db.DateTime, nullable=True, comment='完成日期')
    notes = db.Column(db.Text, nullable=True, comment='维护备注')
    estimated_days = db.Column(db.Integer, default=1, comment='预计维护天数')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    seat = db.relationship('Seat', backref='maintenance_records', lazy='joined')
    reported_by = db.relationship('User', foreign_keys=[reported_by_id], backref='reported_maintenance', lazy='joined')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_maintenance', lazy='joined')
    
    def __repr__(self):
        return f'<SeatMaintenance Seat {self.seat_id} - {self.issue_type}>'
    
    def to_dict(self):
        """将维护记录对象转换为字典"""
        return {
            'id': self.id,
            'seat_id': self.seat_id,
            'seat_number': self.seat.seat_number if self.seat else None,
            'room_id': self.seat.room_id if self.seat else None,
            'issue_type': self.issue_type,
            'severity': self.severity,
            'description': self.description,
            'reported_by_id': self.reported_by_id,
            'reported_by_name': self.reported_by.real_name if self.reported_by else None,
            'reporter_phone': self.reporter_phone,
            'status': self.status,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to.real_name if self.assigned_to else None,
            'maintenance_date': self.maintenance_date.isoformat() if self.maintenance_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'notes': self.notes,
            'estimated_days': self.estimated_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

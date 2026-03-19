"""
审计日志模型
"""
from datetime import datetime
from app.models import db


class AuditLog(db.Model):
    """审计日志表 - 记录所有关键操作"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True, comment='日志ID')
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='操作人ID')
    action = db.Column(db.String(100), nullable=False, comment='操作类型')
    module = db.Column(db.String(50), nullable=False, comment='操作模块 (user, seat, reservation, announcement, etc)')
    resource_type = db.Column(db.String(50), nullable=True, comment='资源类型 (User, Seat, Reservation, etc)')
    resource_id = db.Column(db.Integer, nullable=True, comment='资源ID')
    description = db.Column(db.String(500), nullable=False, comment='操作描述')
    old_values = db.Column(db.JSON, nullable=True, comment='修改前的值')
    new_values = db.Column(db.JSON, nullable=True, comment='修改后的值')
    status = db.Column(db.String(20), default='success', comment='操作状态 (success, failed)')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息（如果操作失败）')
    ip_address = db.Column(db.String(50), nullable=True, comment='操作者IP地址')
    user_agent = db.Column(db.String(500), nullable=True, comment='用户浏览器信息')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')
    
    # 关系
    operator = db.relationship('User', backref='audit_logs', lazy='joined')
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.resource_type}>'
    
    def to_dict(self):
        """将日志对象转换为字典"""
        return {
            'id': self.id,
            'operator_id': self.operator_id,
            'operator_name': self.operator.real_name if self.operator else 'System',
            'action': self.action,
            'module': self.module,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'status': self.status,
            'error_message': self.error_message,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

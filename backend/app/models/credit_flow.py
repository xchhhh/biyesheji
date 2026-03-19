"""
信用积分流水模型
"""
from datetime import datetime
from app.models import db


class CreditFlow(db.Model):
    """信用积分流水表"""
    __tablename__ = 'credit_flows'
    
    id = db.Column(db.Integer, primary_key=True, comment='流水ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    action = db.Column(db.String(50), nullable=False, comment='行为 (如: no_show, late_cancel, check_in_success 等)')
    points_change = db.Column(db.Integer, nullable=False, comment='积分变化 (可正可负)')
    reason = db.Column(db.String(200), nullable=False, comment='原因描述')
    reservation_id = db.Column(db.Integer, nullable=True, comment='相关预约ID')
    balance_after = db.Column(db.Integer, nullable=False, comment='变化后的积分余额')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    # user 关系由 User.credit_flows backref 提供，不重复定义
    
    # 添加索引
    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<CreditFlow {self.id}>'
    
    def to_dict(self):
        """将信用积分流水对象转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'points_change': self.points_change,
            'reason': self.reason,
            'reservation_id': self.reservation_id,
            'balance_after': self.balance_after,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

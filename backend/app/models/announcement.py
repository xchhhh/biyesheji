"""
公告模型
"""
from datetime import datetime
from app.models import db


class Announcement(db.Model):
    """系统公告表"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True, comment='公告ID')
    title = db.Column(db.String(255), nullable=False, comment='公告标题')
    content = db.Column(db.Text, nullable=False, comment='公告内容')
    type = db.Column(db.String(50), default='general', comment='公告类型 (general-一般, maintenance-维护, emergency-紧急)')
    priority = db.Column(db.Integer, default=0, comment='优先级 (0-低, 1-中, 2-高)')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='发布人ID')
    status = db.Column(db.Integer, default=1, comment='状态 (0-草稿, 1-已发布, 2-已下架)')
    is_pinned = db.Column(db.Boolean, default=False, comment='是否置顶')
    start_time = db.Column(db.DateTime, nullable=True, comment='开始显示时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束显示时间')
    view_count = db.Column(db.Integer, default=0, comment='浏览次数')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    author = db.relationship('User', backref='announcements', lazy='joined')
    
    def __repr__(self):
        return f'<Announcement {self.title}>'
    
    def to_dict(self):
        """将公告对象转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'priority': self.priority,
            'author_id': self.author_id,
            'author_name': self.author.real_name if self.author else None,
            'status': self.status,
            'is_pinned': self.is_pinned,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

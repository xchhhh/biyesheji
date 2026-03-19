"""
用户模型
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, comment='用户ID')
    openid = db.Column(db.String(128), unique=True, nullable=True, comment='微信 openid')
    phone = db.Column(db.String(20), unique=True, nullable=True, comment='手机号')
    password_hash = db.Column(db.String(255), nullable=True, comment='密码哈希值')
    nickname = db.Column(db.String(100), nullable=True, comment='昵称')
    avatar_url = db.Column(db.String(500), nullable=True, comment='头像 URL')
    student_id = db.Column(db.String(20), unique=True, nullable=True, comment='学号')
    real_name = db.Column(db.String(100), nullable=True, comment='真实姓名')
    credit_score = db.Column(db.Integer, default=100, comment='信用积分 (初始100分)')
    status = db.Column(db.Integer, default=1, comment='用户状态 (1-正常, 0-禁用)')
    last_login = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    credit_flows = db.relationship('CreditFlow', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.openid or self.phone}>'
    
    def set_password(self, password):
        """设置密码（自动加密）"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """检查密码是否正确"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_private=False):
        """将用户对象转换为字典"""
        data = {
            'id': self.id,
            'openid': self.openid,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'student_id': self.student_id,
            'real_name': self.real_name,
            'credit_score': self.credit_score,
            'status': self.status,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_private:
            data['phone'] = self.phone
        return data

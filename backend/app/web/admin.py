"""
Web管理界面路由
"""
from flask import Blueprint, render_template, current_app
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
web_admin_bp = Blueprint('web_admin', __name__, url_prefix='/admin')


def require_web_admin(f):
    """Web管理员认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 这里可以添加真实的认证逻辑
        # 目前使用测试账户
        return f(*args, **kwargs)
    return decorated_function


@web_admin_bp.route('/', methods=['GET'])
@web_admin_bp.route('/dashboard', methods=['GET'])
@require_web_admin
def admin_dashboard():
    """管理员数据看板"""
    return render_template('admin.html')


@web_admin_bp.route('/login', methods=['GET'])
def admin_login():
    """管理员登录页面"""
    return render_template('admin_login.html')

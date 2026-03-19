"""
Flask 应用工厂函数
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import config_by_name
from app.models import db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    """
    Flask 应用工厂函数
    
    Args:
        config_name: 配置名称，支持 'development', 'testing', 'production'
                    如果不指定，使用环境变量 FLASK_ENV，默认 'development'
    
    Returns:
        Flask 应用实例
    """
    
    # 确定配置
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_name = config_name.lower()
    if config_name not in config_by_name:
        config_name = 'development'
    
    logger.info(f'Creating Flask app with config: {config_name}')
    
    # 创建 Flask 应用
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config_by_name[config_name])
    
    # 初始化扩展
    db.init_app(app)
    CORS(app)  # 启用 CORS
    Migrate(app, db)  # 数据库迁移
    
    # 注册蓝图
    _register_blueprints(app)
    
    # 创建 app context 并创建数据库表
    with app.app_context():
        db.create_all()
        logger.info('Database tables created')
    
    # 注册错误处理器
    _register_error_handlers(app)
    
    logger.info('Flask app created successfully')
    
    return app


def _register_blueprints(app: Flask):
    """
    注册蓝图
    
    Args:
        app: Flask 应用实例
    """
    from app.auth.blueprint import auth_bp
    from app.auth.simple import simple_auth_bp
    from app.auth.mini_program import mini_program_auth_bp
    from app.api.reservation import reservation_bp
    from app.api.user import user_bp
    from app.api.admin import admin_bp
    from app.api.management import management_bp
    from app.api.rooms import rooms_bp
    from app.web.admin import web_admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(simple_auth_bp)
    app.register_blueprint(mini_program_auth_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(management_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(web_admin_bp)
    logger.info('Blueprints registered: auth, simple_auth, mini_program_auth, reservation, user, admin, management, rooms, web_admin')


def _register_error_handlers(app: Flask):
    """
    注册错误处理器
    
    Args:
        app: Flask 应用实例
    """
    from app.utils import ApiResponse
    
    @app.errorhandler(404)
    def not_found(error):
        """处理 404 错误"""
        return ApiResponse.not_found('Resource not found'), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """处理 405 错误"""
        return ApiResponse.error('Method not allowed', code=405), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """处理 500 错误"""
        logger.error(f'Internal server error: {str(error)}')
        return ApiResponse.server_error('Internal server error'), 500
    
    logger.info('Error handlers registered')

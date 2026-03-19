"""
Flask 应用入口
"""
import os
from dotenv import load_dotenv
from app import create_app

# 加载 .env 文件
load_dotenv()

# 创建应用实例
app = create_app()


if __name__ == '__main__':
    """
    本地开发时运行此文件启动服务器
    
    使用方法:
        python run.py
    
    或者使用 Flask CLI:
        flask run
    
    访问地址: http://localhost:5000
    """
    host = os.getenv('API_HOST', '127.0.0.1')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f'Starting Flask server at http://{host}:{port}')
    print(f'Debug mode: {debug}')
    
    app.run(host=host, port=port, debug=debug, use_reloader=True)

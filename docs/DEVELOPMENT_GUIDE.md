# Flask 后端开发指南

## 🎯 目标

本指南旨在帮助开发者快速上手 Flask 项目，了解项目结构、开发流程和最佳实践。

---

## 📚 开发流程

### 1. 项目初始化

```bash
# 1.1 克隆/进入项目目录
cd c:\Users\30794\Desktop\毕业设计

# 1.2 创建虚拟环境
python -m venv venv

# 1.3 激活虚拟环境
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 1.4 安装依赖
pip install -r requirements.txt

# 1.5 配置环境变量
# 编辑 .env 文件
```

### 2. 数据库初始化

```bash
# 创建数据库（在 MySQL 中）
mysql -u root -p -e "CREATE DATABASE library_reservation CHARACTER SET utf8mb4;"

# 初始化表和示例数据
python init_db.py
```

### 3. 启动开发服务器

```bash
# 方式 1：直接运行
python run.py

# 方式 2：使用 Flask CLI
set FLASK_APP=run.py
set FLASK_ENV=development
flask run

# 方式 3：调试模式
flask run --debug
```

访问 http://127.0.0.1:5000

---

## 🏗️ 添加新功能的步骤

### 例：添加座位预约功能

#### Step 1: 添加新的路由处理器

在 `app/auth/blueprint.py` 中添加新的接口，或在其他地方创建新的蓝图：

```python
# app/reservations/blueprint.py
from flask import Blueprint, request, jsonify, current_app
from app.models import db, Reservation, Seat
from app.utils import ApiResponse
from app.auth import AuthService

reservations_bp = Blueprint('reservations', __name__, url_prefix='/api/v1/reservations')

@reservations_bp.route('/create', methods=['POST'])
def create_reservation():
    """创建预约"""
    try:
        # 获取请求数据
        data = request.get_json() or {}
        user_id = request.user_id  # 从 JWT token 获取
        seat_id = data.get('seat_id')
        reservation_date = data.get('reservation_date')
        reservation_time = data.get('reservation_time')
        
        # 数据验证
        if not all([seat_id, reservation_date, reservation_time]):
            return jsonify(ApiResponse.bad_request('Missing required fields')), 400
        
        # 创建预约
        reservation = Reservation(
            user_id=user_id,
            seat_id=seat_id,
            room_id=...,  # 从座位信息获取
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            status=0  # 预约中
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        return jsonify(ApiResponse.success(
            data=reservation.to_dict(),
            message='Reservation created'
        )), 201
        
    except Exception as e:
        logger.error(f'Error creating reservation: {str(e)}')
        return jsonify(ApiResponse.server_error()), 500
```

#### Step 2: 在应用工厂中注册蓝图

编辑 `app/__init__.py` 的 `_register_blueprints` 函数：

```python
def _register_blueprints(app: Flask):
    """注册蓝图"""
    from app.auth.blueprint import auth_bp
    from app.reservations.blueprint import reservations_bp  # 新增
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(reservations_bp)  # 新增
    logger.info('Blueprints registered')
```

#### Step 3: 添加测试

在 `tests/test_reservations.py` 中添加测试：

```python
def test_create_reservation():
    """测试创建预约"""
    with app.test_client() as client:
        response = client.post('/api/v1/reservations/create', json={
            'seat_id': 1,
            'reservation_date': '2026-03-20',
            'reservation_time': '08:00-10:00'
        }, headers={
            'Authorization': f'Bearer {token}'
        })
        assert response.status_code == 201
```

---

## 🔄 数据库迁移

### 使用 Flask-Migrate

```bash
# 初始化迁移环境（仅需一次）
flask db init

# 创建新的迁移脚本
flask db migrate -m "Add new column"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 手动修改数据库

如果不使用迁移工具：

```python
# 在 Python 中直接操作

from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    # 添加新列
    # ALTER TABLE users ADD COLUMN new_column VARCHAR(100);
    
    # 删除表
    # db.drop_all()
    
    # 重建表
    # db.create_all()
    pass
```

---

## 🔑 认证装饰器使用

### 使用 `@auth_instance.login_required` 装饰器

```python
from app.auth import AuthService
from app.utils import JWTHandler
from flask import current_app

# 在蓝图中使用
@reservations_bp.route('/my-reservations', methods=['GET'])
@auth_instance.login_required
def get_my_reservations():
    """获取我的预约列表"""
    user_id = request.user_id  # 从装饰器获得
    user_info = request.token_payload  # 完整的 token 信息
    
    reservations = Reservation.query.filter_by(user_id=user_id).all()
    return jsonify(ApiResponse.success(
        data=[r.to_dict() for r in reservations]
    ))
```

### 手动验证 Token

```python
from app.auth import AuthService
from app.utils import JWTHandler

jwt_handler = JWTHandler(
    secret_key=current_app.config['JWT_SECRET_KEY'],
    algorithm=current_app.config['JWT_ALGORITHM']
)

token = request.headers.get('Authorization', '').replace('Bearer ', '')
payload = jwt_handler.verify_token(token)

if not payload:
    return jsonify(ApiResponse.unauthorized()), 401

user_id = payload['user_id']
```

---

## 📝 代码规范

### 命名规范

```python
# 模块名：小写 + 下划线
# 类名：PascalCase
class ReservationService:
    pass

# 函数名：小写 + 下划线
def create_reservation():
    pass

# 常量名：大写 + 下划线
DEFAULT_TIMEOUT = 30
```

### 文档字符串

```python
def create_reservation(user_id: int, seat_id: int) -> Reservation:
    """
    创建预约
    
    Args:
        user_id: 用户ID
        seat_id: 座位ID
    
    Returns:
        新创建的 Reservation 对象
    
    Raises:
        ValueError: 如果座位不可用
    """
    pass
```

### 类型提示

```python
from typing import Optional, List, Dict, Any

def query_reservations(user_id: int) -> List[Dict[str, Any]]:
    """查询预约列表"""
    pass

def get_user(user_id: int) -> Optional[User]:
    """获取用户，不存在返回 None"""
    pass
```

---

## 🐛 调试技巧

### 1. 启用 SQL 日志

```python
# app/config.py
SQLALCHEMY_ECHO = True  # 会打印所有 SQL 语句
```

### 2. 启用调试模式

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run
```

### 3. 使用 Python Debugger

```python
import pdb

@app.route('/debug')
def debug_route():
    pdb.set_trace()  # 程序会在此暂停
    return 'debug'
```

### 4. 查看日志

```python
import logging

logger = logging.getLogger(__name__)

logger.debug('调试信息')
logger.info('普通信息')
logger.warning('警告信息')
logger.error('错误信息')
logger.critical('严重错误')
```

---

## ✅ 最佳实践

### 1. 使用模型的 to_dict() 方法

```python
# ✅ 好的做法
user = User.query.get(1)
data = user.to_dict()
return jsonify(data)

# ❌ 不好的做法
return jsonify({
    'id': user.id,
    'name': user.name,
    # 重复代码...
})
```

### 2. 统一错误响应

```python
# ✅ 好的做法
from app.utils import ApiResponse
return jsonify(ApiResponse.error('User not found')), 404

# ❌ 不好的做法
return jsonify({'error': 'User not found'}), 404
```

### 3. 使用蓝图组织路由

```python
# ✅ 好的做法
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
reservations_bp = Blueprint('reservations', __name__, url_prefix='/api/v1/reservations')
# 然后在 __init__.py 中注册

# ❌ 不好的做法
# 所有路由都在一个文件中
```

### 4. 数据验证

```python
# ✅ 好的做法
data = request.get_json() or {}
user_id = data.get('user_id')
if not user_id:
    return jsonify(ApiResponse.bad_request('Missing user_id')), 400

# ❌ 不好的做法
user_id = data['user_id']  # 如果缺失会抛出异常
```

---

## 🔒 安全建议

### 1. 输入验证

```python
from marshmallow import Schema, fields, ValidationError

class ReservationSchema(Schema):
    user_id = fields.Int(required=True)
    seat_id = fields.Int(required=True)
    reservation_date = fields.Date(required=True)

schema = ReservationSchema()
try:
    data = schema.load(request.json)
except ValidationError as err:
    return jsonify(err.messages), 400
```

### 2. SQL 注入防护

```python
# ✅ 好的做法（ORM 自动防护）
user = User.query.filter_by(openid=openid).first()

# ❌ 不好的做法（易被注入）
# query = f"SELECT * FROM users WHERE openid = '{openid}'"
```

### 3. 敏感信息

```python
# ✅ 使用环境变量存储敏感信息
SECRET_KEY = os.getenv('SECRET_KEY')

# ❌ 不要硬编码
# SECRET_KEY = 'my-secret-key-123'
```

---

## 📦 依赖管理

### 添加新的依赖包

```bash
# 1. 安装包
pip install new-package

# 2. 更新 requirements.txt
pip freeze > requirements.txt

# 3. 提交到版本控制
git add requirements.txt
```

### 删除不需要的依赖

```bash
# 1. 卸载包
pip uninstall old-package

# 2. 更新 requirements.txt
pip freeze > requirements.txt
```

---

## 🚀 性能优化

### 1. 数据库查询优化

```python
# ✅ 使用 eager loading
user = User.query.options(db.joinedload(User.reservations)).get(1)

# ❌ N+1 查询问题
reservations = []
for user in User.query.all():
    reservations.extend(user.reservations)
```

### 2. 缓存使用

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_popular_seats():
    """缓存热门座位"""
    return Seat.query.filter_by(status=1).all()
```

### 3. 数据库索引

```python
# models 中添加索引
class Reservation(db.Model):
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'reservation_date'),
    )
```

---

## 📚 常用命令速查

```bash
# 开发服务器
python run.py
flask run

# 数据库
python init_db.py
flask db migrate
flask db upgrade

# 测试
python tests/test_auth.py
pytest

# 依赖管理
pip install -r requirements.txt
pip freeze > requirements.txt
```

---

## 🔗 相关资源

- [Flask 官方文档](https://flask.palletsprojects.com/)
- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [PyJWT 官方文档](https://pyjwt.readthedocs.io/)
- [Flask-CORS 官方文档](https://flask-cors.readthedocs.io/)

---

**最后更新**: 2026-03-17

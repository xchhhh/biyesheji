# 项目完整目录结构和说明

## 📁 最终的项目目录结构

```
毕业设计/
├── app/                                    # Flask 应用主包
│   ├── __init__.py                        # 应用工厂函数（核心！）
│   ├── config.py                          # 配置管理（支持多种环境）
│   │
│   ├── models/                            # 数据模型层（ORM）
│   │   ├── __init__.py                   # 数据库实例和模型导入
│   │   ├── user.py                       # 用户模型
│   │   ├── seat.py                       # 座位模型
│   │   ├── reading_room.py               # 阅览室模型
│   │   ├── reservation.py                # 预约记录模型
│   │   └── credit_flow.py                # 信用积分流水模型
│   │
│   ├── auth/                              # 认证模块（核心功能）
│   │   ├── __init__.py                   # 认证服务和装饰器
│   │   └── blueprint.py                  # 认证蓝图（登录、token etc）
│   │
│   ├── utils/                             # 工具函数层
│   │   ├── __init__.py                   # 工具导入
│   │   ├── wechat.py                     # 微信 API 交互
│   │   ├── jwt_handler.py                # JWT Token 处理
│   │   └── response.py                   # 统一响应格式
│   │
│   └── api/                               # API 接口（预留，后续扩展）
│       ├── __init__.py
│       └── v1/                            # API v1 版本
│           └── __init__.py
│
├── tests/                                 # 测试模块
│   └── test_auth.py                      # 认证功能测试
│
├── migrations/                            # 数据库迁移（Flask-Migrate）
│   ├── versions/
│   ├── env.py
│   ├── alembic.ini
│   └── script.py.mako
│
├── run.py                                 # 项目主入口（启动服务器）
├── init_db.py                             # 数据库初始化脚本
├── requirements.txt                       # Python 依赖列表
├── .env                                   # 环境变量配置（私密，需填写）
├── .env.example                           # 环境变量示例（模板）
├── .gitignore                             # Git 忽略文件
│
└── 📄 文档文件
    ├── BACKEND_SETUP.md                  # 后端项目配置指南（快速开始）
    ├── API_DOCUMENTATION.md              # API 完整文档和小程序示例代码
    ├── DATABASE_STRUCTURE.md             # 数据库结构详细说明（已存在）
    ├── database_design.md                # 数据库设计（已存在）
    ├── high_concurrency_reservation.py   # 高并发预约处理（Redis）
    ├── redis_cache.py                    # Redis 缓存策略
    └── SYSTEM_ARCHITECTURE.md            # 系统整体架构（已存在）
```

---

## 🗂️ 各层级说明

### 1️⃣ Models 层（app/models/）
**职责**：数据持久化和 ORM 映射

- **db.py**: SQLAlchemy 数据库实例
- **user.py**: 用户表模型
- **seat.py**: 座位表模型
- **reading_room.py**: 阅览室表模型
- **reservation.py**: 预约记录表模型
- **credit_flow.py**: 信用积分流水表模型

**关键特性**：
- ✅ 完整的表关系定义（FK, relationships）
- ✅ 数据验证和约束
- ✅ 中文注释和文档字符串
- ✅ to_dict() 方法便于序列化

---

### 2️⃣ Auth 层（app/auth/）
**职责**：处理用户身份认证

- **__init__.py**: AuthService 和 login_required 装饰器
- **blueprint.py**: 认证路由和接口实现

**提供的接口**：
- `POST /api/v1/auth/login` - 微信登录
- `POST /api/v1/auth/verify-token` - 验证 token
- `POST /api/v1/auth/refresh-token` - 刷新 token

---

### 3️⃣ Utils 层（app/utils/）
**职责**：通用工具和服务

- **wechat.py**: 微信接口交互（code2session）
- **jwt_handler.py**: JWT Token 生成和验证
- **response.py**: API 统一响应格式

---

### 4️⃣ Config 层（app/config.py）
**职责**：配置管理（多环境支持）

**支持的环境**：
- `development` - 开发环境（默认）
- `testing` - 测试环境
- `production` - 生产环境

**配置内容**：
- 数据库连接
- Redis 连接
- JWT 密钥和过期时间
- 微信 API 配置

---

## 🚀 快速启动流程

```
1. 安装依赖
   pip install -r requirements.txt
   
2. 配置环境变量
   编辑 .env 文件，填入你的配置
   
3. 初始化数据库
   python init_db.py
   
4. 启动服务器
   python run.py
   
5. 访问服务
   http://127.0.0.1:5000/api/v1/auth/login
```

---

## 📦 主要依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| Flask | 2.3.0 | Web 框架 |
| Flask-SQLAlchemy | 3.0.3 | ORM 框架 |
| Flask-Migrate | 4.0.4 | 数据库迁移 |
| PyJWT | 2.8.1 | JWT Token 处理 |
| requests | 2.31.0 | HTTP 请求 |
| PyMySQL | 1.1.0 | MySQL 驱动 |
| python-dotenv | 1.0.0 | 环境变量管理 |
| Flask-CORS | 4.0.0 | 跨域资源共享 |

---

## 🔑 关键文件说明

### run.py - 项目入口
```python
# 启动开发服务器
python run.py

# 或使用 Flask CLI
flask run

# 生产环境使用 gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'
```

### init_db.py - 数据库初始化
```python
# 创建所有表和示例数据
python init_db.py
```

### config.py - 配置文件
```python
# 支持三种环境
FLASK_ENV=development   # 开发
FLASK_ENV=testing       # 测试
FLASK_ENV=production    # 生产
```

---

## 📝 代码架构模式

### 工厂模式（Factory Pattern）
```python
# app/__init__.py
def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    return app
```

### 蓝图模式（Blueprint Pattern）
```python
# app/auth/blueprint.py
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    pass
```

### 装饰器模式（Decorator Pattern）
```python
# app/auth/__init__.py
@auth_instance.login_required
def protected_route():
    pass
```

---

## 🔐 安全特性

✅ **JWT Token 验证**
- 支持 Authorization Header
- Token 过期时间管理
- Token 刷新机制

✅ **CORS 支持**
- 允许跨域请求
- 可配置允许的源

✅ **错误处理**
- 统一错误响应格式
- 详细的错误日志

✅ **环境变量管理**
- .env 文件管理敏感信息
- 支持开发/测试/生产环境

---

## 📊 下一阶段计划

### Phase 2 - 核心业务功能
- [ ] 座位预约接口
- [ ] 座位查询接口
- [ ] 预约取消接口
- [ ] 座位签到/签出接口

### Phase 3 - 数据看板
- [ ] 用户统计数据
- [ ] 座位热力图
- [ ] 预约趋势分析

### Phase 4 - 高并发优化
- [ ] Redis 缓存集成
- [ ] 座位库存管理
- [ ] 秒杀场景优化

---

## 🔗 文件关系图

```
run.py (入口)
  ↓
app/__init__.py (工厂函数)
  ├─ config.py (配置)
  ├─ models/__init__.py (数据库)
  │  ├─ user.py
  │  ├─ seat.py
  │  ├─ reading_room.py
  │  ├─ reservation.py
  │  └─ credit_flow.py
  ├─ auth/blueprint.py (路由)
  │  └─ auth/__init__.py (认证服务)
  │     ├─ utils/jwt_handler.py
  │     └─ utils/wechat.py
  └─ utils/response.py (响应)
```

---

## 💡 使用建议

### 1. 开发时
- 启用 DEBUG 模式：`FLASK_ENV=development`
- 使用 Flask CLI：`flask run`
- 查看 SQL 日志：`SQLALCHEMY_ECHO=True`

### 2. 测试时
- 使用内存数据库：`SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'`
- 运行单元测试：`python tests/test_auth.py`

### 3. 部署时
- 使用生产配置：`FLASK_ENV=production`
- 使用 Gunicorn：`gunicorn -w 4 run.py`
- 启用 HTTPS
- 隐藏调试信息

---

**最后更新**: 2026-03-17
**作者**: AI 助手
**版本**: 1.0

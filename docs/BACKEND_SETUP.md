# Flask 项目骨架与用户认证 - 完整设置指南

## 📋 项目结构

```
毕业设计/
├── app/                           # Flask 应用包
│   ├── __init__.py               # 应用工厂函数
│   ├── config.py                 # 配置文件
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py              # 用户模型
│   │   ├── seat.py              # 座位模型
│   │   ├── reading_room.py       # 阅览室模型
│   │   ├── reservation.py        # 预约记录模型
│   │   └── credit_flow.py        # 信用积分流水模型
│   ├── auth/                     # 认证模块
│   │   ├── __init__.py          # 认证服务
│   │   └── blueprint.py         # 认证蓝图（登录、验证token等）
│   ├── utils/                    # 工具模块
│   │   ├── __init__.py
│   │   ├── wechat.py            # 微信接口工具
│   │   ├── jwt_handler.py        # JWT Token 处理
│   │   └── response.py           # 统一响应格式
│   └── api/                      # API 模块（预留）
├── tests/                        # 测试文件
│   └── test_auth.py             # 认证测试
├── run.py                        # 应用入口
├── requirements.txt              # 项目依赖
├── .env                         # 环境变量配置（需要修改）
├── .env.example                 # 环境变量示例
└── 项目文档/
    ├── BACKEND_SETUP.md         # 本文件
    ├── database_design.md       # 数据库设计文档
    └── API_DOCUMENTATION.md     # API 文档（后续）

```

## 🚀 快速开始

### 1. 克隆或创建项目
```bash
cd c:\Users\30794\Desktop\毕业设计
```

### 2. 创建虚拟环境
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# 或 cmd
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
# 复制 .env.example 为 .env
copy .env.example .env

# 编辑 .env 文件，填入你的配置：
# - MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD
# - WECHAT_APPID, WECHAT_SECRET
# - JWT_SECRET_KEY
# - 其他配置项
```

### 5. 初始化数据库
```bash
# 确保 MySQL 服务正在运行
# 创建数据库
mysql -u root -p -e "CREATE DATABASE library_reservation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 运行初始化脚本创建表
python init_db.py
```

### 6. 启动应用
```bash
python run.py
```

服务器将在 http://127.0.0.1:5000 上运行

## 🔐 核心功能说明

### 用户认证模块 (app/auth/)

#### 1. 微信登录接口 (`/api/v1/auth/login`)

**功能**：接收微信小程序的授权 code，完成用户登录

**请求**：
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
    "code": "021ZXX..."  # 微信小程序授权返回的 code
}
```

**响应成功 (200)**：
```json
{
    "code": 200,
    "message": "Login successful",
    "data": {
        "user_id": 1,
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "id": 1,
            "openid": "openid_value",
            "nickname": "User_xxxx",
            "avatar_url": null,
            "student_id": null,
            "real_name": null,
            "credit_score": 100,
            "status": 1,
            "last_login": "2026-03-17T10:20:30",
            "created_at": "2026-03-17T10:20:30"
        }
    },
    "success": true
}
```

**响应错误 (400/500)**：
```json
{
    "code": 400,
    "message": "Missing code parameter",
    "data": null,
    "success": false
}
```

#### 2. Token 验证接口 (`/api/v1/auth/verify-token`)

**功能**：验证 JWT Token 的有效性

**请求**：
```bash
POST /api/v1/auth/verify-token
Content-Type: application/json

{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**响应**：
```json
{
    "code": 200,
    "message": "Token is valid",
    "data": {
        "user_id": 1,
        "openid": "openid_value",
        "valid": true
    },
    "success": true
}
```

#### 3. Token 刷新接口 (`/api/v1/auth/refresh-token`)

**功能**：使用旧 token 生成新 token（即使旧 token 已过期）

**请求**：
```bash
POST /api/v1/auth/refresh-token
Content-Type: application/json

{
    "token": "old-token-string"
}
```

**响应**：
```json
{
    "code": 200,
    "message": "Token refreshed successfully",
    "data": {
        "token": "new-token-string"
    },
    "success": true
}
```

## 🔑 JWT Token 使用说明

### 在 HTTP 请求中使用 Token

支持三种方式传递 token：

1. **Authorization Header（推荐）**
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

2. **URL 参数**
```bash
GET /api/v1/protected?token=eyJ0eXAiOiJKV1QiLCJhbGc...
```

3. **JSON Body**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "other_param": "value"
}
```

### Token 结构

JWT Token 包含以下信息：
```python
{
    "user_id": 1,           # 用户ID
    "openid": "openid_xxx", # 微信 openid
    "credit_score": 100,    # 信用积分
    "iat": 1710730830,      # 签发时间
    "exp": 1710738030       # 过期时间（默认 7200 秒后）
}
```

## 🛠️ 技术栈

| 组件 | 说明 |
|------|------|
| **Flask** | Web框架 |
| **Flask-SQLAlchemy** | ORM 框架 |
| **Flask-Migrate** | 数据库迁移工具 |
| **PyJWT** | JWT Token 处理 |
| **requests** | HTTP 请求库 |
| **PyMySQL** | MySQL 驱动 |
| **python-dotenv** | 环境变量管理 |
| **Flask-CORS** | 跨域资源共享 |

## 📝 数据库配置

### MySQL 连接字符串格式
```
mysql+pymysql://username:password@host:port/database?charset=utf8mb4
```

### 例子
```
mysql+pymysql://root:mypassword@localhost:3306/library_reservation?charset=utf8mb4
```

## 🧪 测试

### 运行测试
```bash
python tests/test_auth.py
```

### 使用 curl 测试登录接口
```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code": "your-wechat-code"}'
```

## 🐛 常见问题

### 1. 数据库连接失败
- 检查 MySQL 服务是否启动
- 检查 .env 中的数据库配置是否正确
- 检查数据库用户名和密码

### 2. 微信登录返回错误
- 确认 WECHAT_APPID 和 WECHAT_SECRET 正确
- 检查网络连接和防火墙
- 查看服务器日志获取详细错误信息

### 3. Token 验证失败
- 确保 JWT_SECRET_KEY 配置正确
- 检查 token 是否已过期
- 确保 token 格式正确

## 📞 支持的认证指标

- ✅ 微信小程序登录
- ✅ JWT Token 生成和验证
- ✅ Token 刷新功能
- ✅ 信用积分系统集成
- ✅ 用户信息管理
- ✅ 错误统一响应格式

## 🔄 下一步

1. **预约管理接口**：实现座位预约、查询、取消等功能
2. **座位展示接口**：获取座位状态和热力图数据
3. **违规记录模块**：处理迟到、缺座等违规行为
4. **数据看板**：提供统计数据接口
5. **Redis 缓存**：集成高并发场景下的缓存策略

## 📚 相关文档

- [数据库设计文档](database_design.md) - 详细的表结构和关系说明
- [高并发预约处理](high_concurrency_reservation.py) - Redis 缓存策略
- [系统架构文档](SYSTEM_ARCHITECTURE.md) - 整体系统设计

---

**最后更新**: 2026-03-17

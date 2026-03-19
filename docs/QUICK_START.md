# 🚀 快速启动指南

## 📋 目录
1. [系统需求](#系统需求)
2. [后端启动](#后端启动)
3. [小程序测试](#小程序测试)
4. [功能演示](#功能演示)
5. [常见问题](#常见问题)

---

## 系统需求

### 软件要求
- Python 3.8 或更高版本
- Flask 3.1.2
- SQLite 3
- 微信小程序开发者工具

### 依赖包
```bash
pip install -r requirements.txt
```

主要依赖：
- Flask 3.1.2
- Flask-SQLAlchemy 3.1.1
- Flask-CORS 4.0.0
- Flask-Migrate
- PyJWT
- Werkzeug (密码加密)
- Requests 2.32.5

### 系统架构
```
┌──────────────────────────┐
│   微信小程序前端         │
│  (mini-program/)         │
└────────────┬─────────────┘
             │ HTTP请求
             │ /api/auth/login
             │ /api/auth/register
             ↓
┌──────────────────────────┐
│   Flask 后端服务        │
│  (http://127.0.0.1:5000) │
└────────────┬─────────────┘
             │
             ↓
┌──────────────────────────┐
│   SQLite 数据库         │
│  (library_reservation.db) │
└──────────────────────────┘
```

---

## 后端启动

### 步骤 1: 进入项目目录

```bash
cd c:\Users\30794\Desktop\毕业设计
```

### 步骤 2: 启动 Flask 服务

```bash
python run.py
```

**预期输出**:
```
Creating Flask app with config: development
Blueprints registered: auth, mini_program_auth, reservation, admin
Database tables created
Starting Flask server at http://127.0.0.1:5000
Debug mode: True
Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### 步骤 3: 验证服务运行

**在 PowerShell 中运行**：
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/register" -Method OPTIONS
```

或者使用 curl.exe（Windows 10后内置）：
```bash
curl.exe http://127.0.0.1:5000/api/auth/register -X OPTIONS
```

或者使用 Python：
```python
import requests
response = requests.get("http://127.0.0.1:5000")
print(response.status_code)  # 应该返回 404 或 200
```

✅ 服务启动成功（返回200或404状态码）！

---

## 小程序测试

### 使用微信小程序开发者工具

1. **打开开发者工具**
   - 在微信小程序开发者工具中选择 "导入项目"
   - 选择路径: `c:\Users\30794\Desktop\毕业设计\mini-program`
   - 选择 AppID: 填入你的 AppID（或选择"不使用AppID"用于开发）

2. **确认后端地址**
   - 打开 `mini-program/app.js`
   - 查看 `globalData.apiUrl` 是否指向 `http://127.0.0.1:5000`

3. **启动预览**
   - 在开发者工具中点击 "预览"
   - 使用微信扫描二维码
   - 或在开发者工具中直接查看

### 页面导航
```
小程序首页
    ↓
[登录页面] (pages/login/login)
    ├─ 输入手机号和密码
    ├─ 点击"登录"
    └─ 或点击"去注册" → [注册页面]

[注册页面] (pages/register/register)
    ├─ 填写信息：
    │  ├─ 真实姓名
    │  ├─ 学号
    │  ├─ 手机号码
    │  ├─ 设置密码
    │  └─ 确认密码
    └─ 点击"完成注册" → 自动登录
    
[座位预约页面] (pages/seats/seats)
    └─ 浏览座位并预约
```

---

## 功能演示

### 演示 1: 用户注册

**步骤**:
1. 打开小程序 → 看到登录页面
2. 点击 "还没有账户？去注册"
3. 填写注册信息：
   - 真实姓名: `李四`
   - 学号: `2022002222`
   - 手机号: `13999999999`
   - 密码: `password123`
   - 确认密码: `password123`
4. 点击 "完成注册"

**预期结果**:
- ✅ 显示 "注册成功！"
- ✅ 自动跳转到座位预约页面
- ✅ Token 存储到本地

### 演示 2: 用户登录

**步骤**:
1. 打开小程序 → 看到登录页面
2. 填写登录信息：
   - 手机号: `13999999999`
   - 密码: `password123`
3. 勾选 "记住我"（可选）
4. 点击 "登录"

**预期结果**:
- ✅ 登录成功
- ✅ 跳转到座位预约页面
- ✅ 下次打开时自动填充手机号（如果选中记住我）

### 演示 3: 错误处理

**测试错误的手机号格式**:
1. 在注册页面输入: `123456`
2. 点击 "完成注册"
- ✅ 显示错误: "请输入有效的手机号码"

**测试密码不匹配**:
1. 密码: `password123`
2. 确认密码: `password456`
3. 点击 "完成注册"
- ✅ 显示错误: "两次输入的密码不一致"

**测试已注册的手机号**:
1. 用已注册的手机号尝试注册
2. 点击 "完成注册"
- ✅ 显示错误: "既有账户"

---

## 接口测试

### 快速测试脚本（推荐）

使用 PowerShell 测试脚本（无需手动输入命令）：

```powershell
powershell -ExecutionPolicy Bypass -File "test_api.ps1"
```

这个脚本会自动测试：
- ✅ 用户注册
- ✅ 用户登录
- ✅ 错误密码拒绝
- ✅ 重复注册拒绝

### 使用 Python 测试

```python
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# 1. 注册
register_data = {
    "phone_number": "13888888888",
    "password": "test123456",
    "real_name": "张三",
    "student_id": "2022001111"
}

response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json=register_data
)

print("Register Response:", response.status_code)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 2. 登录
login_data = {
    "phone_number": "13888888888",
    "password": "test123456"
}

response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json=login_data
)

print("\nLogin Response:", response.status_code)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### 使用 PowerShell 手动测试

**注册**:
```powershell
$body = @{
    phone_number = "13888888888"
    password = "test123456"
    real_name = "张三"
    student_id = "2022001111"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing
```

**登录**:
```powershell
$body = @{
    phone_number = "13888888888"
    password = "test123456"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing
```

### 使用 cURL 测试（需要 curl.exe）

```bash
# 注册
curl.exe -X POST http://127.0.0.1:5000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"phone_number\":\"13888888888\",\"password\":\"test123456\",\"real_name\":\"张三\",\"student_id\":\"2022001111\"}"

# 登录
curl.exe -X POST http://127.0.0.1:5000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"phone_number\":\"13888888888\",\"password\":\"test123456\"}"
```

---

## 常见问题

### Q1: 后端无法启动？

**错误**: ModuleNotFoundError: No module named 'flask'

**解决**:
```bash
pip install -r requirements.txt
```

---

### Q2: 数据库连接失败？

**错误**: sqlite3.OperationalError: database is locked

**解决**:
1. 关闭所有 python.exe 进程
2. 删除 `instance/library_reservation.db`
3. 重新启动服务

```bash
taskkill /IM python.exe /F
del instance\library_reservation.db
python run.py
```

---

### Q3: 小程序无法连接后端？

**现象**: 请求超时或显示"网络连接失败"

**检查列表**:
1. 后端服务是否运行？
   ```bash
   curl http://127.0.0.1:5000
   ```

2. 小程序中的 apiUrl 是否正确？
   ```javascript
   // app.js
   globalData: {
     apiUrl: 'http://127.0.0.1:5000'  // 检查这里
   }
   ```

3. 防火墙是否阻止了 5000 端口？
   - Windows: 检查防火墙设置
   - 允许 Python 程序通过防火墙

4. 是否使用了代理或VPN？
   - 某些代理可能阻止本地请求

---

### Q4: 注册成功但无法登录？

**可能原因**:
1. 密码输入错误
2. 手机号不匹配
3. 用户状态被禁用

**解决**:
1. 检查密码是否正确（大小写敏感）
2. 检查手机号是否匹配
3. 查看数据库中用户的 status 字段

```sql
SELECT id, phone, student_id, status FROM users WHERE phone='13888888888';
```

---

### Q5: Token 过期了怎么办？

**现象**: API 返回 401 错误

**原因**: Token 默认有效期为 24 小时

**解决**:
1. 重新登录获取新 Token
2. 小程序会自动清除旧 Token 并存储新 Token

```javascript
// 小程序会自动处理，无需手动操作
wx.setStorageSync('token', newToken)
```

---

### Q6: 如何查看日志？

运行服务时，所有日志会输出到终端：

```
2026-03-17 19:07:34,814 - app - INFO - Creating Flask app
2026-03-17 19:07:34,965 - app - INFO - Blueprints registered
2026-03-17 19:07:35,007 - werkzeug - INFO - Running on http://127.0.0.1:5000
```

对于长期运行，可以重定向到文件：

```bash
python run.py > server.log 2>&1
```

---

## 📊 测试数据

### 预设测试账户

| 手机号 | 密码 | 说明 |
|--------|------|------|
| 13888888888 | test123456 | 测试用户1 |

### 添加更多测试账户

使用 Python 脚本添加：

```python
import os
os.chdir(r'c:\Users\30794\Desktop\毕业设计')

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # 添加测试用户
    users = [
        User(
            phone="13999999999",
            real_name="李四",
            student_id="2022002222",
            nickname="李四",
            credit_score=100,
            status=1,
            openid="miniapp_13999999999"
        ),
        User(
            phone="13777777777",
            real_name="王五",
            student_id="2022003333",
            nickname="王五",
            credit_score=100,
            status=1,
            openid="miniapp_13777777777"
        ),
    ]
    
    for user in users:
        user.set_password("password123")
        db.session.add(user)
    
    db.session.commit()
    print("Test users added successfully!")
```

---

## 🔧 配置修改

### 修改服务器地址

编辑 `app.js`:
```javascript
App({
  globalData: {
    apiUrl: 'http://127.0.0.1:5000'  // 修改这里
  }
})
```

### 修改默认端口

编辑 `.env`:
```
API_HOST=127.0.0.1
API_PORT=8000  # 改为 8000 或其他端口
FLASK_ENV=development
```

### 修改数据库位置

编辑 `app/config.py`:
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///./instance/library_reservation.db'  # 修改路径
```

---

## 📈 性能优化建议

### 数据库优化
1. 为 phone 和 student_id 添加索引（已有）
2. 定期清理过期的 Token
3. 添加查询缓存

### 服务优化
1. 使用生产级 WSGI 服务器（如 Gunicorn）
2. 添加负载均衡
3. 启用 Redis 缓存

### 前端优化
1. 启用本地缓存
2. 减少 API 调用
3. 使用离线模式

---

## 🆘 获取帮助

如遇到问题，请检查：

1. **服务状态**
   ```bash
   curl http://127.0.0.1:5000/
   ```

2. **数据库状态**
   ```bash
   ls -la instance/
   ```

3. **日志**
   - 查看终端输出
   - 查看 Flask 日志

4. **相关文档**
   - [AUTH_TEST_REPORT.md](AUTH_TEST_REPORT.md) - 测试报告
   - [USER_GUIDE.md](mini-program/USER_GUIDE.md) - 用户指南
   - [REGISTRATION_GUIDE.md](REGISTRATION_GUIDE.md) - 注册指南

---

**最后更新**: 2026年3月17日  
**版本**: 1.0.0

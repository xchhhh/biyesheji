# 🧪 微信小程序本地测试完整指南

## 📋 前置条件检查

### ✅ 系统要求
- Windows 7 或更高版本
- Python 3.8+
- 微信开发者工具最新版本
- 文本编辑器（VS Code 推荐）

### ✅ 已安装的包
```bash
Flask==3.1.2
SQLAlchemy==2.0+
PyJWT==2.8+
python-dotenv==1.0+
```

---

## 🚀 第一步：启动后端服务

### 方案 A：直接运行（推荐开发时使用）

```bash
# 1. 进入项目目录
cd C:\Users\30794\Desktop\毕业设计

# 2. 启动 Flask 后端
python run.py
```

**预期输出：**
```
 * Running on http://127.0.0.1:5000
 * Debugger is active!
 * Debugger PIN: 847-852-703
```

### 方案 B：使用虚拟环境（推荐）

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python run.py
```

**✅ 后端启动后，继续下一步**

---

## 📱 第二步：安装和配置微信开发者工具

### 步骤 1：下载微信开发者工具
1. 访问 [微信官方下载](https://developers.weixin.qq.com/community/develop/tools/download)
2. 选择 **稳定版** 下载（Windows）
3. 安装到默认位置

### 步骤 2：打开项目

1. **打开微信开发者工具**
2. **选择"导入项目"**
3. **填写项目信息：**

| 字段 | 值 |
|------|-----|
| 项目路径 | `C:\Users\30794\Desktop\毕业设计\mini-program` |
| AppID | `wx1234567890abcdef` （本地测试用，暂不需要真实 AppID） |
| 项目名 | `Seat Reservation` |

4. **点击"导入"**

### 步骤 3：配置本地服务

1. 打开 **微信开发者工具** → **详情** 标签页
2. 勾选以下选项：
   - ✅ **不校验合法域名、web-view（仅开发者工具）**
   - ✅ **显示 wxml/wxss 代码本地修改提示**

---

## 🔗 第三步：配置后端地址

### 方法 1：使用本地服务（推荐）

编辑 `mini-program/utils/config.js`：

```javascript
// 当前配置（已是本地地址）
const API_BASE_URL = 'http://localhost:5000/api';
```

> 确保地址是 `http://localhost:5000` 或 `http://127.0.0.1:5000`

### 方法 2：使用真实服务器地址

如果要测试线上环境：
```javascript
const API_BASE_URL = 'http://your-server-address.com/api';
```

---

## 🧪 第四步：本地测试流程

### 测试 1：查看编译器

1. 打开微信开发者工具
2. 点击 **编译** 按钮
3. 查看 **编译器窗口** - 应该显示登录界面

**预期：**
```
✅ 页面加载，显示登录表单
✅ 输入框、按钮都可见
```

### 测试 2：测试用户注册

1. 在编译器中点击 **注册** 按钮
2. 填写表单：
   - 手机号：`13800000001`
   - 密码：`password123`
   - 确认密码：`password123`
   - 姓名：`测试用户`
   - 学号：`2022008888`

3. 点击 **注册**

**预期结果：**
```
✅ 提示 "注册成功"
✅ 自动跳转到登录页面
✅ 开发者工具的 Console 标签无错误
```

### 测试 3：测试用户登录

1. 使用刚注册的账号登录：
   - 手机号：`13800000001`
   - 密码：`password123`

2. 点击 **登录**

**预期结果：**
```
✅ 提示 "登录成功"
✅ 跳转到座位预约页面
✅ 显示座位网格
```

### 测试 4：查看座位和预约

1. 在座位页面中：
   - 查看座位网格展示
   - 尝试点击可用座位
   - 查看预约流程

**预期结果：**
```
✅ 座位网格正常显示
✅ 可以选择座位
✅ 提交预约表单
```

---

## 🐛 常见问题排查

### 问题 1：无法连接到后端（Network Error）

**症状：**
```
错误：Cannot POST http://localhost:5000/api/auth/register
```

**解决方案：**
1. ✅ 确保 `python run.py` 正在运行
2. ✅ 检查 Flask 是否显示 `Running on http://127.0.0.1:5000`
3. ✅ 在 config.js 中验证 API_BASE_URL 正确性
4. ✅ 微信开发者工具勾选了 "不校验合法域名"

### 问题 2：跨域错误（CORS Error）

**症状：**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**解决方案：**
- 后端已启用 CORS（在 Flask 中配置）
- 微信开发者工具需要勾选 "不校验合法域名"

### 问题 3：显示 404 页面

**症状：**
- 点击按钮无反应或显示 404 错误

**检查清单：**
1. 后端是否运行？运行 `powershell -File test_api.ps1` 测试
2. API 端点是否存在？

```powershell
# 快速 API 测试
$body = '{"phone_number":"13888888888","password":"test123"}'
Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

### 问题 4：手机号格式错误

**症状：**
```
错误：手机号格式不正确
```

**解决方案：**
- 输入有效的 11 位手机号（以 1 开头）
- 示例：`13800000001`

---

## 🛠️ 开发工具使用技巧

### 查看网络请求

1. **打开开发者工具**
2. **点击 Network 标签**
3. **执行操作（如登录）**
4. **查看请求和响应**

**查看内容：**
- Request Headers：请求头
- Request Body：请求体
- Response：服务器响应
- Status Code：HTTP 状态码

### 查看控制台日志

1. **点击 Console 标签**
2. **执行任何操作**
3. **查看 js 日志和错误**

### 调试本地代码

1. **右键点击页面元素** → **审查元素**
2. 可以查看 WXML 结构和样式
3. 实时编辑查看效果

---

## ✅ 完整测试流程检查清单

- [ ] 后端服务已启动（运行 run.py）
- [ ] 微信开发者工具已安装
- [ ] 项目已导入开发者工具
- [ ] 配置已勾选 "不校验合法域名"
- [ ] config.js 中 API_BASE_URL 正确
- [ ] 成功编译项目
- [ ] 测试用户注册流程
- [ ] 测试用户登录流程
- [ ] 查看座位页面
- [ ] Console 无错误

---

## 🚀 运行命令快速参考

### 启动后端
```bash
python run.py
```

### 测试 API（不打开小程序）
```powershell
powershell -ExecutionPolicy Bypass -File "test_api.ps1"
```

### 重启后端
```bash
# 先按 Ctrl+C 停止当前服务
# 然后重新运行
python run.py
```

---

## 📱 小程序主要页面

| 页面 | 路径 | 功能 |
|------|------|------|
| **登录页** | pages/login/login | 用户登录 |
| **注册页** | pages/register/register | 新用户注册 |
| **座位页** | pages/seats/seats | 座位预约的核心功能 |

---

## 💡 建议

1. **开发时保持两个窗口打开：**
   - PowerShell：运行 Flask 后端
   - 微信开发者工具：查看小程序界面

2. **修改代码后：**
   - 微信开发者工具会自动重新编译（如果启用自动编译）
   - 手动编译：Ctrl+B

3. **调试技巧：**
   - 在 JS 代码中使用 `console.log()` 输出调试信息
   - 在开发者工具的 Console 标签中查看

4. **快速测试不同场景：**
   - 使用 `test_api.ps1` 快速生成测试用户
   - 每次生成的手机号都是唯一的（基于时间戳）

---

**准备好了？现在就可以开始测试了！🎉**

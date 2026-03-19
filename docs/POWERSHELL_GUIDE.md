# 🪟 Windows PowerShell 快速测试指南

## 📋 概述

本指南提供了在 Windows PowerShell 中测试 API 的方法。避免了 PowerShell 中的 `curl` 别名问题，提供了原生 PowerShell 解决方案。

---

## ⚡ 快速开始

### 方式 1: 运行自动化测试脚本（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File "test_api.ps1"
```

**功能**:
- ✅ 自动注册测试用户
- ✅ 自动登录验证
- ✅ 测试错误处理
- ✅ 彩色输出结果

**预期输出**:
```
======================================================================
API Testing Script for WeChat Mini Program Auth System
======================================================================

[Test 1] Registering a new user...
[SUCCESS] User registered successfully!
User ID: 3
Phone: 13666666666

[Test 2] Logging in with the same credentials...
[SUCCESS] User logged in successfully!
User ID: 3
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

[Test 3] Testing with wrong password...
[SUCCESS] Wrong password correctly rejected!
Error message: Invalid phone number or password

[Test 4] Testing duplicate registration with same phone...
[SUCCESS] Duplicate phone correctly rejected!
Error message: Phone number already registered

======================================================================
All tests completed!
======================================================================
```

---

## 🔧 手动测试

### 1️⃣ 注册新用户

```powershell
$body = @{
    phone_number = "13888888888"
    password = "test123456"
    real_name = "TestUser"
    student_id = "2022001111"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing
```

**成功响应** (状态码 201):
```json
{
  "code": 201,
  "message": "User registered successfully",
  "data": {
    "user_id": 1,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "phone": "13888888888",
      "real_name": "TestUser",
      "student_id": "2022001111",
      "credit_score": 100
    }
  }
}
```

### 2️⃣ 用户登录

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

**成功响应** (状态码 200):
```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "user_id": 1,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "phone": "13888888888",
      "real_name": "TestUser",
      "student_id": "2022001111",
      "credit_score": 100
    }
  }
}
```

### 3️⃣ 错误处理 - 错误的密码

```powershell
$body = @{
    phone_number = "13888888888"
    password = "wrongpassword"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing
```

**错误响应** (状态码 401):
```json
{
  "code": 401,
  "message": "Invalid phone number or password",
  "error": "Authentication failed"
}
```

### 4️⃣ 错误处理 - 重复手机号

```powershell
$body = @{
    phone_number = "13888888888"
    password = "newpassword"
    real_name = "AnotherUser"
    student_id = "2022002222"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing
```

**错误响应** (状态码 400):
```json
{
  "code": 400,
  "message": "Phone number already registered",
  "error": "This phone number already has an account"
}
```

---

## 💡 PowerShell 技巧

### 保存响应到变量

```powershell
$response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing

$data = $response.Content | ConvertFrom-Json
$data.data.user_id      # 获取用户ID
$data.data.access_token # 获取Token
```

### 格式化输出

```powershell
# 美化 JSON 输出
$response.Content | ConvertFrom-Json | ConvertTo-Json | Write-Host

# 只显示特定字段
$data = $response.Content | ConvertFrom-Json
"User ID: $($data.data.user_id)"
"Token: $($data.data.access_token.Substring(0,50))..."
```

### 捕获错误

```powershell
try {
    $response = Invoke-WebRequest -Uri $uri `
      -Method POST `
      -Headers $headers `
      -Body $body `
      -UseBasicParsing `
      -ErrorAction Stop
    Write-Host "Success: $($response.StatusCode)" -ForegroundColor Green
} catch {
    $errorData = $_.Exception.Response.GetResponseStream() | `
      ForEach-Object { [System.IO.StreamReader]::new($_).ReadToEnd() } | `
      ConvertFrom-Json
    Write-Host "Error: $($errorData.message)" -ForegroundColor Red
}
```

### 循环测试多个用户

```powershell
$users = @(
    @{phone="13888888888"; password="test123456"; name="User1"; id="2022001111"},
    @{phone="13999999999"; password="test123456"; name="User2"; id="2022002222"},
    @{phone="13777777777"; password="test123456"; name="User3"; id="2022003333"}
)

foreach ($user in $users) {
    $body = @{
        phone_number = $user.phone
        password = $user.password
        real_name = $user.name
        student_id = $user.id
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/auth/register" `
      -Method POST `
      -Headers @{"Content-Type"="application/json"} `
      -Body $body `
      -UseBasicParsing
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "[$($user.phone)] Registered: User ID $($data.data.user_id)"
}
```

---

## 🆚 PowerShell vs cURL vs Python

| 特性 | PowerShell | cURL | Python |
|------|-----------|------|--------|
| 内置 | ✅ 是 | ⚠️ Win10+ | ❌ 需安装 |
| 语法 | PowerShell | Bash | Python |
| 易学性 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 自动化 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 跨平台 | ❌ | ✅ | ✅ |

---

## 📚 常用 Invoke-WebRequest 参数

```powershell
Invoke-WebRequest `
  -Uri "http://127.0.0.1:5000/api/auth/login"  # API地址
  -Method POST                                   # HTTP方法
  -Headers @{                                    # 请求头
      "Content-Type" = "application/json"
      "Authorization" = "Bearer $token"
  } `
  -Body $jsonBody                               # 请求主体
  -UseBasicParsing                              # 不解析HTML脚本
  -ErrorAction SilentlyContinue                 # 出错不中断
  -TimeoutSec 10                                # 超时10秒
```

---

## 🐛 常见问题

### Q1: "脚本执行风险"警告？

**解决**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

或在运行时指定:
```powershell
powershell -ExecutionPolicy Bypass -File "test_api.ps1"
```

### Q2: 如何在脚本中保存 Token？

```powershell
$response = Invoke-WebRequest ... -UseBasicParsing
$data = $response.Content | ConvertFrom-Json
$token = $data.data.access_token

# 存储到环境变量
$env:API_TOKEN = $token

# 在后续请求中使用
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $env:API_TOKEN"
}
```

### Q3: 如何处理 Unicode 字符（中文）？

```powershell
# 使用 -Encoding 参数
$response = Invoke-WebRequest ... -UseBasicParsing
$text = [System.Text.Encoding]::UTF8.GetString($response.Content)
$data = $text | ConvertFrom-Json
```

### Q4: 响应太慢？

检查网络连接：
```powershell
Test-Connection 127.0.0.1 -Count 1
```

增加超时时间：
```powershell
Invoke-WebRequest ... -TimeoutSec 30
```

### Q5: 无法连接后端？

检查服务是否运行：
```powershell
# 检查5000端口
netstat -ano | findstr :5000

# 或使用Test-NetConnection
Test-NetConnection -ComputerName 127.0.0.1 -Port 5000
```

---

## 📖 参考资源

- [PowerShell Invoke-WebRequest 文档](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-webrequest)
- [HTTP 状态码参考](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [JSON 和 ConvertTo-Json](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/convertto-json)

---

## ✅ 下一步

1. ✅ 运行 `test_api.ps1` 验证 API
2. ✅ 在小程序中测试登录和注册
3. ✅ 查看 [QUICK_START.md](QUICK_START.md) 获取更多信息
4. ✅ 查看 [USER_GUIDE.md](mini-program/USER_GUIDE.md) 了解用户流程

---

**版本**: 1.0.0  
**最后更新**: 2026年3月17日  
**平台**: Windows PowerShell 5.1+

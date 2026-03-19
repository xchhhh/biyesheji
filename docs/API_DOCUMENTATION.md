# 微信小程序 + Flask 后端认证流程完整指南

## 📚 完整的用户登录和认证流程

本文档详细描述了如何在微信小程序中使用后端提供的认证接口。

---

## 第一步：微信小程序端获取 Code

### 小程序端 JavaScript 代码示例

```javascript
// pages/login/login.js
Page({
  data: {
    isLogin: false,
    userInfo: null,
    token: null
  },

  // 点击登录按钮时调用
  onLogin: function() {
    wx.login({
      success: (res) => {
        if (res.code) {
          // 获取到授权 code，发送给后端
          this.sendCodeToBackend(res.code);
        } else {
          wx.showToast({
            title: '登录失败',
            icon: 'error'
          });
        }
      },
      fail: (err) => {
        console.error('wx.login failed:', err);
        wx.showToast({
          title: '登录失败',
          icon: 'error'
        });
      }
    });
  },

  // 发送 code 到后端
  sendCodeToBackend: function(code) {
    // 显示加载动画
    wx.showLoading({
      title: '登录中...',
      mask: true
    });

    wx.request({
      url: 'http://127.0.0.1:5000/api/v1/auth/login',  // 后端地址
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        code: code
      },
      success: (res) => {
        wx.hideLoading();
        
        if (res.statusCode === 200 && res.data.success) {
          // 登录成功
          const responseData = res.data.data;
          
          // 保存 token
          wx.setStorageSync('token', responseData.token);
          wx.setStorageSync('user_id', responseData.user_id);
          wx.setStorageSync('user_info', responseData.user);
          
          this.setData({
            isLogin: true,
            userInfo: responseData.user,
            token: responseData.token
          });
          
          // 跳转到首页
          wx.redirectTo({
            url: '/pages/index/index'  // 根据实际情况修改
          });
          
          wx.showToast({
            title: '登录成功',
            icon: 'success'
          });
        } else {
          // 登录失败
          wx.showToast({
            title: res.data.message || '登录失败',
            icon: 'error'
          });
        }
      },
      fail: (err) => {
        wx.hideLoading();
        console.error('Request error:', err);
        wx.showToast({
          title: '网络错误，请重试',
          icon: 'error'
        });
      }
    });
  }
});
```

---

## 第二步：后端接收 Code 并返回 Token

### 后端处理流程

```
小程序客户端
    |
    | POST /api/v1/auth/login
    | {
    |   "code": "021ZXX..."
    | }
    |
    v
后端服务器
    |
    ├─ 获取请求中的 code
    ├─ 调用微信接口
    │  └─ https://api.weixin.qq.com/sns/jscode2session
    │     params: appid, secret, js_code, grant_type
    ├─ 微信返回 openid 和 session_key
    ├─ 在数据库中查找或创建用户
    ├─ 生成 JWT Token
    └─ 返回用户信息和 Token
    |
    v
小程序客户端
    |
    └─ 保存 Token 到本地存储
```

---

## 第三步：在后续请求中使用 Token

### 方法一：使用 Authorization Header（推荐）

```javascript
// 封装 HTTP 请求函数
function request(url, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token');
    
    const header = {
      'Content-Type': 'application/json'
    };
    
    // 如果有 token，添加到 Authorization header
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }
    
    wx.request({
      url: base_url + url,
      method: method,
      header: header,
      data: data,
      success: (res) => {
        if (res.statusCode === 401) {
          // 401 说明 token 已过期或无效
          // 清除本地 token 并重新登录
          wx.clearStorageSync();
          wx.redirectTo({
            url: '/pages/login/login'
          });
        }
        resolve(res);
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
}

// 使用示例
async function getAllSeats(roomId) {
  const res = await request(`/api/v1/seats?room_id=${roomId}`, 'GET');
  if (res.data.success) {
    // 处理返回的座位数据
    return res.data.data;
  }
}
```

### 方法二：使用 URL 参数

```javascript
const token = wx.getStorageSync('token');
const url = `/api/v1/protected?token=${token}`;

wx.request({
  url: url,
  // ...
});
```

---

## 第四步：Token 验证和刷新

### 验证 Token 是否有效

```javascript
// 验证 token 是否有效
function verifyToken() {
  const token = wx.getStorageSync('token');
  
  if (!token) {
    return false;  // 没有 token
  }
  
  wx.request({
    url: 'http://127.0.0.1:5000/api/v1/auth/verify-token',
    method: 'POST',
    data: {
      token: token
    },
    success: (res) => {
      if (res.data.success && res.data.data.valid) {
        // Token 有效
        console.log('Token is valid');
      } else {
        // Token 无效或过期
        wx.clearStorageSync();
        wx.redirectTo({
          url: '/pages/login/login'
        });
      }
    }
  });
}
```

### 刷新 Token

```javascript
// 刷新 token
async function refreshToken() {
  const oldToken = wx.getStorageSync('token');
  
  try {
    const res = await new Promise((resolve, reject) => {
      wx.request({
        url: 'http://127.0.0.1:5000/api/v1/auth/refresh-token',
        method: 'POST',
        data: {
          token: oldToken
        },
        success: resolve,
        fail: reject
      });
    });
    
    if (res.data.success) {
      const newToken = res.data.data.token;
      wx.setStorageSync('token', newToken);
      return true;
    } else {
      return false;
    }
  } catch (err) {
    console.error('Failed to refresh token:', err);
    return false;
  }
}
```

---

## 完整的 API 请求/响应示例

### 1. 登录接口

**请求**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "code": "021ZXX..."
}
```

**成功响应（200）**
```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "user_id": 1,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJvcGVuaWQiOiJvSlZrQzRXZ2djT3h4eHh4eHgwMDEiLCJpYXQiOjE3MTA3MzA4MzAsImV4cCI6MTcxMDczODAzMH0.Kw8-z...",
    "user": {
      "id": 1,
      "openid": "oJVkC4WggcOxxxxxxxxxx001",
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

**错误响应（400）**
```json
{
  "code": 400,
  "message": "Missing code parameter",
  "data": null,
  "success": false
}
```

### 2. 验证 Token 接口

**请求**
```bash
POST /api/v1/auth/verify-token
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**成功响应（200）**
```json
{
  "code": 200,
  "message": "Token is valid",
  "data": {
    "user_id": 1,
    "openid": "oJVkC4WggcOxxxxxxxxxx001",
    "valid": true
  },
  "success": true
}
```

**错误响应（401）**
```json
{
  "code": 401,
  "message": "Token is invalid or expired",
  "data": null,
  "success": false
}
```

### 3. 刷新 Token 接口

**请求**
```bash
POST /api/v1/auth/refresh-token
Content-Type: application/json

{
  "token": "old-jwt-token-string"
}
```

**成功响应（200）**
```json
{
  "code": 200,
  "message": "Token refreshed successfully",
  "data": {
    "token": "new-jwt-token-string"
  },
  "success": true
}
```

---

## 安全建议

### 1. Token 存储
- ✅ 使用 `wx.setStorageSync()` 存储 token（微信小程序本地存储）
- ❌ 不要在 localStorage 存储 token（容易被 XSS 攻击）
- ❌ 不要在 cookie 中存储 token（用户可见）

### 2. HTTPS 要求
- 生产环境必须使用 HTTPS
- 微信小程序API域名必须配置 HTTPS

### 3. Token 过期处理
- 建议在用户选择操作频繁的功能时主动刷新 token
- 当收到 401 响应时，清除本地 token 并重新登录
- 不要在 token 还未过期时频繁刷新

### 4. 敏感信息保护
- 不要在 token 中存储密码或支付信息
- 不要在客户端验证 token（只在后端验证）
- 确保 JWT_SECRET_KEY 不被泄露

---

## 调试技巧

### 1. 使用微信开发者工具
- 在 Console 查看 API 请求/响应
- 在 Storage 查看本地数据
- 在 Network 查看 HTTP 请求详情

### 2. 查看后端日志
```python
# 后端会输出详细的日志信息
import logging
logger = logging.getLogger(__name__)
logger.info('用户登录成功')
```

### 3. 使用 curl 测试后端接口
```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_code"}'

curl -X POST http://127.0.0.1:5000/api/v1/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{"token": "your_token_here"}'
```

---

## 常见问题 FAQ

### Q1: Code 错误响应：40001 invalid credential
**A**: WECHAT_APPID 或 WECHAT_SECRET 不正确。请检查微信开发者平台的配置。

### Q2: Token 立即过期
**A**: 检查后端的 JWT_SECRET_KEY 和 JWT_EXPIRATION 配置。

### Q3: 登录成功但后续请求返回 401
**A**: 
1. 检查 token 是否正确传递
2. 检查 token 是否已过期（过期时间默认 7200 秒）
3. 尝试刷新 token

### Q4: 跨域错误 CORS
**A**: 确保后端启用了 CORS（Flask-CORS 已包含在项目中）

---

## 下一步

1. **实现座位预约功能**：使用 token 验证用户身份
2. **实现用户信息更新**：允许用户完善学号、姓名等信息
3. **实现预约历史查询**：获取用户的预约记录
4. **实现积分系统**：根据用户行为更新信用积分

---

**最后更新**: 2026-03-17

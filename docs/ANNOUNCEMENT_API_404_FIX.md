# 公告API 404错误修复

## 问题诊断

### 错误现象
- **错误代码**: 404
- **错误信息**: "请求的资源不存在"
- **根本原因**: URL路径重复，导致请求的端点不存在

### URL构建错误

#### ❌ 错误的构建方式
```
API_BASE_URL:         http://127.0.0.1:5000/api
endpoint (错误):      /api/v1/user/announcements
完整URL (错误):       http://127.0.0.1:5000/api/api/v1/user/announcements
                                                    ↑
                                           双重 /api 导致404
```

#### ✅ 正确的构建方式
```
API_BASE_URL:         http://127.0.0.1:5000/api
endpoint (正确):      /v1/user/announcements
完整URL (正确):       http://127.0.0.1:5000/api/v1/user/announcements
```

## 修复详情

### 文件修改: `mini-program/utils/announcement.js`

**修改前** ❌
```javascript
const response = await api.get('/api/v1/user/announcements', {
  limit: limit
});
```

**修改后** ✅
```javascript
// 注意：API_BASE_URL已经包含'/api'，所以这里只需要相对路径
const response = await api.get('/v1/user/announcements', {
  limit: limit
});
```

### 配置验证

**文件**: `mini-program/utils/config.js`
```javascript
const API_BASE_URL = 'http://127.0.0.1:5000/api';
//                                            ↑
//                              已包含/api前缀
```

**文件**: `app/api/user.py`
```python
user_bp = Blueprint('user', __name__, url_prefix='/api/v1/user')
//                                                ↑
//                               蓝图的前缀定义
```

## 请求链路验证

### 小程序端 → 后端端工作流程

```
1. 小程序调用
   api.get('/v1/user/announcements', { limit: 1 })
   
2. api.js构建URL
   url = config.API_BASE_URL + endpoint
   url = 'http://127.0.0.1:5000/api' + '/v1/user/announcements'
   url = 'http://127.0.0.1:5000/api/v1/user/announcements' ✅
   
3. 添加token到请求头
   Authorization: Bearer {token}
   
4. 发送GET请求

5. 后端蓝图匹配
   url_prefix = '/api/v1/user'
   route = '/announcements'
   完整路由 = '/api/v1/user/announcements' ✅ 匹配！
   
6. 执行 user.py 中的 get_announcements() 函数

7. 返回公告列表
```

## API端点详细信息

### 后端端点
- **蓝图**: `app/api/user.py`
- **蓝图前缀**: `/api/v1/user`
- **路由**: `GET /announcements`
- **完整路由**: `GET /api/v1/user/announcements` ✅
- **认证**: 需要有效的JWT token

### 小程序调用方式
```javascript
const response = await api.get('/v1/user/announcements', {
  limit: 5  // 返回最多5条公告
});
```

### 返回数据格式
```json
[
  {
    "id": 1,
    "title": "系统维护通知",
    "content": "周末进行系统维护",
    "type": "maintenance",
    "priority": 2,
    "is_pinned": true,
    "created_at": "2026-03-18T10:00:00"
  },
  ...
]
```

## 测试验证

### 验证步骤

1. **启动后端服务**
   ```bash
   cd c:\Users\30794\Desktop\毕业设计
   python run.py
   ```

2. **打开小程序**
   - 登录账户
   - 进入座位选择页面
   - 查看是否显示公告弹窗

3. **查看浏览器控制台**
   - Network标签：检查 `/api/v1/user/announcements` 请求
   - Console标签：查看是否有错误信息
   - 应该看到：`[Announcement] 成功获取公告列表: [...]`

4. **数据库检查**
   - 确保数据库中有状态为1(已发布)的公告
   - 确保公告在有效时间范围内

### 调用跟踪日志
```
[GET] http://127.0.0.1:5000/api/v1/user/announcements?limit=1
Response (200): [...]
[Announcement] 成功获取公告列表: [...]
```

## 常见问题排查

### 问题1: 仍然返回404
- ✅ 检查后端服务是否运行（需要看到 `Running on http://127.0.0.1:5000`）
- ✅ 检查user_bp是否正确注册（在 `app/__init__.py` 中）
- ✅ 确保 `Announcement` 模型被正确导入

### 问题2: 返回200但无公告数据
- ✅ 检查数据库中是否有公告记录
- ✅ 检查公告状态是否为1(已发布)
- ✅ 检查公告是否在有效时间范围内

### 问题3: 返回401 (未授权)
- ✅ 检查localStorage中是否有有效的auth_token
- ✅ 检查token是否过期
- ✅ 重新登录获取新token

## 代码规范建议

### API调用规范

✅ **正确的模式**：
```javascript
// API_BASE_URL = 'http://baseurl/api'
// 去掉前导的 /api
api.get('/v1/user/announcements', params)
api.get('/reservations/seats/1', params)
```

❌ **错误的模式**：
```javascript
// ❌ 不要重复添加/api
api.get('/api/v1/user/announcements', params)  // 导致 /api/api/v1/...
api.get('/api/reservations/seats/1', params)   // 导致 /api/api/reservations/...
```

## 修复总结

| 项目 | 状态 |
|------|------|
| 问题诊断 | ✅ 完成 - URL路径重复 |
| 代码修改 | ✅ 完成 - announcement.js |
| 路由验证 | ✅ 完成 - /api/v1/user/announcements |
| 测试建议 | ✅ 提供 |

---
修复日期: 2026-03-18
修复类型: API路由错误
影响范围: 公告获取功能
优先级: 高

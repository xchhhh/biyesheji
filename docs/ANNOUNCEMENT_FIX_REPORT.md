# 公告获取错误修复 - 详细总结

## 问题描述

用户客户端出现以下错误：
```
TypeError: api.get is not a function
    at _callee$ (announcement.js? [sm]:25)
```

这个错误表明 `api.js` 中不存在 `get` 方法。

## 根本原因分析

### 问题1: API模块缺少通用HTTP方法
**文件**: `mini-program/utils/api.js`

- ❌ **问题**: 仅导出了特定的API方法 (`getSeats`, `submitReservation` 等)
- ❌ **缺陷**: 没有通用的 `get()`, `post()`, `put()`, `del()` 方法
- ✅ **解决**: 添加了通用的HTTP方法

### 问题2: 公告管理模块使用了不存在的方法
**文件**: `mini-program/utils/announcement.js`

- ❌ **问题**: 第25行调用了 `api.get()` 但该方法不存在
- ❌ **问题**: 不正确地在params中传递headers
- ✅ **解决**: 修改为正确的调用方式

## 修复详情

### 修复1: 在 api.js 中添加通用HTTP方法

**文件**: `mini-program/utils/api.js`

添加了以下四个通用方法：

```javascript
/**
 * 通用 GET 请求
 */
function get(endpoint, params = {}) {
  let queryStr = '';
  
  // 构建查询字符串，跳过headers等特殊参数
  const queryParams = {};
  for (const key in params) {
    if (key !== 'headers' && params.hasOwnProperty(key)) {
      queryParams[key] = params[key];
    }
  }
  
  if (Object.keys(queryParams).length > 0) {
    queryStr = '?' + Object.keys(queryParams)
      .map(key => `${key}=${encodeURIComponent(queryParams[key])}`)
      .join('&');
  }
  
  return request('GET', endpoint + queryStr);
}

/**
 * 通用 POST 请求
 */
function post(endpoint, data = {}) {
  return request('POST', endpoint, data);
}

/**
 * 通用 PUT 请求
 */
function put(endpoint, data = {}) {
  return request('PUT', endpoint, data);
}

/**
 * 通用 DELETE 请求
 */
function del(endpoint, data = {}) {
  return request('DELETE', endpoint, data);
}
```

同时更新了导出：
```javascript
module.exports = {
  request,
  get,      // ✅ 新增
  post,     // ✅ 新增
  put,      // ✅ 新增
  del,      // ✅ 新增
  getSeats,
  submitReservation,
  // ... 其他方法
};
```

**关键特性**:
- ✅ 自动处理查询参数编码
- ✅ 跳过非查询参数 (如headers)
- ✅ 利用底层 `request()` 函数处理token认证
- ✅ 支持所有HTTP方法

### 修复2: 修正 announcement.js 的调用方式

**文件**: `mini-program/utils/announcement.js`

**修改前**:
```javascript
const response = await api.get('/api/v1/user/announcements', {
  limit: limit,
  headers: {
    'Authorization': `Bearer ${token}`  // ❌ 不应该在这里传
  }
});
```

**修改后**:
```javascript
// 调用API获取公告（token会由api.js自动处理）
const response = await api.get('/api/v1/user/announcements', {
  limit: limit  // ✅ 仅传查询参数
});
```

**改进点**:
- ✅ 去除了不必要的headers参数
- ✅ token由api.js的 `request()` 函数自动处理
- ✅ 简化了调用逻辑
- ✅ 调整了响应处理逻辑

## API端点信息

### 后端公告获取端点
- **文件**: `app/api/user.py`
- **蓝图前缀**: `/api/v1/user`
- **路由**: `GET /announcements`
- **完整URL**: `/api/v1/user/announcements`
- **查询参数**:
  - `limit`: 返回的公告数量 (默认10)
  - `priority`: 优先级筛选 (0=低, 1=中, 2=高)
- **返回格式**: 直接返回公告对象数组

### 后端返回格式

```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "title": "系统维护通知",
      "content": "周末进行系统维护...",
      "type": "maintenance",
      "priority": 2,
      "is_pinned": true,
      "created_at": "2026-03-18T10:00:00"
    }
  ]
}
```

## 调用流程

```
用户页面 (seats.js)
    ↓
AnnouncementManager.loadAndShowAnnouncement()
    ↓
AnnouncementManager.getAnnouncements(limit)
    ↓
api.get('/api/v1/user/announcements', { limit })  ✅ 现在已修复
    ↓
api.request('GET', '/api/v1/user/announcements?limit=N')
    ↓
后端处理 + 返回公告列表
    ↓
显示公告弹窗
```

## 验证清单

- ✅ `api.js` 中添加了通用 `get()` 方法
- ✅ `api.js` 中添加了通用 `post()`, `put()`, `del()` 方法
- ✅ `api.js` 正确导出了所有方法
- ✅ `announcement.js` 不再在params中传headers
- ✅ `announcement.js` 使用了正确的API端点
- ✅ 后端 `/api/v1/user/announcements` 端点已验证
- ✅ Token处理由 `app.js` 中的 `getToken()` 处理

## 测试建议

1. **验证公告获取**
   - 打开小程序的座位选择页面
   - 在浏览器的Network面板中查看是否成功调用了 `/api/v1/user/announcements`
   - 检查是否返回了公告数据

2. **验证Token传递**
   - 在api.js中添加console.log检查是否正确传递了Authorization头
   - 确保 `app.getToken()` 正确返回了token

3. **验证错误处理**
   - 移除token并重新加载页面
   - 应该看到警告信息而不是崩溃

## 后续改进建议

1. **缓存公告**
   - 可以在本地缓存公告，避免每次都调用API

2. **错误重试**
   - 添加自动重试逻辑处理网络暂时中断

3. **公告分类**
   - 支持按类型和优先级筛选公告

4. **消息通知**
   - 当新公告发布时主动推送通知

---
修复日期: 2026-03-18
修复人: AI Assistant
状态: ✅ 完成

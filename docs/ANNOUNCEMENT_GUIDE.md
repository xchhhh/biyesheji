# 公告弹窗功能使用指南

## 功能概述

用户登录进入座位选择页面时，如果有新的公告，会自动显示一个公告弹窗。用户可以选择"确定"阅读公告，或点击"下次不显示"来关闭该公告（除非是紧急公告）。

## 用户端体验

### 公告显示流程
1. 用户登录后进入座位页面
2. 系统自动获取当前有效的公告
3. 如果有新公告且未被"下次不显示"，显示公告弹窗
4. 用户可以：
   - 点击"确定"阅读公告
   - 点击"下次不显示"（下次登录不再显示该公告）

### 公告优先级规则
- **优先级低 (0)**: 普通通知，可选择"下次不显示"
- **优先级中 (1)**: 重要通知，可选择"下次不显示"
- **优先级高 (2)**: 紧急公告，**不显示"下次不显示"按钮**，用户必须确认

### 公告类型
- `general`: 一般通知
- `maintenance`: 系统维护通知
- `emergency`: 紧急通知

## 管理员端操作

### 发送公告 API

**创建新公告**
```
POST /api/admin/announcements
Authorization: Bearer {admin_token}

Request Body:
{
    "title": "系统维护通知",
    "content": "本周末进行数据库优化升级，预计停机2小时。",
    "type": "maintenance",
    "priority": 1,
    "is_pinned": false,
    "start_time": "2026-03-20T00:00:00",
    "end_time": "2026-03-21T23:59:59"
}

Response (201 Created):
{
    "code": 201,
    "message": "公告已发布",
    "data": {
        "id": 1,
        "title": "系统维护通知",
        ...
    }
}
```

### 公告字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 公告标题 |
| `content` | string | ✅ | 公告内容（可包含换行） |
| `type` | string | ❌ | 公告类型: general/maintenance/emergency (默认: general) |
| `priority` | integer | ❌ | 优先级: 0-低, 1-中, 2-高 (默认: 0) |
| `is_pinned` | boolean | ❌ | 是否置顶 (默认: false) |
| `start_time` | datetime | ❌ | 开始显示时间 (不设置则立即显示) |
| `end_time` | datetime | ❌ | 结束显示时间 (不设置则永久显示) |

### 更新公告

**修改已发布的公告**
```
PUT /api/admin/announcements/{announcement_id}
Authorization: Bearer {admin_token}

Request Body: (与创建相同的字段)
Response (200 OK)
```

### 删除/下架公告

**下架已发布的公告**
```
DELETE /api/admin/announcements/{announcement_id}
Authorization: Bearer {admin_token}

Response (200 OK):
{
    "code": 200,
    "message": "公告已下架"
}
```

## 使用场景示例

### 场景1: 系统维护通知
```json
{
    "title": "系统维护通知",
    "content": "本周日 14:00-16:00 进行系统维护，期间无法使用座位预约功能。",
    "type": "maintenance",
    "priority": 1,
    "start_time": "2026-03-20T00:00:00",
    "end_time": "2026-03-22T23:59:59"
}
```

### 场景2: 紧急通知（停电）
```json
{
    "title": "🚨 紧急通知：停电",
    "content": "校园将于今日15:00-18:00 进行紧急停电维修。所有自习室关闭。",
    "type": "emergency",
    "priority": 2,
    "end_time": "2026-03-18T20:00:00"
}
```

### 场景3: 一般公告
```json
{
    "title": "座位预约系统升级完成",
    "content": "座位预约系统已升级，新增了推荐座位功能。根据您的习惯为您推荐最适合的座位。",
    "type": "general",
    "priority": 0
}
```

## 前端API集成

### 在其他页面中使用公告功能

```javascript
const AnnouncementManager = require('../../utils/announcement');

// 1. 获取公告列表
const announcements = await AnnouncementManager.getAnnouncements(5);

// 2. 显示特定公告
await AnnouncementManager.showAnnouncementModal(announcements[0]);

// 3. 手动加载并显示第一条新公告
await AnnouncementManager.loadAndShowAnnouncement();

// 4. 标记公告为"下次不显示"
AnnouncementManager.dismissAnnouncement(announcementId);

// 5. 清除"下次不显示"标记
AnnouncementManager.clearDismissal(announcementId);

// 6. 重置所有公告显示状态（调试用）
AnnouncementManager.resetAllDismissals();
```

## 相关API端点

### 用户端接口
- `GET /api/v1/user/announcements` - 获取有效的公告列表
  - Query: `limit=10` (返回数量限制)
  - Query: `priority=1` (按优先级筛选，可选)

### 管理员接口
- `GET /api/admin/announcements` - 获取所有公告
- `POST /api/admin/announcements` - 创建新公告
- `PUT /api/admin/announcements/{id}` - 更新公告
- `DELETE /api/admin/announcements/{id}` - 删除/下架公告

## 本地存储数据结构

公告的"下次不显示"状态保存在小程序本地存储中：
- 键名: `announcement_dismissed_{announcement_id}`
- 值: `true`

例如：禁用ID为1的公告的键名为 `announcement_dismissed_1`

## 注意事项

1. **时间区间**: 公告的显示受 `start_time` 和 `end_time` 的控制
   - 如果不设置 `start_time`，则立即显示
   - 如果不设置 `end_time`，则永久有效

2. **优先级**: 公告列表按优先级排序显示，高优先级的公告优先显示

3. **置顶**: `is_pinned=true` 的公告会显示在列表顶部

4. **浏览次数**: 每次用户查看公告，`view_count` 会自动增加

5. **下次不显示**: 每个用户的"下次不显示"设置是独立的，存储在本地

## 测试步骤

### 1. 创建测试公告
在管理后台或通过API创建一条测试公告

### 2. 登录小程序
登录后进入座位页面，查看是否显示公告弹窗

### 3. 测试下次不显示
- 点击"下次不显示"
- 重新进入页面，相同公告不应再显示

### 4. 测试紧急公告
- 创建优先级为2的公告
- 登录验证，确认没有"下次不显示"按钮

### 5. 清除测试数据
- 在浏览器开发者工具中清除相关的本地存储键
- 或创建新的公告进行测试

# 公告弹窗功能实现完成

## ✅ 功能实现总结

已成功为座位预约系统实现了**公告弹窗功能**，支持管理员在后台发送公告，用户登录后自动显示，且支持"下次不显示"功能。

---

## 📋 实现清单

### 后端实现 (Python/Flask)

#### 1. **数据库模型** ✅
- 文件: [app/models/announcement.py](app/models/announcement.py)
- 表结构已存在，包含以下字段：
  - `id`: 公告ID
  - `title`: 标题
  - `content`: 内容
  - `type`: 类型 (general/maintenance/emergency)
  - `priority`: 优先级 (0-低, 1-中, 2-高)
  - `is_pinned`: 是否置顶
  - `status`: 状态 (0-草稿, 1-已发布, 2-已下架)
  - `start_time/end_time`: 显示时间范围
  - `created_at/updated_at`: 时间戳

#### 2. **用户API端点** ✅
- 文件: [app/api/user.py](app/api/user.py) (新增第7部分)
- 端点: `GET /api/v1/user/announcements`
- 功能：
  - 获取当前有效的公告列表（已发布且在时间范围内）
  - 支持按优先级筛选
  - 支持分页/限制数量
  - 自动更新浏览次数
  - 按置顶、优先级、创建时间排序

#### 3. **管理员API端点** ✅
- 文件: [app/api/management.py](app/api/management.py)
- 已存在的端点：
  - `GET /api/admin/announcements` - 获取公告列表
  - `POST /api/admin/announcements` - 创建公告
  - `PUT /api/admin/announcements/{id}` - 更新公告
  - `DELETE /api/admin/announcements/{id}` - 删除/下架公告

---

### 前端实现 (WeChat Mini Program)

#### 1. **公告管理模块** ✅
- 文件: [mini-program/utils/announcement.js](mini-program/utils/announcement.js)
- 主要功能：
  - `getAnnouncements()` - 获取公告列表
  - `shouldShowAnnouncement()` - 检查是否显示
  - `dismissAnnouncement()` - 标记为"下次不显示"
  - `showAnnouncementModal()` - 显示公告弹窗
  - `loadAndShowAnnouncement()` - 自动加载并显示公告

#### 2. **座位页面集成** ✅
- 文件: [mini-program/pages/seats/seats.js](mini-program/pages/seats/seats.js)
- 修改内容：
  - 导入公告管理模块
  - 在 `onLoad()` 中添加公告加载
  - 新增 `loadAnnouncements()` 方法

#### 3. **本地存储** ✅
- 用户"下次不显示"的状态保存在本地
- 键名模式: `announcement_dismissed_{announcement_id}`
- 值: `true`

---

## 🎯 使用流程

### 用户端流程

```
1. 用户登录
   ↓
2. 进入座位选择页面 (seats)
   ↓
3. 页面加载时自动调用 loadAnnouncements()
   ↓
4. 如果有新公告，显示弹窗：
   ├─ 用户点击"确定" → 关闭弹窗，继续使用
   └─ 用户点击"下次不显示" → 标记公告，本地不再显示
   ↓
5. 用户正常使用座位预约功能
```

### 管理员端流程

```
1. 管理员登录后台
   ↓
2. 创建/编辑/发布公告
   ↓
3. 设置：
   ├─ 标题和内容
   ├─ 类型 (general/maintenance/emergency)
   ├─ 优先级 (0-低, 1-中, 2-高)
   ├─ 显示时间范围 (可选)
   └─ 是否置顶
   ↓
4. 保存发布
   ↓
5. 用户登录后自动看到新公告
```

---

## 🔑 核心特性

### 1. 智能显示机制
- ✅ 只显示已发布的公告
- ✅ 检查时间范围（start_time/end_time）
- ✅ 按优先级排序，高优先级优先显示
- ✅ 置顶公告显示在顶部
- ✅ 自动跳过用户已"下次不显示"的公告

### 2. 优先级系统
- **0 (低)**: 普通通知 → 显示"下次不显示"按钮
- **1 (中)**: 重要通知 → 显示"下次不显示"按钮
- **2 (高)**: 紧急公告 → **不显示"下次不显示"按钮**，用户必须确认

### 3. 公告类型
- `general`: 一般通知
- `maintenance`: 系统维护
- `emergency`: 紧急通知

### 4. "下次不显示"功能
- 用户可以选择不再显示特定公告
- 状态保存在本地存储中
- 仅影响该用户，管理员可继续更新公告
- 高优先级公告无法关闭（必须确认）

---

## 📡 API 端点说明

### 用户获取公告
```http
GET /api/v1/user/announcements?limit=10&priority=1
Authorization: Bearer {token}

Response (200 OK):
{
    "code": 200,
    "message": "Success",
    "data": [
        {
            "id": 1,
            "title": "系统维护通知",
            "content": "...",
            "type": "maintenance",
            "priority": 1,
            "is_pinned": false,
            "created_at": "2026-03-18T10:00:00"
        }
    ]
}
```

### 管理员创建公告
```http
POST /api/admin/announcements
Authorization: Bearer {admin_token}
Content-Type: application/json

Request:
{
    "title": "系统维护通知",
    "content": "本周日进行系统维护...",
    "type": "maintenance",
    "priority": 1,
    "is_pinned": false,
    "start_time": "2026-03-20T00:00:00",
    "end_time": "2026-03-22T23:59:59"
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

---

## 📁 文件清单

### 新增文件
- ✅ [mini-program/utils/announcement.js](mini-program/utils/announcement.js) - 公告管理工具模块
- ✅ [test_announcement.py](test_announcement.py) - 公告系统测试脚本
- ✅ [ANNOUNCEMENT_GUIDE.md](ANNOUNCEMENT_GUIDE.md) - 公告功能使用指南

### 修改文件
- ✅ [app/api/user.py](app/api/user.py) - 添加获取公告API
- ✅ [mini-program/pages/seats/seats.js](mini-program/pages/seats/seats.js) - 集成公告加载功能

---

## 🧪 测试结果

### API测试 ✅
```python
# 获取公告列表 - 成功返回
GET /api/v1/user/announcements
Response: 200 OK
Data: [
    {
        "id": 1,
        "title": "test",
        "content": "xx",
        "type": "general",
        "priority": 1,
        "is_pinned": false,
        "created_at": "2026-03-17T19:40:45.681387"
    }
]
```

### 弹窗显示流程 ✅
```javascript
// 用户登录进入座位页面
onLoad() {
    this.loadSeats();      // 加载座位
    this.loadAnnouncements();  // 加载并显示公告 ✅
}

// 获取公告并显示
async loadAnnouncements() {
    const shown = await AnnouncementManager
        .loadAndShowAnnouncement();
    // 自动显示公告弹窗
}
```

---

## 🚀 快速开始

### 1. 启动后端
```bash
cd /毕业设计
python run.py
# 服务器运行在 http://127.0.0.1:5000
```

### 2. 小程序用户端
```javascript
const AnnouncementManager = require('../../utils/announcement');

// 自动加载并显示公告
await AnnouncementManager.loadAndShowAnnouncement();

// 或者获取公告列表
const announcements = await AnnouncementManager.getAnnouncements(5);
```

### 3. 测试公告功能
```bash
# 运行测试脚本
python test_announcement.py
```

---

## 💡 使用示例

### 场景1: 紧急停电通知
```json
{
    "title": "🚨 紧急通知：停电维修",
    "content": "校园将于今日15:00-18:00进行紧急停电维修。所有自习室关闭。",
    "type": "emergency",
    "priority": 2,
    "is_pinned": true,
    "end_time": "2026-03-18T20:00:00"
}
```
**效果**: 用户登录时必须看到且确认，无法关闭

### 场景2: 系统维护通知
```json
{
    "title": "系统维护通知",
    "content": "本周日14:00-16:00进行数据库升级，期间无法使用。",
    "type": "maintenance",
    "priority": 1,
    "start_time": "2026-03-20T00:00:00",
    "end_time": "2026-03-22T23:59:59"
}
```
**效果**: 用户可以选择"下次不显示"

### 场景3: 功能更新通知
```json
{
    "title": "座位预约系统升级完成",
    "content": "新增推荐座位功能，系统会为您推荐最佳座位。",
    "type": "general",
    "priority": 0
}
```
**效果**: 普通通知，用户可以快速关闭或隐藏

---

## 📝 注意事项

1. **时间处理**
   - 使用UTC时间存储
   - 可不设置 `start_time` (立即显示)
   - 可不设置 `end_time` (永久有效)

2. **优先级规则**
   - 优先级2的公告用户无法"下次不显示"
   - 用于紧急通知，确保用户必须看到

3. **本地存储**
   - 各用户的"下次不显示"状态独立
   - 清除浏览器存储会重置状态

4. **显示顺序**
   - 按置顶 > 优先级 > 创建时间排序
   - 每页默认显示10条

---

## 🔄 后续扩展

- [ ] 添加公告阅读状态追踪
- [ ] 支持公告模板系统
- [ ] 添加公告富文本编辑器
- [ ] 支持公告分类管理
- [ ] 添加公告发布日志审计
- [ ] 支持推送通知（使用微信通知）

---

## 📞 技术支持

### 相关文件
- [ANNOUNCEMENT_GUIDE.md](ANNOUNCEMENT_GUIDE.md) - 详细使用指南
- [app/models/announcement.py](app/models/announcement.py) - 数据模型
- [app/api/user.py](app/api/user.py) - 用户API
- [app/api/management.py](app/api/management.py) - 管理API
- [mini-program/utils/announcement.js](mini-program/utils/announcement.js) - 前端工具

### API端点
- `GET /api/v1/user/announcements` - 用户获取公告
- `GET /api/admin/announcements` - 管理员查看公告列表
- `POST /api/admin/announcements` - 创建公告
- `PUT /api/admin/announcements/{id}` - 更新公告
- `DELETE /api/admin/announcements/{id}` - 删除公告

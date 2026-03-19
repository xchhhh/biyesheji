# 座位维修申请功能 - 完整实现指南

## 📋 功能概述

添加了完整的座位维修申请功能，用户可以：
1. **提交维修申报** - 报告座位问题（损坏、脏污、家具问题、电气问题等）
2. **查看申报历史** - 跟踪维修申请的处理进度
3. **实时更新** - 管理员处理后立即显示最新状态
4. **扫描二维码** - 快速输入座位号

---

## 🔧 后端实现

### 新增API端点

#### 1. 报告座位维修
```
POST /api/reservations/maintenance/report
Content-Type: application/json
Authorization: Bearer {token}

请求体:
{
  "seat_id": 1100,                    // 座位ID (必需)
  "issue_type": "broken",             // 问题类型 (必需)
  "severity": "high",                 // 严重程度 (必需)
  "description": "座位扶手损坏",      // 问题描述 (必需)
  "phone": "13800138000"              // 联系电话 (可选)
}

有效的issue_type值:
- broken    : 座位损坏
- dirty     : 座位脏污
- furniture : 家具问题
- electrical: 电气问题
- other     : 其他问题

有效的severity值:
- low       : 低
- medium    : 中
- high      : 高
- critical  : 严重

返回 (201 Created):
{
  "code": 201,
  "success": true,
  "message": "维修申请已提交，管理员会尽快处理",
  "data": {
    "report_id": 1,
    "seat_id": 1100,
    "seat_number": "A-001",
    "issue_type": "broken",
    "severity": "high",
    "status": "pending",
    "created_at": "2026-03-17T19:49:36.567140"
  }
}
```

#### 2. 获取维修申报状态
```
GET /api/reservations/maintenance/status?page=1&per_page=10&status=pending
Authorization: Bearer {token}

查询参数:
- page      : 页码 (默认: 1)
- per_page  : 每页数量 (默认: 10)  
- status    : 筛选状态 (可选)
  - pending      : 待处理
  - in_progress  : 处理中
  - completed    : 已完成
  - cancelled    : 已取消

返回 (200 OK):
{
  "code": 200,
  "success": true,
  "data": {
    "total": 1,
    "page": 1,
    "per_page": 10,
    "pages": 1,
    "maintenance_requests": [
      {
        "id": 1,
        "seat_id": 1100,
        "seat_number": "A-001",
        "room_id": 1,
        "room_name": "一楼自习室",
        "issue_type": "broken",
        "issue_type_text": "座位损坏",
        "severity": "high",
        "severity_text": "高",
        "description": "座位扶手损坏",
        "status": "pending",
        "status_text": "待处理",
        "assigned_to_name": null,
        "maintenance_date": null,
        "completion_date": null,
        "notes": null,
        "estimated_days": 1,
        "created_at": "2026-03-17T19:49:36.567140",
        "updated_at": "2026-03-17T19:49:36.567140"
      }
    ]
  }
}
```

### 文件修改
- `app/api/reservation.py` - 新增两个维修申请API端点和三个辅助函数
- `app/models/__init__.py` - 已包含SeatMaintenance模型
- `app/models/seat_maintenance.py` - 维修申请数据模型

---

## 💻 前端实现

### 新增页面

#### 页面路由
```
pages/maintenance/maintenance.js      - 页面逻辑
pages/maintenance/maintenance.wxml    - 页面模板
pages/maintenance/maintenance.wxss    - 页面样式
pages/maintenance/maintenance.json    - 页面配置
```

### 页面功能

#### 标签页1: 申报维修
- **座位号输入** - 支持手动输入或扫描二维码
  - 支持格式: A-001, A001, 1100等
  
- **问题类型选择** - 5种问题类型，带图标
  - 🔨 座位损坏
  - 🧹 座位脏污
  - 🪑 家具问题
  - ⚡ 电气问题
  - ❓ 其他问题

- **严重程度选择** - 4个等级
  - 低 (绿色)
  - 中 (橙色)
  - 高 (红色)
  - 严重 (紫色)

- **问题描述** - 文本框，支持500字以内
  - 实时显示字数统计

- **联系电话** - 可选，方便管理员联系

- **二维码扫描** - 一键扫描座位二维码

#### 标签页2: 申报历史
- **筛选功能** - 按状态筛选
  - 全部
  - 待处理
  - 处理中
  - 已完成

- **申报卡片** - 显示维修申报详情
  - 座位号和阅览室
  - 问题类型和严重程度
  - 当前状态
  - 处理人（如已分配）
  - 处理备注（如有）
  - 完成时间（如已完成）

- **实时上拉加载** - 支持无限滚动加载更多

### 在"我的"页面中的集成
- 在"我的信息"菜单中添加"🔧 座位维修申请"菜单项
- 点击即可导航到维修申请页面

### API调用更新
- `mini-program/utils/api.js` - 新增两个维修申请相关的API方法
  - `reportMaintenance(data)` - 提交维修申报
  - `getMaintenanceStatus(params)` - 获取维修申报列表

### 应用配置更新
- `mini-program/app.json` - 添加maintenance页面路由

---

## 🔄 工作流程

### 用户维修申报流程
```
用户发现座位问题
    ↓
打开"座位维修申请"页面
    ↓
选择问题类型和严重程度
    ↓
详细描述问题
    ↓
提交维修申报
    ↓
申报成功，进入"申报历史"
    ↓
查看被处理
    ↓
状态更新为"处理中"
    ↓
管理员完成维修
    ↓
状态更新为"已完成"
```

### 状态转移
```
待处理 (pending)
   ↓
处理中 (in_progress)
   ↓
已完成 (completed)
   
或
   ↓
已取消 (cancelled)
```

---

## 🧪 测试结果

✅ **维修申请提交测试** (Status: 201)
```
curl -X POST http://127.0.0.1:5000/api/reservations/maintenance/report \
  -H "X-Test-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "seat_id": 1100,
    "issue_type": "broken",
    "severity": "high",
    "description": "座位扶手损坏",
    "phone": "13800138000"
  }'

响应:
{
  "code": 201,
  "message": "维修申请已提交，管理员会尽快处理",
  "data": {
    "report_id": 1,
    "seat_id": 1100,
    "seat_number": "A-001",
    "issue_type": "broken",
    "severity": "high",
    "status": "pending",
    "created_at": "2026-03-17T19:49:36.567140"
  }
}
```

✅ **维修申报列表查询测试** (Status: 200)
```
curl http://127.0.0.1:5000/api/reservations/maintenance/status?page=1&per_page=10 \
  -H "X-Test-User-Id: 1"

响应: 成功返回维修申报列表，包含1条记录
```

---

## 📱 前端使用指南

### 1. 打开维修申请页面
- 在"我的"页面找到"🔧 座位维修申请"菜单项
- 点击进入维修申请页面

### 2. 提交维修申报
- 输入座位号（或点击📱扫一扫）
- 选择问题类型（5选1）
- 选择严重程度（4选1）
- 输入详细的问题描述（5-500字）
- 填写联系电话（可选）
- 点击"提交维修申报"按钮

### 3. 查看申报进度
- 切换到"申报历史"标签页
- 查看已提交的维修申报列表
- 点击卡片可查看详细信息
- 使用"按状态筛选"快速查找

---

## 🎨 用户界面

### 颜色方案
| 元素 | 颜色 |
|------|------|
| 主色 | #3c6fda (蓝色) |
| 优先级低 | #4CAF50 (绿色) |
| 优先级中 | #FF9800 (橙色) |
| 优先级高 | #F44336 (红色) |
| 优先级严重 | #9C27B0 (紫色) |

### 页面布局
- 顶部标签页切换
- 标签页1: 表单输入
- 标签页2: 申报列表
- 底部操作按钮

---

## 🔐 权限控制

- ✅ 用户必须登录才能提交维修申报
- ✅ 用户只能查看自己提交的维修申报
- ✅ 只有管理员才能修改维修申报状态

---

## 📊 数据库

### 表结构
```
seat_maintenance 表
├── id (PK)
├── seat_id (FK)
├── issue_type (枚举: broken, dirty, furniture, electrical, other)
├── severity (枚举: low, medium, high, critical)
├── description (文本)
├── reported_by_id (FK - 用户ID)
├── reporter_phone (电话)
├── status (枚举: pending, in_progress, completed, cancelled)
├── assigned_to_id (FK - 维修人员ID)
├── maintenance_date (时间戳)
├── completion_date (时间戳)
├── notes (维修备注)
├── estimated_days (预计天数)
├── created_at (创建时间)
└── updated_at (更新时间)
```

---

## 🚀 后续扩展

### 可添加的功能
1. **维修优先级队列** - 根据严重程度自动排序
2. **预计维修时间** - 显示预计完成时间
3. **维修进度通知** - 推送通知用户维修进展
4. **维修历史分析** - 统计常见问题
5. **反馈评分** - 用户对维修质量评分
6. **维修成本统计** - 管理员查看维修成本
7. **自动派单** - 根据维修人员负载自动分配

---

## 💡 技术栈

### 后端
- Flask / SQLAlchemy (ORM)
- 关系数据库 (SQLite)
- RESTful API

### 前端
- WeChat Mini-Program (小程序)
- WXML / WXSS / JavaScript

### 集成
- JWT 认证
- 二维码扫描
- 实时状态同步

---

## 📝 注意事项

1. **座位ID计算** - 前端会自动将座位号（如A-001）转换为座位ID
2. **时区处理** - 所有时间戳均为UTC+0
3. **错误处理** - 后端返回详细的错误信息供调试
4. **性能** - 支持分页加载，每页最多10条记录

---

## ✅ 验证清单

- [x] 后端API端点已实现
- [x] 数据库模型已存在
- [x] 前端页面已完成
- [x] API调用已集成  
- [x] 菜单项已添加到"我的"页面
- [x] app.json已更新路由
- [x] 所有API已测试可用
- [x] 前端样式已完成
- [x] 用户认证已验证

---

需要在WeChat开发者工具中重新编译mini-program以看到所有更新！

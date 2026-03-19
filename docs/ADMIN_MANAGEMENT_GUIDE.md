<!--
自习室管理系统 - 管理和运维功能完整说明
-->

# 自习室管理系统 - 管理和运维功能

## 📋 概述

本模块提供了完整的管理和运维功能，包括Web版综合管理后台、座位维护管理、用户管理、公告管理、值班人员快查和完整的审计日志系统。

## 1️⃣ 综合管理后台 - Web版管理界面

### 功能特性
- **响应式设计**：完晤支持桌面端、平板和手机
- **现代化UI**：渐变色设计，专业美观
- **实时数据**：所有数据实时更新
- **多语言支持**：中文界面

### 访问方式
```
登录地址: http://localhost:5000/admin/login
管理后台: http://localhost:5000/admin/

测试账户:
- 用户名: root
- 密码: 123456
```

### 主要模块

#### 控制面板 (Dashboard)
显示关键业务指标的统计概览：
- **系统用户**：总用户数、活跃用户、禁用用户
- **今日预约**：总预约数、签到数、完成数
- **座位状态**：总座位、占用座位、维修座位
- **待处理维护**：需要处理的座位维护请求数

图表展示：
- 各房间占用率分布
- 最近操作日志实时显示

## 2️⃣ 座位维护管理

### 核心功能

#### 2.1 损坏座位标记
```
PUT /api/admin/seats/<seat_id>/maintenance
Content-Type: application/json

请求体:
{
    "issue_type": "broken",          # 问题类型: broken, dirty, furniture, electrical, other
    "severity": "high",              # 严重程度: low, medium, high, critical
    "description": "座位破损",       # 详细描述
    "reporter_phone": "13800000000" # 报告人电话
}

响应:
{
    "code": 200,
    "message": "维护记录已创建",
    "data": {
        "id": 1,
        "seat_id": 5,
        "issue_type": "broken",
        "severity": "high",
        "status": "pending",
        ...
    }
}
```

#### 2.2 维修跟踪
```
GET /api/admin/seats/maintenance?page=1&per_page=20&status=pending&severity=high

查询参数:
- page: 页码 (default: 1)
- per_page: 每页数量 (default: 20)
- status: 状态 (pending, in_progress, completed, cancelled)
- severity: 严重程度 (low, medium, high, critical)
- room_id: 房间ID
```

#### 2.3 完成维修
```
POST /api/admin/seats/maintenance/<maintenance_id>/complete
Content-Type: application/json

请求体:
{
    "notes": "已修复，座位正常使用"
}

响应:
{
    "code": 200,
    "message": "维护完成",
    "data": {
        "id": 1,
        "status": "completed",
        "completion_date": "2026-03-18T12:00:00",
        ...
    }
}
```

## 3️⃣ 用户管理

### 核心功能

#### 3.1 用户列表查询
```
GET /api/admin/users?page=1&per_page=20&status=1&search=

查询参数:
- page: 页码
- per_page: 每页数量
- status: 0-禁用, 1-正常, -1-全部
- search: 搜索关键词 (昵称/电话/学号/真名)

响应示例:
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "nickname": "学生1",
            "phone": "13800000001",
            "student_id": "202101001",
            "real_name": "张三",
            "credit_score": 100,
            "status": 1,
            "status_label": "正常",
            "last_login": "2026-03-18T10:00:00",
            "created_at": "2026-01-01T00:00:00"
        },
        ...
    ],
    "pagination": {
        "total": 150,
        "page": 1,
        "per_page": 20,
        "pages": 8
    }
}
```

#### 3.2 禁用和启用账户
```
# 禁用用户
POST /api/admin/users/<user_id>/disable
Content-Type: application/json

请求体:
{
    "reason": "严重违规行为"  # 禁用原因
}

# 启用用户
POST /api/admin/users/<user_id>/enable

响应:
{
    "code": 200,
    "message": "用户已禁用",
    "data": {
        "user_id": 5,
        "status": 0
    }
}
```

#### 3.3 强制取消预约
```
POST /api/admin/users/<user_id>/cancel-reservations
Content-Type: application/json

请求体:
{
    "reason": "设备故障，强制取消"  # 取消原因
}

响应:
{
    "code": 200,
    "message": "已取消 3 个预约",
    "data": {
        "cancelled_count": 3
    }
}
```

#### 3.4 用户详情查看
```
GET /api/admin/users/<user_id>

响应:
{
    "code": 200,
    "data": {
        "user": {
            "id": 5,
            "nickname": "学生5",
            "credit_score": 85,
            ...
        },
        "statistics": {
            "total_reservations": 45,
            "completed_reservations": 43,
            "cancelled_reservations": 2
        },
        "recent_reservations": [...],
        "credit_flows": [...]
    }
}
```

## 4️⃣ 公告管理

### 核心功能

#### 4.1 发布公告
```
POST /api/admin/announcements
Content-Type: application/json

请求体:
{
    "title": "系统维护通知",
    "content": "本周日02:00-04:00进行系统维护...",
    "type": "maintenance",           # general, maintenance, emergency
    "priority": 2,                   # 0-低, 1-中, 2-高
    "is_pinned": true,               # 是否置顶
    "start_time": "2026-03-19T00:00:00",
    "end_time": "2026-03-20T00:00:00"
}

响应:
{
    "code": 200,
    "message": "公告已发布",
    "data": {
        "id": 1,
        "title": "系统维护通知",
        "type": "maintenance",
        "priority": 2,
        "status": 1,
        "is_pinned": true,
        "created_at": "2026-03-18T12:00:00"
    }
}
```

#### 4.2 公告列表
```
GET /api/admin/announcements?page=1&per_page=20&status=1

查询参数:
- page: 页码
- per_page: 每页数量
- status: 0-草稿, 1-已发布, 2-已下架

响应包含: 标题、类型、优先级、作者、浏览次数、状态等
```

#### 4.3 更新公告
```
PUT /api/admin/announcements/<announcement_id>
Content-Type: application/json

请求体: 同发布公告的字段

响应: 更新后的公告数据
```

#### 4.4 删除/下架公告
```
DELETE /api/admin/announcements/<announcement_id>

# 公告状态变为2 (已下架)，但数据不会被物理删除
```

## 5️⃣ 值班人员 - 快速查看实时占用情况

### 功能说明
为值班人员提供快速查看各房间实时座位占用情况的界面和接口。

### 接口示例

#### 5.1 获取所有房间快查数据
```
GET /api/admin/duty-dashboard

响应:
{
    "code": 200,
    "data": [
        {
            "room_id": 1,
            "room_name": "读书室1",
            "floor": 1,
            "total_seats": 100,
            "occupied_seats": 45,
            "empty_seats": 50,
            "maintenance_seats": 5,
            "occupancy_rate": 45.0,
            "active_reservations": 45
        },
        ...
    ],
    "timestamp": "2026-03-18T12:00:00"
}
```

#### 5.2 获取指定房间详情
```
GET /api/admin/duty-dashboard/room/<room_id>

响应:
{
    "code": 200,
    "data": {
        "room": {
            "id": 1,
            "name": "读书室1",
            "floor": 1
        },
        "seats": [
            {
                "seat_id": 1,
                "seat_number": "1A1",
                "status": 1,                 # 0-空闲, 1-占用, 2-维修
                "status_label": "占用",
                "user_name": "学生1"
            },
            ...
        ]
    }
}
```

## 6️⃣ 审计日志 - 所有关键操作的日志记录

### 日志覆盖的操作
- ✅ 用户禁用/启用
- ✅ 预约强制取消
- ✅ 座位维护问题报告
- ✅ 维护完成
- ✅ 公告发布/更新/删除
- ✅ 其他管理操作

### 记录内容
```
{
    "id": 1,
    "operator_id": 1,                    # 操作人ID
    "operator_name": "管理员",           # 操作人姓名
    "action": "disable",                 # 操作类型
    "module": "user",                    # 操作模块
    "resource_type": "User",             # 资源类型
    "resource_id": 5,                    # 资源ID
    "description": "禁用用户 学生5",     # 操作描述
    "old_values": {"status": 1},         # 修改前的值
    "new_values": {"status": 0},         # 修改后的值
    "status": "success",                 # 操作状态
    "error_message": null,               # 错误信息
    "ip_address": "192.168.1.100",       # 操作者IP
    "user_agent": "Mozilla/5.0...",      # 浏览器信息
    "created_at": "2026-03-18T12:00:00"  # 操作时间
}
```

### 查询审计日志
```
GET /api/admin/audit-logs?page=1&per_page=50&module=user&action=disable&status=success

查询参数:
- page: 页码
- per_page: 每页数量
- module: 模块 (user, maintenance, announcement, reservation, etc)
- action: 操作 (create, update, delete, enable, disable, etc)
- status: 状态 (success, failed)

# 默认显示最近7天的日志
```

## 🔐 身份认证

### 认证方式
现在支持两种认证方式：

1. **Token认证**
```
请求头: X-Admin-Token: admin_test_token
```

2. **用户ID认证**
```
请求头: X-User-Id: 1
```

### 测试账户
```
用户名: root
密码: 123456

登录后可在Web界面中管理系统。
在API中使用认证令牌: admin_test_token
```

## 📊 系统统计接口

```
GET /api/admin/statistics/overview

响应:
{
    "code": 200,
    "data": {
        "users": {
            "total": 150,           # 总用户数
            "active": 145,          # 活跃用户
            "disabled": 5           # 禁用用户
        },
        "today": {
            "total_reservations": 200,  # 今日总预约
            "checked_in": 180,          # 已签到
            "completed": 150            # 已完成
        },
        "seats": {
            "total": 500,               # 总座位
            "occupied": 250,            # 占用座位
            "maintenance": 20,          # 维修座位
            "empty": 230                # 空闲座位
        },
        "maintenance": {
            "pending": 5                # 待处理维护
        }
    }
}
```

## 🚀 快速开始

### 1. 启动服务器
```bash
python run.py
```

### 2. 访问管理后台
```
浏览器访问: http://localhost:5000/admin/login
输入账户: root / 123456
```

### 3. 进行管理操作
- 查看统计数据
- 管理用户（禁用/启用/取消预约）
- 报告座位维护
- 发布系统公告
- 查看审计日志
- 快速查看座位占用情况

## 📝 API使用示例

### Python示例
```python
import requests

headers = {
    'X-Admin-Token': 'admin_test_token',
    'Content-Type': 'application/json'
}

# 获取用户列表
response = requests.get(
    'http://localhost:5000/api/admin/users?page=1&per_page=20',
    headers=headers
)
print(response.json())

# 禁用用户
response = requests.post(
    'http://localhost:5000/api/admin/users/5/disable',
    headers=headers,
    json={'reason': '严重违规'}
)
print(response.json())
```

### JavaScript/Fetch示例
```javascript
const headers = {
    'X-Admin-Token': 'admin_test_token',
    'Content-Type': 'application/json'
};

// 发布公告
fetch('/api/admin/announcements', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        title: '系统维护通知',
        content: '今晚维护',
        type: 'maintenance',
        priority: 2,
        is_pinned: true
    })
})
.then(r => r.json())
.then(data => console.log(data));
```

## ✨ 功能特点

✅ **完整的Web管理界面** - 现代化设计，易于使用
✅ **实时数据统计** - 关键指标动态更新
✅ **座位维护追踪** - 完整的问题报告和维修流程
✅ **灵活的用户管理** - 支持禁用、启用、强制取消等操作
✅ **系统公告管理** - 支持多种类型和优先级设置
✅ **值班快查** - 快速查看实时占用情况
✅ **完整的审计日志** - 记录所有关键操作，便于追溯和分析
✅ **安全的身份认证** - 支持Token和用户ID认证
✅ **响应式设计** - 支持各种设备
✅ **详细的日志记录** - IP地址、浏览器信息等

## 🔗 文件结构

```
app/
├── api/
│   ├── management.py          # 管理员操作接口
│   └── admin.py               # 管理员数据看板API
├── static/
│   ├── css/
│   │   └── admin.css          # 管理界面样式
│   └── js/
│       └── admin.js           # 管理界面脚本
├── templates/
│   ├── admin.html             # 管理界面主页
│   └── admin_login.html       # 登录页面
├── web/
│   └── admin.py               # Web路由
└── models/                    # 数据模型
    ├── audit_log.py           # 审计日志模型
    ├── announcement.py        # 公告模型
    ├── seat_maintenance.py    # 座位维护模型
    └── ...
```

## 📞 支持

如有问题，请检查：
1. 服务器是否正常运行
2. 数据库连接是否正常
3. 认证令牌是否正确
4. 浏览器console中是否有错误信息

---

**版本**: 1.0
**最后更新**: 2026-03-18
**状态**: ✅ 完成并测试


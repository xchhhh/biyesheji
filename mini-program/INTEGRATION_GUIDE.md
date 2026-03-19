# Step 5 - 后端集成指南

## 🔗 小程序与后端系统对接

### 项目层次结构

```
毕业设计/
├── 后端                        # Flask 后端
│   ├── app/
│   │   ├── __init__.py        # 应用工厂
│   │   ├── models/            # 数据模型
│   │   ├── auth/              # 认证模块
│   │   ├── api/
│   │   │   └── reservation.py # 座位预约API ← 小程序调用
│   │   └── utils/
│   │       ├── redis_lock.py  # Redis锁（防超卖）
│   │       └── api.py         # API响应工具
│   ├── requirements.txt
│   └── run.py                 # 启动文件
│
├── mini-program/              # 微信小程序
│   ├── pages/seats/           # 座位选择页面
│   ├── utils/
│   │   ├── api.js             # 小程序API调用
│   │   └── config.js          # 配置
│   └── app.js                 # 应用启动
└── ...
```

## 📡 API 接口映射

### 小程序 ← → 后端

#### 座位查询接口
```
小程序请求:
GET /api/reservations/seats/{room_id}
Headers: {
  Authorization: Bearer <JWT_TOKEN>,
  Content-Type: application/json
}
Params: {
  date: "2024-03-20"  (可选)
}

后端响应 (200):
{
  "code": 0,
  "data": {
    "total": 100,
    "available": 45,
    "occupied": 50,
    "maintenance": 5,
    "seats": [
      {
        "id": 101,
        "seat_number": "A1",
        "status": 0,
        "room_id": 1
      }
    ]
  }
}
```

#### 预约提交接口
```
小程序请求:
POST /api/reservations/reserve
Headers: {
  Authorization: Bearer <JWT_TOKEN>,
  Content-Type: application/json
}
Body: {
  "seat_id": 101,
  "room_id": 1,
  "reservation_date": "2024-03-20",
  "time_slot": "08:00-10:00"
}

后端响应 (200):
{
  "code": 0,
  "data": {
    "reservation_id": 1001,
    "seat_number": "A1",
    "room_id": 1,
    "status": 0,
    "user_id": 123,
    "created_at": "2024-03-17T10:30:00"
  }
}

错误响应 (409):
{
  "code": 409,
  "message": "座位已被他人预约"
}
```

## 🔐 认证流程

### JWT Token 管理

**获取 Token:**
```javascript
// 小程序登录获取token (from Phase 2Step 2)
// 调用微信登录API
wx.login({
  success(res) {
    // res.code 发送到后端
    // 后端验证后返回JWT token
  }
});

// 将token存储到本地
app.setToken(token);
```

**使用 Token:**
```javascript
// api.js 中自动附加
const header = {
  'Authorization': `Bearer ${app.getToken()}`
};

wx.request({
  header: header,  // ← 所有请求都带上token
  // ...
});
```

**Token 过期处理:**
```javascript
// 后端返回 401 时
if (statusCode === 401) {
  app.clearToken();  // 清除本地token
  wx.navigateTo({
    url: '/pages/login/login'  // 跳转到登录
  });
}
```

## 🚀 本地开发启动步骤

### 1. 启动后端服务

```bash
# 切换到后端目录
cd c:\Users\30794\Desktop\毕业设计

# 确保虚拟环境已激活
python -m venv venv
.\venv\Scripts\activate  # Windows

# 安装依赖 (如果还未安装)
pip install -r requirements.txt

# 初始化数据库 (首次运行)
python init_db.py

# 启动Flask应用（开发模式）
python run.py
```

**输出应该显示:**
```
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
 * Restarting with reloader
 * Debugger is active!
 * Debugger PIN: 123-456-789
```

### 2. 启动小程序开发

**使用微信开发者工具:**
1. 打开微信开发者工具
2. 选择 `mini-program` 文件夹导入
3. 确保 `utils/config.js` 中 API_BASE_URL 指向本地：
   ```javascript
   const API_BASE_URL = 'http://localhost:5000/api';
   ```
4. 点击"编译"或按 Ctrl+S 自动编译

### 3. 配置网络请求

**在 project.config.json 中禁用 URL 检查（开发环境）:**
```json
{
  "setting": {
    "urlCheck": false  // ← 允许 http://localhost
  }
}
```

**生产环境必须使用 HTTPS:**
```json
{
  "setting": {
    "urlCheck": true  // ← 生产环境启用
  }
}
```

## 🧪 测试座位预约流程

### 场景：用户预约座位

**步骤1：查询座位**
```javascript
// small-program/pages/seats/seats.js
api.getSeats(1, '2024-03-20')
  .then(response => {
    console.log('座位列表:', response);
    // 显示 100 个座位，绿色可选，红色已占用
  });
```

**后端处理:**
```python
# app/api/reservation.py
@reservation_bp.route('/seats/<int:room_id>', methods=['GET'])
@token_required
def get_seats(room_id):
    date = request.args.get('date')
    
    # 从 Redis 或数据库查询座位状态
    seats = Seat.query.filter_by(room_id=room_id).all()
    
    return ApiResponse.success({
        'seats': [s.to_dict() for s in seats],
        ...
    })
```

**步骤2：用户点击座位并打开Modal**
```javascript
// WXML: <view ... bindtap="onSelectSeat"> 
// JS: 显示日期、时间选择框 + 确认按钮
```

**步骤3：提交预约**
```javascript
// 用户填写日期和时间后，点击确认
api.submitReservation({
  seat_id: 101,
  room_id: 1,
  reservation_date: '2024-03-20',
  time_slot: '08:00-10:00'
})
.then(response => {
  wx.showToast({ title: '预约成功!' });
  // 刷新座位列表
  this.loadSeats();
});
```

**后端处理 (核心anti-overselling逻辑):**
```python
# app/api/reservation.py
@reservation_bp.route('/reserve', methods=['POST'])
@token_required
def submit_reservation(user_id):
    data = request.json
    seat_id = data.get('seat_id')
    room_id = data.get('room_id')
    reservation_date = data.get('reservation_date')
    time_slot = data.get('time_slot')
    
    # 核心：调用 Redis Lua 脚本进行原子操作
    from app.utils.redis_lock import ReservationLuaScript
    lua_script = ReservationLuaScript(redis_client)
    
    result = lua_script.atomic_reserve_seat(
        seat_id=seat_id,
        user_id=user_id,
        room_id=room_id,
        reservation_date=reservation_date,
        time_slot=time_slot
    )
    
    if result['success']:
        # 创建数据库记录
        reservation = Reservation(
            user_id=user_id,
            seat_id=seat_id,
            status=0,  # 待签到
            ...
        )
        db.session.add(reservation)
        db.session.commit()
        
        return ApiResponse.success({
            'reservation_id': reservation.id
        })
    else:
        # 座位被他人抢走
        return ApiResponse.conflict('座位已被他人预约')
```

## 🔄 实时同步数据

### 座位状态缓存策略

**后端 (Redis 缓存):**
```python
# 座位状态 TTL = 5 分钟
SEAT_STATUS_TTL = 300  # 秒

# 预约成功时更新缓存
redis_client.setex(
    f'seat:status:{room_id}:{seat_id}',
    SEAT_STATUS_TTL,
    '1'  # 状态：已占用
)
```

**小程序 (定时刷新):**
```javascript
// pages/seats/seats.js
onShow() {
  // 每次返回页面时刷新
  this.loadSeats();
  
  // 设置定时刷新（可选）
  this.refreshTimer = setInterval(() => {
    this.loadSeats();
  }, 30000);  // 每30秒刷新一次
}

onHide() {
  // 页面隐藏时清除定时器
  if (this.refreshTimer) {
    clearInterval(this.refreshTimer);
  }
}
```

## 🛠️ 故障排查

### 常见问题及解决方案

#### 问题1：小程序无法连接后端
```
错误: Network connection failed
```

**解决方案:**
1. 检查后端是否运行：`http://localhost:5000`
2. 检查 `config.js` 中的 API_BASE_URL
3. 确保防火墙未阻止 5000 端口
4. 开发工具中禁用 URL 检查：`project.config.json` - `"urlCheck": false`

#### 问题2：座位预约返回 409 冲突错误
```
{
  "code": 409,
  "message": "座位已被他人预约"
}
```

**原因:** 多个用户同时预约同一座位 (正常竞争行为)

**解决方案:**
- 小程序收到 409 后，刷新座位列表
- 提示用户"座位已被他人抢走，请选择其他座位"
- 自动重新加载可用座位

#### 问题3：Token 过期，无法预约
```
401 Unauthorized
```

**解决方案:**
```javascript
// api.js 中处理
if (statusCode === 401) {
  app.clearToken();
  wx.navigateTo({ url: '/pages/login/login' });
}
```

#### 问题4：Redis 连接失败
```
ERROR: Redis connection refused
```

**解决方案:**
1. 确保 Redis 服务已启动
2. 检查 Redis 地址和端口
3. 后端应该自动降级到数据库查询（带警告日志）

## 📊 监控和日志

### 后端日志查看

```bash
# 在后端服务启动后
# 查看预约请求日志
tail -f /var/log/flask_app.log

# 或在Flask中配置日志
import logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 小程序日志查看

**在微信开发者工具中:**
1. 打开调试器 (F12 或 Ctrl+Shift+I)
2. 选择 "Console" 标签
3. 查看 `console.log()` 输出
4. 查看网络请求 (Network 标签)

## 🎯 下一步计划

### Phase 5.1 - 我的预约页面
- [ ] 显示用户的所有预约
- [ ] 支持签到/签退
- [ ] 支持取消预约

### Phase 5.2 - 二维码签到
- [ ] 扫描 QR 码进行签到
- [ ] 整合后端 `/reservations/check-in` API

### Phase 5.3 - 座位热力分析
- [ ] 显示不同时间段的热力图
- [ ] 推荐最佳座位
- [ ] 每日使用统计

### Phase 5.4 - 生产部署
- [ ] 配置 HTTPS
- [ ] 部署到腾讯云/阿里云
- [ ] 配置小程序发布

---

**相关文档:**
- [完整开发指南](./MINI_PROGRAM_GUIDE.md)
- [快速参考](./QUICK_REFERENCE.md)
- [后端API文档](../STEP_3_QUICK_REFERENCE.md)

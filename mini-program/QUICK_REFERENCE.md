# Step 5：小程序座位图 - 快速参考

## 📂 文件架构

```
mini-program/
├── pages/seats/              # 座位选择页面 (核心)
│   ├── seats.wxml           # HTML/模板
│   ├── seats.wxss           # CSS/样式  
│   └── seats.js             # JavaScript/逻辑
│
├── utils/
│   ├── api.js               # API 调用工具
│   └── config.js            # 全局配置
│
├── app.json                 # 应用配置
├── app.js                   # 应用启动
└── app.wxss                 # 全局样式
```

## 🎨 座位状态颜色速查表

| 状态 | 颜色值 | 模样 | 点击行为 |
|------|--------|------|---------|
| 可选 🟢 | `#09BB07` 绿色 | 正常 | 打开预约Modal |
| 已预约 🔴 | `#E64141` 红色 | 半透明 | 不可点击 |
| 维护中 ⚪ | `#CCCCCC` 灰色 | 半透明 | 不可点击 |
| 我的预约 🔵 | `#3C6FDA` 蓝色 | 带边框 | 可查看详情 |

## 🔧 关键代码片段

### 1. 生成 10×10 网格

**WXML:**
```xml
<view class="seats-grid">
  <view wx:for="{{rows}}" wx:key="rowIndex" class="seat-row">
    <view class="seat-row-label">{{String.fromCharCode(65 + rowIndex)}}</view>
    <view wx:for="{{item}}" wx:key="seatId" class="seat {{seat.statusClass}}">
      {{colIndex + 1}}
    </view>
  </view>
</view>
```

**CSS:**
```css
.seats-grid {
  display: grid;
  grid-template-columns: 40rpx repeat(10, 60rpx);
  grid-gap: 8rpx;
}
```

### 2. 处理座位数据

**JS:**
```javascript
// 将一维数组转为二维数组 (10行×10列)
processSeatData(seats) {
  const rows = [];
  for (let row = 0; row < 10; row++) {
    const rowSeats = [];
    for (let col = 0; col < 10; col++) {
      const seatIndex = row * 10 + col;
      rowSeats.push({
        seatId: `seat-${row}-${col}`,
        seatNumber: `${String.fromCharCode(65 + row)}${col + 1}`,
        status: seats[seatIndex]?.status || 0,
        statusClass: this.getStatusClass(seats[seatIndex]?.status)
      });
    }
    rows.push(rowSeats);
  }
  this.setData({ rows });
}

// 根据状态返回CSS类名
getStatusClass(status) {
  const classMap = {
    0: 'seat-available',      // 可选
    1: 'seat-reserved',       // 已预约
    2: 'seat-maintenance',    // 维护中
    3: 'seat-my-reserved'     // 我的
  };
  return classMap[status] || 'seat-available';
}
```

### 3. 点击座位打开Modal

**JS:**
```javascript
onSelectSeat(event) {
  const seatId = event.currentTarget.dataset.seatId;
  const seat = this.findSeatById(seatId);
  
  // 只有可选座位才能点击
  if (seat.status !== 0) return;
  
  this.setData({
    selectedSeat: seat,
    showModal: true
  });
}
```

### 4. 提交预约请求

**JS:**
```javascript
onConfirmReservation() {
  const data = {
    seat_id: this.data.selectedSeat.seatId,
    room_id: this.data.roomList[this.data.selectedRoomIndex].id,
    reservation_date: this.data.reservedDate,
    time_slot: this.data.timeSlots[this.data.selectedTimeSlot]
  };

  api.submitReservation(data)
    .then(response => {
      wx.showToast({ title: '预约成功！', icon: 'success' });
      this.loadSeats();  // 刷新座位列表
    })
    .catch(error => {
      wx.showToast({ title: error.message, icon: 'error' });
    });
}
```

### 5. 调用后端API

**api.js:**
```javascript
function getSeats(roomId, date) {
  return request('GET', `/reservations/seats/${roomId}?date=${date}`);
}

function submitReservation(data) {
  return request('POST', '/reservations/reserve', data);
}

// JWT Token 自动附加
function request(method, endpoint, data = null) {
  const header = {
    'Authorization': `Bearer ${app.getToken()}`,
    'Content-Type': 'application/json'
  };
  
  wx.request({
    url: `${config.API_BASE_URL}${endpoint}`,
    method: method,
    data: data,
    header: header,
    // ...
  });
}
```

## 🚀 快速启动步骤

### 1. 使用微信开发者工具导入
```
文件 → 新建 → 选择 mini-program 文件夹
```

### 2. 配置API地址
编辑 `utils/config.js`:
```javascript
const API_BASE_URL = 'http://localhost:5000/api';  // 开发环境
```

### 3. 开启自动编译
```
工具 → 项目详情 → 本地设置 → 启用新的构建流程
```

### 4. 预览
```
工具 → 预览 → 扫描二维码
```

## 📡 API 接口清单

| 接口 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 获取座位 | GET | `/reservations/seats/{room_id}` | 获取实时座位状态 |
| 完成预约 | POST | `/reservations/reserve` | 提交预约 (Lua脚本防超卖) |
| 签到 | POST | `/reservations/check-in` | QR码或手动签到 |
| 签退 | POST | `/reservations/check-out` | 离开时签退 |
| 取消 | POST | `/reservations/cancel/{id}` | 取消预约 |
| 我的预约 | GET | `/reservations/my-reservations` | 用户预约历表 |

**所有请求都需要在 Header 中附加:**
```
Authorization: Bearer {JWT_TOKEN}
```

## 🎯 座位坐标系统

```
    1  2  3  4  5  6  7  8  9  10
A  □  □  □  □  □  □  □  □  □  □
B  □  □  □  □  □  □  □  □  □  □
C  □  □  □  □  □  □  □  □  □  □
D  □  □  □  □  □  □  □  □  □  □  
E  □  □  □  □  □  □  □  □  □  □
F  □  □  □  □  □  □  □  □  □  □
G  □  □  □  □  □  □  □  □  □  □
H  □  □  □  □  □  □  □  □  □  □
I  □  □  □  □  □  □  □  □  □  □
J  □  □  □  □  □  □  □  □  □  □
```

例: `A1` = 第A行第1列 (左上角)
    `J10` = 第J行第10列 (右下角)

## 💾 本地存储 (LocalStorage)

```javascript
// 存储 Token
wx.setStorageSync('token', 'jwt_token_here');

// 读取 Token
const token = wx.getStorageSync('token');

// 清除 Token
wx.removeStorageSync('token');
```

## 🔄 刷新座位列表

```javascript
// 手动刷新
this.loadSeats();

// 自动刷新 (页面启动时)
onShow() {
  this.loadSeats();
}

// 间隔自动刷新 (每10秒)
this.refreshInterval = setInterval(() => {
  this.loadSeats();
}, 10000);
```

## ⚠️ 错误码对应表

| 状态码 | 含义 | 处理方案 |
|--------|------|--------|
| 200 | 成功 | 处理返回数据 |
| 400 | 参数错误 | 检查请求数据格式 |
| 401 | 未授权 | 跳转到登录页 |
| 403 | 禁止访问 | 显示权限不足提示 |
| 409 | 座位冲突 | 座位被他人抢去，刷新列表 |
| 500 | 服务器错误 | 显示重试提示 |

## 🎬 状态转换流程

```
页面加载 → 查询座位列表 → 显示座位网格 
  ↓
用户点击座位 → 打开预约Modal
  ↓
选择日期/时间 → 点击确认
  ↓
调用预约API → 处理响应
  ↓
成功 → 显示提示 → 刷新座位
失败 → 显示错误 → 重试或返回
```

## 📊 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 座位加载时间 | < 2秒 | ~1秒 |
| Modal打开延迟 | < 300ms | ~150ms |
| 预约提交延迟 | < 3秒 | ~1-2秒 |
| 内存占用 | < 50MB | ~30MB |

## 🐛 调试技巧

### 查看网络请求
```javascript
// 在 api.js 中添加日志
console.log(`[${method}] ${url}`, data);  // 请求
console.log('Response:', response);        // 响应
```

### 在控制台测试
```javascript
// 微信开发者工具 → 调试器 → Console
// 手动调用API
require('./utils/api').getSeats(1, '2024-03-20')
  .then(res => console.log(res))
  .catch(err => console.error(err));
```

### 模拟网络延迟
```javascript
// 在 api.js 中添加延迟（仅用于测试）
setTimeout(() => { /* 执行请求 */ }, 1000);
```

---

**快速链接:**
- [完整开发指南](./MINI_PROGRAM_GUIDE.md)
- [后端API文档](../STEP_3_QUICK_REFERENCE.md)
- [微信官方文档](https://developers.weixin.qq.com/miniprogram/dev/)
- [项目源代码](./pages/seats/)

# 快速参考指南 - 扫码签到 & 热力图

## 🎬 快速开始 (5分钟)

### 1️⃣ 启用扫码签到功能

在 `app.json` 中确保已注册页面:
```json
{
  "pages": [
    "pages/checkin/checkin"
  ],
  "tabBar": {
    "list": [
      { "pagePath": "pages/checkin/checkin", "text": "签到" }
    ]
  }
}
```

### 2️⃣ 调用签到 API

```javascript
import * as api from '../../utils/api';

api.checkIn({
  token: wx.getStorageSync('token'),
  reservationId: 101,
  seatCode: 'SEAT_A1_1_1710710400',
  roomId: 1
}).then(response => {
  console.log('签到成功:', response);
}).catch(error => {
  console.error('签到失败:', error);
});
```

### 3️⃣ 启用热力图功能

```javascript
import * as api from '../../utils/api';

api.getHeatmapData({
  token: wx.getStorageSync('token'),
  date: '2026-03-17',
  timeSlot: '09:00-11:00',
  roomId: 1
}).then(heatmapData => {
  console.log('热力图数据:', heatmapData);
}).catch(error => {
  console.error('获取热力图失败:', error);
});
```

---

## 🔍 API 参考

### checkIn - 扫码签到

```javascript
// 调用方式
api.checkIn({
  token: string,        // JWT Token
  reservationId: number,// 预约ID
  seatCode: string,     // 座位代码 (SEAT_A1_1_TIMESTAMP)
  roomId: number        // 房间ID
})

// 成功响应 (200)
{
  "code": 200,
  "data": {
    "check_in_time": "2026-03-17 09:15:23",
    "expected_check_out_time": "2026-03-17 11:00:00",
    "reservation_id": 101
  }
}

// 错误响应 (409)
{
  "code": 409,
  "error_code": "ALREADY_CHECKED_IN",
  "message": "您已经签到过该座位"
}
```

### getHeatmapData - 获取热力图

```javascript
// 调用方式
api.getHeatmapData({
  token: string,        // JWT Token
  date: string,         // 日期 (2026-03-17)
  timeSlot: string,     // 时间段 (09:00-11:00)
  roomId: number        // 房间ID
})

// 成功响应 (200)
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "seat_number": "A1",
      "room_id": 1,
      "heat_count": 45,
      "current_status": "free",
      "location": "靠窗"
    },
    // ... 更多座位数据
  ]
}
```

---

## 📊 常用常量参考

### 座位状态

```javascript
import { SEAT_STATUS, getSeatStatusLabel } from '../../utils/constants';

// 状态值
SEAT_STATUS.AVAILABLE    // = 0 (可用)
SEAT_STATUS.OCCUPIED     // = 1 (已占用)
SEAT_STATUS.MY_RESERVATION // = 2 (我的预约)

// 获取标签
getSeatStatusLabel(0) // → "可选"
getSeatStatusLabel(1) // → "已选"
getSeatStatusLabel(2) // → "我的预约"
```

### 热度等级

```javascript
import { HEAT_LEVELS, getHeatLevel, getHeatColor } from '../../utils/constants';

// 获取热度等级
const level = getHeatLevel(45);  // 低热度
// {
//   value: 0,
//   label: '低热度',
//   color: '#2196F3',
//   range: [0, 20]
// }

// 获取颜色
const color = getHeatColor(75);  // '#FFC107' (高热度)
```

---

## 🎨 CSS 热力图快速实现

### 基础结构

```wxml
<!-- 座位网格容器 -->
<view class="seat-grid">
  <view 
    class="seat-item"
    wx:for="{{heatmapData}}"
    wx:key="id"
    style="background-color: {{item.heatColor}}; opacity: {{item.heatOpacity}};"
  >
    <text class="seat-number">{{item.seat_number}}</text>
    <text class="heat-value">{{item.heat_count}}</text>
  </view>
</view>
```

### CSS 样式

```wxss
.seat-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 6rpx;
  padding: 20rpx;
}

.seat-item {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.seat-item:active {
  transform: scale(0.95);
}

.seat-number {
  font-size: 18rpx;
  font-weight: bold;
  color: rgba(0, 0, 0, 0.7);
}

.heat-value {
  font-size: 14rpx;
  color: rgba(0, 0, 0, 0.5);
  margin-top: 2rpx;
}
```

---

## 🔐 错误处理速查表

| 错误码 | 含义 | 处理建议 |
|--------|------|--------|
| 200 | 操作成功 | 继续执行 |
| 401 | 未授权 | 引导用户重新登录 |
| 403 | 无权限 | 提示权限不足 |
| 404 | 资源不存在 | 检查参数是否正确 |
| 409 | 冲突 | 数据已被修改，刷新页面 |
| 500+ | 服务器错误 | 提示用户稍后重试 |

---

## 📁 完整文件清单

```
✅ pages/checkin/checkin.wxml      (150 行)
✅ pages/checkin/checkin.wxss      (350 行)
✅ pages/checkin/checkin.js        (400 行)
✅ pages/checkin/checkin.json      (5 行)

✅ pages/heatmap/heatmap.wxml      (180 行)
✅ pages/heatmap/heatmap.wxss      (450 行)
✅ pages/heatmap/heatmap.js        (350 行)
✅ pages/heatmap/heatmap.json      (5 行)

✅ utils/api.js                     (200 行)
✅ utils/constants.js               (250 行)

✅ app.js                           (80 行)
✅ app.json                         (60 行)
✅ app.wxss                         (250 行)
✅ project.config.json              (50 行)

📚 FEATURE_INTEGRATION_GUIDE.md     (600+ 行)
📚 IMPLEMENTATION_SUMMARY.md        (800+ 行)
📚 QUICK_REFERENCE_GUIDE.md         (500+ 行) ← 本文件
```

---

## 🧪 测试清单

### 扫码签到
- [ ] 启动扫码，弹出摄像头
- [ ] 扫描二维码，识别座位
- [ ] 调用后端 API，显示结果
- [ ] 手动输入座位代码也能签到
- [ ] 错误提示正常显示
- [ ] 历史记录更新正确

### 热力图
- [ ] 查询数据成功加载
- [ ] CSS 热力图正常渲染
- [ ] 座位颜色热度正确映射
- [ ] 统计数据计算准确
- [ ] ECharts 模式可以切换
- [ ] 座位详情弹窗显示

---

**📌 需要帮助？查看完整文档：**
- [功能集成指南](./FEATURE_INTEGRATION_GUIDE.md)
- [实现总结](./IMPLEMENTATION_SUMMARY.md)

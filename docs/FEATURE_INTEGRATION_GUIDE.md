# 座位热力图与扫码签到功能实现指南

## 🎯 功能概述

本项目已完成两个重要的前端功能模块：**扫码签到系统** 和 **座位热力图展示**。这两个功能与后端 API 集成，为用户提供完整的座位管理体验。

---

## 📱 扫码签到功能（Check-in）

### 功能特性

✅ **二维码扫描**：集成微信原生 `wx.scanCode` API
✅ **座位验证**：支持一维码和二维码格式识别  
✅ **手动输入**：提供备选方案，支持直接输入座位代码
✅ **实时反馈**：成功/失败结果实时显示
✅ **历史记录**：展示最近的签到记录
✅ **错误处理**：完善的企业级错误提示

### 页面结构

```
pages/checkin/
├── checkin.wxml      - 页面标记（HTML相当品）
├── checkin.wxss      - 页面样式（CSS相当品）
├── checkin.js        - 页面逻辑与事件处理
└── checkin.json      - 页面配置
```

### 核心功能实现

#### 1️⃣ 启动扫码
```javascript
handleScanCode() {
  wx.scanCode({
    onlyFromCamera: false,
    scanType: ['qrCode', 'barCode'],
    success: (res) => {
      this.processScannedCode(res.result);
    }
  });
}
```

#### 2️⃣ 处理扫码结果
```javascript
async processScannedCode(scannedCode) {
  // 解析二维码格式: SEAT_A1_1_1234567890
  const match = scannedCode.match(/^SEAT_([A-Z0-9]+)_(\d+)_(\d+)$/);
  
  if (match) {
    // 验证时间戳（防过期）
    // 调用 checkIn API
  }
}
```

#### 3️⃣ 调用后端 API
```javascript
api.checkIn({
  token,
  reservationId: currentReservation.reservation_id,
  seatCode,
  roomId: currentReservation.room_id
})
```

### 二维码格式说明

推荐的二维码编码格式：
```
SEAT_{SEAT_CODE}_{ROOM_ID}_{TIMESTAMP}
例: SEAT_A1_1_1710710400
```

**字段说明**：
- `SEAT_CODE`: 座位标识（如 A1, B5, C10）
- `ROOM_ID`: 阅览室ID
- `TIMESTAMP`: Unix时间戳（用于验证二维码有效期）

### 后端集成

后端需实现的 API 端点：

```bash
POST /api/reservations/check-in
请求体:
{
  "reservation_id": 101,
  "seat_code": "SEAT_A1_1_1710710400",
  "room_id": 1
}

响应:
{
  "code": 200,
  "data": {
    "check_in_time": "2026-03-17 09:15:23",
    "expected_check_out_time": "2026-03-17 11:15:23",
    "reservation_id": 101
  }
}
```

### 错误处理映射

| 错误码 | 场景 | 用户提示 |
|------|------|--------|
| `RESERVATION_NOT_FOUND` | 没有该座位预约 | 预约不存在 |
| `ALREADY_CHECKED_IN` | 已经签过到 | 已签到 |
| `SEAT_CODE_MISMATCH` | 二维码与预约座位不符 | 座位代码不匹配 |
| `TIME_SLOT_NOT_STARTED` | 预约时间还没开始 | 还未到预约时间 |
| `ROOM_NOT_OPEN` | 阅览室还未开放 | 阿览室未开放 |

---

## 🔥 座位热力图功能（Heatmap）

### 功能特性

✅ **CSS动态热力图**：基于背景透明度的轻量级实现
✅ **ECharts集成**：专业的可视化展示方案
✅ **数据选择器**：按日期、时间段、房间筛选
✅ **统计仪表盘**：实时座位统计信息
✅ **热度排行**：座位使用频率排名前10
✅ **座位详情**：点击座位查看具体信息
✅ **多视角展示**：表格、热力图、拆机统计结果

### 页面结构

```
pages/heatmap/
├── heatmap.wxml      - 页面标记
├── heatmap.wxss      - 页面样式
├── heatmap.js        - 页面逻辑
└── heatmap.json      - 页面配置
```

### 热力图实现方案

#### 方案一：CSS 背景透明度（推荐）

```javascript
// 处理热力图数据
processHeatmapData(rawData) {
  return rawData.map(seat => {
    const heatCount = seat.heat_count || 0;
    
    // 确定颜色梯度
    let heatColor;
    if (heatCount <= 20) {
      heatColor = '#2196F3'; // 蓝色 - 低热度
    } else if (heatCount <= 50) {
      heatColor = '#4CAF50'; // 绿色 - 中热度
    } else if (heatCount <= 80) {
      heatColor = '#FFC107'; // 黄色 - 高热度
    } else {
      heatColor = '#F44336'; // 红色 - 极热度
    }
    
    // 计算透明度 (0.3-1.0)
    const heatIntensity = Math.min(heatCount / 100, 1);
    const opacity = 0.3 + heatIntensity * 0.7;
    
    return {
      ...seat,
      heatColor,
      heatOpacity: opacity
    };
  });
}
```

**WXML 标记**：
```wxml
<view class="seat-grid css-mode">
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

#### 方案二：ECharts 热力图

ECharts 微信小程序版本提供更专业的可视化：

```javascript
// 导入 ECharts 库
import * as echarts from '../../utils/echarts.min.js';

initializeChart(heatmapData) {
  const option = {
    title: {
      text: '座位热力分布',
      left: 'center'
    },
    tooltip: { show: true },
    grid: { containLabel: true },
    xAxis: {
      type: 'category',
      data: Array.from({length: 10}, (_, i) => String(i + 1))
    },
    yAxis: {
      type: 'category',
      data: ['行1', '行2', '行3', '行4', '行5', '行6', '行7', '行8', '行9', '行10']
    },
    visualMap: {
      min: 0,
      max: 100,
      splitNumber: 5,
      inRange: {
        color: ['#2196F3', '#4CAF50', '#FFC107', '#F44336']
      }
    },
    series: [{
      name: '座位热度',
      type: 'heatmap',
      data: heatmapData.map(seat => [
        parseInt(seat.seat_number.charCodeAt(1)) - 1,
        parseInt(seat.seat_number.charCodeAt(0)) - 65,
        seat.heat_count
      ]),
      label: { show: true }
    }]
  };
  
  this.chart.setOption(option);
}
```

### 热度等级定义

| 等级 | 范围 | 颜色 | 描述 |
|------|------|------|------|
| 低热度 | 0-20 | 蓝 (#2196F3) | 使用频率低，容易找到座位 |
| 中热度 | 21-50 | 绿 (#4CAF50) | 正常使用频率 |
| 高热度 | 51-80 | 黄 (#FFC107) | 较热门，可能不易找到座位 |
| 极热度 | 81+ | 红 (#F44336) | 非常热门，推荐选择其他座位 |

### 后端 API 集成

```bash
GET /api/statistics/heatmap?date=2026-03-17&time_slot=09:00-11:00&room_id=1

响应:
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
    ...
  ]
}
```

### 统计信息计算

```javascript
calculateStats(heatmapData) {
  const totalSeats = heatmapData.length;
  const occupiedCount = heatmapData.filter(s => s.current_status === 'occupied').length;
  const occupancyRate = Math.round((occupiedCount / totalSeats) * 100);
  
  this.setData({
    stats: {
      totalSeats,
      occupiedCount,
      availableCount: totalSeats - occupiedCount,
      occupancyRate
    }
  });
}
```

---

## 🔌 API 服务层集成

### 新增 API 方法

在 `utils/api.js` 中添加了两个新方法：

#### 签到 API
```javascript
export function checkIn(options) {
  const { token, reservationId, seatCode, roomId } = options;
  return request({
    method: 'POST',
    url: '/api/reservations/check-in',
    data: {
      reservation_id: reservationId,
      seat_code: seatCode,
      room_id: roomId
    },
    token
  });
}
```

#### 热力图 API
```javascript
export function getHeatmapData(options) {
  const { token, date, timeSlot, roomId } = options;
  const params = new URLSearchParams({
    date,
    time_slot: timeSlot,
    room_id: roomId
  }).toString();

  return request({
    method: 'GET',
    url: `/api/statistics/heatmap?${params}`,
    token
  });
}
```

---

## 📋 常量配置

`utils/constants.js` 提供了集中的常量管理：

```javascript
// 座位状态
export const SEAT_STATUS = {
  AVAILABLE: 0,
  OCCUPIED: 1,
  MY_RESERVATION: 2
};

// 热力图等级
export const HEAT_LEVELS = {
  LOW: { value: 0, label: '低热度', color: '#2196F3' },
  MEDIUM: { value: 1, label: '中热度', color: '#4CAF50' },
  HIGH: { value: 2, label: '高热度', color: '#FFC107' },
  EXTREME: { value: 3, label: '极热度', color: '#F44336' }
};

// 时间段
export const TIME_SLOTS = [
  { id: 1, label: '09:00-11:00', value: '09:00-11:00' },
  // ...
];

// 阅览室
export const ROOMS = [
  { id: 1, name: '阅览室A', location: '一楼西侧' },
  // ...
];
```

---

## 🎨 页面导航注册

`app.json` 已更新，注册了新页面：

```json
{
  "pages": [
    "pages/index/index",
    "pages/reservation/reservation",
    "pages/checkin/checkin",        // 新增
    "pages/heatmap/heatmap",         // 新增
    "pages/my/my"
  ],
  "tabBar": {
    "list": [
      { "pagePath": "pages/checkin/checkin", "text": "签到" },
      { "pagePath": "pages/heatmap/heatmap", "text": "热力图" }
    ]
  }
}
```

---

## 🧪 功能测试清单

### 扫码签到测试

- [ ] 点击"启动扫码"按钮，弹出摄像头
- [ ] 扫描二维码，成功解析座位代码
- [ ] 二维码格式验证通过
- [ ] 调用后端API成功
- [ ] 显示签到成功信息
- [ ] 历史记录更新正确
- [ ] 手动输入座位代码也能签到
- [ ] 错误提示正常显示

### 热力图测试

- [ ] 选择日期、时间、房间后查询
- [ ] CSS热力图正常渲染（10x10网格）
- [ ] 座位颜色颜度正确映射
- [ ] 统计卡片数据正确计算
- [ ] 点击座位展示详情弹窗
- [ ] ECharts模式切换流畅
- [ ] 热度排行表格显示正确
- [ ] 总结信息计算准确

---

## 📦 文件清单

### 新增文件
```
pages/checkin/
├── checkin.wxml
├── checkin.wxss
├── checkin.js
└── checkin.json

pages/heatmap/
├── heatmap.wxml
├── heatmap.wxss
├── heatmap.js
└── heatmap.json

utils/
├── api.js (已更新，新增 checkIn/getHeatmapData)
└── constants.js

app.json (已更新，注册新页面)
app.js (新增)
app.wxss (新增)
project.config.json (新增)
```

---

## 🚀 部署说明

### 前端部署
1. 将所有文件上传到 WeChat 开发者工具
2. 在 `project.config.json` 中配置正确的 AppID
3. 设置 API_BASE_URL 指向你的后端服务
4. 构建并预览

### 后端部署
需要实现以下 API 端点：
- `POST /api/reservations/check-in` - 签到
- `GET /api/statistics/heatmap` - 获取热力图数据
- `POST /api/reservations/check-out` - 签出（可选）
- `GET /api/statistics/seat-ranking` - 座位排行（可选）

---

## 💡 最佳实践

### 1. 二维码生成
在后端为每个座位生成动态二维码，包含时间戳用于有效期验证：
```python
import qrcode
timestamp = int(time.time())
data = f"SEAT_A1_1_{timestamp}"
qr = qrcode.make(data)
```

### 2. 热力图缓存
热力图数据变化不频繁，建议设置缓存策略：
```python
# Redis 缓存热力图数据 30 分钟
cache_key = f"heatmap:{date}:{time_slot}:{room_id}"
redis.setex(cache_key, 1800, json.dumps(data))
```

### 3. 完并发处理
扫码签到时需要做并发安全检查：
```python
# 使用 Redis Lua 脚本保证原子性
# 检查座位状态 -> 更新座位状态 -> 创建签到记录
```

### 4. 用户隐私
不要在热力图中显示用户个人信息，只显示使用统计数据。

---

## 📞 故障排查

### 问题：扫码后没有响应
- 检查 `wx.scanCode` API 是否被正确调用
- 确保已在 `app.json` 中声明摄像头权限
- 验证后端 `/api/reservations/check-in` 端点是否可达

### 问题：热力图数据为空
- 确保后端 `/api/statistics/heatmap` 返回正确数据格式
- 检查日期、时间段参数是否正确传递
- 验证该时间段是否有有效数据

### 问题：性能卡顿
- CSS热力图：优化座位数量或使用虚拟滚动
- ECharts热力图：使用事件节流，避免频繁更新

---

## 📚 相关资源

- [微信小程序官方文档](https://developers.weixin.qq.com/miniprogram/)
- [wx.scanCode API](https://developers.weixin.qq.com/miniprogram/dev/api/device/scan/wx.scanCode.html)
- [ECharts 小程序版本](https://github.com/ecomfe/echarts-for-weixin)
- [Flask 后端框架](https://flask.palletsprojects.com/)
- [Redis 缓存](https://redis.io/)

---

祝开发顺利！🎉

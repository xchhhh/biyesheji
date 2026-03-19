# Step 5：小程序基础页面与座位图渲染 - 完整实现指南

## 📋 项目结构概览

```
mini-program/
├── app.json                  # 小程序全局配置
├── app.js                    # 小程序启动文件
├── app.wxss                  # 全局样式表
├── project.config.json       # IDE 项目配置
├── sitemap.json             # 页面 SEO 配置
│
├── pages/
│   └── seats/
│       ├── seats.wxml       # 座位选择页面 (HTML结构)
│       ├── seats.wxss       # 座位选择页面样式
│       └── seats.js         # 座位选择页面逻辑
│
└── utils/
    ├── api.js               # API 调用工具
    └── config.js            # 全局配置和存储工具
```

## 🎯 核心功能实现

### 1. 座位网格渲染（10×10 CSS Grid）

#### WXML 结构
```wxml
<view class="seats-grid">
  <!-- 自动生成 10×10 网格 -->
  <view wx:for="{{rows}}" wx:key="rowIndex" class="seat-row">
    <view class="seat-row-label">{{String.fromCharCode(65 + rowIndex)}}</view>
    <view wx:for="{{item}}" wx:key="seatId" class="seat {{seat.statusClass}}">
      {{colIndex + 1}}
    </view>
  </view>
</view>
```

**关键技术点:**
- 使用 CSS Grid 布局实现 10×10 座位网格
- `wx:for` 循环生成行和列
- 动态绑定座位状态样式类

#### 网格尺寸计算
- 每个座位: 60rpx × 60rpx
- 间距: 8rpx
- 总宽度: (40 + 60×10 + 8×10)rpx ≈ 760rpx

#### CSS Grid 定义
```css
.seats-grid {
  display: grid;
  grid-template-columns: 40rpx repeat(10, 60rpx);  /* 列标签 + 10列座位 */
  grid-gap: 8rpx;
}
```

### 2. 座位状态样式

| 状态 | 颜色 | CSS类 | 用户操作 |
|------|------|-------|--------|
| 可选 | 绿色 (#09BB07) | `seat-available` | 可点击预约 |
| 已预约 | 红色 (#E64141) | `seat-reserved` | 不可点击，半透明 |
| 维护中 | 灰色 (#CCC) | `seat-maintenance` | 不可点击 |
| 我的预约 | 蓝色 (#3C6FDA) | `seat-my-reserved` | 可点击查看详情 |

#### 样式实现
```wxss
/* 可选座位 - 绿色 */
.seat-available {
  background-color: #09bb07;
  color: white;
  box-shadow: 0 4rpx 8rpx rgba(9, 187, 7, 0.2);
}

.seat-available:active {
  transform: scale(0.95);  /* 点击反馈 */
}

/* 已预约座位 - 红色半透明 */
.seat-reserved {
  background-color: #e64141;
  opacity: 0.6;
  cursor: not-allowed;
}

/* 我的预约座位 - 蓝色带边框 */
.seat-my-reserved {
  background-color: #3c6fda;
  border: 2rpx solid #0a47a5;
}
```

### 3. 后端接口调用（模拟实现）

#### 获取座位列表接口
```javascript
api.getSeats(roomId, reservationDate)
  .then(response => {
    // 响应格式:
    // {
    //   "total": 100,
    //   "available": 45,
    //   "occupied": 50,
    //   "maintenance": 5,
    //   "seats": [
    //     { "id": "seat-1", "status": 0 },  // 0=可选
    //     { "id": "seat-2", "status": 1 },  // 1=已预约
    //     ...
    //   ]
    // }
    this.processSeatData(response.seats);
  })
  .catch(error => {
    // 错误处理：使用模拟数据
    this.generateMockSeats();
  });
```

#### 提交预约接口
```javascript
api.submitReservation({
  seat_id: 101,
  room_id: 1,
  reservation_date: "2024-03-20",
  time_slot: "08:00-10:00"
})
.then(response => {
  // 预约成功
  console.log('预约ID:', response.reservation_id);
})
.catch(error => {
  // 错误处理（座位被占、token失效等）
  console.error('预约失败:', error.message);
});
```

### 4. Modal 确认框

#### 功能特性
- ✓ 底部弹出动画
- ✓ 半透明遮罩背景
- ✓ 选择日期和时间段
- ✓ 预约说明提示

#### 打开 Modal
```javascript
onSelectSeat(event) {
  // 只有"可选"座位才能点击
  if (seat.status !== 0) return;

  this.setData({
    selectedSeat: seat,
    showModal: true  // 显示模态框
  });
}
```

#### 关闭 Modal
```javascript
onCancelModal() {
  this.setData({
    showModal: false,
    selectedSeat: null
  });
}
```

## 🔧 开发与调试

### 1. 使用微信开发者工具

**开发工具下载**: [https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)

**导入项目步骤:**
1. 打开微信开发者工具
2. 点击"导入项目"
3. 选择 `mini-program` 文件夹
4. 输入测试用的 AppID （可使用测试ID或校园代码）
5. 点击导入

### 2. 配置 AppID

编辑 `project.config.json`:
```json
{
  "appid": "your_test_appid_here",
  "projectname": "seat-reservation"
}
```

获取测试 AppID:
- 微信开发平台: https://developers.weixin.qq.com/
- 或使用开发者工具的"测试号"功能

### 3. 本地调试

**VS Code 设置（推荐）:**
1. 安装 "小程序编程" 插件
2. VS Code 右键查看 WXML 预览
3. 配合微信开发者工具的"自动编译"使用

**常见调试技巧:**
```javascript
// 在 JS 中打印日志
console.log('座位数据:', this.data.rows);

// 在开发者工具控制台查看
// 可在模拟器或真机上查看

// 使用微信开发者工具的"条件编译"
// #ifdef WECHAT
  console.log('微信小程序');
// #endif
```

### 4. 真机调试

**预览步骤:**
1. 微信开发者工具：菜单 → 预览
2. 用微信扫描二维码
3. 在微信中打开小程序进行测试
4. 手机上右滑进入"开发调试"模式查看日志

## 📡 后端接口对接

### 配置 API 基址

编辑 `utils/config.js`:
```javascript
// 开发环境
const API_BASE_URL = 'http://localhost:5000/api';

// 生产环境（替换为实际服务器）
const API_BASE_URL = 'https://api.example.com/api';
```

### 接口列表

#### 1. 获取座位列表
```
GET /api/reservations/seats/{room_id}?date=YYYY-MM-DD
```

**请求头:**
```
Authorization: Bearer {jwt_token}
```

**响应示例:**
```json
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
      },
      {
        "id": 102,
        "seat_number": "A2",
        "status": 1,
        "room_id": 1
      }
    ]
  }
}
```

#### 2. 提交预约
```
POST /api/reservations/reserve
```

**请求体:**
```json
{
  "seat_id": 101,
  "room_id": 1,
  "reservation_date": "2024-03-20",
  "time_slot": "08:00-10:00"
}
```

**成功响应:**
```json
{
  "code": 0,
  "data": {
    "reservation_id": 1001,
    "seat_number": "A1",
    "status": 0,
    "created_at": "2024-03-17 10:30:00"
  }
}
```

**错误响应:**
- 409 Conflict: 座位已被他人预约
- 400 Bad Request: 请求参数错误
- 401 Unauthorized: token 过期或无效

## 🎨 UI/UX 优化建议

### 1. 加载状态优化
```javascript
// 显示加载中指示器
this.setData({ isLoading: true });

// 模拟网络延迟
setTimeout(() => {
  this.loadSeats();
}, 500);
```

### 2. 错误处理
```javascript
.catch(error => {
  // 网络错误
  if (error.code === -1) {
    wx.showToast({
      title: '网络连接失败',
      icon: 'error'
    });
  }
  
  // 服务器错误
  if (error.code === 500) {
    wx.showToast({
      title: '服务器错误，请稍后重试',
      icon: 'error'
    });
  }

  // 业务逻辑错误
  if (error.code === 409) {
    wx.showToast({
      title: '座位已被他人预约',
      icon: 'error'
    });
  }
});
```

### 3. 用户反馈
- 座位点击时显示选中状态
- 提交预约时优化表单验证
- 成功后显示浮窗提示

### 4. 性能优化
- 座位列表缓存（5分钟TTL）
- 延迟加载图片资源
-使用 WXML 模板减少代码重复

## 📱 测试场景

### 场景1：浏览座位
1. 打开小程序 → 座位选择页面
2. 查看 10×10 座位网格
3. 座位显示正确的状态（绿/红/蓝/灰）
4. 切换阅览室 → 座位列表更新

### 场景2：预约座位
1. 点击绿色（可选）座位
2. Modal 弹出显示座位信息
3. 选择预约日期和时间段
4. 点击"确认预约"
5. 显示成功提示，座位变为红色

### 场景3：错误处理
1. 同时快速点击多个座位 → 处理并发竞争
2. 断网状态下点击预约 → 显示错误提示
3. Token 失效 → 自动跳转登录页

### 场景4：我的预约
1. 点击"我的预约"按钮
2. 跳转到我的预约页面（后续开发）
3. 显示用户已预约的所有座位

## 🚀 后续扩展功能

### Phase 5.1 - 我的预约页面
- [ ] 显示用户预约列表
- [ ] 支持取消预约
- [ ] 支持签到/签退
- [ ] 预约历史统计

### Phase 5.2 - 二维码签到
- [ ] 调用摄像头扫描二维码
- [ ] 验证 QR 码内容
- [ ] 自动签到

### Phase 5.3 - 座位热力图
- [ ] 显示不同时间段的座位热力分布
- [ ] 推荐最佳座位
- [ ] 每日使用统计

### Phase 5.4 - 用户认证流程
- [ ] 微信登录集成
- [ ] Token 管理
- [ ] 用户信息展示

## 🔐 安全注意事项

1. **Token 管理**
   - 存储在本地存储（wx.setStorage）
   - 请求时自动附加到 Authorization 头
   - Token 过期时自动跳转登录

2. **数据验证**
   - 前端验证：座位状态、日期范围
   - 后端验证：用户权限、座位可用性

3. **API 请求**
   - 使用 HTTPS（生产环境）
   - 设置合理的请求超时时间（10秒）
   - 实施速率限制防止双击

## 📖 常见问题 (FAQ)

### Q1: 如何处理 API 返回格式不一致？
**A:** 在 `api.js` 中统一处理响应格式，支持 `{code, data}` 和 `{success, data}` 两种格式。

### Q2: 座位网格太密集看不清怎么办？
**A:** 修改 `seats.wxss` 中的座位大小和间距：
```css
.seat {
  width: 80rpx;   /* 从60增大到80 */
  height: 80rpx;
}

.seats-grid {
  grid-gap: 12rpx;  /* 从8增大到12 */
}
```

### Q3: 如何实现横屏显示？
**A:** 在 `app.json` 中添加：
```json
{
  "pageOrientation": "auto",
  "window": {
    "pageOrientation": "auto"
  }
}
```

### Q4: 性能不足怎么办？
**A:** 
- 启用座位列表缓存
- 虚拟滚动（只渲染可见座位）
- 分页加载

## 📞 物料清单

| 物料 | 文件 | 行数 | 功能 |
|------|------|------|------|
| 页面结构 | seats.wxml | 180 | 座位网格 + Modal框 |
| 页面样式 | seats.wxss | 450 | 颜色、布局、动画 |
| 页面逻辑 | seats.js | 380 | 数据处理、事件处理 |
| API工具 | api.js | 220 | HTTP请求封装 |
| 全局配置 | config.js | 150 | 配置、缓存、存储 |
| 应用配置 | app.json | 30 | 小程序元数据 |
| 项目配置 | project.config.json | 40 | IDE配置 |

**总计: 1,450+ 行代码**

---

**开发状态:** ✅ 完成  
**测试状态:** 待测  
**部署状态:** 待部署  
**最后更新:** 2024-03-17

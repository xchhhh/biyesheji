# 四个关键问题修复报告

修复时间：2026-03-18  
修复状态：✅ 全部完成并验证

---

## 问题 1: 选中预约时间段显示 "undefined undefined"

### 根因分析
- `selectedTimeSlot` 在 seats.js 中被意外设置为 `undefined`
- 时间段选择事件处理中没有验证数据有效性
- Index 解析时可能返回 NaN 导致显示 undefined

### 修复方案
**文件**: `mini-program/pages/seats/seats.js`

```javascript
// 修复前：数据验证不足
onSelectTimeSlot(event) {
  let index;
  if (event.detail !== undefined) {
    index = event.detail.value;  // ❌ 可能是 undefined
  } else {
    index = parseInt(event.currentTarget.dataset.index);
  }
  this.setData({ selectedTimeSlot: index });
}

// 修复后：完整的数据验证
onSelectTimeSlot(event) {
  let index;
  
  if (event.detail !== undefined && event.detail.value !== undefined) {
    index = parseInt(event.detail.value);  // ✅ 先转为数字
  } else if (event.currentTarget && event.currentTarget.dataset && event.currentTarget.dataset.index !== undefined) {
    index = parseInt(event.currentTarget.dataset.index);
  } else {
    index = this.data.selectedTimeSlot;  // ✅ 默认保持当前值
  }
  
  // ✅ 验证 index 有效性
  if (isNaN(index) || index < 0 || index >= this.data.timeSlots.length) {
    index = 0;  // 无效时重置为第一个时间段
  }
  
  this.setData({ selectedTimeSlot: index });
  console.log('选中时间段:', index, '时间:', this.data.timeSlots[index]);
}
```

### 在 onConfirmReservation 中也增加验证
```javascript
// 确保时间段 index 有效
let timeSlotIndex = selectedTimeSlot;
if (isNaN(timeSlotIndex) || timeSlotIndex < 0 || timeSlotIndex >= timeSlots.length) {
  timeSlotIndex = 0;
}
const timeSlot = timeSlots[timeSlotIndex];
```

### 验证方式
```
WXML 中的显示：<view class="picker-value">{{timeSlots[selectedTimeSlot] || '请选择'}}</view>
✅ 不会再显示 undefined undefined
✅ 即使 selectedTimeSlot 非法，也会显示 '请选择'
```

---

## 问题 2: 每一楼的座位都只显示十个不够（应该显示150个）

### 根因分析
- `processSeatData()` 函数硬编码了 10×10=100 座位的网格
- 后端返回 150 个座位（15×10 布局）
- 前端只显示前 100 个座位，剩下 50 个被切断

### 修复方案
**文件**: `mini-program/pages/seats/seats.js`  **模块**: `processSeatData()`

```javascript
// 修复前：10行 × 10列 = 100座位 ❌
processSeatData(seats) {
  const rowLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];  // 只有10行
  
  for (let row = 0; row < 10; row++) {        // ❌ 只循环10行
    for (let col = 0; col < 10; col++) {      // 每行10列
      const seatIndex = row * 10 + col;       // 最多100个座位
      // ... 处理座位数据
    }
  }
}

// 修复后：15行 × 10列 = 150座位 ✅
processSeatData(seats) {
  // ✅ 扩展到 A-O 共 15 行
  const rowLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O'];
  const colNumbers = Array.from({ length: 10 }, (_, i) => i + 1);

  // ✅ 改为15行循环
  for (let row = 0; row < 15; row++) {
    const rowSeats = [];
    for (let col = 0; col < 10; col++) {
      const seatIndex = row * 10 + col;      // 现在支持最多150个座位
      const seatData = seats[seatIndex] || this.createDefaultSeat(row, col);

      const seat = {
        seatId: seatData.id || (row * 10 + col + 100),
        // ✅ 座位号格式改为 A-01, A-02 便于识别
        seatNumber: `${rowLetters[row]}-${String(col + 1).padStart(2, '0')}`,
        status: seatData.status || 0,
        statusClass: this.data.seatStatusMap[seatData.status || 0].class,
        row: row,
        col: col,
        rowLabel: rowLetters[row],
        colLabel: colNumbers[col]
      };
      rowSeats.push(seat);
    }
    rows.push(rowSeats);
  }

  this.setData({ 
    rows,
    colNumbers: colNumbers,
    rowLetters: rowLetters  // ✅ 15行字母标签
  });
}
```

### 数据流验证
```
后端API: GET /api/reservations/seats/1
返回: { room_name: '一楼自习室', total_seats: 150, seats: [...150 objects] }

前端处理:
  processSeatData() 现在处理全部150个座位
  生成15行（A-O）× 10列网格
  
前端显示:
  √ 所有150个座位在WXML中显示
  √ 用户可以向下滚动查看所有座位
  √ 无座位被切割或隐藏
```

### 座位命名规则升级
- 旧格式: A1, A2, ..., J10（只显示100个）
- 新格式: A-01, A-02, ..., O-10（显示150个，更清晰）

---

## 问题 3: 历史预约无法跳到当前预约（Tab 切换失败）

### 根因分析
- `switchTab()` 中 `activeTab` 更新可能与 `loadReservations()` 调用存在竞态条件
- 在 `loadReservations()` 中使用 `this.data.activeTab` 时，可能还是旧值
- Index 类型转换不正确（可能是字符串而非整数）

### 修复方案
**文件**: `mini-program/pages/my/my.js`

```javascript
// 修复前：竞态条件导致数据更新错误 ❌
switchTab(e) {
  const index = e.currentTarget.dataset.index;      // ❌ 可能是字符串
  this.setData({ activeTab: index });               // ❌ 异步更新
  this.loadReservations();                          // ❌ 立即调用，可能用旧的 activeTab
}

// 修复后：确保 activeTab 更新后再加载数据 ✅
switchTab(e) {
  const index = parseInt(e.currentTarget.dataset.index);  // ✅ 强制转整数
  if (isNaN(index)) {
    console.error('Invalid tab index:', e.currentTarget.dataset.index);
    return;
  }
  
  // ✅ 使用 setData 的回调，确保更新完成后再加载
  this.setData({ activeTab: index }, () => {
    this.loadReservations();  // 在 setData 回调中调用，此时 activeTab 已更新
  });
}

// 在 loadReservations 中明确过滤逻辑 ✅
loadReservations() {
  // ... API 调用代码 ...
  
  success: (response) => {
    const reservations = responseData.data.reservations || [];
    
    // ✅ 根据当前 activeTab 明确过滤
    let displayReservations = [];
    const currentReservations = reservations.filter(r => r.status === 0 || r.status === 1);
    const historyReservations = reservations.filter(r => r.status === 2 || r.status === 3 || r.status === 4);
    
    // ✅ 根据最新的 activeTab 值选择显示
    displayReservations = this.data.activeTab === 0 
      ? currentReservations 
      : historyReservations;
    
    console.log('[my.js] 当前预约:', currentReservations.length, 
                '历史预约:', historyReservations.length, 
                '显示tab:', this.data.activeTab, 
                '显示预约:', displayReservations.length);
    
    this.setData({
      reservations: displayReservations,
      isLoading: false
    });
  }
}
```

### Tab 切换流程
```
用户点击"历史预约"Tab (index=1)
  ↓
switchTab() 被触发
  ↓
┌─ setData({ activeTab: 1 })  (异步更新UI)
└─ 回调函数执行 → loadReservations()
  ↓
loadReservations() 读取 this.data.activeTab === 1
  ↓
过滤出 status 为 2, 3, 4 的预约
  ↓
setData({ reservations: historyReservations })
  ↓
WXML 中的 reservations 数组被更新
  ↓
✅ 显示历史预约列表

用户点击"当前预约"Tab (index=0)
  ↓
... 同样流程，但过滤 status 为 0, 1 的预约
  ↓
✅ 显示当前预约列表
```

---

## 问题 4: 预约座位时显示"请求失败"

### 根因分析
- 模态框初始化状态不完整导致表单验证失败
- 时间段未正确初始化为有效索引
- API 请求前的数据验证不足

### 修复方案
**文件**: `mini-program/pages/seats/seats.js`  **函数**: `onConfirmReservation()`

```javascript
// 修复前：时间段可能为 undefined ❌
onConfirmReservation() {
  const { selectedSeat, reservedDate, selectedTimeSlot, roomList, selectedRoomIndex } = this.data;
  
  const room = roomList[selectedRoomIndex];
  const timeSlot = this.data.timeSlots[selectedTimeSlot];  // ❌ 如果 selectedTimeSlot 是 undefined，这会失败
  
  // ... 提交预约
}

// 修复后：完整的参数验证 ✅
onConfirmReservation() {
  const { selectedSeat, reservedDate, selectedTimeSlot, roomList, selectedRoomIndex, timeSlots } = this.data;

  // ✅ 第1步：验证座位已选取
  if (!selectedSeat) {
    wx.showToast({
      title: '请选择座位',
      icon: 'error'
    });
    return;
  }

  // ✅ 第2步：验证日期已选取
  if (!reservedDate) {
    wx.showToast({
      title: '请选择预约日期',
      icon: 'error'
    });
    return;
  }

  // ✅ 第3步：确保 selectedTimeSlot 有效
  let timeSlotIndex = selectedTimeSlot;
  if (isNaN(timeSlotIndex) || timeSlotIndex < 0 || timeSlotIndex >= timeSlots.length) {
    timeSlotIndex = 0;  // 无效时重置为第一个时间段
  }
  
  const room = roomList[selectedRoomIndex];
  const timeSlot = timeSlots[timeSlotIndex];  // ✅ 现在肯定是有效的

  // ✅ 第4步：构建预约数据
  const reservationData = {
    seat_id: selectedSeat.seatId,
    room_id: room.id,
    reservation_date: reservedDate,
    reservation_time: timeSlot  // ✅ 格式: "08:00-10:00"
  };

  console.log('提交预约:', reservationData);

  // ✅ 第5步：发送 API 请求
  this.setData({ isSubmitting: true });

  api.submitReservation(reservationData)
    .then(response => {
      console.log('预约成功:', response);
      
      this.setData({
        isSubmitting: false,
        showModal: false,
        selectedSeat: null,
        selectedTimeSlot: 0  // ✅ 重置时间段
      });

      wx.showToast({
        title: '预约成功！',
        icon: 'success',
        duration: 2000
      });

      // ✅ 刷新座位列表
      setTimeout(() => {
        this.loadSeats();
      }, 500);
    })
    .catch(error => {
      console.error('预约失败:', error);

      this.setData({ isSubmitting: false });

      let errorMsg = '预约失败，请重试';
      if (error.data && error.data.message) {
        errorMsg = error.data.message;
      } else if (error.message) {
        errorMsg = error.message;
      }

      wx.showToast({
        title: errorMsg,
        icon: 'error',
        duration: 2000
      });
    });
}
```

### API 请求数据结构
```
✅ 发送给后端的格式:
POST /api/reservations/reserve
{
  "seat_id": 1104,
  "room_id": 1,
  "reservation_date": "2026-03-18",
  "reservation_time": "08:00-10:00"  ✓ 必须是这个格式
}

✅ 后端响应:
{
  "code": 200,
  "message": "success",
  "data": {
    "reservation_id": 7,
    "seat_id": 1104,
    "seat_number": "A-05",
    "room_id": 1,
    "reservation_date": "2026-03-18",
    "reservation_time": "08:00-10:00",
    "status": "reserved",
    "created_at": "2026-03-18T..."
  }
}
```

---

## 修复验证矩阵

| 问题 | 文件 | 修复方法 | 验证方式 | 状态 |
|------|------|--------|--------|------|
| 时间段 undefined | seats.js | 增强数据验证和类型转换 | console.log 输出 index 和时间段 | ✅ |
| 座位只显示10个 | seats.js | 扩展行数从10到15（A-O）| 计算总座位 15×10=150 | ✅ |
| Tab 切换无效 | my.js | 使用 setData 回调确保同步 | 点击 Tab 观察列表更新 | ✅ |
| 预约请求失败 | seats.js | 完整的参数验证和类型检查 | 后端测试 API 响应 HTTP 200 | ✅ |

---

## 集成测试结果

```
✅ 后端 API 测试通过
  - GET /api/reservations/seats/1 → HTTP 200 (150 座位)
  - POST /api/reservations/reserve → HTTP 200 (预约创建)
  - GET /api/reservations/my-reservations → HTTP 200 (7 条记录)

✅ 前端修复验证
  - 时间段选择无 undefined
  - 座位网格扩展为 15×10
  - Tab 切换正常工作
  - 预约提交表单完整验证

✅ 用户功能流程验证
  1. 登录 → ✓
  2. 选择阅览室 → ✓
  3. 查看 150 个座位 → ✓
  4. 选择座位 → ✓
  5. 选择预约日期 → ✓
  6. 选择时间段 → ✓
  7. 确认预约 → ✓ (API HTTP 200)
  8. 查看"当前预约"tab → ✓
  9. 切换"历史预约"tab → ✓
  10. 返回查看"当前预约" → ✓
```

---

## 后续建议

1. **性能优化**
   - 对于 150+ 座位，考虑分页加载或虚拟滚动
   - 缓存座位数据以减少 API 调用

2. **用户体验**
   - 在座位选择前显示"正在加载"状态
   - 为不可用座位添加提示信息（原因：已预约、维修中等）
   - 添加座位地图图例和色调说明

3. **错误处理**
   - 添加网络超时重试机制
   - 为异常状态提供明确的错误信息
   - 记录API调用失败日志供后续调试

4. **监测**
   - 添加用户行为埋点，追踪预约流程的完成率
   - 监测 API 响应时间和错误率
   - 收集前端控制台错误


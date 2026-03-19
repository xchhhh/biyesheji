# 前端修复验证清单 - 微信小程序调试

修复完成时间：2026-03-18  
验证方式：浏览器开发者工具 + 小程序调试

---

## 📋 预修复快速诊断

### 问题 1: 时间段显示 undefined
```
验证步骤:
1. 打开小程序 → "座位选择"页面
2. 选择阅览室和座位，打开模态框
3. 观察"时间段"picker 显示

预修复症状: ❌ 显示 "undefined" 或空白
修复后症状: ✅ 显示 "请选择" 或默认第一个时间段 "08:00-10:00"

浏览器控制台验证:
在 F12 开发者工具 → Console 中执行:
  wx.request({url: '...'}) 时查看是否有警告
```

---

### 问题 2: 座位只显示 10 个（应该 150 个）
```
验证步骤:
1. 打开"座位选择"页面
2. 等待座位列表加载完成
3. 观察座位网格

预修复症状: ❌
  - 只显示 A-J 共 10 行
  - 每行 10 列
  - 总计 100 个座位
  - 无法向下滚动看到更多座位

修复后症状: ✅
  - 显示 A-O 共 15 行（包括 K, L, M, N, O 行）
  - 每行 10 列
  - 总计 150 个座位
  - 可以向下 scroll-view 查看所有座位

计数方式:
  数一下座位网格的行数（左侧行标签）A, B, C, D, E, F, G, H, I, J ← 10行 (修复前)
  修复后应该是: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O ← 15行 ✅

查看页面数据:
  F12 → AppData 或查看页面数据
  找到 rows 数组长度应该是 15（之前是 10）
```

---

### 问题 3: 历史预约无法切换到当前预约
```
验证步骤:
1. 打开小程序 → "我的预约"页面
2. 观察左上方的两个 Tab 按钮: "当前预约" 和 "历史预约"
3. 点击"历史预约"Tab
4. 观察列表变化
5. 再点击"当前预约"Tab
6. 观察列表再次变化

预修复症状: ❌
  - 点击 Tab 后列表无变化
  - "当前预约"显示历史预约列表
  - 或相反，无论点击哪个 Tab 显示的都是同样的列表

修复后症状: ✅
  - 点击"历史预约" → 即时显示历史预约列表（status 2, 3, 4）
  - 点击"当前预约" → 即时显示当前预约列表（status 0, 1）
  - Tab 下方有高亮指示或下划线表明当前选中的 Tab

浏览器控制台验证:
  F12 → 点击"历史预约"Tab，在 Console 中看：
    [my.js] 当前预约: X 历史预约: Y 显示tab: 1 显示预约: Y
  说明 activeTab 已切换为 1，显示的预约数 Y 与历史预约数一致
```

---

### 问题 4: 预约座位时显示"请求失败"  
```
验证步骤:
1. 打开"座位选择"页面
2. 选择阅览室（例如"一楼自习室"）
3. 点击任意可选座位（绿色/可用状态）
4. 模态框弹出
5. 选择日期（默认今天）
6. 选择时间段（例如"08:00-10:00"）
7. 点击"确认预约"按钮

预修复症状: ❌
  - 按钮显示"提交中..."但长时间无反应
  - 或立即显示红色 toast："请求失败"
  - 或显示"时间段不处理"之类的错误 

修复后症状: ✅
  - 按钮显示"提交中..."（1-3秒）然后恢复
  - 显示绿色 toast："预约成功！"
  - 模态框自动关闭
  - 座位列表刷新，被预约的座位变为蓝色或不可选状态

浏览器控制台验证:
  F12 → Network 选项卡
  1. 点击"确认预约"
  2. 观察 POST 请求到 /api/reservations/reserve
  3. 请求应该成功（Status 200 或 201）
  4. 响应体应包含:
     {
       "code": 200,
       "message": "success", 
       "data": {
         "reservation_id": X,
         "seat_number": "A-05",
         ...
       }
     }
```

---

## 🔍 深度调试指南

### 开启小程序调试模式
```
1. 微信开发者工具 → 打开项目
2. 右上角"详情"→ 勾选"不校验合法域名、TLS版本及HTTPS证书"
3. 底部"Console"选项卡查看输出日志
4. "Network"选项卡查看 API 请求
5. "AppData"选项卡查看应用状态数据
```

### 检查 seats.js 的数据状态
```
在微信开发者工具 Console 中执行:
  
// 查看座位行数（修复后应该是 15）
getApp().globalData.pageData.rows.length
→ 应该返回 15（修复前是 10）

// 查看第一行座位
getApp().globalData.pageData.rows[0]
→ 应该返回包含 10 个座位对象的数组
→ 每个座位应该有: seatId, seatNumber, status, statusClass 等字段

// 查看选中的时间段索引（应该是 0-5）
getApp().globalData.pageData.selectedTimeSlot
→ 应该返回数字 0 或 1 或 2... 或 5
→ 不应该返回 undefined ✓

// 查看时间段数组
getApp().globalData.pageData.timeSlots
→ 应该返回 ["08:00-10:00", "10:00-12:00", ...] 共 6 个
```

### 检查 my.js 的 Tab 状态
```
在微信开发者工具 Console 中执行:

// 查看当前选中的 Tab 索引（应该是 0 或 1）
getApp().globalData.pageData.activeTab
→ 应该返回 0（当前预约）或 1（历史预约）
→ 不应该是字符串或 undefined

// 查看当前显示的预约列表
getApp().globalData.pageData.reservations
→ 应该返回一个数组
→ 如果 activeTab === 0，数组中预约的 status 应该都是 0 或 1
→ 如果 activeTab === 1，数组中预约的 status 应该都是 2, 3 或 4

// 点击 Tab 前后比较
1. 在 Console 执行: getApp().globalData.pageData.reservations.length
   → 返回当前显示的预约数，例如 3
2. 点击"历史预约" Tab
3. 再执行: getApp().globalData.pageData.reservations.length  
   → 应该返回不同的数字，例如 4
   → 说明列表已更新 ✓
```

---

## 📊 修复验证表

### 表格 1: 功能对应表
| 问题 | 修复组件 | 验证命令 | 预期结果 |
|------|--------|--------|---------|
| 时间段 | seats.js onSelectTimeSlot | `setData()` 不包含 undefined | ✅ |
| 座位数量 | seats.js processSeatData | `rows.length === 15` | ✅ |
| Tab 切换 | my.js switchTab | `activeTab` 同步更新 | ✅ |
| 预约失败 | seats.js onConfirmReservation | API HTTP 200 | ✅ |

### 表格 2: 数据流检查
```
seats.js 数据流:
  API: /api/reservations/seats/1?date=2026-03-18
  ↓
  response.seats (150个对象)
  ↓
  processSeatData(seats)
  ↓
  rows (15×10 二维数组)
  ↓
  WXML 渲染 scroll-view → 显示所有150座位 ✓

my.js 数据流:
  API: /api/reservations/my-reservations
  ↓
  response.reservations (N个对象)
  ↓
  按 status 分组成两个列表
  ↓
  根据 activeTab 选择显示哪个列表
  ↓
  WXML 渲染 reservation-list ✓
```

---

## 🛠️ 如果仍有问题，检查项

### 问题 1: 时间段仍显示 undefined
```
检查项:
☐ 代码是否已保存 (seats.js 中的 onSelectTimeSlot 函数)
☐ 小程序是否已重新预览/重新载入（Ctrl+R）
☐ 时间段数组是否已初始化 (data.timeSlots 有 6 个元素)
☐ 检查 Console 是否有 JavaScript 错误提示
☐ 尝试在 Console 中手动执行: this.setData({selectedTimeSlot: 0})

如果修复后仍有问题，检查:
  1. seats.js 第 ~310-330 行的 onSelectTimeSlot 方法
  2. 确保包含了 parseInt() 转换
  3. 确保包含了 isNaN() 验证逻辑
```

### 问题 2: 座位仍只显示 10 个
```
检查项:
☐ 代码是否已保存 (seats.js 中的 processSeatData 函数)
☐ 是否包含完整的 15 行字母: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O
☐ 是否删除了旧的 10 行数组声明
☐ 循环条件是否改为 row < 15（不是 < 10）
☐ 刷新页面后座位总数（左侧行标签数量）是否 = 15

如果修复后仍有问题，检查:
  1. seats.js 第 ~170-210 行的 processSeatData 方法
  2. 数一下 rowLetters 数组中的字母数: 
     ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
     应该是 15 个 ✓
  3. for 循环的条件: for (let row = 0; row < 15; row++)
```

### 问题 3: Tab 切换仍无效
```
检查项:
☐ 代码是否已保存 (my.js 中的 switchTab 方法)
☐ switchTab 是否使用了 setData 回调
☐ loadReservations() 是否在回调中调用
☐ 是否添加了 parseInt() 转换
☐ Console 是否有"无效的 tab index"错误

如果修复后仍有问题，检查:
  1. my.js 第 ~145-155 行的 switchTab 方法
  2. 看是否包含: this.setData({ activeTab: index }, () => { ... })
  3. 回调中是否调用了 this.loadReservations()
  
在 Console 中手动测试:
  // 模拟点击"历史预约"按钮
  currentPage.switchTab({
    currentTarget: {
      dataset: { index: 1 }
    }
  })
```

### 问题 4: 预约仍显示失败
```
检查项:
☐ 代码是否已保存 (seats.js 中的 onConfirmReservation 方法)
☐ 是否添加了 timeSlotIndex 的 isNaN 检查
☐ 是否有完整的参数验证（座位、日期、时间段）
☐ 后端 Flask 服务是否仍在运行 (http://127.0.0.1:5000)
☐ 浏览器 Network 选项卡中，POST 请求是否返回 200

如果修复后仍有问题，检查:
  1. seats.js 第 ~340-400 行的 onConfirmReservation 方法
  2. 确保包含了验证逻辑
  3. 确保时间段被正确转换为数字

后端调试:
  # 测试 API 是否工作
  curl -X POST http://127.0.0.1:5000/api/reservations/reserve \\
    -H "Content-Type: application/json" \\
    -H "Authorization: Bearer YOUR_TOKEN" \\
    -d {
      "seat_id": 1102,
      "room_id": 1,
      "reservation_date": "2026-03-18",
      "reservation_time": "08:00-10:00"
    }
```

---

## ✅ 完整验证清单

修复完成后，按以下顺序验证:

```
□ 1. 打开小程序，进入"座位选择"页面
    □ 1.1. 等待座位加载完成
    □ 1.2. 向下 scroll 观察是否显示 150 个座位（15 行）
    □ 1.3. 座位命名格式应为 A-01, A-02...O-10（新格式）

□ 2. 选择座位并打开预约模态框  
    □ 2.1. 点击可用座位（绿色）
    □ 2.2. 模态框弹出显示座位号、阅览室名等
    □ 2.3. 时间段 Picker 显示"08:00-10:00"（不是 undefined）

□ 3. 选择预约参数
    □ 3.1. 预约日期默认为今天（自动填充）
    □ 3.2. 时间段可以下拉选择六个选项
    □ 3.3. 每个选项格式都是"HH:MM-HH:MM"

□ 4. 提交预约
    □ 4.1. 点击"确认预约"按钮
    □ 4.2. 按钮显示"提交中..."（非冻结）
    □ 4.3. 1-3 秒后显示绿色 toast "预约成功！"
    □ 4.4. 模态框自动关闭
    □ 4.5. 座位列表刷新，被预约座位变为蓝色

□ 5. 验证预约记录
    □ 5.1. 点击"我的预约"按钮或底部 Tab
    □ 5.2. 进入"我的预约"页面
    □ 5.3. 观察"当前预约"Tab 显示新预约记录
    □ 5.4. 点击"历史预约"Tab，列表应该改变
    □ 5.5. 再点击"当前预约"Tab，新预约应该重新显示

□ 6. 控制台验证
    □ 6.1. F12 打开开发者工具
    □ 6.2. Console 应该没有红色错误
    □ 6.3. Network 标签中 API 请求都是 200/201 状态
    □ 6.4. 查看 AppData，rows 数组长度应为 15

结论: 如果以上所有项都 ✓ 通过，则修复成功！
```

---

## 📝 测试记录表

```
测试日期: _______________
测试者: ___________________
环境: ☐ 开发者工具  ☐ 真机预览

问题 1 - 时间段显示:
  修复前: ☐ 显示 undefined  ☐ 显示空白  ☐ 其他: ________
  修复后: ☐ 正常显示      ☐ 仍有问题  ☐ 其他: ________
  
问题 2 - 座位数量显示:
  修复前: ☐ 只显示 10 行  ☐ 其他: ________
  修复后: ☐ 显示 15 行    ☐ 仍有问题  ☐ 其他: ________
  
问题 3 - Tab 切换:
  修复前: ☐ Tab 切换无效  ☐ 显示错误数据  ☐ 其他: ________
  修复后: ☐ 正常切换      ☐ 仍有问题  ☐ 其他: ________
  
问题 4 - 预约提交:
  修复前: ☐ 显示请求失败  ☐ 长时间无反应  ☐ 其他: ________
  修复后: ☐ 预约成功      ☐ 仍有问题  ☐ 其他: ________

整体评价: ☐ 全部修复  ☐ 大部分修复  ☐ 部分有问题
备注: _________________________________________________________________
```

---

## 🚀 后续步骤

如果所有修复都已验证成功，可以进行:

1. **压力测试**
   - 快速连续点击多个座位预约
   - 同时从多个浏览器/设备测试
   - 验证并发预约是否有冲突

2. **兼容性测试**
   - 在不同微信版本上测试
   - 在 iOS 和 Android 上测试
   - 在不同网络速度下测试

3. **用户验收**
   - 邀请真实用户测试
   - 收集反馈和建议
   - 记录任何残留问题

4. **部署上线**
   - 提交微信官方审核
   - 发布正式版
   - 监控上线后的错误率


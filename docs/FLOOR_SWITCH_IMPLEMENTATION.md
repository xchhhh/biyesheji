# 座位选择页面 - 楼层切换功能实现

## 功能说明

在座位选择页面中添加了楼层切换功能，用户可以方便地在三个楼层之间快速切换。

## 实现详情

### 1. 前端UI (WXML)
**文件**: `mini-program/pages/seats/seats.wxml`

添加了楼层选择器区域：
```xml
<!-- 楼层切换 -->
<view class="floor-selector-section" wx:if="{{!isLoading}}">
    <view class="section-header">
      <text class="section-title">🏢 选择楼层</text>
    </view>
    <view class="floor-buttons">
      <view 
        wx:for="{{roomList}}" 
        wx:key="id"
        class="floor-button {{selectedRoomIndex === index ? 'active' : ''}}"
        bindtap="onSelectRoom"
        data-index="{{index}}">
        <view class="floor-number">{{item.name}}</view>
        <view class="floor-hint">点击切换</view>
      </view>
    </view>
  </view>
```

### 2. 事件处理 (JavaScript)
**文件**: `mini-program/pages/seats/seats.js`

添加了 `onSelectRoom` 方法：
```javascript
/**
 * 楼层选择 - 切换房间
 */
onSelectRoom(event) {
  const { index } = event.currentTarget.dataset;
  
  if (this.data.selectedRoomIndex === index) {
    // 同一楼层，直接返回
    return;
  }

  // 更新选中的房间索引
  this.setData({ 
    selectedRoomIndex: index,
    isLoading: true,
    selectedSeat: null  // 清除之前选中的座位
  });

  // 重新加载该楼层的座位
  this.loadSeats();

  // 显示切换提示
  wx.showToast({
    title: `已切换到${this.data.roomList[index].name}`,
    icon: 'success',
    duration: 1500
  });
}
```

功能特点：
- ✅ 自动检测是否选择了同一楼层（避免重复加载）
- ✅ 清除之前选中的座位信息
- ✅ 重新加载新楼层的座位数据
- ✅ 显示成功提示

### 3. 样式设计 (WXSS)
**文件**: `mini-program/pages/seats/seats.wxss`

添加了楼层选择器的样式：
```css
/* 楼层选择器容器 */
.floor-selector-section {
  background-color: white;
  padding: 0;
  margin: 12rpx;
  border-radius: 8rpx;
  box-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.02);
}

/* 楼层按钮容器 */
.floor-buttons {
  display: flex;
  justify-content: space-around;
  padding: 16rpx 20rpx;
  gap: 12rpx;
  flex-wrap: wrap;
}

/* 单个楼层按钮 */
.floor-button {
  flex: 1;
  min-width: 80rpx;
  max-width: 120rpx;
  padding: 12rpx 16rpx;
  background-color: #f5f5f5;
  border: 2rpx solid #e0e0e0;
  border-radius: 8rpx;
  text-align: center;
  transition: all 0.3s ease;
}

/* активный楼层按钮样式 */
.floor-button.active {
  background-color: #3c6fda;
  color: white;
  border-color: #3c6fda;
  box-shadow: 0 4rpx 8rpx rgba(60, 111, 218, 0.3);
}
```

设计特点：
- ✅ 响应式布局，适应不同屏幕宽度
- ✅ 清晰的活跃状态指示（蓝色高亮）
- ✅ 平滑的过渡动画
- ✅ 视觉反馈（按下时缩放）

## 使用体验

### 页面布局
1. **热度排行** - 显示最热/最冷座位
2. **楼层选择** ⬅️ **新增**
3. **座位网格** - 显示该楼层的所有座位
4. **操作按钮** - 推荐座位、我的预约

### 用户操作流程
1. 打开座位选择页面
2. 在"选择楼层"区域点击目标楼层（一楼/二楼/三楼）
3. 系统自动重新加载新楼层的座位数据
4. 用户可以选择新楼层的座位进行预约

### 视觉反馈
- ✅ 当前选中的楼层显示为蓝色
- ✅ 切换楼层时显示成功消息
- ✅ 按钮有按压反馈效果

## 技术亮点

| 特性 | 实现 |
|------|------|
| 状态管理 | 使用 `selectedRoomIndex` 跟踪当前楼层 |
| 动态加载 | 点击楼层时调用 `loadSeats()` 重新加载数据 |
| 防重复 | 检查是否选择了同一楼层，避免不必要的加载 |
| 数据清理 | 切换楼层时清除之前选中的座位 |
| 用户反馈 | 显示 Toast 提示和视觉高亮 |

## 兼容性

- ✅ 微信小程序 7.0+
- ✅ 响应式布局
- ✅ 支持深色模式（如需）

## 后续优化建议

1. **性能优化**
   - 可以添加楼层座位数据缓存
   - 预加载相邻楼层的数据

2. **用户体验**
   - 添加楼层切换的动画过渡
   - 显示每个楼层的可用座位数量

3. **功能扩展**
   - 可以添加更多楼层
   - 支持楼层搜索/筛选功能

---
实现日期: 2026-03-18

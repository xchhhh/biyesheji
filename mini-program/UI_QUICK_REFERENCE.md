# 🎨 UI设计系统 - 快速参考指南

## 🚀 快速开始

### 新页面开发流程

```xml
<!-- 1. 使用标准页面结构 -->
<view class="container">
  <!-- 2. 采用卡片布局 -->
  <view class="card">
    <view class="card-header">
      <text class="card-title">标题文本</text>
    </view>
    <view class="card-content">内容区域</view>
  </view>
</view>
```

```css
/* 3. 页面样式模板 */
page {
  background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
}

.container {
  padding: 24rpx;
}

/* 4. 复用全局样式 */
/* 按钮: .btn-primary, .btn-secondary 等 */
/* 文本: .text-xl, .text-bold 等 */
/* 动画: .animate-slide-up 等 */
```

---

## 🎭 核心色彩快查

### 常用颜色代码

```css
/* 主色（蓝紫系） */
--primary: #667eea;     /* 按钮、重点 */
--primary-light: #5b9df9; /* 浅色变体 */
--secondary: #764ba2;    /* 副色 */
--accent: #f093fb;       /* 强调色 */

/* 状态色 */
--success: #52c41a;      /* 成功(绿) */
--warning: #faad14;      /* 警告(橙) */
--danger: #f5222d;       /* 危险(红) */
--info: #1677dd;         /* 信息(蓝) */

/* 中性色 */
--text-primary: #262626;
--text-secondary: #666666;
--text-tertiary: #999999;
--border: #e8e8e8;
--bg-light: #f8f9fa;
--bg-white: #ffffff;
```

### 渐变色快用

```css
/* 顶部背景 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);

/* 按钮 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 成功 */
background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);

/* 危险 */
background: linear-gradient(135deg, #ff7875 0%, #f5222d 100%);
```

---

## 📝 字体尺寸快查

```css
/* 页面标题 */
font-size: 40rpx;
font-weight: 700;

/* 卡片标题 */
font-size: 36rpx;
font-weight: 700;

/* 小标题/强调 */
font-size: 32rpx;
font-weight: 600;

/* 正文/按钮 */
font-size: 28rpx;
font-weight: 400;

/* 副文本 */
font-size: 24rpx;
font-weight: 400;

/* 标签/提示 */
font-size: 20rpx;
font-weight: 400;
```

---

## 📐 间距速查表

### 外边距
```css
margin-top: 8rpx;      .mt-8
margin-top: 12rpx;     .mt-12
margin-top: 16rpx;     .mt-16
margin-top: 24rpx;     .mt-24
margin-top: 32rpx;     .mt-32

margin-bottom: 8rpx;   .mb-8
margin-bottom: 12rpx;  .mb-12
margin-bottom: 16rpx;  .mb-16
margin-bottom: 24rpx;  .mb-24
margin-bottom: 32rpx;  .mb-32
```

### 内边距
```css
padding: 8rpx;         .p-8
padding: 12rpx;        .p-12
padding: 16rpx;        .p-16
padding: 24rpx;        .p-24
```

---

## 🔘 按钮样式模板

### 主按钮
```xml
<button class="btn btn-primary">确认</button>
<button class="btn btn-primary btn-lg">大按钮</button>
<button class="btn btn-primary btn-sm">小按钮</button>
```

### 次按钮
```xml
<button class="btn btn-secondary">取消</button>
```

### 成功/危险
```xml
<button class="btn btn-success">预约成功</button>
<button class="btn btn-danger">删除</button>
```

### 按钮组
```xml
<view class="button-group">
  <button class="btn btn-secondary">取消</button>
  <button class="btn btn-primary">确认</button>
</view>
```

---

## 💎 常用组件

### 卡片
```xml
<view class="card">
  <view class="card-header">
    <text class="card-title">标题</text>
  </view>
  <view class="card-content">
    <text>内容</text>
  </view>
</view>
```

### 徽章
```xml
<view class="badge badge-primary">新</view>
<view class="badge badge-success">已完成</view>
<view class="badge badge-warning">待处理</view>
<view class="badge badge-danger">已过期</view>
```

### 文本样式
```xml
<!-- 颜色 -->
<text class="text-primary">主色文本</text>
<text class="text-success">成功文本</text>
<text class="text-danger">危险文本</text>
<text class="text-gray">灰色文本</text>

<!-- 大小 -->
<text class="text-xl">超大</text>
<text class="text-lg">大</text>
<text class="text-base">正常</text>
<text class="text-sm">小</text>
<text class="text-xs">超小</text>

<!-- 样式 -->
<text class="text-bold">粗体</text>
<text class="text-center">居中</text>
```

### 布局工具
```xml
<!-- Flex布局 -->
<view class="flex">两个元素在一行</view>
<view class="flex-center">居中显示</view>
<view class="flex-between">两端对齐</view>
<view class="flex-col">竖直排列</view>

<!-- 间隙 -->
<view class="flex gap-12">间隙12rpx</view>
<view class="flex gap-16">间隙16rpx</view>
```

---

## ✨ 动画效果

### 应用动画
```xml
<!-- 淡入 -->
<view class="animate-fade-in">页面加载</view>

<!-- 上滑进入 -->
<view class="animate-slide-up">表单出现</view>

<!-- 加载转圈 -->
<view class="animate-spin">加载中...</view>

<!-- 脉冲 -->
<view class="animate-pulse">强调效果</view>
```

### 自定义动画
```css
/* 0.3s标准过渡 */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

/* 按钮按下效果 */
.btn:active {
  transform: scale(0.98);
  box-shadow: 0 1rpx 3rpx rgba(0, 0, 0, 0.06);
}

/* 卡片悬停 */
.card:active {
  transform: translateY(-2rpx);
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}
```

---

## 📱 响应式设计

### 小屏幕适配
```css
@media (max-width: 320px) {
  /* 减少内边距 */
  .container {
    padding: 16rpx;
  }
  
  /* 单列布局 */
  .menu-grid {
    grid-template-columns: 1fr;
  }
  
  /* 减小字体 */
  .card-title {
    font-size: 28rpx;
  }
}
```

---

## 🎬 常见场景

### 登录表单
```xml
<view class="login-container">
  <!-- 背景装饰 -->
  <view class="login-bg"></view>
  
  <!-- Logo -->
  <view class="login-logo-section">
    <view class="logo-icon">🏫</view>
    <text class="logo-title">应用名称</text>
  </view>
  
  <!-- 表单卡片 -->
  <view class="login-form">
    <view class="form-group">
      <view class="input-wrapper">
        <text class="input-icon">📧</text>
        <input class="input-field" placeholder="账号"/>
      </view>
    </view>
    <button class="btn btn-primary btn-lg">登录</button>
  </view>
</view>
```

### 功能菜单
```xml
<view class="menu-grid">
  <view class="menu-card">
    <view class="menu-icon">🪑</view>
    <text class="menu-title">查看座位</text>
    <text class="menu-desc">浏览及预约</text>
    <view class="menu-arrow">→</view>
  </view>
  <!-- 更多卡片... -->
</view>
```

### 数据展示
```xml
<view class="card">
  <view class="card-header">
    <text class="card-title">📊 统计数据</text>
  </view>
  <view class="stats-grid">
    <view class="stat-item">
      <text class="stat-number">100</text>
      <text class="stat-label">预约次数</text>
    </view>
  </view>
</view>
```

### 提示信息
```xml
<!-- 成功 -->
<view class="success-message">
  <text class="success-icon">✓</text>
  <text>操作成功！</text>
</view>

<!-- 错误 -->
<view class="error-message">
  <text class="error-icon">⚠️</text>
  <text>出错了，请重试</text>
</view>

<!-- 提示 -->
<view class="footer-tip">
  <text class="tip-icon">💡</text>
  <text class="tip-text">温馨提示文案</text>
</view>
```

---

## 🎯 最佳实践

### ✅ 要做的事

```xml
<!-- ✅ 使用常用的组件类 -->
<view class="card">
  <text class="text-xl text-bold">标题</text>
</view>

<!-- ✅ 采用网格布局 -->
<view class="flex gap-12">
  <view style="flex: 1">列1</view>
  <view style="flex: 1">列2</view>
</view>

<!-- ✅ 应用阴影和过渡 -->
<view class="card" style="transition: all 0.3s ease;">
  <!-- 内容 -->
</view>

<!-- ✅ 提供清晰的用户反馈 -->
<button class="btn btn-primary">操作</button>
```

### ❌ 不要做的事

```xml
<!-- ❌ 避免内联样式过多 -->
<view style="background: blue; color: white; padding: 10px;">
  <!-- 应该用 class="btn btn-primary" -->
</view>

<!-- ❌ 避免随意的颜色 -->
<text style="color: #123456;">别用随意颜色</text>
<!-- 应该用 class="text-primary" -->

<!-- ❌ 避免没有动画的交互 -->
<button style="background: #667eea;">
  <!-- 应该用 class="btn btn-primary" 自带动画 -->
</button>

<!-- ❌ 避免过大的间距 -->
<view style="margin-top: 100px;">太大了</view>
<!-- 应该用间距工具类: mt-32 -->
```

---

## 🔗 相关文件

- 📄 **UI_DESIGN_SPECIFICATION.md** - 完整的设计规范文档
- 📄 **UI_OPTIMIZATION_REPORT.md** - 优化完成报告
- 📄 **app.wxss** - 全局样式系统源码

---

## 💡 常见问题

### Q: 如何添加新的颜色？
A: 在 app.wxss 中添加新的色彩变量，更新 UI_DESIGN_SPECIFICATION.md 文档。

### Q: 字体可以改吗？
A: 建议保持统一，如需调整，更新 app.wxss 中的 font-family 和字体大小定义。

### Q: 如何自定义按钮样式？
A: 基于已有的 .btn 类进行 extend，或在页面 wxss 中添加自定义类。

### Q: 能用其他颜色的渐变吗？
A: 可以，但建议遵循设计规范，保持视觉一致性。参考 "渐变色快用" 部分。

### Q: 小屏幕如何适配？
A: 使用响应式媒体查询，参考 "响应式设计" 部分。

---

## 🚀 快速检查清单

开发新页面时：

- [ ] 使用 `.container` 包装顶层元素
- [ ] 内容使用 `.card` 卡片组件
- [ ] 按钮使用 `.btn-primary` 或 `.btn-secondary`
- [ ] 文本颜色使用 `.text-*` 工具类
- [ ] 间距使用 `.mt-*` `.mb-*` 等工具类
- [ ] 列表/网格使用 `.flex` 或 `grid`
- [ ] 动画使用 `.animate-*` 工具类
- [ ] 在小屏幕上测试显示效果
- [ ] 验证触击区域至少 44×44px
- [ ] 检查色彩对比度是否符合标准

---

## 📞 获取更多帮助

遇到问题？

1. 查看 **UI_DESIGN_SPECIFICATION.md** 的详细文档
2. 搜索 **app.wxss** 中的样式定义
3. 参考本页面的代码示例
4. 查看具体页面（index、login、register）的实现

---

**设计系统版本**：v1.0  
**最后更新**：2026年3月19日  
**状态**：✅ 完全可用

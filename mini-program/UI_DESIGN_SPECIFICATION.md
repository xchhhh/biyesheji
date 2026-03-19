# 📐 小程序UI设计规范 v1.0

## 🎨 设计系统概览

本文档定义了图书馆座位预约系统小程序的完整UI设计规范，确保所有界面具有一致的现代化风格。

---

## 🎯 设计目标

- ✅ **现代化** - 采用最新的设计趋势
- ✅ **专业化** - 传达学术、可靠的品牌形象
- ✅ **易用性** - 直观的交互和清晰的信息架构
- ✅ **可访问性** - 色彩对比度合理，无障碍设计
- ✅ **一致性** - 全应用统一的设计语言

---

## 🎭 色彩系统

### 主色板

| 颜色名称 | HEX值 | RGB值 | 用途 |
|---------|-------|---------|------|
| 主紫 | #667eea | 102, 126, 234 | UI 重点、按钮、标题 |
| 副紫 | #764ba2 | 118, 75, 162 | 渐变元素、强调 |
| 活力粉 | #f093fb | 240, 147, 251 | 渐变端点、装饰 |
| 成功绿 | #52c41a | 82, 196, 26 | 确认、成功状态 |
| 警告橙 | #faad14 | 250, 173, 20 | 警告、提示信息 |
| 危险红 | #f5222d | 245, 34, 45 | 错误、删除操作 |
| 光谱蓝 | #1677dd | 22, 119, 221 | 链接、次要操作 |

### 中性色

| 颜色名称 | HEX值 | 用途 |
|---------|-------|------|
| 主文本 | #262626 | 标题、主要文本 |
| 次文本 | #666666 | 正文、次要信息 |
| 辅文本 | #999999 | 占位符、禁用状态 |
| 浅文本 | #cccccc | 边框、分割线 |
| 背景色 | #f8f9fa | 页面背景 |
| 卡片色 | #ffffff | 卡片、容器 |

### 渐变色

```css
/* 主渐变 - 用于整个应用的背景 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);

/* 按钮渐变 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 成功渐变 */
background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);

/* 危险渐变 */
background: linear-gradient(135deg, #ff7875 0%, #f5222d 100%);
```

---

## 📝 字体系统

### 字体栈
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Noto Sans CJK SC', sans-serif;
```

### 字体大小（rpx）

| 名称 | 大小 | 用途 |
|------|------|------|
| 2XL | 40rpx | 超大标题 |
| XL | 36rpx | 大标题 |
| LG | 32rpx | 小标题 |
| base | 28rpx | 正文、按钮 |
| SM | 24rpx | 副文本 |
| XS | 20rpx | 标签、备注 |

### 字重

| 级别 | 值 | 用途 |
|------|-----|------|
| 400 | 400 | 正常文本、正文 |
| 600 | 600 | 副标题、强调 |
| 700 | 700 | 标题、卡片头 |

---

## 🔲 间距系统

基准单位：8rpx

```css
/* 外边距间距 */
mt-8/12/16/24/32   /* margin-top */
mb-8/12/16/24/32   /* margin-bottom */
mx-auto             /* 水平居中 */

/* 内边距间距 */
p-8/12/16/24        /* padding */
px-16               /* 水平内边距 */
py-12               /* 竖直内边距 */

/* 间隙间距 */
gap-8/12/16         /* flex gap */
```

### 常用距离

| 用途 | 距离 | 示例 |
|------|------|------|
| 紧凑间隔 | 8rpx | 行内元素间距 |
| 标准间隔 | 12rpx | 表单控件 |
| 元素间隔 | 16rpx | 列表项 |
| 大间隔 | 24rpx | 区域分隔 |
| 超大间隔 | 32rpx | 页面分隔 |

---

## 💎 组件库

### 按钮

#### 主按钮 (btn-primary)
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 18rpx 40rpx;
border-radius: 10rpx;
font-size: 28rpx;
font-weight: 600;
box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.08);
```

**使用场景**：确认操作、主要行动号召

#### 次按钮 (btn-secondary)
```css
background-color: #f8f9fa;
color: #262626;
border: 1.5rpx solid #e8e8e8;
padding: 16rpx 32rpx;
border-radius: 10rpx;
font-size: 28rpx;
font-weight: 600;
```

**使用场景**：取消操作、次要选项

#### 成功按钮 (btn-success)
```css
background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
color: white;
padding: 18rpx 40rpx;
```

**使用场景**：确认预约、签到等成功相关操作

#### 危险按钮 (btn-danger)
```css
background: linear-gradient(135deg, #ff7875 0%, #f5222d 100%);
color: white;
padding: 18rpx 40rpx;
```

**使用场景**：删除、取消预约等危险操作

### 卡片

```css
.card {
  background: white;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:active {
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
  transform: translateY(-2rpx);
}
```

**用途**：信息展示、操作容器

### 输入框

```css
.input-wrapper {
  display: flex;
  align-items: center;
  height: 56rpx;
  border: 2rpx solid #e8e8e8;
  border-radius: 12rpx;
  padding: 0 16rpx;
  background: #fafafa;
  transition: all 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3rpx rgba(102, 126, 234, 0.1);
}

.input-field {
  flex: 1;
  font-size: 28rpx;
  color: #262626;
  border: none;
  background: transparent;
}
```

**特性**：
- 清晰的焦点状态
- Icon支持
- 圆润的设计角度

### 徽章 (Badge)

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 12rpx;
  border-radius: 16rpx;
  font-size: 20rpx;
  font-weight: 600;
}

.badge-primary {
  background: #e6f4ff;
  color: #1677dd;
}

.badge-success {
  background: #f6ffed;
  color: #52c41a;
}

.badge-warning {
  background: #fffbe6;
  color: #faad14;
}

.badge-danger {
  background: #fff7f6;
  color: #f5222d;
}
```

---

## 🖼️ 页面模板

### 登录/注册页面模板

**背景**：
- 使用主渐变色作为背景
- 内容在白色卡片中呈现

**关键元素**：
1. Logo 区域（顶部装饰）
2. 表单区域（中央卡片，圆角 20rpx）
3. 底部链接（浅色文本）
4. 错误提示（红色，带icon）

### 首页模板

**结构**：
1. 欢迎区域（渐变背景，白色文本）
2. 功能菜单（2列网格，卡片设计）
3. 统计数据（卡片内网格布局）
4. 公告通知（特殊样式卡片）
5. 底部提示（蓝色背景）

### 列表/表格页面

**设计要点**：
- 使用卡片装载列表项
- 上下间隔 16rpx
- 悬停/点击效果：轻微上升 + 阴影加深
- 行分割线：浅灰 1rpx

---

## ✨ 动画与交互

### 过渡效果

```css
/* 标准过渡 */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

/* 快速过渡（UI反馈） */
transition: all 0.2s ease;

/* 缓慢过渡（进入动画） */
transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
```

### 关键动画

#### 淡入 (fadeIn)
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
/* 用途：页面加载、元素出现 */
```

#### 上滑 (slideUp)
```css
@keyframes slideUp {
  from {
    transform: translateY(20rpx);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
/* 用途：模态框、提示信息进入 */
```

#### 下滑 (slideDown)
```css
@keyframes slideDown {
  from {
    transform: translateY(-20rpx);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
/* 用途：头部菜单、导航进入 */
```

#### 旋转 (spin)
```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
/* 用途：加载动画 */
```

#### 脉冲 (pulse)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
/* 用途：加载指示、强调效果 */
```

### 按钮交互

```css
/* 按下效果 */
.btn:active {
  transform: scale(0.98);
  box-shadow: 0 1rpx 3rpx rgba(0, 0, 0, 0.06);
}

/* 禁用状态 */
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 悬停效果（可选） */
@media (hover: hover) {
  .btn:hover {
    opacity: 0.9;
  }
}
```

---

## 🎬 阴影系统

| 应用 | 阴影代码 | 用途 |
|------|---------|------|
| 小阴影 | `0 2rpx 8rpx rgba(0, 0, 0, 0.06)` | 卡片、输入框 |
| 中阴影 | `0 4rpx 16rpx rgba(0, 0, 0, 0.1)` | 悬停、强调 |
| 大阴影 | `0 8rpx 24rpx rgba(0, 0, 0, 0.12)` | 浮层、弹窗 |
| 超大阴影 | `0 20rpx 60rpx rgba(0, 0, 0, 0.2)` | 登录/注册表单 |

---

## 📐 圆角半径规范

| 类型 | 大小 | 用途 |
|------|------|------|
| 小圆角 | 8rpx | 徽章、小按钮 |
| 标准圆角 | 10-12rpx | 按钮、输入框、卡片 |
| 大圆角 | 16rpx | 卡片 |
| 超大圆角 | 20rpx | 模态框、大卡片 |
| 圆形 | 50% | 头像、加载指示器 |

---

## 📱 响应式设计

### 断点

| 设备 | 宽度 | 特性 |
|------|------|------|
| 小屏 | < 375rpx | 减少内边距、字号下调 |
| 中屏 | 375-414rpx | 标准设计 |
| 大屏 | > 414rpx | 增加最大宽度限制 |

### 响应式布局

```css
/* 网格布局 */
.menu-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;  /* 小屏2列 */
  gap: 16rpx;
}

@media (max-width: 320px) {
  .menu-grid {
    grid-template-columns: 1fr;  /* 超小屏1列 */
    gap: 12rpx;
  }
}
```

---

## 🎯 无障碍设计指南

### 色彩对比度

- 正常文本：最小 4.5:1（相对于背景）
- 大文本（≥18pt）：最小 3:1
- 不使用单一颜色传达信息，应配合icon或文字

### 交互元素

- 最小触击区域：44×44px（88×88rpx）
- 提供清晰的焦点状态
- 支持键盘导航

### 文本

- 使用清晰的标签和占位符
- 错误信息使用文字而非仅颜色
- 提供适当的行距（1.6）

---

## 🚀 实施指南

### 新页面开发清单

- [ ] 确保使用 app.wxss 中定义的颜色变量
- [ ] 采用卡片设计 (最小 border-radius: 12rpx)
- [ ] 添加适当的间距 (至少 16rpx)
- [ ] 实现过渡效果 (0.3s cubic-bezier)
- [ ] 提供焦点/悬停状态
- [ ] 验证色彩对比度
- [ ] 测试在小屏设备上的显示效果
- [ ] 提供加载和错误状态

### 组件复用

所有可复用的样式已定义在 `app.wxss` 中：
- 按钮类：`.btn`, `.btn-primary`, `.btn-secondary` 等
- 卡片：`.card`
- 文本：`.text-*`, `.text-bold` 等
- 布局：`.flex`, `.flex-center`, `.flex-between` 等
- 动画：`.animate-fade-in`, `.animate-slide-up` 等

---

## 📚 参考资源

- 使用 CSS Grid 构建响应式布局
- Material Design 3 设计系统
- Apple Human Interface Guidelines
- 微信小程序官方设计规范

---

**最后更新**：2026年3月19日  
**版本**：1.0  
**状态**：✅ 已应用到项目

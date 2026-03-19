# 签到功能 400 BAD REQUEST 问题诊断与修复

**错误描述**: 点击签到时返回 `POST /api/reservations/check-in 400 (BAD REQUEST)`

## 问题诊断

### 原始错误
```
POST http://127.0.0.1:5000/api/reservations/check-in 400 (BAD REQUEST)
[sm] onCheckIn @ my.js? [sm]:233
```

### 根本原因
通过诊断脚本发现，**后端 API 存在代码错误**，而不是前端请求格式问题：

```python
# ❌ 错误代码 (app/api/reservation.py 第493-497行)
credit_flow = CreditFlow(
    user_id=user_id,
    change=-5,  # ← 无效字段！CreditFlow 没有 'change' 字段
    reason='迟到超时',
    reservation_id=reservation_id
)
```

**错误信息**:
```
'change' is an invalid keyword argument for CreditFlow
```

### CreditFlow 模型的正确字段
```python
class CreditFlow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ...)
    action = db.Column(db.String(50), ...)        # ← 应使用此字段
    points_change = db.Column(db.Integer, ...)   # ← 不是 'change'
    reason = db.Column(db.String(200), ...)
    reservation_id = db.Column(db.Integer, ...)
    balance_after = db.Column(db.Integer, ...)   # ← 必需字段
    created_at = db.Column(db.DateTime, ...)
```

## 修复方案

### 修复内容
文件: `app/api/reservation.py`

**修复前**:
```python
credit_flow = CreditFlow(
    user_id=user_id,
    change=-5,
    reason='迟到超时',
    reservation_id=reservation_id
)
```

**修复后**:
```python
credit_flow = CreditFlow(
    user_id=user_id,
    action='no_show',                    # ← 新增
    points_change=-5,                    # ← 修改: change → points_change
    reason='迟到超时',
    reservation_id=reservation_id,
    balance_after=user.credit_score      # ← 新增: 提供修改后的余额
)
```

### 修复详情
1. **`change` → `points_change`**: 使用正确的字段名
2. **添加 `action` 字段**: 记录操作类型（'no_show' 表示缺席）
3. **添加 `balance_after` 字段**: 记录修改后的积分余额

## 前端改进

同时改进了前端 `my.js` 的签到函数，添加了：

✅ **输入验证**: 确保 `reservationId` 不为空  
✅ **数据类型转换**: `parseInt(reservationId)` 确保是数字  
✅ **用户确认**: 显示确认对话框 (`wx.showModal`)  
✅ **错误信息**: 从响应中解析并显示详细错误原因  
✅ **调试日志**: 完整的参数和返回值日志  

## 验证方法

### 方法1: 运行诊断脚本
```bash
python test_checkin_simple.py
```

### 方法2: 手动测试
```bash
# 获取有效预约ID
python -c "from app import create_app; from app.models import *; 
app = create_app();
cur = app.app_context()
cur.push()
print(Reservation.query.filter_by(status=0).first().id)"

# 测试签到 API
curl -X POST http://127.0.0.1:5000/api/reservations/check-in \
  -H "X-Test-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"reservation_id": 2}'
```

## 修复影响范围

| 组件 | 修改 | 说明 |
|------|------|------|
| 后端 API | ✅ 修复 | CreditFlow 字段名错误 |
| 前端签到 | ✅ 改进 | 数据验证、错误处理、日志 |
| 预约列表 | ✓ 无需修改 | 数据结构正确 |

##测试列表

- [x] 后端CreditFlow字段修复
- [x] 前端签到函数完善
- [x] 签到功能诊断测试
- [ ] 集成测试 (需要完整环境)
- [ ] UI测试 (需要真实设备)

## 后续建议

1. **添加单元测试**: 为 check-in 端点添加单元测试
2. **数据验证**: 在模型层添加字段验证
3. **错误日志**: 记录所有 CreditFlow 相关操作
4. **文档**: 更新 API 文档中的请求/响应格式

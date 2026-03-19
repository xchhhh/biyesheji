# 并发预约测试文档

## 📋 概述

本文档详细说明如何运行并发预约系统测试，验证系统在高并发场景下的性能和稳定性。测试目标是验证系统能否支持 **100+ 个并发用户** 同时进行座位预约操作，且保证 **99%+ 的成功率** 和 **稳定的响应时间**。

## 🎯 测试目标

| 指标 | 目标值 | 说明 |
|------|-------|------|
| **并发用户数** | 100+ | 同时发起预约请求的用户数 |
| **成功率** | ≥ 99% | 预约请求成功的百分比 |
| **P99 响应时间** | < 1000ms | 99% 的请求在 1 秒内完成 |
| **吞吐量** | ≥ 100 req/s | 每秒可处理的请求数 |
| **零重复预约** | 100% | 无单座多预约的情况发生 |

## 📁 测试文件说明

### 1. **test_concurrent_reservation_v2.py** - 线程并发测试
使用 Python `threading` 模块的并发测试脚本。

**特点：**
- 简单易用，无需额外依赖
- 快速生成测试结果
- 支持多场景配置

**运行方式：**
```bash
python test_concurrent_reservation_v2.py
```

**配置参数（在脚本中修改）：**
```python
NUM_USERS = 100                    # 并发用户数
RESERVATIONS_PER_USER = 1          # 每个用户的预约数
NUM_ROOMS = 3                      # 阅览室数量
NUM_SEATS_PER_ROOM = 100          # 每个房间的座位数
API_BASE_URL = "http://localhost:5000"
```

**输出：**
- 控制台实时日志
- `test_results_YYYYMMDD_HHMMSS.json` - JSON 格式的详细结果

---

### 2. **test_locust_load.py** - Locust 专业负载测试
使用 Locust 框架的企业级负载测试脚本。

**特点：**
- 专业的负载测试框架
- 提供 Web UI 实时监控
- 支持分布式测试
- 生成详细的 HTML 报告

**安装依赖：**
```bash
pip install locust
```

**运行方式：**

**方式 1：命令行运行**
```bash
# 100 个用户，每秒增加 10 个用户，运行 60 秒
locust -f test_locust_load.py --host=http://localhost:5000 -u 100 -r 10 --run-time 60s

# 参数说明：
# -u: 并发用户总数
# -r: 每秒增加的用户数 (缓坡)
# --run-time: 测试持续时间
```

**方式 2：Web UI 交互运行**
```bash
# 启动 Web UI
locust -f test_locust_load.py --host=http://localhost:5000

# 然后在浏览器访问: http://localhost:8089
# 在 Web UI 中设置用户数、增速等参数
```

**输出：**
- 实时图表和统计
- `locust_results_YYYYMMDD_HHMMSS.json` - 详细的测试数据

---

### 3. **test_data_generator.py** - 测试数据生成
生成并发测试所需的测试数据。

**功能：**
- 生成 100 个测试用户
- 创建 3 个阅览室，每个 100 个座位（共 300 个座位）
- 生成 7 个时间槽配置
- 生成认证 Token
- 生成历史预约记录

**运行方式：**
```bash
python test_data_generator.py
```

**输出文件：**
- `test_data.json` - 完整的测试数据（JSON 格式）
- `test_users.csv` - 测试用户列表（便于导入）
- `test_tokens.txt` - 认证 Token 列表

**生成的数据包括：**
```json
{
  "users": [100 个测试用户],
  "rooms": [3 个阅览室],
  "seats": [300 个座位],
  "time_slots": [7 个时间槽],
  "tokens": [100 个认证令牌],
  "reservations": [500 条历史预约记录]
}
```

---

### 4. **test_analysis_report.py** - 测试结果分析
分析测试结果并生成详细的性能报告。

**功能：**
- 加载测试结果 JSON 文件
- 计算关键性能指标
- 生成 HTML 格式的美观报告
- 性能评估和建议

**运行方式：**
```bash
python test_analysis_report.py
```

**自动查找最新的测试结果文件并生成报告**

**输出文件：**
- `test_report_YYYYMMDD_HHMMSS.html` - HTML 格式的美观报告

---

## 🚀 快速开始（完整流程）

### 步骤 1：生成测试数据
```bash
python test_data_generator.py
```

**预期输出：**
```
✓ 生成了 100 个测试用户
✓ 生成了 3 个阅览室
✓ 生成了 300 个座位 (3 个房间 × 100 个座位)
✓ 生成了 7 个时间槽
✓ 生成了 100 个测试 Token
✓ 生成了 500 条历史预约记录
✓ 测试数据已保存到: test_data.json
✓ 部分测试用户数据已保存到: test_users.csv
✓ 测试 Tokens 已保存到: test_tokens.txt
```

### 步骤 2：运行线程并发测试
```bash
python test_concurrent_reservation_v2.py
```

**预期输出：**
```
============================================================
开始并发预约测试
============================================================
并发用户数: 100
每个用户预约数: 1
目标 API: http://localhost:5000
============================================================
成功创建 100 个测试用户
创建 100 个线程...
启动所有线程...
所有线程执行完毕，总耗时: 45.32s

============================================================
并发预约测试结果汇总
============================================================
总请求数: 100
成功请求: 99
失败请求: 1
成功率: 99.00%

响应时间统计 (毫秒):
  平均响应时间: 245.67
  最小响应时间: 120.45
  最大响应时间: 890.23
  P99 响应时间: 850.12

性能指标:
  吞吐量: 2.21 请求/秒
  测试耗时: 45.23 秒

✓ 测试结果已保存到: test_results_20240115_143025.json
============================================================
```

### 步骤 3：（可选）运行 Locust 专业测试
```bash
# 方式 1：直接命令行运行
locust -f test_locust_load.py --host=http://localhost:5000 -u 100 -r 10 --run-time 60s

# 方式 2：启动 Web UI 交互
locust -f test_locust_load.py --host=http://localhost:5000
```

### 步骤 4：分析测试结果
```bash
python test_analysis_report.py
```

**输出示例：**
```
✓ 成功加载结果文件: test_results_20240115_143025.json

======================================================================
并发预约测试结果分析
======================================================================

📊 总体指标:
  总请求数: 100
  成功请求: 99
  失败请求: 1
  成功率: 99.00%

⚡ 性能指标:
  平均响应时间: 245.67 ms
  最小响应时间: 120.45 ms
  最大响应时间: 890.23 ms
  P99 响应时间: 850.12 ms
  吞吐量: 2.21 请求/秒

📈 性能评估:
  ✅ 成功率: 99.00% (良好)
  ✅ P99 响应时间: 850.12ms (在 1000ms 限制内)
  ✅ 吞吐量: 2.21 请求/秒 (良好)

✓ HTML 报告已生成: test_report_20240115_143139.html
```

---

## 🔧 测试场景配置

### 基础场景（推荐用于初始测试）
```python
NUM_USERS = 50
RESERVATIONS_PER_USER = 1
NUM_ROOMS = 3
NUM_SEATS_PER_ROOM = 100
```

### 中等压力场景
```python
NUM_USERS = 100
RESERVATIONS_PER_USER = 1
NUM_ROOMS = 3
NUM_SEATS_PER_ROOM = 100
```

### 高压力场景（压力测试）
```python
NUM_USERS = 200
RESERVATIONS_PER_USER = 2
NUM_ROOMS = 3
NUM_SEATS_PER_ROOM = 100
```

### 极端场景（极限测试）
```python
NUM_USERS = 500
RESERVATIONS_PER_USER = 3
NUM_ROOMS = 3
NUM_SEATS_PER_ROOM = 100
```

---

## 📊 测试指标说明

### 关键指标

| 指标 | 说明 | 单位 | 正常范围 |
|------|------|------|----------|
| **成功率** | 预约成功的请求数 / 总请求数 | % | ≥ 99% |
| **平均响应时间** | 所有请求响应时间的平均值 | ms | < 500ms |
| **P99 响应时间** | 99% 的请求在此时间内完成 | ms | < 1000ms |
| **最大响应时间** | 最慢请求的响应时间 | ms | < 2000ms |
| **吞吐量** | 每秒处理的请求数 | req/s | ≥ 50 |
| **错误率** | 请求失败的百分比 | % | < 1% |

### 衍生指标

- **P50（中位数）**：50% 的请求在此时间内完成
- **P95**：95% 的请求在此时间内完成
- **P99**：99% 的请求在此时间内完成
- **并发度**：同时处理的请求数

---

## ⚙️ 环境要求

### Python 版本
- Python 3.8+

### 依赖库
```bash
# 基础测试依赖
pip install requests

# Locust 专业测试（可选）
pip install locust

# 数据生成（内置的 json, csv）
# 无需额外安装
```

### 系统要求
- 至少 2GB RAM
- 网络连接正常
- 后端服务器可访问

---

## 🚀 性能优化建议

根据测试结果，如果性能指标未达到预期，可考虑以下优化方案：

### 1. **缓存优化**
```python
# 在模型中增加缓存
cache.set(f'room_capacity_{room_id}', capacity_data, timeout=60)
```

### 2. **数据库优化**
```sql
-- 为常查询字段添加索引
CREATE INDEX idx_reservation_date ON reservations(reservation_date);
CREATE INDEX idx_room_status ON reservations(room_id, status);
```

### 3. **连接池优化**
```python
# 增加数据库连接池大小
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

### 4. **异步处理**
```python
# 使用异步框架（如 AsyncIO）处理并发请求
async def reserve_seat_async(seat_id, user_id):
    # 异步逻辑
    pass
```

### 5. **负载均衡**
- 部署多个应用实例
- 使用 Nginx / HAProxy 进行负载均衡
- 根据 CPU/内存 使用情况自动扩展

### 6. **限流和熔断**
```python
# 实现限流（如每个用户每分钟最多 10 个请求）
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)
def reserve_seat(seat_id):
    # 预约逻辑
    pass
```

---

## 📝 测试报告生成

### HTML 报告
自动生成美观的 HTML 报告，包含：
- 总体性能指标
- 详细的响应时间统计
- 错误分析
- 性能评估
- 优化建议

### JSON 报告
机器可读的 JSON 格式，便于集成到 CI/CD 流程

### CSV 报告
表格格式的数据，便于 Excel 分析

---

## 🔍 故障排查

### 问题 1：连接超时
**现象**：大量超时错误
**解决方案**：
- 检查后端服务是否正常运行
- 增加超时时间（在脚本中改大 `REQUEST_TIMEOUT`）
- 检查网络连接

### 问题 2：成功率过低
**现象**：大量失败请求
**解决方案**：
- 检查测试数据是否正确导入
- 验证认证 Token 是否有效
- 检查座位是否充足（是否存在座位不足的情况）

### 问题 3：响应时间过长
**现象**：P99 响应时间超过 1 秒
**解决方案**：
- 检查后端数据库性能
- 启用缓存以减少数据库查询
- 增加应用实例进行并发处理

### 问题 4：内存占用过高
**现象**：测试过程中内存不断增长
**解决方案**：
- 减少并发用户数
- 增加垃圾回收频率
- 检查是否有内存泄漏

---

## 📚 参考资源

### 相关文档
- [Flask 性能优化](https://flask.palletsprojects.com/en/2.0.x/performance/)
- [SQLAlchemy 性能优化](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [Locust 文档](https://docs.locust.io/)
- [HTTP 性能测试最佳实践](https://www.w3.org/TR/web-performance/)

### 性能基准参考
- 一般企业应用：100-500 req/s
- 高性能应用：1000+ req/s
- 超大流量应用：10000+ req/s

---

## 📞 支持和反馈

如在测试过程中遇到问题，请检查：
1. 所有依赖是否正确安装
2. 后端服务是否正常运行
3. 网络连接是否正常
4. 测试数据是否正确生成
5. 查看详细的错误日志

---

## 📋 测试检查清单

在运行完整的并发测试前，请确认以下事项：

- [ ] Python 版本 ≥ 3.8
- [ ] 所有依赖库已安装 (`pip install requests locust`)
- [ ] 后端服务正常运行且可访问
- [ ] 数据库已正确初始化
- [ ] 测试数据已生成 (`test_data.json` 存在)
- [ ] API 认证成功（Token 生成正确）
- [ ] 网络连接稳定
- [ ] 磁盘空间充足（for 日志和报告）
- [ ] 系统资源充足（RAM 至少 2GB）

---

## 📌 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2024-01-15 | 初始版本 - 包含线程测试、Locust 测试、数据生成和分析 |

---

**测试框架由自动化测试系统生成**  
**最后更新：2024-01-15**

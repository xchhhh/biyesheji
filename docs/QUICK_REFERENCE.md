# 高校图书馆座位预约系统 - 快速参考和开发计划

## 📋 第一阶段总结（需求确认与数据库设计）✅ 完成

### ✓ 已完成的工作

#### 1. **数据库设计**
- ✅ 7张核心业务表设计完成
  - `users` - 用户表
  - `reading_rooms` - 阅览室表
  - `seats` - 座位表
  - `reservations` - 预约记录表（核心表）
  - `credit_logs` - 信用积分流水表
  - `seat_status` - 座位实时状态表
  - `dashboard_stats` - 数据看板统计表

- ✅ 完整的SQL初始化脚本（包含：建表、索引、视图、存储过程、触发器）
- ✅ 索引优化和分区策略设计
- ✅ 数据量估算和性能规划

#### 2. **Redis缓存设计**
- ✅ 分层缓存结构设计
- ✅ 缓存键命名规范
- ✅ TTL过期策略
- ✅ 高并发场景处理方案（分布式锁、预约队列）
- ✅ Lua脚本保证原子性操作
- ✅ 限流和防护机制

#### 3. **系统架构设计**
- ✅ B/S架构设计
- ✅ 分层技术架构（表现层、API网关、应用层、缓存层、数据库层）
- ✅ 主从复制和读写分离
- ✅ 监控和告警机制

#### 4. **代码实现**
- ✅ Redis缓存管理类 (`redis_cache.py`)
  - 座位状态缓存操作
  - 用户预约缓存操作
  - 信用积分管理
  - 分布式锁实现
  - 限流控制
  - 热力图数据缓存

- ✅ 高并发预约处理服务 (`high_concurrency_reservation.py`)
  - 带队列的预约流程
  - 直接预约模式
  - Lua脚本原子操作
  - 异步数据库写入
  - 用户通知机制
  - 统计监控

---

## 📚 关键文件说明

| 文件 | 用途 | 重要性 |
|------|------|--------|
| [database_design.md](database_design.md) | 详细的数据库设计文档 | ⭐⭐⭐⭐⭐ |
| [init_database.sql](init_database.sql) | 完整的数据库初始化脚本 | ⭐⭐⭐⭐⭐ |
| [redis_cache.py](redis_cache.py) | Redis缓存管理类 | ⭐⭐⭐⭐ |
| [high_concurrency_reservation.py](high_concurrency_reservation.py) | 高并发预约处理服务 | ⭐⭐⭐⭐ |
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | 系统架构和部署指南 | ⭐⭐⭐⭐ |

---

## 🚀 快速开始（本地开发）

### 第一步：环境准备（10分钟）

```bash
# 1. 安装MySQL
# macOS: brew install mysql
# Ubuntu: sudo apt-get install mysql-server
# Windows: https://dev.mysql.com/downloads/

# 2. 安装Redis
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
# Windows: https://github.com/microsoftarchive/redis/releases

# 3. 验证安装
mysql --version
redis-cli --version
```

### 第二步：数据库初始化（5分钟）

```bash
# 启动MySQL服务
mysql -u root -p

# 在MySQL命令行中执行初始化脚本
source init_database.sql;

# 验证
USE library_seat_booking;
SHOW TABLES;  # 应该显示7张表
```

### 第三步：启动Redis（2分钟）

```bash
# 另开一个终端
redis-server

# 验证Redis存活
redis-cli ping  # 返回 PONG
```

### 第四步：开发环境配置（5分钟）

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows (PowerShell)

# 安装依赖
pip install redis mysql-connector-python

# 测试Redis连接
python -c "import redis; r = redis.Redis(); print(r.ping())"
```

---

## 📊 数据库核心表关系

```
users (用户)
  ├─ 一对多 → reservations (预约)
  ├─ 一对多 → credit_logs (信用积分流水)
  └─ 一对多 → seat_status (座位状态)

reading_rooms (阅览室)
  ├─ 一对多 → seats (座位)
  ├─ 一对多 → reservations (预约)
  └─ 一对多 → seat_status (座位状态)

seats (座位)
  ├─ 一对多 → reservations (预约)
  └─ 一对一 → seat_status (座位状态)

reservations (预约) [核心表]
  ├─ 多对一 → users (用户)
  ├─ 多对一 → seats (座位)
  ├─ 多对一 → reading_rooms (阅览室)
  └─ 一对多 → credit_logs (可能关联的积分扣分)

credit_logs (信用积分流水)
  └─ 多对一 → users (用户)

seat_status (座位实时状态)
  ├─ 一对一 → seats (座位)
  └─ 多对一 → reading_rooms (阅览室)

dashboard_stats (数据看板统计)
  └─ 多对一 → reading_rooms (可选关联阅览室)
```

---

## 💾 Redis缓存层Key设计速查表

### 座位相关

```
seat:status:{room_id}:{seat_id}
  ├─ current_status: "free" | "reserved" | "occupied"
  ├─ user_id: 123
  ├─ reservation_id: 456
  └─ TTL: 24小时

room:seats:status:{room_id}
  ├─ seat_001: "free"
  ├─ seat_002: "reserved"
  └─ TTL: 24小时
```

### 用户相关

```
user:credit_score:{user_id}
  ├─ value: 95
  └─ TTL: 1小时

user:banned:{user_id}
  ├─ value: "1" (存在则被禁用)
  └─ TTL: 自定义

user:reservations:{user_id}:{date}
  ├─ members: [reservation_id1, reservation_id2, ...]
  └─ TTL: 24小时
```

### 高并发相关

```
lock:reserve:{seat_id}:{date}:{time_slot}
  ├─ value: uuid
  └─ TTL: 30秒 (防止死锁)

queue:reserve:{room_id}:{date}:{time_slot}
  ├─ list: [request_data1, request_data2, ...]
  └─ TTL: 5分钟

rate_limit:reserve:{user_id}:{date}
  ├─ value: 请求计数
  └─ TTL: 24小时
```

### 热力图相关

```
room:heatmap:hourly:{room_id}:{date}:{hour}
  ├─ seat_001: 15
  ├─ seat_002: 8
  └─ seat_003: 23
  └─ TTL: 30分钟
```

---

## 🔄 高并发预约流程（时序图）

```
用户并发请求 → 限流检查 → 获取分布式锁
                                 ↓
                    ┌─────加锁成功──┴──失败加入队列
                    ↓
            检查座位状态
                    ↓
            ┌──空闲────通常完成
            └──已占用──返回失败
            
座位被释放 → 处理等待队列 → 通知下一个用户
```

---

## 📈 系统扩展点支持

### 已支持的功能

- ✅ 多阅览室管理
- ✅ 多座位类型（普通/靠窗/安静）
- ✅ 信用积分机制
- ✅ 用户违规记录
- ✅ 预约热力图
- ✅ 数据看板统计
- ✅ 主从复制（读写分离）
- ✅ Redis集群（可选）

### 可扩展方向

- [ ] 长期座位租赁
- [ ] 校园卡集成
- [ ] 自动签到识别
- [ ] 短信/邮件通知
- [ ] 商城积分兑换
- [ ] AI推荐座位

---

## ⚠️ 高并发场景注意事项

### 潜在问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 座位重复预约 | 缓存和数据库不同步 | 使用Lua脚本保证原子性 |
| 预约速度慢 | 数据库锁争抢 | 使用Redis队列分散流量 |
| 内存溢出 | Redis缓存过大 | 设置合理TTL和maxmemory策略 |
| 数据丢失 | Redis故障 | 启用持久化（RDB+AOF） |
| 积分错误 | 并发扣分冲突 | 在数据库层使用事务 |
| 队列堆积 | 处理速度慢 | 优化处理逻辑，增加服务器 |

### 性能基准

基于本设计，预期性能指标：

```
场景：早上8点抢座高峰
├─ 并发用户数：1000+
├─ 平均响应时间：< 500ms
├─ 成功预约率：> 95%
├─ 系统可用性：> 99.9%
└─ 数据一致性：强一致性

达成方式：
├─ Redis使用分布式锁
├─ 预约队列平滑处理
├─ 异步数据库写入
├─ 多层缓存
└─ CDN静态资源加速
```

---

## 📝 下一阶段开发计划

### 🎯 第二阶段：后端API开发

**目标**：实现Flask应用层和完整API接口

工作内容：
1. Flask项目结构搭建
2. 认证模块开发（微信登录）
3. 预约管理API实现
4. 座位查询API实现
5. 用户信息API实现
6. 数据看板API实现
7. 单元测试编写

时间估计：2-3周

---

### 🎯 第三阶段：前端开发

**目标**：实现微信小程序前端

工作内容：
1. 登录页面
2. 座位地图页面（含热力图）
3. 预约管理页面
4. 个人信息页面
5. 数据看板页面
6. 实时更新（WebSocket）集成

时间估计：2-3周

---

### 🎯 第四阶段：系统测试和优化

**目标**：性能测试、安全测试、系统优化

工作内容：
1. 压力测试（1000+并发）
2. 安全渗透测试
3. 性能优化调整
4. 部署方案验证
5. 监控告警配置

时间估计：1-2周

---

### 🎯 第五阶段：上线运维

**目标**：系统部署、运维和迭代

工作内容：
1. 生产环境部署
2. 数据迁移
3. 故障演练
4. 运维文档编写
5. 用户培训

时间估计：1周

---

## 🛠️ 常用开发命令

### MySQL操作

```bash
# 连接数据库
mysql -u root -p library_seat_booking

# 备份
mysqldump -u root -p library_seat_booking > backup.sql

# 恢复
mysql -u root -p library_seat_booking < backup.sql

# 查看表结构
DESCRIBE reservations;

# 查看索引
SHOW INDEX FROM reservations;
```

### Redis操作

```bash
# 连接
redis-cli

# 查看所有Key
KEYS *

# 查看特定Key
KEYS seat:status:*

# 查看内存
INFO memory

# 查看慢查询
SLOWLOG GET 10

# 清空数据库
FLUSHDB     # 清空当前数据库
FLUSHALL    # 清空所有数据库

# 监控实时命令
MONITOR
```

### Python测试

```python
# 测试Redis连接
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print(r.ping())  # 应返回 True

# 测试MySQL连接
import mysql.connector
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='library_seat_booking'
)
print(conn.is_connected())  # 应返回 True

# 测试缓存功能
from redis_cache import RedisCache
cache = RedisCache()
cache.set_seat_status(1, 101, "free")
print(cache.get_seat_status(1, 101))
```

---

## 📞 故障排查快速指南

### Redis无法连接

```bash
# 检查Redis是否运行
redis-cli ping

# 检查端口
netstat -an | grep 6379

# 查看Redis日志
redis-server --loglevel verbose
```

### MySQL无法连接

```bash
# 检查MySQL是否运行
sudo service mysql status

# 查看MySQL日志
tail -f /var/log/mysql/error.log

# 重启MySQL
sudo service mysql restart
```

### 预约失败问题排查

```bash
# 1. 检查座位状态
redis-cli HGETALL "seat:status:1:101"

# 2. 检查用户禁用状态
redis-cli EXISTS "user:banned:1001"

# 3. 检查限流器
redis-cli GET "rate_limit:reserve:1001:2024-03-20"

# 4. 检查锁状态
redis-cli KEYS "lock:reserve:*"

# 5. 检查数据库预约记录
mysql> SELECT * FROM reservations WHERE user_id=1001;
```

---

## 📖 推荐学习资源

1. **Redis官方文档**
   - https://redis.io/documentation
   - 重点：Lua脚本、事务、集群

2. **MySQL优化指南**
   - https://dev.mysql.com/doc/
   - 重点：索引、分区、主从复制

3. **Flask文档**
   - https://flask.palletsprojects.com/
   - 重点：蓝图、扩展、最佳实践

4. **微信小程序官方文档**
   - https://developers.weixin.qq.com/miniprogram/

---

## ✨ 总结

本阶段完成了系统的底层设计和规划：

✅ **7张核心数据库表** - 支持高并发、可扩展
✅ **完整的Redis缓存方案** - 分层缓存、分布式锁、限流
✅ **高并发处理架构** - 预约队列、异步处理、原子操作
✅ **系统架构设计** - B/S架构、主从复制、监控告警
✅ **生产级部署方案** - Docker、Nginx、Supervisor

现在已具备开始第二阶段（后端API开发）的基础！

---

---

## 📋 第二阶段总结（Flask 项目骨架与用户认证）✅ 完成

### ✓ 已完成的工作

#### 1. **Flask 项目骨架**
- ✅ 完整的项目目录结构
- ✅ 应用工厂模式实现
- ✅ 蓝图模块化设计
- ✅ 多环境配置支持（开发、测试、生产）

#### 2. **数据模型实现**
- ✅ User 模型（用户认证、信用积分）
- ✅ Seat 模型（座位状态管理）
- ✅ ReadingRoom 模型（阿览室信息）
- ✅ Reservation 模型（预约记录）
- ✅ CreditFlow 模型（积分流水）
- ✅ 完整的关系定义和索引优化

#### 3. **用户认证模块**
- ✅ `POST /api/v1/auth/login` - 微信小程序登录
- ✅ `POST /api/v1/auth/verify-token` - Token 验证
- ✅ `POST /api/v1/auth/refresh-token` - Token 刷新
- ✅ JWT Token 生成和验证
- ✅ login_required 装饰器

#### 4. **工具模块**
- ✅ WechatService - 微信接口交互
- ✅ JWTHandler - JWT Token 处理
- ✅ ApiResponse - 统一响应格式
- ✅ AuthService - 认证服务

#### 5. **配置管理**
- ✅ 多环境配置支持
- ✅ 环境变量管理（.env）
- ✅ 数据库连接字符串
- ✅ JWT 密钥管理

#### 6. **文档和测试**
- ✅ BACKEND_SETUP.md - 快速开始指南
- ✅ API_DOCUMENTATION.md - API 完整文档
- ✅ DEVELOPMENT_GUIDE.md - 开发规范
- ✅ PROJECT_STRUCTURE.md - 项目结构说明
- ✅ test_auth.py - API 测试脚本
- ✅ init_db.py - 数据库初始化脚本

### 📁 完整项目结构

```
app/
├── __init__.py           # 应用工厂函数
├── config.py             # 环境配置
├── models/               # 数据模型（5个）
├── auth/                 # 认证模块
├── utils/                # 工具模块（3个工具类）
└── api/                  # API 模块（预留）

run.py                   # 启动入口
init_db.py              # 数据库初始化
requirements.txt        # 8 个依赖包
总计：20+ 个文件
```

### 🚀 快速开始

```bash
1. pip install -r requirements.txt
2. 编辑 .env 文件配置
3. python init_db.py
4. python run.py
5. 访问 http://127.0.0.1:5000
```

### ✨ 核心特性

- ✅ 工厂模式 - 灵活应用初始化
- ✅ 蓝图模式 - 模块化路由
- ✅ 装饰器模式 - 简洁认证
- ✅ 错误处理完善 - 统一响应
- ✅ 日志记录充分 - 便于调试
- ✅ 生产就绪 - 支持多环境

### 📞 下一步

- [ ] 座位预约功能 (Phase 3)
- [ ] 数据看板功能
- [ ] Redis 缓存集成
- [ ] 生产环境部署

---

**最后更新**: 2026-03-17  
**阶段状态**: ✅ 完成  
**下一步**: Phase 3 - 座位预约功能开发  
**预计总工期**: 8-10周

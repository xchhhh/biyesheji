# 高校图书馆座位预约系统 - 数据库设计文档

## 一、系统架构概述

**技术栈**：Python Flask + 微信小程序 + MySQL + Redis

**B/S架构**：
- 前端：微信小程序
- 后端：Flask 应用服务器
- 数据库：MySQL（持久化存储）
- 缓存：Redis（高并发处理、会话管理）

**核心业务模块**：
1. 预约管理 - 用户预约座位
2. 座位状态展示 - 包含热力图展示
3. 违规记录 - 信用积分机制
4. 数据看板 - 统计和分析

---

## 二、数据库表结构设计

### 2.1 用户表（users）

存储用户的基本信息和信用积分。

```sql
CREATE TABLE `users` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  `student_id` VARCHAR(20) UNIQUE NOT NULL COMMENT '学号',
  `name` VARCHAR(100) NOT NULL COMMENT '用户姓名',
  `phone` VARCHAR(11) COMMENT '手机号',
  `school` VARCHAR(100) COMMENT '所属学院',
  `major` VARCHAR(100) COMMENT '专业',
  `wechat_openid` VARCHAR(100) UNIQUE NOT NULL COMMENT '微信小程序openid',
  `credit_score` INT DEFAULT 100 COMMENT '信用积分（初始100分）',
  `total_violations` INT DEFAULT 0 COMMENT '总违规次数',
  `is_banned` TINYINT DEFAULT 0 COMMENT '是否被禁用（0=正常，1=禁用）',
  `banned_until` DATETIME COMMENT '封禁截止时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  KEY `idx_student_id` (`student_id`),
  KEY `idx_wechat_openid` (`wechat_openid`),
  KEY `idx_credit_score` (`credit_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

---

### 2.2 阅览室表（reading_rooms）

存储不同阅览室的信息。

```sql
CREATE TABLE `reading_rooms` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '阅览室ID',
  `room_code` VARCHAR(50) UNIQUE NOT NULL COMMENT '阅览室编码（如：A101）',
  `room_name` VARCHAR(100) NOT NULL COMMENT '阅览室名称',
  `total_seats` INT NOT NULL COMMENT '总座位数',
  `floor` INT COMMENT '楼层',
  `location` VARCHAR(200) COMMENT '具体位置描述',
  `open_time` TIME NOT NULL COMMENT '开放开始时间',
  `close_time` TIME NOT NULL COMMENT '关闭结束时间',
  `image_url` VARCHAR(255) COMMENT '阅览室示意图URL',
  `is_active` TINYINT DEFAULT 1 COMMENT '是否启用（0=禁用，1=启用）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_room_code` (`room_code`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='阅览室表';
```

---

### 2.3 座位表（seats）

存储每个阅览室中的座位信息。

```sql
CREATE TABLE `seats` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '座位ID',
  `room_id` INT NOT NULL COMMENT '阅览室ID',
  `seat_code` VARCHAR(50) NOT NULL COMMENT '座位编号（如：A-001）',
  `seat_row` VARCHAR(10) COMMENT '行（如：A、B、C）',
  `seat_col` INT COMMENT '列（如：1、2、3）',
  `x_coordinate` DECIMAL(10, 2) COMMENT '座位在热力图中的X坐标',
  `y_coordinate` DECIMAL(10, 2) COMMENT '座位在热力图中的Y坐标',
  `seat_type` ENUM('regular', 'window', 'quiet') DEFAULT 'regular' COMMENT '座位类型（普通、靠窗、安静区）',
  `is_active` TINYINT DEFAULT 1 COMMENT '是否启用（0=停用，1=启用）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY `uk_room_seat` (`room_id`, `seat_code`),
  KEY `idx_room_id` (`room_id`),
  KEY `idx_seat_type` (`seat_type`),
  CONSTRAINT `fk_seats_room_id` FOREIGN KEY (`room_id`) REFERENCES `reading_rooms` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='座位表';
```

---

### 2.4 预约记录表（reservations）

核心表，记录所有座位预约信息。

```sql
CREATE TABLE `reservations` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '预约ID',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `seat_id` INT NOT NULL COMMENT '座位ID',
  `room_id` INT NOT NULL COMMENT '阅览室ID',
  `reserve_date` DATE NOT NULL COMMENT '预约日期',
  `start_time` TIME NOT NULL COMMENT '开始时间',
  `end_time` TIME NOT NULL COMMENT '结束时间',
  `status` ENUM('pending', 'active', 'completed', 'cancelled', 'no_show') DEFAULT 'pending' COMMENT '状态（待确认、进行中、已完成、已取消、未签到）',
  `check_in_time` DATETIME COMMENT '签到时间',
  `check_out_time` DATETIME COMMENT '退座时间',
  `is_violation` TINYINT DEFAULT 0 COMMENT '是否违规（0=否，1=是：未签到）',
  `violation_reason` VARCHAR(255) COMMENT '违规原因描述',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  KEY `idx_user_id` (`user_id`),
  KEY `idx_seat_id` (`seat_id`),
  KEY `idx_room_id` (`room_id`),
  KEY `idx_reserve_date` (`reserve_date`),
  KEY `idx_status` (`status`),
  KEY `idx_user_date` (`user_id`, `reserve_date`),
  KEY `idx_seat_date` (`seat_id`, `reserve_date`),
  CONSTRAINT `fk_reservations_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reservations_seat_id` FOREIGN KEY (`seat_id`) REFERENCES `seats` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reservations_room_id` FOREIGN KEY (`room_id`) REFERENCES `reading_rooms` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预约记录表';
```

---

### 2.5 信用积分流水表（credit_logs）

记录用户的每一笔信用积分变化，用于审计和追踪。

```sql
CREATE TABLE `credit_logs` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '流水ID',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `operation_type` ENUM('deduction', 'recovery', 'manual_adjust') DEFAULT 'deduction' COMMENT '操作类型（扣分、恢复、手动调整）',
  `points_change` INT NOT NULL COMMENT '积分变化值（负数表示扣分）',
  `reason` VARCHAR(255) NOT NULL COMMENT '原因描述',
  `related_reservation_id` INT COMMENT '关联的预约ID',
  `balance_after` INT NOT NULL COMMENT '操作后的信用积分余额',
  `operator` VARCHAR(100) COMMENT '操作者（系统或管理员）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_operation_type` (`operation_type`),
  CONSTRAINT `fk_credit_logs_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='信用积分流水表';
```

---

### 2.6 座位实时状态表（seat_status）

用于快速查询座位的实时状态（可选，用于优化查询性能）。

```sql
CREATE TABLE `seat_status` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `seat_id` INT NOT NULL COMMENT '座位ID',
  `room_id` INT NOT NULL COMMENT '阅览室ID',
  `current_status` ENUM('free', 'reserved', 'occupied', 'occupied_pending') DEFAULT 'free' COMMENT '座位状态（空闲、已预约、被占用、被占用待确认）',
  `last_reservation_id` INT COMMENT '最后一条预约记录ID',
  `status_changed_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '状态最后更改时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_seat_id` (`seat_id`),
  KEY `idx_room_id` (`room_id`),
  KEY `idx_current_status` (`current_status`),
  CONSTRAINT `fk_seat_status_seat_id` FOREIGN KEY (`seat_id`) REFERENCES `seats` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='座位实时状态表';
```

---

### 2.7 数据看板统计表（dashboard_stats）

存储定期生成的统计数据，支持数据看板快速展示。

```sql
CREATE TABLE `dashboard_stats` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `stat_date` DATE NOT NULL COMMENT '统计日期',
  `stat_type` VARCHAR(50) NOT NULL COMMENT '统计类型（daily_total、hourly_peak等）',
  `room_id` INT COMMENT '阅览室ID（为NULL时表示全校数据）',
  `total_reservations` INT DEFAULT 0 COMMENT '总预约数',
  `completed_reservations` INT DEFAULT 0 COMMENT '已完成预约数',
  `cancelled_reservations` INT DEFAULT 0 COMMENT '已取消预约数',
  `violation_count` INT DEFAULT 0 COMMENT '违规次数',
  `occupancy_rate` DECIMAL(5, 2) COMMENT '座位占用率（百分比）',
  `peak_hour` INT COMMENT '高峰时段小时数',
  `peak_hour_occupancy` DECIMAL(5, 2) COMMENT '高峰时段占用率',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY `uk_stat_date_type` (`stat_date`, `stat_type`, `room_id`),
  KEY `idx_stat_date` (`stat_date`),
  KEY `idx_room_id` (`room_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据看板统计表';
```

---

## 三、Redis缓存设计

### 3.1 缓存Key结构设计

使用分层命名空间：`{模块}:{对象}:{标识}:{字段}`

#### 3.1.1 座位状态缓存

```
# 单个座位状态（Hash）
seat:status:{room_id}:{seat_id}
  - current_status: "free" | "reserved" | "occupied"
  - reservation_id: 12345
  - expires_at: 2024-03-17 14:30:00

# 单个阅览室所有座位状态（Hash）
room:seats:status:{room_id}
  - seat_001: "free"
  - seat_002: "reserved"
  - seat_003: "occupied"

# 按时间段的座位可用性（Sorted Set，用于高效查询）
room:seats:available:{room_id}:{date}:{time_slot}
  - sorted by seat_id
  - members: seat_001, seat_002, ...

# 实时座位计数（String）
room:seats:count:{room_id}
  - total: 100
  - free: 45
  - reserved: 30
  - occupied: 25
```

#### 3.1.2 用户预约缓存

```
# 用户当日预约（List）
user:reservations:{user_id}:{date}
  - [reservation_id1, reservation_id2, ...]

# 用户信用积分（String）
user:credit_score:{user_id}
  - value: 95

# 用户禁用状态（String）
user:banned:{user_id}
  - value: "1" 或过期
  - ttl: 封禁时长

# 用户预约历史（Sorted Set，用于快速查询）
user:reservation:history:{user_id}
  - score: timestamp
  - member: reservation_id
```

#### 3.1.3 热力图数据缓存

```
# 座位热度统计（Sorted Set）
room:seat:heatmap:{room_id}:{date}
  - score: 访问次数/热度值
  - member: seat_id

# 按时间段的座位热度（Hash）
room:heatmap:hourly:{room_id}:{date}:{hour}
  - seat_001: 15
  - seat_002: 8
  - seat_003: 23
```

#### 3.1.4 分布式锁和计数器

```
# 防止重复预约的锁（String，SET with NX）
lock:reserve:seat:{seat_id}:{date}:{time_slot}
  - value: "locked"
  - ttl: 5秒

# 预约请求计数器（用于限流）
rate_limit:reserve:{user_id}:{date}
  - value: 请求数
  - ttl: 1天

# 预约队列（List，用于高并发场景）
queue:reserve:pending
  - [request_id1, request_id2, ...]
```

#### 3.1.5 会话和临时数据缓存

```
# 用户会话（Hash）
session:{session_id}
  - user_id: 12345
  - wechat_openid: oxxxxxx
  - login_time: 1710698400
  - ttl: 24小时

# 微信授权数据（String）
wechat:auth:{user_id}
  - value: access_token
  - ttl: 2小时
```

---

### 3.2 高并发场景处理方案（早上8点抢座）

#### 问题分析
- **突发流量**：大量用户同时预约
- **竞态条件**：多个用户抢同一个座位
- **数据一致性**：预约状态需要立即反映

#### 解决方案

**方案 A: 使用 Redis 分布式锁 + 预约队列**

```python
# 伪代码示例
def reserve_seat_high_concurrency(user_id, room_id, seat_id, date, time_slot):
    lock_key = f"lock:reserve:seat:{seat_id}:{date}:{time_slot}"
    queue_key = f"queue:reserve:{room_id}:{date}:{time_slot}"
    
    # 1. 尝试获取分布式锁（SET NX EX）
    lock_value = str(uuid4())
    acquired = redis_client.set(lock_key, lock_value, nx=True, ex=30)
    
    if not acquired:
        # 2. 加入等待队列
        request_id = str(uuid4())
        redis_client.lpush(queue_key, request_id)
        return {"status": "queued", "request_id": request_id}
    
    try:
        # 3. 检查座位状态（从Redis快速查询）
        seat_status = redis_client.hget(f"seat:status:{room_id}:{seat_id}", "current_status")
        
        if seat_status != "free":
            return {"status": "failed", "reason": "Seat not available"}
        
        # 4. 更新Redis中的座位状态
        redis_client.hset(
            f"seat:status:{room_id}:{seat_id}",
            mapping={
                "current_status": "reserved",
                "reservation_id": reservation_id,
                "user_id": user_id
            }
        )
        redis_client.expire(f"seat:status:{room_id}:{seat_id}", 86400)  # 24小时
        
        # 5. 异步插入数据库
        queue_db_insert.delay(reservation_data)
        
        return {"status": "success", "reservation_id": reservation_id}
        
    finally:
        # 6. 处理等待队列中的下一个请求
        next_request = redis_client.rpop(queue_key)
        if next_request:
            # 通知下一个请求继续处理
            redis_client.publish(f"channel:reserve:{room_id}", next_request)
        
        # 7. 释放锁
        if redis_client.get(lock_key) == lock_value:
            redis_client.delete(lock_key)
```

**方案 B: 使用 Lua 脚本保证原子性**

```lua
-- Redis Lua脚本：原子性地预约座位
local seat_key = KEYS[1]
local lock_key = KEYS[2]
local seat_status_key = KEYS[3]

local user_id = ARGV[1]
local reservation_id = ARGV[2]
local ttl = ARGV[3]

-- 检查座位状态 + 更新原子操作
local current_status = redis.call('HGET', seat_status_key, 'current_status')

if current_status == 'free' or current_status == nil then
    redis.call('HSET', seat_status_key, 'current_status', 'reserved')
    redis.call('HSET', seat_status_key, 'user_id', user_id)
    redis.call('HSET', seat_status_key, 'reservation_id', reservation_id)
    redis.call('EXPIRE', seat_status_key, ttl)
    return 1  -- 预约成功
else
    return 0  -- 座位已被预约
end
```

#### 缓存更新策略

```
# 1. Cache-Aside（旁路缓存）
读取流程：
  1. 查询 Redis 缓存
  2. 缓存未命中 → 查询 MySQL
  3. 将结果写回 Redis
  4. 返回数据

写入流程：
  1. 先更新 MySQL
  2. 删除 Redis 缓存（或更新）
  3. 返回结果

# 2. 失效时间（TTL）策略
座位状态：24小时
用户信息：1小时
热力图数据：30分钟
会话数据：24小时
临时队列数据：5分钟

# 3. 缓存预热
系统启动时：
  1. 加载所有阅览室信息到 Redis
  2. 初始化所有座位为 "free" 状态
  3. 加载当日的所有预约到缓存

# 4. 缓存穿透防护
  1. 对不存在的数据设置负值缓存（TTL: 5分钟）
  2. 使用布隆过滤器（Bloom Filter）预过滤请求
```

---

### 3.3 Redis集群建议（可选，用于超高并发）

```
# 配置建议
Redis Cluster（6个节点）：
  - 3个主节点 + 3个从节点
  - 单个节点内存：4GB
  - 总容量：12GB
  
或使用
Redis Sentinel（高可用）：
  - 1个主节点 + 2个从节点
  - 自动故障转移
  - 内存：8GB

# 监控关键指标
  - 缓存命中率：目标 > 80%
  - 平均响应时间：< 10ms
  - 内存使用率：< 80%
  - 连接数：监控连接池
```

---

## 四、索引优化建议

### 4.1 必须建立的索引

```sql
-- 用户表
- idx_credit_score: 用于信用积分查询
- idx_wechat_openid: 用于微信登录查询

-- 座位表
- idx_room_id: 查询某阅览室所有座位
- idx_seat_type: 按座位类型过滤

-- 预约表（最关键）
- idx_user_id: 查询用户预约列表
- idx_seat_id: 查询座位某日所有预约
- idx_reserve_date: 按日期范围查询
- uk_user_date_status: 复合索引，查询用户今日预约

-- 信用积分流水表
- idx_user_id: 查询用户积分流水
- idx_created_at: 按时间范围查询
```

### 4.2 分区策略（MySQL分表）

```sql
-- 预约表按日期分区（减少表大小）
ALTER TABLE reservations PARTITION BY RANGE (YEAR_MONTH(reserve_date)) (
    PARTITION p_202401 VALUES LESS THAN (202402),
    PARTITION p_202402 VALUES LESS THAN (202403),
    PARTITION p_202403 VALUES LESS THAN (202404),
    ...
    PARTITION p_max VALUES LESS THAN MAXVALUE
);

-- 信用积分表按月份分区
ALTER TABLE credit_logs PARTITION BY RANGE (YEAR_MONTH(created_at)) (
    ...
);
```

---

## 五、数据量估算

```
假设场景：
- 学生用户：10000人
- 阅览室：20个
- 单个阳览室座位：100个
- 总座位数：2000个
- 每日预约量：5000条
- 系统运行周期：4年

数据表大小估算：
- users: 10000条 × 1KB ≈ 10MB
- reading_rooms: 20条 × 500B ≈ 10KB
- seats: 2000条 × 500B ≈ 1MB
- reservations (4年): 5000×365×4条 ≈ 730万条 × 1.5KB ≈ 11GB
- credit_logs (4年): 70万条 × 500B ≈ 350MB
- 总数据库大小：约 15GB

Redis内存估算：
- 座位状态缓存：2000×500B ≈ 1MB
- 用户预约缓存：10000×10条×100B ≈ 10MB
- 热力图数据：2000×8个时间段×100B ≈ 1.6MB
- 会话数据：假设1000个在线用户×1KB ≈ 1MB
- 其他缓存：5MB
- 总计：约 20MB（可以很轻松地运行在单个Redis实例上）
```

---

## 六、数据库初始化脚本总和

完整的建表语句请见 [init_database.sql](./init_database.sql) 文件。

---

## 七、后续设计方向

1. **性能优化**
   - 定期清理过期预约数据
   - 创建物化视图加速统计查询
   - 使用读写分离（MySQL主从复制）

2. **安全性**
   - 用户密码加密存储
   - API请求签名验证
   - 防止SQL注入、XSS攻击

3. **扩展性**
   - 支持多校区部署
   - 支持长期座位租赁
   - 整合校园卡系统

4. **可观测性**
   - 详细的操作日志
   - 监控告警机制
   - 数据备份恢复方案

---

**本文档版本**：1.0  
**最后更新**：2026-03-17  
**状态**：待审核

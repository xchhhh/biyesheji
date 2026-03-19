# 高校图书馆座位预约系统 - 系统架构与部署指南

## 一、系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        微信小程序客户端                              │
│  (用户界面、座位选择、预约管理)                                     │
└────────────────────────┬────────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        │  HTTPS/WSS                      │ HTTPS
        │  (WebSocket实时更新)            │ (RESTful API)
        │                                 │
┌───────▼──────────────────────────────────▼──────────────────────────┐
│                         CDN / 负载均衡器                            │
│  (HTTPS、静态资源缓存、请求分发)                                   │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│  Flask APP   │  │  Flask APP  │  │  Flask APP  │
│   Server 1   │  │   Server 2  │  │   Server 3  │
│ (端口5000~)  │  │ (端口5001~) │  │ (端口5002~) │
└───────┬──────┘  └──────┬──────┘  └──────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────────────────────────────────▼──────────────┐
│               缓存层 (Redis)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Master  │  │ Slave 1  │  │ Slave 2  │              │
│  │(Port 6379)  │(6380)    │  │(6381)    │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│  • 座位状态    • 用户会话    • 热力图数据              │
│  • 预约队列    • 信用积分    • 限流计数器              │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴──────────┐
        │                   │
┌───────▼─────────────┐  ┌──▼──────────────────┐
│   Message Queue     │  │  定时任务队列        │
│   (RabbitMQ/Redis)  │  │  (Celery/APScheduler)│
│  ┌─────────────┐    │  │ • 违规检测           │
│  │ 数据库写入  │    │  │ • 统计计算           │
│  │ 通知发送    │    │  │ • 缓存更新           │
│  │ 日志处理    │    │  │ • 数据备份           │
│  └─────────────┘    │  └───────┬──────────────┘
└─────────────────────┘          │
                                  │
        ┌─────────────────────────▼──────────────┐
        │                                        │
┌───────▼──────────────────────────────────────────▼─────┐
│                 数据库层 (MySQL)                       │
│  ┌─────────────────────────┐  ┌─────────────────────┐ │
│  │      主数据库           │  │   从数据库 (只读)   │ │
│  │  (Port 3306)            │  │   (Port 3307~)      │ │
│  │ • 用户表                │  │                     │ │
│  │ • 阅览室表              │  │   主从复制          │ │
│  │ • 座位表                │  │                     │ │
│  │ • 预约表                │  │   读写分离          │ │
│  │ • 积分流水表            │  │                     │ │
│  │ • 统计表                │  │                     │ │
│  └─────────────────────────┘  └─────────────────────┘ │
│                                                        │
│                    备份/恢复机制                       │
└────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────┐
│          监控和日志系统                   │
│  • ELK Stack (Elasticsearch/Logstash)   │
│  • Prometheus + Grafana                 │
│  • Jaeger (链路追踪)                    │
│  • 告警系统 (AlertManager)              │
└──────────────────────────────────────────┘
```

---

## 二、详细分层设计

### 2.1 表现层（表现前端）

**微信小程序客户端**

- 用户认证与授权
- 座位地图展示（包含热力图）
- 实时座位状态更新（WebSocket）
- 预约管理界面
- 个人信息展示

**特点**：
- 轻量级，响应快
- 离线缓存功能
- 支持PWA（可选）

### 2.2 API网关层

**负载均衡和反向代理**

- Nginx/HAProxy 负载均衡
- SSL/TLS加密
- 静态資源緩存
- 请求路由和限流

### 2.3 应用层（Python Flask）

```
Flask Application Structure:
├── app.py                 # 应用入口
├── config.py             # 配置管理
├── controllers/          # 控制层
│   ├── auth_controller.py       # 认证
│   ├── reservation_controller.py # 预约
│   ├── seat_controller.py       # 座位
│   └── dashboard_controller.py  # 数据看板
├── services/            # 业务逻辑层
│   ├── reservation_service.py
│   ├── seat_service.py
│   ├── user_service.py
│   └── cache_service.py
├── models/              # 数据模型层
│   ├── user.py
│   ├── reservation.py
│   ├── seat.py
│   └── reading_room.py
├── utils/               # 工具函数
│   ├── decorators.py     # 装饰器（认证、限流）
│   ├── converters.py     # 数据转换
│   └── validators.py     # 参数验证
├── middleware/          # 中间件
│   ├── auth_middleware.py
│   ├── error_handler.py
│   └── logging_middleware.py
└── tests/               # 单元测试
```

**核心API端点**

| 端点 | 方法 | 功能 | 说明 |
|------|-----|-----|------|
| `/api/auth/login` | POST | 微信登录 | openid换取session |
| `/api/reservation/reserve` | POST | 创建预约 | 高并发处理 |
| `/api/reservation/list` | GET | 预约列表 | 用户预约历史 |
| `/api/reservation/cancel` | DELETE | 取消预约 | 释放座位 |
| `/api/reservation/{id}/checkin` | POST | 签到 | 标记入场 |
| `/api/seat/status` | GET | 座位状态 | 获取实时状态 |
| `/api/seat/heatmap` | GET | 热力图 | 座位热度展示 |
| `/api/room/list` | GET | 阅览室列表 | 快速查询 |
| `/api/user/profile` | GET | 用户信息 | 含信用积分 |
| `/api/dashboard/stats` | GET | 数据统计 | 汇总数据 |

### 2.4 缓存层（Redis）

**多层缓存策略**

```
第1层: 应用内存缓存（LocalCache）
  - 高频访问的配置
  - TTL: 5-10分钟
  
第2层: Redis缓存（分布式缓存）
  - 座位状态
  - 用户会话
  - 热力图数据
  - TTL: 30分钟 - 24小时
  
第3层: MySQL数据库（持久化）
  - 完整数据存储
  - 事务支持
  - 备份恢复
```

**缓存键设计规范**

```
命名规范: {module}:{sub_module}:{object_type}:{identifier}

示例:
  - seat:status:1:101           # 1号阅览室的101座位状态
  - user:credit_score:1001      # 用户1001的信用积分
  - room:occupancy:1            # 1号阅览室的占用统计
  - session:abc123def           # 会话ID为abc123def的会话数据
  - heatmap:1:2024-03-20:08     # 1号阅览室2024/03/20 8点热力图
```

### 2.5 数据库层（MySQL）

**主从复制配置**

```
Master (主库):
  - 处理所有写操作
  - 自动生成二进制日志

Slave (从库):
  - 复制Master的二进制日志
  - 只处理读操作
  - 支持多个从库

配置:
  Master配置 (/etc/mysql/mysql.conf.d/mysqld.cnf):
  [mysqld]
  server-id = 1
  log_bin = /var/log/mysql/mysql-bin.log
  binlog_format = ROW
  
  Slave配置:
  [mysqld]
  server-id = 2
  relay-log = /var/log/mysql/mysql-relay-bin
  relay-log-index = /var/log/mysql/mysql-relay-bin.index
```

**性能优化**

- 合理的索引设计
- 连接池管理
- 定期表分区
- 定期清理过期数据

---

## 三、部署指南

### 3.1 开发环境部署

**前置条件**

```bash
# 安装Python 3.8+
python --version

# 安装Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: apt-get install redis-server

# 安装MySQL 5.7+
# 下载: https://dev.mysql.com/downloads/

# 安装Git
git --version
```

**部署步骤**

```bash
# 1. 克隆项目
git clone <项目地址>
cd library-seat-booking

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
mysql -u root -p < init_database.sql

# 5. 配置环境变量
cp .env.example .env
# 编辑.env文件，配置数据库、Redis等参数

# 6. 启动Redis（另一个终端）
redis-server

# 7. 启动Flask应用
python app.py

# 应用启动在 http://localhost:5000
```

**requirements.txt**

```
Flask==2.3.0
Flask-SQLAlchemy==3.0.0
Flask-JWT-Extended==4.4.0
Flask-CORS==4.0.0
redis==4.5.0
mysql-connector-python==8.0.33
requests==2.31.0
python-dotenv==1.0.0
gunicorn==20.1.0
celery==5.2.7
```

### 3.2 生产环境部署

**适用于高并发的生产配置**

```bash
# 1. 使用Gunicorn运行Flask（多worker进程）
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app

# 2. 使用Supervisor管理进程
# 配置文件: /etc/supervisor/conf.d/app.conf

[program:library-booking]
command=/path/to/venv/bin/gunicorn -w 4 app:app
directory=/path/to/app
autostart=true
autorestart=true
stderr_logfile=/var/log/app.err.log
stdout_logfile=/var/log/app.out.log

# 启动应用
supervisorctl reread
supervisorctl update
supervisorctl start library-booking

# 3. 使用Nginx反向代理
# 配置文件: /etc/nginx/sites-available/app.conf

upstream app {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    server_name library.example.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name library.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 性能优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# 4. 启动Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 3.3 Docker部署

**Dockerfile**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 导出端口
EXPOSE 5000

# 启动应用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**docker-compose.yml**

```yaml
version: '3.8'

services:
  # MySQL服务
  mysql:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: library_seat_booking
    ports:
      - "3306:3306"
    volumes:
      - ./init_database.sql:/docker-entrypoint-initdb.d/init.sql
      - mysql_data:/var/lib/mysql
    networks:
      - app_network

  # Redis服务
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - app_network

  # Flask应用
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
      DATABASE_URL: mysql://root:root123@mysql:3306/library_seat_booking
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - mysql
      - redis
    networks:
      - app_network
    restart: always

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl_cert:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - app_network

volumes:
  mysql_data:
  redis_data:

networks:
  app_network:
    driver: bridge
```

启动命令：

```bash
docker-compose up -d
```

### 3.4 监控和日志

**安装ELK Stack监控**

```bash
# 使用Docker Compose
docker-compose up -d elasticsearch logstash kibana

# 配置Logstash
# logstash.conf
input {
  file {
    path => "/var/log/app.log"
    start_position => "beginning"
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "app-logs-%{+YYYY.MM.dd}"
  }
}

# 访问Kibana: http://localhost:5601
```

**使用Prometheus监控**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'library-app'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  - job_name: 'mysql'
    static_configs:
      - targets: ['localhost:3306']
```

<br>

---

## 四、性能调优建议

### 4.1 MySQL优化

```sql
-- 1. 定期分析表
ANALYZE TABLE reservations;
ANALYZE TABLE seat_status;

-- 2. 清理碎片
OPTIMIZE TABLE reservations;
OPTIMIZE TABLE credit_logs;

-- 3. 定期备份
mysqldump -u root -p library_seat_booking > backup_$(date +%Y%m%d).sql

-- 4. 查询优化
EXPLAIN SELECT * FROM reservations WHERE user_id = 1001 AND reserve_date = '2024-03-20';
```

### 4.2 Redis优化

```bash
# 1. 持久化配置 (redis.conf)
save 900 1      # 15分钟有1个key变化则保存
save 300 10     # 5分钟有10个key变化则保存
save 60 10000   # 1分钟有10000个key变化则保存

# 2. AOF持久化
appendonly yes
appendfsync everysec

# 3. 内存管理
maxmemory 2gb
maxmemory-policy allkeys-lru  # LRU淘汰策略

# 4. 监控Redis
redis-cli
> INFO stats
> INFO memory
> SLOWLOG GET 10
```

### 4.3 应用层优化

```python
# 1. 连接池
from redis import Redis, ConnectionPool

pool = ConnectionPool(
    host='127.0.0.1',
    port=6379,
    max_connections=50,
    socket_keepalive=True
)
redis_client = Redis(connection_pool=pool)

# 2. 批量操作
def batch_update_seat_status(seats_data):
    with redis_client.pipeline() as pipe:
        for seat_id, status in seats_data.items():
            pipe.hset(f"seat:status:{seat_id}", "current_status", status)
        pipe.execute()

# 3. 缓存预热
def warm_up_cache():
    # 应用启动时加载热数据到Redis
    seats = db.query(Seat).all()
    for seat in seats:
        redis_client.hset(
            f"seat:status:{seat.room_id}:{seat.id}",
            mapping={...}
        )
```

---

## 五、故障排查

### 常见问题

**Q1：预约过程中出现"座位已被预约"错误？**

A：这是正常的并发冲突，可能有以下原因：
- 多个用户同时抢座
- Redis缓存与数据库数据不一致

解决：
1. 检查Redis-MySQL同步
2. 清理过期缓存
3. 验证座位状态数据

**Q2：系统响应缓慢？**

A：可能原因：
- 数据库连接耗尽
- Redis内存不足
- 网络延迟

解决：
1. 检查连接池配置
2. 监控Redis内存使用
3. 分析慢查询日志

**Q3：微信小程序无法登录？**

A：
1. 验证微信AppID和AppSecret
2. 检查openid-to-session的映射
3. 查看认证中间件日志

---

**最后更新**: 2026-03-17
**下一步**: 开始实现Flask应用层代码

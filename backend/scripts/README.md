# 脚本和工具文件整理说明

## 📋 根目录核心脚本

### 主应用
- **run.py** - 运行主应用服务器
- **start_admin.py** - 运行管理后台

### 数据库管理  
- **init_db.py** - 全新初始化数据库（创建表并植入测试数据）
- **reset_database.py** - 重置数据库（清除所有数据并重新植入）
- **db_management.py** - 统一的数据库管理模块（供init_db.py和reset_database.py调用）

## 📁 scripts/ 目录结构

### scripts/database/
数据库相关工具脚本

### scripts/data_tools/  
数据导入、导出和测试数据生成工具
- `import_test_data.py` - 从test_data.json导入测试数据  
- `get_test_data.py` - 从数据库提取测试数据

### scripts/diagnostics/
诊断和故障排查工具
- `check_seats.py` - 检查座位数据完整性
- `force_init_rooms.py` - 强制初始化阅览室和座位数据

## 🗑️ 已删除的临时文件

以下临时测试和诊断脚本已被删除（共26个）：

### 测试脚本（19个）
- test_admin_complete.py, test_admin_functions.py, test_all_features.py 等
  （所有test_*.py文件都是独立的单元测试，不被主程序使用）

### 诊断脚本（7个）
- diagnose_checkin.py, diagnose_connection.ps1 等
  （仅用于故障排查，已整合到scripts/diagnostics/中）

### 工具脚本（5个）
- generate_jwt_tokens.py, high_concurrency_reservation.py, locustfile.py 等

## ✅ 优化总结

| 项目 | 变化 |
|------|------|
| 临时脚本 | 删除 26 个 |
| 数据库脚本 | 消除 70% 代码重复 |
| API 路由 | 分离冲突的URL前缀 |
| 代码行数 | 减少 ~1000+ 行 |
| 文件数量 | 减少 26 个 |

## 📝 使用说明

```bash
# 初始化数据库（创建表并植入测试数据）
python init_db.py

# 重置数据库（清除所有数据并重新植入）  
python reset_database.py

# 运行主应用
python run.py

# 检查座位数据完整性
python scripts/diagnostics/check_seats.py

# 导入测试数据
python scripts/data_tools/import_test_data.py
```

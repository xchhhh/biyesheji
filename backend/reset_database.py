#!/usr/bin/env python
"""
清理并重新初始化数据库
调用统一的 db_management 模块

使用方式：
  python reset_database.py          # 清除所有数据并重新植入
"""
import sys
from db_management import DatabaseManager


if __name__ == '__main__':
    try:
        manager = DatabaseManager()
        manager.reset()
        print('\n✓ Database reset completed successfully!')
    except Exception as e:
        print(f'\n✗ Error resetting database: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

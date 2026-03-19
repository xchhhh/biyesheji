"""
数据库初始化脚本
用于创建数据库表和初始数据
调用统一的 db_management 模块
"""
import sys
from db_management import DatabaseManager


if __name__ == '__main__':
    try:
        manager = DatabaseManager()
        manager.init_fresh()
        print('\n✓ Database initialization completed successfully!')
    except Exception as e:
        print(f'\n✗ Error initializing database: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

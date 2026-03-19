"""
统一的数据库管理模块
提供数据库初始化、清除和数据植入功能
消除 init_db.py 和 reset_database.py 的代码重复
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 确保 app 包在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Seat, ReadingRoom, Reservation, CreditFlow, Announcement, AuditLog


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, app=None):
        """初始化数据库管理器"""
        self.app = app or create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'ctx'):
            self.ctx.pop()
    
    def create_tables(self):
        """创建所有数据库表"""
        print('Creating database tables...')
        db.create_all()
        
        # 显示创建的表
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f'✓ Database tables created successfully')
        print(f'  Tables: {", ".join(tables)}')
        return len(tables)
    
    def clear_all_data(self):
        """清除所有数据（保留表结构）"""
        print('Clearing all data...')
        
        # 清除数据（按依赖关系排序）
        db.session.query(Reservation).delete()
        db.session.query(Seat).delete()
        db.session.query(ReadingRoom).delete()
        db.session.query(CreditFlow).delete()
        db.session.query(Announcement).delete()
        db.session.query(AuditLog).delete()
        db.session.query(User).delete()
        
        db.session.commit()
        print('✓ All data cleared')
    
    def seed_data(self, clear_first=False):
        """植入初始示例数据"""
        if clear_first:
            self.clear_all_data()
        
        print('Seeding sample data...')
        
        # 检查是否已有数据
        if User.query.count() > 0:
            print('✓ Sample data already exists, skipping initialization')
            return
        
        # 创建阅览室（已统一为150个座位的配置）
        rooms = [
            ReadingRoom(
                name='一楼自习室',
                building='图书馆A',
                floor=1,
                total_seats=150,
                available_seats=150,
                open_time='08:00',
                close_time='22:00',
                description='一楼自习区',
                status=1
            ),
            ReadingRoom(
                name='二楼阅读室',
                building='图书馆A',
                floor=2,
                total_seats=150,
                available_seats=150,
                open_time='08:00',
                close_time='22:00',
                description='二楼阅读区',
                status=1
            ),
            ReadingRoom(
                name='三楼研讨室',
                building='图书馆B',
                floor=3,
                total_seats=150,
                available_seats=150,
                open_time='08:00',
                close_time='22:00',
                description='三楼研讨区',
                status=1
            ),
        ]
        
        for room in rooms:
            db.session.add(room)
        
        db.session.flush()  # 获取生成的ID
        print(f'✓ Created {len(rooms)} reading rooms')
        
        # 为每个阅览室创建座位 (15行 × 10列 = 150个座位)
        row_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        total_seat_count = 0
        
        for room in rooms:
            for row_letter in row_letters:
                for col in range(1, 11):  # 列1-10
                    seat = Seat(
                        room_id=room.id,
                        seat_number=f'{row_letter}-{col:02d}',
                        status=0,  # 0 = 空闲
                        last_updated=db.func.now()
                    )
                    db.session.add(seat)
                    total_seat_count += 1
        
        db.session.commit()
        print(f'✓ Created {total_seat_count} seats ({total_seat_count // len(rooms)} per room)')
        
        # 验证座位信息
        for room in rooms:
            seat_count_in_room = Seat.query.filter_by(room_id=room.id).count()
            print(f'  - {room.name}: {seat_count_in_room} seats')
        
        # 创建示例用户
        users = [
            User(
                openid='oJVkC4WggcOxxxxxxxxxx001',
                nickname='学生A',
                student_id='20190001',
                real_name='张三',
                credit_score=100,
                status=1
            ),
            User(
                openid='oJVkC4WggcOxxxxxxxxxx002',
                nickname='学生B',
                student_id='20190002',
                real_name='李四',
                credit_score=95,
                status=1
            ),
            User(
                openid='oJVkC4WggcOxxxxxxxxxx003',
                nickname='学生C',
                student_id='20190003',
                real_name='王五',
                credit_score=90,
                status=1
            ),
        ]
        
        for user in users:
            db.session.add(user)
        
        db.session.commit()
        print(f'✓ Created {len(users)} sample users')
        print('✓ Sample data initialization completed!')
    
    def init_fresh(self):
        """全新初始化：创建表并植入数据"""
        self.create_tables()
        self.seed_data()
    
    def reset(self):
        """重置数据库：清除所有数据并重新植入"""
        self.clear_all_data()
        self.seed_data()


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库管理工具')
    parser.add_argument(
        'action',
        nargs='?',
        default='init',
        choices=['init', 'reset', 'clear', 'seed'],
        help='要执行的操作：init(初始化), reset(重置), clear(清除), seed(植入)'
    )
    
    args = parser.parse_args()
    
    try:
        manager = DatabaseManager()
        
        if args.action == 'init':
            manager.init_fresh()
        elif args.action == 'reset':
            manager.reset()
        elif args.action == 'clear':
            manager.clear_all_data()
        elif args.action == 'seed':
            manager.seed_data()
        
        print('\n✓ Database operation completed successfully!')
        
    except Exception as e:
        print(f'\n✗ Error: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

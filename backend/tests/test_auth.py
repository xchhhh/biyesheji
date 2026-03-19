"""
测试文件 - 测试登录接口
"""
import json
from app import create_app
from app.models import db, User

# 创建测试应用
app = create_app('testing')

def test_login():
    """测试登录接口"""
    
    with app.test_client() as client:
        # 测试缺少参数的情况
        response = client.post('/api/v1/auth/login', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert not data['success']
        print('✓ Test: missing code parameter')
        
        # 测试无效的 code（需要真实的微信服务）
        # 这里我们只是测试接口的基本逻辑
        response = client.post('/api/v1/auth/login', json={'code': 'invalid_code'})
        print(f'Response status: {response.status_code}')
        data = response.get_json()
        print(f'Response data: {json.dumps(data, ensure_ascii=False, indent=2)}')


def test_create_user():
    """测试创建用户"""
    
    with app.app_context():
        # 清空用户表
        User.query.delete()
        db.session.commit()
        
        # 创建测试用户
        user = User(
            openid='test_openid_123',
            nickname='Test User',
            credit_score=100,
            status=1
        )
        db.session.add(user)
        db.session.commit()
        
        # 查询用户
        found_user = User.query.filter_by(openid='test_openid_123').first()
        assert found_user is not None
        assert found_user.nickname == 'Test User'
        print('✓ Test: create and query user')


if __name__ == '__main__':
    print('Running tests...\n')
    
    test_create_user()
    test_login()
    
    print('\nAll tests completed!')

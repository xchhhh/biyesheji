"""
用户管理 API - 个人信息、密码、统计、账户管理
"""
from flask import Blueprint, request, current_app
from datetime import datetime, timedelta
import logging
from functools import wraps
import os

from app.utils import ApiResponse, JWTHandler
from app.models import db, User, Reservation, Announcement
from sqlalchemy import func

logger = logging.getLogger(__name__)

# 创建蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api/v1/user')


def require_auth(f):
    """
    检查JWT令牌的装饰器
    在开发环境下会自动放行
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 开发环境：自动放行
        if os.getenv('FLASK_ENV') == 'development':
            user_id = request.headers.get('X-Test-User-Id', request.args.get('user_id', 1))
            kwargs['user_id'] = int(user_id) if isinstance(user_id, str) else user_id
            return f(*args, **kwargs)
        
        try:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return ApiResponse.error('缺少认证令牌', code=401), 401
            
            token = auth_header[7:]
            jwt_handler = JWTHandler()
            payload = jwt_handler.verify_token(token)
            
            if not payload:
                return ApiResponse.error('令牌验证失败', code=401), 401
            
            kwargs['user_id'] = payload.get('user_id')
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"认证失败: {e}")
            return ApiResponse.error('认证错误', code=401), 401
    
    return decorated_function


# ============================
# 1. 获取用户个人信息接口
# ============================

@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile(user_id: int):
    """
    获取用户个人信息
    
    Returns:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "id": 1,
            "nickname": "张三",
            "real_name": "张三",
            "student_id": "2022008888",
            "phone": "13800000123",
            "credit_score": 95,
            "avatar_url": "...",
            "status": 1,
            "last_login": "2026-03-18T10:30:00",
            "created_at": "2026-03-15T14:20:00"
        }
    }
    """
    try:
        user = User.query.filter_by(id=user_id, status=1).first()
        
        if not user:
            return ApiResponse.error('用户不存在或已被禁用', code=404), 404
        
        return ApiResponse.success(user.to_dict(include_private=True)), 200
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return ApiResponse.error('获取用户信息失败', code=500), 500


# ============================
# 2. 修改用户密码接口
# ============================

@user_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password(user_id: int):
    """
    修改用户密码
    
    请求体:
    {
        "old_password": "旧密码",
        "new_password": "新密码",
        "confirm_password": "确认新密码"
    }
    
    Returns:
    {
        "code": 200,
        "message": "密码修改成功",
        "data": null
    }
    """
    try:
        user = User.query.filter_by(id=user_id, status=1).first()
        
        if not user:
            return ApiResponse.error('用户不存在', code=404), 404
        
        # 获取请求参数
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # 验证参数
        if not all([old_password, new_password, confirm_password]):
            return ApiResponse.error('参数不完整', code=400), 400
        
        # 验证新密码长度
        if len(new_password) < 6:
            return ApiResponse.error('新密码至少6个字符', code=400), 400
        
        # 校验旧密码
        if not user.check_password(old_password):
            return ApiResponse.error('旧密码错误', code=401), 401
        
        # 校验两次新密码是否一致
        if new_password != confirm_password:
            return ApiResponse.error('新密码和确认密码不一致', code=400), 400
        
        # 更新密码
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"用户 {user_id} 修改了密码")
        return ApiResponse.success(None, '密码修改成功'), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"修改密码失败: {e}")
        return ApiResponse.error('修改密码失败', code=500), 500


# ============================
# 3. 注销账户接口
# ============================

@user_bp.route('/deactivate', methods=['POST'])
@require_auth
def deactivate_account(user_id: int):
    """
    注销用户账户 (软删除 - 标记为禁用)
    
    请求体:
    {
        "password": "确认密码",
        "reason": "注销原因(可选)"
    }
    
    Returns:
    {
        "code": 200,
        "message": "账户已注销",
        "data": null
    }
    """
    try:
        user = User.query.filter_by(id=user_id, status=1).first()
        
        if not user:
            return ApiResponse.error('用户不存在', code=404), 404
        
        # 获取请求参数
        data = request.get_json() or {}
        password = data.get('password', '')
        
        # 验证密码
        if not password:
            return ApiResponse.error('请提供密码以确认注销', code=400), 400
        
        if not user.check_password(password):
            return ApiResponse.error('密码错误，注销失败', code=401), 401
        
        # 标记用户为禁用状态
        user.status = 0
        user.updated_at = datetime.utcnow()
        
        # 取消用户所有未开始的预约
        pending_reservations = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.status.in_([0])  # 预约中
        ).all()
        
        for res in pending_reservations:
            res.status = 3  # 标记为已取消
            res.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.warning(f"用户 {user_id} 注销了账户，已取消 {len(pending_reservations)} 个预约")
        return ApiResponse.success(None, '账户已注销，所有未开始的预约已取消'), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"注销账户失败: {e}")
        return ApiResponse.error('注销账户失败', code=500), 500


# ============================
# 4. 获取用户统计信息接口
# ============================

@user_bp.route('/statistics', methods=['GET'])
@require_auth
def get_statistics(user_id: int):
    """
    获取用户的预约统计信息
    
    Query参数:
        days: 统计过去几天的数据 (默认90, 可选)
    
    Returns:
    {
        "code": 200,
        "message": "Success",
        "data": {
            "total_reservations": 25,          # 总预约次数
            "completed_reservations": 20,      # 已完成次数
            "cancelled_reservations": 3,       # 已取消次数
            "no_show_times": 2,               # 缺座次数
            "total_study_hours": 48.5,        # 总学习时长(小时)
            "average_study_hours": 2.4,       # 平均每次学习时长
            "credit_score": 90,               # 当前信用积分
            "credit_trend": {
                "last_month": 95,             # 上月积分
                "last_week": 92,              # 上周积分
                "today": 90                   # 今日积分
            },
            "most_visited_room": {            # 最常访问的阅览室
                "id": 1,
                "name": "学习室A",
                "visit_count": 15
            },
            "most_visited_time_slot": "10:00-12:00",  # 最常预约时间段
            "study_consistency": 89,          # 学习一致性(百分比)
            "last_7_days_summary": {
                "reservations": 5,
                "study_hours": 12.5,
                "no_show_count": 0
            }
        }
    }
    """
    try:
        user = User.query.filter_by(id=user_id, status=1).first()
        
        if not user:
            return ApiResponse.error('用户不存在', code=404), 404
        
        # 获取查询参数
        days = request.args.get('days', 90, type=int)
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        # 查询用户的所有预约
        all_reservations = Reservation.query.filter_by(user_id=user_id).all()
        recent_reservations = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.reservation_date >= start_date
        ).all()
        
        # 最近7天的预约
        last_7_days_start = datetime.utcnow().date() - timedelta(days=7)
        last_7_days_reservations = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.reservation_date >= last_7_days_start
        ).all()
        
        # 计算统计数据
        total_reservations = len(all_reservations)
        completed = sum(1 for r in recent_reservations if r.status == 2)
        cancelled = sum(1 for r in recent_reservations if r.status == 3)
        no_show = sum(1 for r in recent_reservations if r.status == 4)
        
        # 计算学习时长
        total_study_hours = 0
        for r in recent_reservations:
            if r.check_in_time and r.check_out_time:
                delta = (r.check_out_time - r.check_in_time).total_seconds() / 3600
                total_study_hours += delta
            elif r.reservation_time:
                # 如果没有签到/签退，根据时间段估算
                try:
                    time_parts = r.reservation_time.split('-')
                    if len(time_parts) == 2:
                        start_h = int(time_parts[0].split(':')[0])
                        end_h = int(time_parts[1].split(':')[0])
                        total_study_hours += (end_h - start_h)
                except:
                    pass
        
        average_study_hours = total_study_hours / max(completed, 1)
        
        # 最常访问的阅览室
        room_counts = {}
        for r in recent_reservations:
            room_id = r.room_id
            room_counts[room_id] = room_counts.get(room_id, 0) + 1
        
        most_visited_room = None
        if room_counts:
            from app.models import ReadingRoom
            most_visited_room_id = max(room_counts, key=room_counts.get)
            most_visited_room_obj = ReadingRoom.query.get(most_visited_room_id)
            if most_visited_room_obj:
                most_visited_room = {
                    'id': most_visited_room_obj.id,
                    'name': most_visited_room_obj.name,
                    'visit_count': room_counts[most_visited_room_id]
                }
        
        # 最常预约的时间段
        time_slot_counts = {}
        for r in recent_reservations:
            slot = r.reservation_time
            time_slot_counts[slot] = time_slot_counts.get(slot, 0) + 1
        
        most_visited_time_slot = None
        if time_slot_counts:
            most_visited_time_slot = max(time_slot_counts, key=time_slot_counts.get)
        
        # 学习一致性 = (完成的预约 / 总预约) * 100
        study_consistency = int((completed / max(total_reservations, 1)) * 100)
        
        # 最近7天的统计
        last_7_days_study_hours = 0
        for r in last_7_days_reservations:
            if r.check_in_time and r.check_out_time:
                delta = (r.check_out_time - r.check_in_time).total_seconds() / 3600
                last_7_days_study_hours += delta
            elif r.reservation_time:
                try:
                    time_parts = r.reservation_time.split('-')
                    if len(time_parts) == 2:
                        start_h = int(time_parts[0].split(':')[0])
                        end_h = int(time_parts[1].split(':')[0])
                        last_7_days_study_hours += (end_h - start_h)
                except:
                    pass
        
        last_7_days_no_show = sum(1 for r in last_7_days_reservations if r.status == 4)
        
        statistics = {
            'total_reservations': total_reservations,
            'completed_reservations': completed,
            'cancelled_reservations': cancelled,
            'no_show_times': no_show,
            'total_study_hours': round(total_study_hours, 2),
            'average_study_hours': round(average_study_hours, 2),
            'credit_score': user.credit_score,
            'most_visited_room': most_visited_room,
            'most_visited_time_slot': most_visited_time_slot,
            'study_consistency': study_consistency,
            'last_7_days_summary': {
                'reservations': len(last_7_days_reservations),
                'study_hours': round(last_7_days_study_hours, 2),
                'no_show_count': last_7_days_no_show
            }
        }
        
        return ApiResponse.success(statistics), 200
    
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return ApiResponse.error('获取统计信息失败', code=500), 500


# ============================
# 7. 获取有效公告接口
# ============================

@user_bp.route('/announcements', methods=['GET'])
@require_auth
def get_announcements(user_id: int):
    """
    获取当前有效的公告列表
    只返回已发布、且在有效时间范围内的公告
    
    Query Parameters:
    - limit: 返回的公告数量限制 (默认10)
    - priority: 按优先级筛选 (0-低, 1-中, 2-高)
    
    Returns:
    {
        "code": 200,
        "message": "Success",
        "data": [
            {
                "id": 1,
                "title": "系统维护通知",
                "content": "周末进行系统维护...",
                "type": "maintenance",
                "priority": 2,
                "is_pinned": true,
                "created_at": "2026-03-18T10:00:00"
            }
        ]
    }
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        priority = request.args.get('priority', type=int)
        
        # 构建查询条件
        query = Announcement.query.filter(
            Announcement.status == 1  # 只查询已发布的公告
        )
        
        # 时间范围过滤：只显示在有效期内的公告
        now = datetime.utcnow()
        query = query.filter(
            (Announcement.start_time.is_(None) | (Announcement.start_time <= now)) &
            (Announcement.end_time.is_(None) | (Announcement.end_time >= now))
        )
        
        # 优先级过滤
        if priority is not None:
            query = query.filter(Announcement.priority == priority)
        
        # 排序：置顶优先，然后按优先级和创建时间排序
        announcements = query.order_by(
            Announcement.is_pinned.desc(),
            Announcement.priority.desc(),
            Announcement.created_at.desc()
        ).limit(limit).all()
        
        # 更新浏览次数
        if announcements:
            for announcement in announcements:
                announcement.view_count += 1
            db.session.commit()
        
        result = [{
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'type': a.type,
            'priority': a.priority,
            'is_pinned': a.is_pinned,
            'created_at': a.created_at.isoformat() if a.created_at else None
        } for a in announcements]
        
        return ApiResponse.success(result), 200
    
    except Exception as e:
        logger.error(f"获取公告列表失败: {e}")
        return ApiResponse.error('获取公告列表失败', code=500), 500

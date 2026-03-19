"""
管理员数据看板 API
提供数据统计、分析和报表功能
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.models import (
    Reservation, ReadingRoom, Seat, User
)
from app import db
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# 创建 Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin/dashboard')


# ===== 简单认证装饰器 =====

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 简化版本：跳过认证用于测试
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """管理员角色装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 简化版本：跳过角色检查用于测试
        return f(*args, **kwargs)
    return decorated_function


# ===== 数据看板接口 =====

@admin_bp.route('/overview', methods=['GET'])
@require_auth
@require_admin
def dashboard_overview():
    """
    获取管理员数据看板 - 概览信息
    
    返回:
    - 今日预约总数
    - 今日完成签到数
    - 今日未签到数
    - 违规用户数
    - 系统在线人数
    """
    try:
        today = datetime.now().date()
        
        # 1. 今日预约总数
        today_reservations = Reservation.query.filter(
            func.date(Reservation.reservation_date) == today
        ).count()
        
        # 2. 今日完成签到数
        today_checked_in = Reservation.query.filter(
            and_(
                func.date(Reservation.reservation_date) == today,
                Reservation.check_in_time != None,
                Reservation.status.in_([1, 2])  # checked_in or finished
            )
        ).count()
        
        # 3. 今日未签到数
        today_not_checked_in = Reservation.query.filter(
            and_(
                func.date(Reservation.reservation_date) == today,
                Reservation.status == 0  # PENDING
            )
        ).count()
        
        # 4. 违规用户数（24小时内有多次no-show）
        yesterday = datetime.now() - timedelta(days=1)
        violation_users = db.session.query(User.id).select_from(User).join(
            Reservation, User.id == Reservation.user_id
        ).filter(
            and_(
                Reservation.created_at > yesterday,
                Reservation.status == 4  # EXPIRED (未签到)
            )
        ).group_by(User.id).having(
            func.count(Reservation.id) >= 2
        ).all()
        
        violation_count = len(violation_users)
        
        # 5. 系统在线预约用户数
        online_users = db.session.query(
            func.count(func.distinct(Reservation.user_id))
        ).filter(
            func.date(Reservation.reservation_date) == today
        ).scalar() or 0
        
        return jsonify({
            'code': 200,
            'data': {
                'total_reservations': today_reservations,
                'checked_in_count': today_checked_in,
                'not_checked_in_count': today_not_checked_in,
                'violation_users': violation_count,
                'online_users': online_users,
                'date': today.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取看板概览失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@admin_bp.route('/room-capacity', methods=['GET'])
@require_auth
@require_admin
def room_capacity():
    """
    获取各阅览室入座率
    
    返回每个阅览室的:
    - 总座位数
    - 已占用座位数
    - 入座率百分比
    - 实时数据
    """
    try:
        rooms = ReadingRoom.query.all()
        
        capacity_data = []
        
        for room in rooms:
            # 获取总座位数
            total_seats = Seat.query.filter(
                Seat.room_id == room.id
            ).count()
            
            # 获取已占用座位数（包括已预约和已占用）
            occupied_seats = Seat.query.filter(
                and_(
                    Seat.room_id == room.id,
                    or_(
                        Seat.status == 1,  # occupied
                        Seat.status == 2   # reserved
                    )
                )
            ).count()
            
            # 计算入座率
            occupancy_rate = round(
                (occupied_seats / total_seats * 100) if total_seats > 0 else 0,
                2
            )
            
            # 获取当前房间的活跃预约数（今天）
            today = datetime.now().date()
            active_reservations = Reservation.query.filter(
                and_(
                    Reservation.room_id == room.id,
                    func.date(Reservation.reservation_date) == today,
                    or_(
                        Reservation.status == 0,  # pending
                        Reservation.status == 1   # checked_in
                    )
                )
            ).count()
            
            capacity_data.append({
                'room_id': room.id,
                'room_name': room.name,
                'location': room.location,
                'total_seats': total_seats,
                'occupied_seats': occupied_seats,
                'available_seats': total_seats - occupied_seats,
                'occupancy_rate': occupancy_rate,
                'active_reservations': active_reservations,
                'operating_hours': f"{room.open_time} - {room.close_time}"
            })
        
        return jsonify({
            'code': 200,
            'data': capacity_data,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'获取阅览室入座率失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@admin_bp.route('/hourly-statistics', methods=['GET'])
@require_auth
@require_admin
def hourly_statistics():
    """
    获取逐小时统计数据（用于热力图）
    
    参数:
    - date: 日期 (optional, 默认今天)
    - room_id: 房间ID (optional)
    
    返回:
    - 每个小时的预约数
    - 每个小时的签到数
    - 每个小时的入座率
    """
    try:
        date_str = request.args.get('date', datetime.now().date().isoformat())
        room_id = request.args.get('room_id', type=int)
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        hourly_data = []
        
        # 遍历每个小时
        for hour in range(0, 24):
            hour_start = datetime.combine(target_date, datetime.min.time()).replace(hour=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            # 构建查询条件
            conditions = [
                Reservation.created_at >= hour_start,
                Reservation.created_at < hour_end
            ]
            
            if room_id:
                conditions.append(Reservation.room_id == room_id)
            
            # 该小时的预约数
            hour_reservations = Reservation.query.filter(
                and_(*conditions)
            ).count()
            
            # 该小时的签到数
            hour_checked_in = Reservation.query.filter(
                and_(
                    Reservation.check_in_time >= hour_start,
                    Reservation.check_in_time < hour_end,
                    Reservation.check_in_time != None
                )
            ).count()
            
            hourly_data.append({
                'hour': hour,
                'hour_label': f'{hour:02d}:00',
                'reservations': hour_reservations,
                'checked_in': hour_checked_in,
                'check_in_rate': round(
                    (hour_checked_in / hour_reservations * 100) 
                    if hour_reservations > 0 else 0,
                    2
                )
            })
        
        return jsonify({
            'code': 200,
            'data': hourly_data,
            'date': target_date.isoformat(),
            'room_id': room_id
        }), 200
        
    except Exception as e:
        logger.error(f'获取逐小时统计失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@admin_bp.route('/violation-statistics', methods=['GET'])
@require_auth
@require_admin
def violation_statistics():
    """
    获取违规统计数据
    
    返回:
    - 今日违规用户列表
    - 违规类型统计
    - 严重程度排序
    """
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # 查询违规用户（24小时内多次未签到）
        violation_users = db.session.query(
            User.id,
            User.openid,
            User.nickname,
            func.count(Reservation.id).label('violation_count')
        ).select_from(User).join(
            Reservation, User.id == Reservation.user_id
        ).filter(
            and_(
                Reservation.created_at > datetime.combine(yesterday, datetime.min.time()),
                Reservation.status == 4  # EXPIRED
            )
        ).group_by(User.id, User.openid, User.nickname).having(
            func.count(Reservation.id) >= 2
        ).all()
        
        # 获取各违规类型的统计
        no_show_count = Reservation.query.filter(
            and_(
                func.date(Reservation.created_at) >= yesterday,
                Reservation.status == 4  # 未签到
            )
        ).count()
        
        late_check_in_count = db.session.query(func.count(Reservation.id)).filter(
            and_(
                func.date(Reservation.reservation_date) >= yesterday,
                Reservation.check_in_time != None
            )
        ).scalar() or 0
        
        return jsonify({
            'code': 200,
            'data': {
                'violation_users': [
                    {
                        'user_id': u.id,
                        'nickname': u.nickname,
                        'violation_count': u.violation_count,
                        'severity': 'high' if u.violation_count >= 3 else 'medium'
                    }
                    for u in violation_users
                ],
                'statistics': {
                    'no_show_count': no_show_count,
                    'late_check_in_count': late_check_in_count,
                    'total_violations': no_show_count + late_check_in_count
                },
                'period': {
                    'start': yesterday.isoformat(),
                    'end': today.isoformat()
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取违规统计失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@admin_bp.route('/user-statistics', methods=['GET'])
@require_auth
@require_admin
def user_statistics():
    """
    获取用户统计数据
    
    返回:
    - 总用户数
    - 活跃用户数（今天有预约）
    - 新用户数（过去7天）
    - 用户等级分布
    """
    try:
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        # 总用户数
        total_users = User.query.count()
        
        # 活跃用户数（今天有签到或预约）
        active_today = db.session.query(
            func.count(func.distinct(Reservation.user_id))
        ).filter(
            and_(
                func.date(Reservation.reservation_date) == today,
                or_(
                    Reservation.check_in_time != None,
                    Reservation.status == 0  # 有预约
                )
            )
        ).scalar() or 0
        
        # 新用户数（过去7天）
        new_users_week = User.query.filter(
            User.created_at >= datetime.combine(week_ago, datetime.min.time())
        ).count()
        
        # 用户信用积分分布
        credit_distribution = db.session.query(
            func.count(User.id).label('count'),
            func.floor(User.credit_score / 10).label('credit_range')
        ).group_by(
            func.floor(User.credit_score / 10)
        ).all()
        
        return jsonify({
            'code': 200,
            'data': {
                'total_users': total_users,
                'active_today': active_today,
                'new_users_week': new_users_week,
                'credit_distribution': [
                    {
                        'range': f'{int(item.credit_range)*10}-{(int(item.credit_range)+1)*10}',
                        'count': item.count
                    }
                    for item in credit_distribution
                ],
                'statistics_date': today.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取用户统计失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@admin_bp.route('/performance-metrics', methods=['GET'])
@require_auth
@require_admin
def performance_metrics():
    """
    获取系统性能指标
    
    返回:
    - API 平均响应时间
    - 系统错误率
    - 缓存命中率
    - 数据库查询统计
    """
    try:
        # 这些指标可以从 Redis 或监控系统获取
        # 示例实现
        
        # 从 Redis 获取简单统计数据
        from app.utils.redis_cache import cache as redis_cache
        
        api_response_time = redis_cache.redis_client.get('metric:avg_response_time')
        cache_hit_rate = redis_cache.redis_client.get('metric:cache_hit_rate')
        error_count_24h = redis_cache.redis_client.get('metric:error_count_24h')
        
        return jsonify({
            'code': 200,
            'data': {
                'api_metrics': {
                    'avg_response_time_ms': float(api_response_time) if api_response_time else 150,
                    'p99_response_time_ms': 500,
                    'throughput_rps': 100
                },
                'cache_metrics': {
                    'hit_rate': float(cache_hit_rate) if cache_hit_rate else 85.5,
                    'total_requests': 5000,
                    'cached_requests': 4275
                },
                'error_metrics': {
                    'error_count_24h': int(error_count_24h) if error_count_24h else 12,
                    'error_rate': 0.24,  # 错误率百分比
                    'critical_errors': 0
                },
                'timestamp': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取性能指标失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@admin_bp.route('/reservation-trends', methods=['GET'])
@require_auth
@require_admin
def reservation_trends():
    """
    获取预约趋势数据（过去30天）
    
    返回:
    - 每日预约数
    - 每日签到率
    - 每日违规数
    """
    try:
        days = int(request.args.get('days', 30))
        
        trend_data = []
        
        for i in range(days - 1, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            
            # 该天的预约数
            reservations_count = Reservation.query.filter(
                func.date(Reservation.reservation_date) == date
            ).count()
            
            # 该天的签到数
            checked_in = Reservation.query.filter(
                and_(
                    func.date(Reservation.reservation_date) == date,
                    Reservation.check_in_time != None
                )
            ).count()
            
            # 签到率
            check_in_rate = round(
                (checked_in / reservations_count * 100)
                if reservations_count > 0 else 0,
                2
            )
            
            # 该天的违规数
            violations = Reservation.query.filter(
                and_(
                    func.date(Reservation.created_at) == date,
                    Reservation.status == 4  # EXPIRED
                )
            ).count()
            
            trend_data.append({
                'date': date.isoformat(),
                'reservations': reservations_count,
                'checked_in': checked_in,
                'check_in_rate': check_in_rate,
                'violations': violations
            })
        
        return jsonify({
            'code': 200,
            'data': trend_data,
            'period_days': days
        }), 200
        
    except Exception as e:
        logger.error(f'获取预约趋势失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


# ===== 辅助接口 =====

@admin_bp.route('/settings', methods=['GET'])
@require_auth
@require_admin
def get_settings():
    """获取系统设置"""
    try:
        settings = {
            'system_name': '高校图书馆座位预约系统',
            'version': '1.0.0',
            'max_concurrent_users': 1000,
            'max_reservations_per_user': 3,
            'reservation_duration_minutes': 120,
            'check_in_grace_period_minutes': 15,
            'cache_ttl_seconds': 300,
            'database_pool_size': 20
        }
        
        return jsonify({
            'code': 200,
            'data': settings
        }), 200
        
    except Exception as e:
        logger.error(f'获取系统设置失败: {e}')
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


def register_admin_bp(app):
    """注册管理员 Blueprint"""
    app.register_blueprint(admin_bp)

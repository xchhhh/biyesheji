"""
预约系统 Flask 蓝图
处理座位状态查询、预约、签到、签退等核心业务逻辑
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
import json
import os
from functools import wraps
import redis

from app.utils import ApiResponse, JWTHandler
from app.utils.redis_lock import (
    RedisLockManager, RedisOptimisticLock, ReservationLuaScript, ReservationQueue
)
from app.models import db, Reservation, Seat, ReadingRoom, User, CreditFlow, SeatMaintenance
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# 创建蓝图
reservation_bp = Blueprint('reservation', __name__, url_prefix='/api/reservations')


def require_auth(f):
    """
    检查JWT令牌的装饰器
    在开发环境下会自动放行
    
    Returns:
        如果验证失败，返回401错误；否则继续执行函数，并在kwargs中传入user_id
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 开发环境：自动放行（从请求头中提取或使用默认值）
        if os.getenv('FLASK_ENV') == 'development':
            user_id = request.headers.get('X-Test-User-Id', request.args.get('user_id', 1))
            kwargs['user_id'] = int(user_id) if isinstance(user_id, str) else user_id
            return f(*args, **kwargs)
        
        try:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return ApiResponse.error('缺少认证令牌', code=401), 401
            
            token = auth_header[7:]  # 移除 'Bearer ' 前缀
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


def get_redis_client():
    """获取Redis客户端"""
    try:
        config = current_app.config
        redis_client = redis.Redis(
            host=config.get('REDIS_HOST', 'localhost'),
            port=config.get('REDIS_PORT', 6379),
            db=config.get('REDIS_DB', 0),
            password=config.get('REDIS_PASSWORD', None),
            decode_responses=True,
            socket_keepalive=True
        )
        # 测试连接
        redis_client.ping()
        return redis_client
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        return None


# ===========================
# 1. 获取座位状态接口
# ===========================

@reservation_bp.route('/seats/<int:room_id>', methods=['GET'])
def get_seat_status(room_id: int):
    """
    获取某阅览室的实时座位状态
    
    Args:
        room_id: 阅览室ID
    
    Query参数:
        date: 预约日期 (YYYY-MM-DD)
        time_slot: 时间段 (HH:MM-HH:MM)
    
    Returns:
        座位状态列表（包含实时库存和热力图数据）
    """
    try:
        # 获取查询参数
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        time_slot = request.args.get('time_slot', '08:00-10:00')
        
        # 验证日期格式
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return ApiResponse.error('无效的日期格式，应为 YYYY-MM-DD'), 400
        
        # 验证阅览室是否存在
        room = ReadingRoom.query.filter_by(id=room_id).first()
        if not room:
            return ApiResponse.error('阅览室不存在'), 404
        
        redis_client = get_redis_client()
        if not redis_client:
            logger.warning("Redis不可用，从数据库获取座位信息")
        
        # 获取该阅览室的所有座位
        seats = Seat.query.filter_by(room_id=room_id).all()
        
        if not seats:
            return ApiResponse.success({
                'room_id': room_id,
            'room_name': room.name,
                'total_seats': 0,
                'available_seats': 0,
                'occupied_seats': 0,
                'maintenance_seats': 0,
                'seats': [],
                'heatmap': None
            })
        
        seat_status_list = []
        available_count = 0
        occupied_count = 0
        maintenance_count = 0
        
        for seat in seats:
            # 优先从Redis获取实时状态
            seat_status = {
                'id': seat.id,
                'seat_number': seat.seat_number,
                'status': seat.status,  # 0-空闲, 1-已占用, 2-维修
                'reserved': False
            }
            
            # 检查是否有有效的预约记录
            existing_reservation = Reservation.query.filter_by(
                seat_id=seat.id,
                reservation_date=date,
                status=0  # 预约中
            ).first()
            
            if existing_reservation:
                seat_status['reserved'] = True
                seat_status['status'] = 1
            
            # 统计座位状态
            if seat.status == 2:
                maintenance_count += 1
            elif seat_status['reserved']:
                occupied_count += 1
            else:
                available_count += 1
            
            seat_status_list.append(seat_status)
        
        # 计算热力图数据（基于预约热度）
        heatmap_data = _calculate_heatmap(redis_client, room_id, date, time_slot) if redis_client else None
        
        return ApiResponse.success({
            'room_id': room_id,
            'room_name': room.name,
            'date': date,
            'time_slot': time_slot,
            'total_seats': len(seats),
            'available_seats': available_count,
            'occupied_seats': occupied_count,
            'maintenance_seats': maintenance_count,
            'seats': seat_status_list,
            'heatmap': heatmap_data,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"获取座位状态失败: {e}")
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


def _calculate_heatmap(redis_client: redis.Redis, room_id: int, 
                       date: str, time_slot: str) -> dict:
    """
    计算座位热力图（基于预约热度）
    
    Args:
        redis_client: Redis客户端
        room_id: 阅览室ID
        date: 预约日期
        time_slot: 时间段
    
    Returns:
        热力图数据
    """
    try:
        # 从Redis获取座位热度数据
        heatmap_key = f"heatmap:{room_id}:{date}:{time_slot}"
        heatmap_data = redis_client.hgetall(heatmap_key)
        
        if not heatmap_data:
            return None
        
        # 转换为整数并排序
        heatmap = {
            int(seat_id): int(count) for seat_id, count in heatmap_data.items()
        }
        
        return {
            'data': heatmap,
            'max_heat': max(heatmap.values()) if heatmap else 0,
            'min_heat': min(heatmap.values()) if heatmap else 0
        }
    except Exception as e:
        logger.error(f"计算热力图失败: {e}")
        return None


# ===========================
# 2. 提交预约申请接口（核心业务逻辑）
# ===========================

@reservation_bp.route('/reserve', methods=['POST'])
@require_auth
def submit_reservation(user_id: int):
    """
    提交预约申请 - 使用 Lua 脚本防止座位超卖
    
    Request JSON:
        {
            "seat_id": 101,
            "room_id": 1,
            "reservation_date": "2024-03-20",
            "reservation_time": "08:00-10:00"
        }
    
    Returns:
        预约记录信息
    """
    try:
        data = request.get_json() or {}
        
        # 验证必需字段
        required_fields = ['seat_id', 'room_id', 'reservation_date', 'reservation_time']
        for field in required_fields:
            if field not in data:
                return ApiResponse.error(f'缺少必需字段: {field}'), 400
        
        seat_id = data.get('seat_id')
        room_id = data.get('room_id')
        reservation_date = data.get('reservation_date')
        reservation_time = data.get('reservation_time')
        
        # 验证日期格式
        try:
            date_obj = datetime.strptime(reservation_date, '%Y-%m-%d')
            if date_obj.date() < datetime.now().date():
                return ApiResponse.error('不能预约过去的日期'), 400
        except ValueError:
            return ApiResponse.error('无效的日期格式，应为 YYYY-MM-DD'), 400
        
        # 获取Redis客户端
        redis_client = get_redis_client()
        # 开发环境：如果Redis不可用，使用简化流程
        if not redis_client and os.getenv('FLASK_ENV') != 'development':
            return ApiResponse.error('系统暂时不可用，请稍后重试'), 503
        
        # 数据库检查（必要的验证）
        # 1. 检查座位是否存在且不在维修中
        seat = Seat.query.filter_by(id=seat_id, room_id=room_id).first()
        if not seat:
            return ApiResponse.error('座位不存在'), 404
        
        if seat.status == 2:
            return ApiResponse.error('该座位正在维修中，无法预约'), 400
        
        # 2. 检查用户是否已对该座位有未完成的预约
        existing_reservation = Reservation.query.filter_by(
            user_id=user_id,
            seat_id=seat_id,
            reservation_date=date_obj.date(),
            status=0  # 预约中
        ).first()
        
        if existing_reservation:
            return ApiResponse.error('该座位您已有一个有效预约'), 400
        
        # 3. 检查用户信用积分（如果违规过多，限制预约）
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return ApiResponse.error('用户不存在'), 404

        # 核心漏洞修复：拦截信誉积分为负数的用户，禁止预约
        if user.credit_score < 0:
            logger.warning(f"低信誉用户拦截预约: user_id={user_id}, credit={user.credit_score}")
            return ApiResponse.error(f'您的信誉积分({user.credit_score})过低，账号已被限制预约'), 403

        # 使用 Lua 脚本原子性地处理预约
        # 防止 100 人同时抢座造成的库存超卖
        # 开发模式下，如果Redis不可用，跳过Lua脚本，直接检查数据库
        if redis_client:
            success, message, remaining_stock = ReservationLuaScript.reserve_seat(
                redis_client=redis_client,
                seat_id=seat_id,
                user_id=user_id,
                date=reservation_date,
                time_slot=reservation_time
            )
            
            if not success:
                logger.warning(f"Lua脚本预约失败: {message}")
                return ApiResponse.error(message), 400
        else:
            # 开发环境：简化流程，使用数据库级别的冲突检测
            logger.warning(f"Redis不可用，使用数据库级冲突检测")
            remaining_stock = 1
        
        # 创建数据库预约记录
        try:
            reservation = Reservation(
                user_id=user_id,
                seat_id=seat_id,
                room_id=room_id,
                reservation_date=date_obj.date(),
                reservation_time=reservation_time,
                status=0  # 预约中
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            logger.info(f"预约成功: user_id={user_id}, seat_id={seat_id}, date={reservation_date}")
            
            # 记录热力图数据（用于后续分析）
            _update_heatmap(redis_client, room_id, seat_id, reservation_date, reservation_time)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"数据库错误: {e}")
            
            # 如果数据库保存失败，需要回滚Redis中的预约（仅当Redis可用时）
            if redis_client:
                ReservationLuaScript.cancel_reservation(
                    redis_client=redis_client,
                    seat_id=seat_id,
                    user_id=user_id,
                    date=reservation_date,
                    time_slot=reservation_time
                )
            
            return ApiResponse.error('预约失败，请稍后重试'), 500
        
        return ApiResponse.success({
            'reservation_id': reservation.id,
            'seat_id': seat_id,
            'seat_number': seat.seat_number,
            'room_id': room_id,
            'reservation_date': reservation_date,
            'reservation_time': reservation_time,
            'remaining_stock': remaining_stock,
            'status': 'reserved',
            'created_at': reservation.created_at.isoformat()
        }, message='预约成功', code=201)
    
    except Exception as e:
        logger.error(f"提交预约异常: {e}")
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


def _update_heatmap(redis_client: redis.Redis, room_id: int, seat_id: int,
                    date: str, time_slot: str):
    """
    更新座位热力图数据
    
    Args:
        redis_client: Redis客户端
        room_id: 阅览室ID
        seat_id: 座位ID
        date: 预约日期
        time_slot: 时间段
    """
    if not redis_client:
        return  # 开发环境：Redis不可用时跳过热力图更新
    
    try:
        heatmap_key = f"heatmap:{room_id}:{date}:{time_slot}"
        redis_client.hincrby(heatmap_key, str(seat_id), 1)
        redis_client.expire(heatmap_key, 86400)  # 24小时过期
    except Exception as e:
        logger.error(f"更新热力图失败: {e}")


# ===========================
# 3. 扫码签到接口
# ===========================

@reservation_bp.route('/check-in', methods=['POST'])
@require_auth
def check_in(user_id: int):
    """
    扫码签到接口
    验证：
    1. 用户是否有当前时间段的有效预约
    2. 是否在预约时间段内
    3. 是否超过迟到时间限制
    
    Request JSON:
        {
            "reservation_id": 123,
            "qr_code_data": "seat:seat_id:date:time_slot"  # 二维码数据
        }
    
    Returns:
        签到结果
    """
    try:
        data = request.get_json() or {}
        
        reservation_id = data.get('reservation_id')
        qr_code_data = data.get('qr_code_data')
        
        if not reservation_id:
            return ApiResponse.error('缺少预约ID'), 400

        if not qr_code_data:
            return ApiResponse.error('缺少签到二维码数据'), 400

        # 查询预约记录
        reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()
        if not reservation:
            return ApiResponse.error('预约记录不存在或不属于当前用户'), 404

        # 核心漏洞修复：验证二维码数据是否真实包含当前记录的座位ID，防止抓包隔空打卡
        # 假设真实系统的二维码通常格式如 "seat:123:date:2024-03-20:..."
        expected_seat_marker = f"seat:{reservation.seat_id}"
        if expected_seat_marker not in qr_code_data:
            logger.warning(f"恶意签到拦截: user_id={user_id}, 提供的qr={qr_code_data}, 期望={expected_seat_marker}")
            return ApiResponse.error('签到失败：二维码无效或您扫描的不是该预约对应的座位'), 400

        # 检查预约状态
        if reservation.status != 0:
            return ApiResponse.error('预约已失效或已完成'), 400
        
        now = datetime.now()
        current_date = now.date()
        
        # 检查预约日期是否正确
        if reservation.reservation_date != current_date:
            return ApiResponse.error('预约日期不匹配，无法签到'), 400
        
        # 解析预约时间段
        time_range = reservation.reservation_time.split('-')
        if len(time_range) != 2:
            return ApiResponse.error('预约时间段格式错误'), 400
        
        try:
            start_time = datetime.strptime(time_range[0], '%H:%M').time()
            end_time = datetime.strptime(time_range[1], '%H:%M').time()
        except ValueError:
            return ApiResponse.error('预约时间格式错误'), 400
        
        current_time = now.time()
        
        # 时间检查逻辑
        early_check_in_minutes = 10  # 提前10分钟可以签到
        late_check_in_minutes = 30   # 超过30分钟视为缺座
        
        start_datetime = datetime.combine(current_date, start_time)
        end_datetime = datetime.combine(current_date, end_time)
        early_start = start_datetime - timedelta(minutes=early_check_in_minutes)
        late_deadline = start_datetime + timedelta(minutes=late_check_in_minutes)
        
        # 检查签到时间是否有效
        if now < early_start:
            minutes_until = int((early_start - now).total_seconds() / 60)
            return ApiResponse.error(f'还不能签到，请在{minutes_until}分钟后再试'), 400
        
        if now > late_deadline:
            # 超过迟到时间，标记为缺座
            reservation.status = 4  # 已迟到
            reservation.no_show_times += 1
            db.session.commit()
            
            # 扣除信用积分
            user = User.query.filter_by(id=user_id).first()
            if user:
                user.credit_score -= 5
                db.session.commit()
                
                # 记录信用流水
                credit_flow = CreditFlow(
                    user_id=user_id,
                    action='no_show',
                    points_change=-5,
                    reason='迟到超时',
                    reservation_id=reservation_id,
                    balance_after=user.credit_score
                )
                db.session.add(credit_flow)
                db.session.commit()
            
            return ApiResponse.error('签到时间已过期，已标记为缺座，扣除信用5分'), 400
        
        # 更新座位占用状态
        seat = Seat.query.filter_by(id=reservation.seat_id).first()
        if seat:
            seat.status = 1  # 已占用
            seat.last_user_id = user_id
            seat.last_updated = now
        
        # 更新预约记录
        reservation.status = 1  # 已签到
        reservation.check_in_time = now
        
        db.session.commit()
        
        logger.info(f"用户签到成功: user_id={user_id}, reservation_id={reservation_id}")
        
        return ApiResponse.success({
            'reservation_id': reservation_id,
            'user_id': user_id,
            'seat_id': reservation.seat_id,
            'check_in_time': now.isoformat(),
            'time_remaining_minutes': int((end_datetime - now).total_seconds() / 60),
            'status': 'checked_in'
        }, message='签到成功')
    
    except Exception as e:
        logger.error(f"签到异常: {e}")
        db.session.rollback()
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


# ===========================
# 4. 签退接口
# ===========================

@reservation_bp.route('/check-out', methods=['POST'])
@require_auth
def check_out(user_id: int):
    """
    签退接口
    记录用户离开阅览室的时间
    
    Request JSON:
        {
            "reservation_id": 123
        }
    
    Returns:
        签退结果及使用时长
    """
    try:
        data = request.get_json() or {}
        
        reservation_id = data.get('reservation_id')
        if not reservation_id:
            return ApiResponse.error('缺少预约ID'), 400
        
        # 查询预约记录
        reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()
        if not reservation:
            return ApiResponse.error('预约记录不存在或不属于当前用户'), 404
        
        # 检查是否已签到
        if reservation.status != 1:
            return ApiResponse.error('预约未签到或已完成'), 400
        
        now = datetime.now()
        
        # 计算使用时长
        check_in_time = reservation.check_in_time
        if not check_in_time:
            return ApiResponse.error('签到记录不存在'), 400
        
        duration_minutes = int((now - check_in_time).total_seconds() / 60)
        
        # 更新预约记录
        reservation.status = 2  # 已结束
        reservation.check_out_time = now
        
        # 更新座位状态
        seat = Seat.query.filter_by(id=reservation.seat_id).first()
        if seat:
            seat.status = 0  # 恢复空闲
            seat.last_updated = now
        
        db.session.commit()
        
        # 计算时间段信息
        time_range = reservation.reservation_time.split('-')
        try:
            start_time = datetime.strptime(time_range[0], '%H:%M').time()
            end_time = datetime.strptime(time_range[1], '%H:%M').time()
            slot_duration_minutes = int((datetime.combine(datetime.now().date(), end_time) - 
                                        datetime.combine(datetime.now().date(), start_time)).total_seconds() / 60)
        except:
            slot_duration_minutes = None
        
        logger.info(f"用户签退成功: user_id={user_id}, reservation_id={reservation_id}, duration={duration_minutes}min")
        
        return ApiResponse.success({
            'reservation_id': reservation_id,
            'user_id': user_id,
            'seat_id': reservation.seat_id,
            'check_in_time': reservation.check_in_time.isoformat(),
            'check_out_time': now.isoformat(),
            'duration_minutes': duration_minutes,
            'reserved_slot_minutes': slot_duration_minutes,
            'status': 'checked_out'
        }, message='签退成功')
    
    except Exception as e:
        logger.error(f"签退异常: {e}")
        db.session.rollback()
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


# ===========================
# 5. 取消预约接口
# ===========================

@reservation_bp.route('/cancel/<int:reservation_id>', methods=['POST'])
@require_auth
def cancel_reservation(user_id: int, reservation_id: int):
    """
    取消预约接口
    只能取消未签到的预约
    
    Returns:
        取消结果
    """
    try:
        # 查询预约记录
        reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()
        if not reservation:
            return ApiResponse.error('预约记录不存在或不属于当前用户'), 404
        
        # 只能取消未签到的预约
        if reservation.status != 0:
            return ApiResponse.error('只能取消未签到的预约'), 400

        # 核心漏洞修复：检查是否属于临近迟到恶意取消，如果距预约开始时间小于30分钟，扣除信誉分
        now = datetime.now()
        current_date = now.date()
        if reservation.reservation_date == current_date:
            time_range = reservation.reservation_time.split('-')
            if len(time_range) == 2:
                try:
                    start_time = datetime.strptime(time_range[0], '%H:%M').time()
                    start_datetime = datetime.combine(current_date, start_time)
                    # 如果当前时间与预约开始时间相差在30分钟以内（或已经超过开始时间）
                    if (start_datetime - now).total_seconds() < 30 * 60:
                        user = User.query.filter_by(id=user_id).first()
                        if user:
                            user.credit_score -= 2
                            credit_flow = CreditFlow(
                                user_id=user_id,
                                action='late_cancel',
                                points_change=-2,
                                reason='临近或超时取消预约',
                                reservation_id=reservation_id,
                                balance_after=user.credit_score
                            )
                            db.session.add(credit_flow)
                            logger.info(f"临近迟到取消扣分: user_id={user_id}, 扣除2分")
                except Exception as e:
                    logger.error(f"解析时间出错: {e}")

        # 从Redis回滚库存
        redis_client = get_redis_client()
        if redis_client:
            ReservationLuaScript.cancel_reservation(
                redis_client=redis_client,
                seat_id=reservation.seat_id,
                user_id=user_id,
                date=reservation.reservation_date.isoformat(),
                time_slot=reservation.reservation_time
            )
        
        # 更新数据库
        reservation.status = 3  # 已取消
        db.session.commit()
        
        logger.info(f"预约取消成功: user_id={user_id}, reservation_id={reservation_id}")
        
        return ApiResponse.success({
            'reservation_id': reservation_id,
            'status': 'cancelled'
        }, message='预约已取消')
    
    except Exception as e:
        logger.error(f"取消预约异常: {e}")
        db.session.rollback()
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


# ===========================
# 6. 获取用户预约列表接口
# ===========================

@reservation_bp.route('/my-reservations', methods=['GET'])
@require_auth
def get_my_reservations(user_id: int):
    """
    获取当前用户的预约列表
    
    Query参数:
        status: 预约状态筛选 (0=预约中, 1=已签到, 2=已结束, 3=已取消, 4=已迟到)
        page: 页码 (默认1)
        per_page: 每页数量 (默认10)
    
    Returns:
        用户预约列表
    """
    try:
        status_filter = request.args.get('status', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 基础查询
        query = Reservation.query.filter_by(user_id=user_id)
        
        # 状态筛选
        if status_filter is not None:
            query = query.filter_by(status=status_filter)
        
        # 按时间倒序排列
        query = query.order_by(Reservation.created_at.desc())
        
        # 分页
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        reservations = []
        for res in paginated.items:
            seat = Seat.query.filter_by(id=res.seat_id).first()
            room = ReadingRoom.query.filter_by(id=res.room_id).first()
            
            reservations.append({
                'id': res.id,
                'seat_id': res.seat_id,
                'seat_number': seat.seat_number if seat else '未知',
                'room_id': res.room_id,
                'room_name': room.name if room else '未知',
                'reservation_date': res.reservation_date.isoformat(),
                'reservation_time': res.reservation_time,
                'status': res.status,
                'check_in_time': res.check_in_time.isoformat() if res.check_in_time else None,
                'check_out_time': res.check_out_time.isoformat() if res.check_out_time else None,
                'reservation_date': res.reservation_date.isoformat(),
                'reservation_time': res.reservation_time,
                'status': res.status,
                'status_text': _get_status_text(res.status),
                'check_in_time': res.check_in_time.isoformat() if res.check_in_time else None,
                'check_out_time': res.check_out_time.isoformat() if res.check_out_time else None,
                'created_at': res.created_at.isoformat()
            })
        
        return ApiResponse.success({
            'total': paginated.total,
            'pages': paginated.pages,
            'page': page,
            'per_page': per_page,
            'reservations': reservations
        })
    
    except Exception as e:
        logger.error(f"获取用户预约列表异常: {e}")
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


# ===========================
# 7. 获取推荐座位接口
# ===========================

@reservation_bp.route('/recommend', methods=['GET'])
@require_auth
def get_seat_recommendations(user_id: int):
    """
    根据拥挤度推荐座位
    
    Query参数:
        room_id: 阅览室ID (必须)
        date: 预约日期 (YYYY-MM-DD, 必须)
        time_slot: 时间段 (HH:MM-HH:MM, 必须)
        count: 推荐座位数量 (默认5)
    
    Returns:
        推荐座位列表和推荐原因
    """
    try:
        room_id = request.args.get('room_id', type=int)
        date_str = request.args.get('date')
        time_slot = request.args.get('time_slot')
        count = request.args.get('count', 5, type=int)
        
        # 参数验证
        if not room_id or not date_str or not time_slot:
            return ApiResponse.error('缺少必要参数: room_id, date, time_slot'), 400
        
        # 获取该阅览室的所有座位
        all_seats = Seat.query.filter_by(room_id=room_id, status=0).all()
        
        if not all_seats:
            return ApiResponse.error('该阅览室没有可用座位'), 404
        
        # 查询该时间段已预约的座位 ID
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return ApiResponse.error('日期格式错误，应为 YYYY-MM-DD'), 400
        
        # 查询该时间段已预约的座位
        reserved_seat_ids = set()
        try:
            # 先检查Reservation表是否有数据
            existing_reservations = Reservation.query.filter(
                Reservation.room_id == room_id,
                Reservation.reservation_date == date_obj
            ).all()
            
            # 从已预约的记录中筛选出该时间段的
            for res in existing_reservations:
                if res.reservation_time == time_slot and res.status in (0, 1):
                    reserved_seat_ids.add(res.seat_id)
        except Exception as e:
            logger.warning(f"查询预约记录时出错: {e}，将继续推荐")
            # 继续执行，不让错误中断功能
        
        # 计算每个座位的拥挤度: 已预约 / 总座位数
        available_seats = []
        crowding_level = len(reserved_seat_ids) / max(len(all_seats), 1) if all_seats else 0
        
        for seat in all_seats:
            if seat.id not in reserved_seat_ids:
                # 从seat_number提取row和col (如"A-001" -> row="A", col="001")
                parts = seat.seat_number.split('-')
                row = parts[0] if len(parts) > 0 else ''
                col = parts[1] if len(parts) > 1 else '0'
                
                available_seats.append({
                    'seat_id': seat.id,
                    'seat_number': seat.seat_number,
                    'room_id': room_id,
                    'room_name': '阅览室',
                    'row': row,
                    'col': col,
                    'crowding_level': crowding_level,
                    'available': True,
                    'recommendation_score': 100 - int(crowding_level * 100)  # 评分
                })
        
        # 按拥挤度排序，选择拥挤度最低的座位
        available_seats.sort(key=lambda x: (x['crowding_level'], x['row'], x['col']))
        recommendations = available_seats[:count]
        
        # 如果没有足够的推荐座位
        if not recommendations:
            return ApiResponse.error('该时间段没有可用座位'), 404
        
        # 生成推荐原因
        avg_crowding = sum(s['crowding_level'] for s in recommendations) / len(recommendations)
        if avg_crowding < 0.3:
            recommendation_reason = '该时间段人较少，推荐座位'
        elif avg_crowding < 0.6:
            recommendation_reason = '该时间段人适中，推荐座位'
        else:
            recommendation_reason = '该时间段人较多，推荐相对较冷的座位'
        
        logger.info(f"推荐座位成功: 用户{user_id}, 房间{room_id}, 日期{date_str}, 返回{len(recommendations)}个座位")
        
        return ApiResponse.success({
            'recommendations': recommendations,
            'recommendation_reason': recommendation_reason,
            'total_available': len(available_seats),
            'average_crowding': avg_crowding
        })
    
    except Exception as e:
        logger.error(f"获取推荐座位异常: {e}", exc_info=True)
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


def _get_status_text(status: int) -> str:
    """获取预约状态的文本表示"""
    status_map = {
        0: '预约中',
        1: '已签到',
        2: '已结束',
        3: '已取消',
        4: '已迟到'
    }
    return status_map.get(status, '未知')


# ===========================
# 8. 座位维修申请接口
# ===========================

@reservation_bp.route('/maintenance/report', methods=['POST'])
@require_auth
def report_maintenance(user_id: int):
    """
    用户报告座位维修问题
    
    Request JSON:
        {
            "seat_id": 101,
            "issue_type": "broken",  # broken-损坏, dirty-脏污, furniture-家具问题, electrical-电气问题, other-其他
            "severity": "high",      # low-低, medium-中, high-高, critical-严重
            "description": "座位扶手损坏",
            "phone": "13800138000"   # 可选，用于管理员联系
        }
    
    Returns:
        维修申请记录
    """
    try:
        data = request.get_json() or {}
        
        # 验证必需字段
        required_fields = ['seat_id', 'issue_type', 'description']
        for field in required_fields:
            if field not in data:
                return ApiResponse.error(f'缺少必需字段: {field}'), 400
        
        seat_id = data.get('seat_id')
        issue_type = data.get('issue_type', 'other')
        severity = data.get('severity', 'medium')
        description = data.get('description', '')
        phone = data.get('phone', '')
        
        # 验证座位是否存在
        seat = Seat.query.filter_by(id=seat_id).first()
        if not seat:
            return ApiResponse.error('座位不存在'), 404
        
        # 检查是否有未处理的维修申请（防止重复申报）
        existing_maintenance = SeatMaintenance.query.filter_by(
            seat_id=seat_id,
            status='pending'
        ).first()
        
        if existing_maintenance:
            return ApiResponse.error('该座位已有待处理的维修申请，请勿重复申报'), 400
        
        # 创建维修申请
        maintenance = SeatMaintenance(
            seat_id=seat_id,
            issue_type=issue_type,
            severity=severity,
            description=description,
            reported_by_id=user_id,
            reporter_phone=phone,
            status='pending',
            estimated_days=1
        )
        
        # 如果未设置为维修状态，则标记为维修中
        if seat.status != 2:
            seat.status = 2  # 标记为维修中
        
        db.session.add(maintenance)
        db.session.commit()
        
        logger.info(f"维修申请已提交: 用户{user_id}, 座位{seat_id}, 问题类型{issue_type}, 严重程度{severity}")
        
        return ApiResponse.success({
            'report_id': maintenance.id,
            'seat_id': seat_id,
            'seat_number': seat.seat_number,
            'issue_type': issue_type,
            'severity': severity,
            'status': 'pending',
            'created_at': maintenance.created_at.isoformat()
        }, message='维修申请已提交，管理员会尽快处理', code=201)
    
    except Exception as e:
        logger.error(f"提交维修申请异常: {e}")
        db.session.rollback()
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


@reservation_bp.route('/maintenance/status', methods=['GET'])
@require_auth
def get_maintenance_status(user_id: int):
    """
    获取用户提交的维修申请列表
    
    Query参数:
        page: 页码 (默认1)
        per_page: 每页数量 (默认10)
        status: 筛选状态 (pending-待处理, in_progress-处理中, completed-已完成)
    
    Returns:
        维修申请列表
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', '')
        
        # 构建查询
        query = SeatMaintenance.query.filter_by(reported_by_id=user_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # 按创建时间倒序
        paginated = query.order_by(SeatMaintenance.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        maintenance_list = []
        for m in paginated.items:
            maintenance_list.append({
                'id': m.id,
                'seat_id': m.seat_id,
                'seat_number': m.seat.seat_number if m.seat else '未知',
                'room_id': m.seat.room_id if m.seat else None,
                'room_name': m.seat.room.name if m.seat and m.seat.room else '未知',
                'issue_type': m.issue_type,
                'issue_type_text': _get_issue_type_text(m.issue_type),
                'severity': m.severity,
                'severity_text': _get_severity_text(m.severity),
                'description': m.description,
                'status': m.status,
                'status_text': _get_maintenance_status_text(m.status),
                'assigned_to_name': m.assigned_to.real_name if m.assigned_to else None,
                'maintenance_date': m.maintenance_date.isoformat() if m.maintenance_date else None,
                'completion_date': m.completion_date.isoformat() if m.completion_date else None,
                'notes': m.notes,
                'estimated_days': m.estimated_days,
                'created_at': m.created_at.isoformat(),
                'updated_at': m.updated_at.isoformat()
            })
        
        return ApiResponse.success({
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages,
            'maintenance_requests': maintenance_list
        })
    
    except Exception as e:
        logger.error(f"获取维修申请状态异常: {e}")
        return ApiResponse.error(f'系统错误: {str(e)}'), 500


def _get_issue_type_text(issue_type: str) -> str:
    """获取问题类型的文本表示"""
    issue_type_map = {
        'broken': '座位损坏',
        'dirty': '座位脏污',
        'furniture': '家具问题',
        'electrical': '电气问题',
        'other': '其他问题'
    }
    return issue_type_map.get(issue_type, '未知问题')


def _get_severity_text(severity: str) -> str:
    """获取严重程度的文本表示"""
    severity_map = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'critical': '严重'
    }
    return severity_map.get(severity, '未知')


def _get_maintenance_status_text(status: str) -> str:
    """获取维修状态的文本表示"""
    status_map = {
        'pending': '待处理',
        'in_progress': '处理中',
        'completed': '已完成',
        'cancelled': '已取消'
    }
    return status_map.get(status, '未知')



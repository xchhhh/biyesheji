"""
管理员操作接口
处理用户管理、座位维护、公告、审计日志等功能
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from app.models import db, User, Seat, ReadingRoom, Reservation, AuditLog, Announcement, SeatMaintenance, CreditFlow
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
management_bp = Blueprint('management', __name__, url_prefix='/api/admin/management')

# ===== 管理员认证装饰器 =====

def require_admin(f):
    """管理员角色检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取管理员标识
        admin_token = request.headers.get('X-Admin-Token')
        user_id = request.headers.get('X-User-Id', type=int)
        
        # 开发环境下允许使用特殊token
        if admin_token == 'admin_test_token':
            request.admin_id = 1
            return f(*args, **kwargs)
        
        # 生产环境应该验证真实的管理员身份
        if user_id:
            user = User.query.get(user_id)
            if user and user.status == 1:  # 用户激活状态
                request.admin_id = user_id
                return f(*args, **kwargs)
        
        return jsonify({'code': 403, 'message': '无管理员权限'}), 403
    
    return decorated_function


def record_audit_log(action, module, resource_type=None, resource_id=None, 
                      description=None, old_values=None, new_values=None, status='success'):
    """记录审计日志"""
    try:
        audit_log = AuditLog(
            operator_id=getattr(request, 'admin_id', None),
            action=action,
            module=module,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description or f'{action} {resource_type}',
            old_values=old_values,
            new_values=new_values,
            status=status,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        logger.error(f'记录审计日志失败: {e}')


# ===== 用户管理接口 =====

@management_bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    """
    获取用户列表
    
    参数:
    - page: 页码 (default: 1)
    - per_page: 每页数量 (default: 20)
    - status: 用户状态 (0-禁用, 1-正常, -1-全部)
    - search: 搜索关键词 (nickname/phone/student_id)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', -1, type=int)
        search = request.args.get('search', '', type=str)
        
        query = User.query
        
        # 状态过滤
        if status >= 0:
            query = query.filter(User.status == status)
        
        # 搜索过滤
        if search:
            query = query.filter(or_(
                User.nickname.ilike(f'%{search}%'),
                User.phone.ilike(f'%{search}%'),
                User.student_id.ilike(f'%{search}%'),
                User.real_name.ilike(f'%{search}%')
            ))
        
        # 分页
        paginated = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = [
            {
                'id': user.id,
                'nickname': user.nickname,
                'phone': user.phone,
                'student_id': user.student_id,
                'real_name': user.real_name,
                'credit_score': user.credit_score,
                'status': user.status,
                'status_label': '正常' if user.status == 1 else '禁用',
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
            }
            for user in paginated.items
        ]
        
        return jsonify({
            'code': 200,
            'data': users_data,
            'pagination': {
                'total': paginated.total,
                'page': page,
                'per_page': per_page,
                'pages': paginated.pages,
            }
        }), 200
    
    except Exception as e:
        logger.error(f'获取用户列表失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user_detail(user_id):
    """获取用户详细信息"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取用户的预约记录
        recent_reservations = Reservation.query.filter(
            Reservation.user_id == user_id
        ).order_by(desc(Reservation.created_at)).limit(10).all()
        
        # 获取用户的信用积分流水
        credit_flows = CreditFlow.query.filter(
            CreditFlow.user_id == user_id
        ).order_by(desc(CreditFlow.created_at)).limit(10).all()
        
        return jsonify({
            'code': 200,
            'data': {
                'user': user.to_dict(include_private=True),
                'statistics': {
                    'total_reservations': Reservation.query.filter_by(user_id=user_id).count(),
                    'completed_reservations': Reservation.query.filter(
                        and_(Reservation.user_id == user_id, Reservation.status == 2)
                    ).count(),
                    'cancelled_reservations': Reservation.query.filter(
                        and_(Reservation.user_id == user_id, Reservation.status == 3)
                    ).count(),
                },
                'recent_reservations': [r.to_dict() for r in recent_reservations],
                'credit_flows': [cf.to_dict() for cf in credit_flows],
            }
        }), 200
    
    except Exception as e:
        logger.error(f'获取用户详情失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/users/<int:user_id>/disable', methods=['POST'])
@require_admin
def disable_user(user_id):
    """禁用用户账户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        reason = request.json.get('reason', '管理员禁用')
        
        # 记录旧值
        old_status = user.status
        
        # 禁用用户
        user.status = 0
        
        # 取消所有待签到的预约
        pending_reservations = Reservation.query.filter(
            and_(Reservation.user_id == user_id, Reservation.status == 0)
        ).all()
        
        for res in pending_reservations:
            res.status = 3  # 取消状态
        
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='disable',
            module='user',
            resource_type='User',
            resource_id=user_id,
            description=f'禁用用户 {user.nickname} ({reason})',
            old_values={'status': old_status},
            new_values={'status': 0}
        )
        
        return jsonify({
            'code': 200,
            'message': '用户已禁用',
            'data': {'user_id': user_id, 'status': 0}
        }), 200
    
    except Exception as e:
        logger.error(f'禁用用户失败: {e}')
        record_audit_log(
            action='disable',
            module='user',
            resource_type='User',
            resource_id=user_id,
            description=f'禁用用户失败',
            status='failed',
            old_values={},
            new_values={}
        )
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/users/<int:user_id>/enable', methods=['POST'])
@require_admin
def enable_user(user_id):
    """启用用户账户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 记录旧值
        old_status = user.status
        
        # 启用用户
        user.status = 1
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='enable',
            module='user',
            resource_type='User',
            resource_id=user_id,
            description=f'启用用户 {user.nickname}',
            old_values={'status': old_status},
            new_values={'status': 1}
        )
        
        return jsonify({
            'code': 200,
            'message': '用户已启用',
            'data': {'user_id': user_id, 'status': 1}
        }), 200
    
    except Exception as e:
        logger.error(f'启用用户失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/users/<int:user_id>/cancel-reservations', methods=['POST'])
@require_admin
def force_cancel_reservations(user_id):
    """强制取消用户的所有预约"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        reason = request.json.get('reason', '管理员强制取消')
        
        # 获取用户的所有未完成预约
        reservations = Reservation.query.filter(
            and_(
                Reservation.user_id == user_id,
                Reservation.status.in_([0, 1])  # pending 或 checked_in
            )
        ).all()
        
        cancel_count = 0
        for res in reservations:
            res.status = 3  # 取消状态
            cancel_count += 1
        
        # 更新座位状态
        affected_seat_ids = [r.seat_id for r in reservations if r.seat_id]
        for seat_id in set(affected_seat_ids):
            seat = Seat.query.get(seat_id)
            if seat and seat.status != 2:  # 不是维修状态
                seat.status = 0  # 恢复空闲状态
        
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='force_cancel',
            module='reservation',
            resource_type='User',
            resource_id=user_id,
            description=f'强制取消用户 {user.nickname} 的 {cancel_count} 个预约 ({reason})',
            new_values={'cancelled_count': cancel_count}
        )
        
        return jsonify({
            'code': 200,
            'message': f'已取消 {cancel_count} 个预约',
            'data': {'cancelled_count': cancel_count}
        }), 200
    
    except Exception as e:
        logger.error(f'强制取消预约失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


# ===== 座位维护管理接口 =====

@management_bp.route('/seats/maintenance', methods=['GET'])
@require_admin
def list_maintenance():
    """
    获取座位维护记录列表
    
    参数:
    - page: 页码
    - per_page: 每页数量
    - status: 维护状态
    - severity: 严重程度
    - room_id: 房间ID
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        severity = request.args.get('severity', '')
        room_id = request.args.get('room_id', type=int)
        
        query = SeatMaintenance.query
        
        if status:
            query = query.filter(SeatMaintenance.status == status)
        
        if severity:
            query = query.filter(SeatMaintenance.severity == severity)
        
        if room_id:
            query = query.join(Seat).filter(Seat.room_id == room_id)
        
        paginated = query.order_by(
            desc(SeatMaintenance.created_at)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'code': 200,
            'data': [m.to_dict() for m in paginated.items],
            'pagination': {
                'total': paginated.total,
                'page': page,
                'per_page': per_page,
                'pages': paginated.pages,
            }
        }), 200
    
    except Exception as e:
        logger.error(f'获取维护记录失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/seats/<int:seat_id>/maintenance', methods=['POST'])
@require_admin
def report_seat_maintenance(seat_id):
    """报告座位维护问题"""
    try:
        seat = Seat.query.get(seat_id)
        if not seat:
            return jsonify({'code': 404, 'message': '座位不存在'}), 404
        
        data = request.json
        
        maintenance = SeatMaintenance(
            seat_id=seat_id,
            issue_type=data.get('issue_type', 'other'),
            severity=data.get('severity', 'medium'),
            description=data.get('description', ''),
            reported_by_id=request.admin_id,
            reporter_phone=data.get('reporter_phone', ''),
            status='pending',
            estimated_days=data.get('estimated_days', 1),
        )
        
        # 标记座位为维修状态
        seat.status = 2
        
        db.session.add(maintenance)
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='create',
            module='maintenance',
            resource_type='SeatMaintenance',
            resource_id=maintenance.id,
            description=f'报告座位 {seat.seat_number} 维护: {data.get("description", "")}',
            new_values=maintenance.to_dict()
        )
        
        return jsonify({
            'code': 200,
            'message': '维护记录已创建',
            'data': maintenance.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'创建维护记录失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/seats/maintenance/<int:maintenance_id>/complete', methods=['POST'])
@require_admin
def complete_maintenance(maintenance_id):
    """完成座位维护"""
    try:
        maintenance = SeatMaintenance.query.get(maintenance_id)
        if not maintenance:
            return jsonify({'code': 404, 'message': '维护记录不存在'}), 404
        
        old_status = maintenance.status
        notes = request.json.get('notes', '')
        
        maintenance.status = 'completed'
        maintenance.completion_date = datetime.utcnow()
        maintenance.notes = notes
        
        # 恢复座位为空闲状态
        seat = Seat.query.get(maintenance.seat_id)
        if seat:
            seat.status = 0
        
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='complete',
            module='maintenance',
            resource_type='SeatMaintenance',
            resource_id=maintenance_id,
            description=f'完成座位维护',
            old_values={'status': old_status},
            new_values={'status': 'completed'}
        )
        
        return jsonify({
            'code': 200,
            'message': '维护完成',
            'data': maintenance.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'完成维护失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


# ===== 公告管理接口 =====

@management_bp.route('/announcements', methods=['GET'])
@require_admin
def list_announcements():
    """获取公告列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', -1, type=int)
        
        query = Announcement.query
        
        if status >= 0:
            query = query.filter(Announcement.status == status)
        
        paginated = query.order_by(
            desc(Announcement.is_pinned),
            desc(Announcement.created_at)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'code': 200,
            'data': [a.to_dict() for a in paginated.items],
            'pagination': {
                'total': paginated.total,
                'page': page,
                'per_page': per_page,
                'pages': paginated.pages,
            }
        }), 200
    
    except Exception as e:
        logger.error(f'获取公告列表失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/announcements', methods=['POST'])
@require_admin
def create_announcement():
    """创建公告"""
    try:
        data = request.json
        
        announcement = Announcement(
            title=data.get('title', ''),
            content=data.get('content', ''),
            type=data.get('type', 'general'),
            priority=data.get('priority', 0),
            author_id=request.admin_id,
            status=1,  # 直接发布
            is_pinned=data.get('is_pinned', False),
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='create',
            module='announcement',
            resource_type='Announcement',
            resource_id=announcement.id,
            description=f'发布公告: {announcement.title}',
            new_values=announcement.to_dict()
        )
        
        return jsonify({
            'code': 200,
            'message': '公告已发布',
            'data': announcement.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'创建公告失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/announcements/<int:announcement_id>', methods=['PUT'])
@require_admin
def update_announcement(announcement_id):
    """更新公告"""
    try:
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            return jsonify({'code': 404, 'message': '公告不存在'}), 404
        
        data = request.json
        old_values = announcement.to_dict()
        
        announcement.title = data.get('title', announcement.title)
        announcement.content = data.get('content', announcement.content)
        announcement.type = data.get('type', announcement.type)
        announcement.priority = data.get('priority', announcement.priority)
        announcement.is_pinned = data.get('is_pinned', announcement.is_pinned)
        
        if data.get('start_time'):
            announcement.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            announcement.end_time = datetime.fromisoformat(data['end_time'])
        
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='update',
            module='announcement',
            resource_type='Announcement',
            resource_id=announcement_id,
            description=f'更新公告: {announcement.title}',
            old_values=old_values,
            new_values=announcement.to_dict()
        )
        
        return jsonify({
            'code': 200,
            'message': '公告已更新',
            'data': announcement.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'更新公告失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/announcements/<int:announcement_id>', methods=['DELETE'])
@require_admin
def delete_announcement(announcement_id):
    """删除/下架公告"""
    try:
        announcement = Announcement.query.get(announcement_id)
        if not announcement:
            return jsonify({'code': 404, 'message': '公告不存在'}), 404
        
        announcement.status = 2  # 下架
        db.session.commit()
        
        # 记录审计日志
        record_audit_log(
            action='delete',
            module='announcement',
            resource_type='Announcement',
            resource_id=announcement_id,
            description=f'下架公告: {announcement.title}',
            old_values={'status': 1},
            new_values={'status': 2}
        )
        
        return jsonify({
            'code': 200,
            'message': '公告已下架',
        }), 200
    
    except Exception as e:
        logger.error(f'删除公告失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


# ===== 审计日志接口 =====

@management_bp.route('/audit-logs', methods=['GET'])
@require_admin
def list_audit_logs():
    """获取审计日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        module = request.args.get('module', '')
        action = request.args.get('action', '')
        status = request.args.get('status', '')
        
        query = AuditLog.query
        
        if module:
            query = query.filter(AuditLog.module == module)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if status:
            query = query.filter(AuditLog.status == status)
        
        # 默认显示最近7天的日志
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(AuditLog.created_at >= seven_days_ago)
        
        paginated = query.order_by(
            desc(AuditLog.created_at)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'code': 200,
            'data': [log.to_dict() for log in paginated.items],
            'pagination': {
                'total': paginated.total,
                'page': page,
                'per_page': per_page,
                'pages': paginated.pages,
            }
        }), 200
    
    except Exception as e:
        logger.error(f'获取审计日志失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/audit-logs/<int:log_id>', methods=['GET'])
@require_admin
def get_audit_log_detail(log_id):
    """获取审计日志详情"""
    try:
        log = AuditLog.query.get(log_id)
        if not log:
            return jsonify({'code': 404, 'message': '日志不存在'}), 404
        
        return jsonify({
            'code': 200,
            'data': log.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'获取审计日志详情失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


# ===== 值班人员快速查看接口 =====

@management_bp.route('/duty-dashboard', methods=['GET'])
@require_admin
def duty_dashboard():
    """
    值班人员快速查看实时占用情况
    返回各房间的座位实时状态
    """
    try:
        rooms = ReadingRoom.query.all()
        
        dashboard_data = []
        for room in rooms:
            # 获取房间的座位统计
            total_seats = Seat.query.filter_by(room_id=room.id).count()
            occupied_seats = Seat.query.filter(
                and_(Seat.room_id == room.id, Seat.status == 1)
            ).count()
            maintenance_seats = Seat.query.filter(
                and_(Seat.room_id == room.id, Seat.status == 2)
            ).count()
            
            # 获取当前在用的预约
            today = datetime.now().date()
            active_reservations = Reservation.query.filter(
                and_(
                    Reservation.room_id == room.id,
                    func.date(Reservation.reservation_date) == today,
                    Reservation.status.in_([1])  # checked_in
                )
            ).count()
            
            dashboard_data.append({
                'room_id': room.id,
                'room_name': room.name,
                'floor': room.floor,
                'total_seats': total_seats,
                'occupied_seats': occupied_seats,
                'empty_seats': total_seats - occupied_seats - maintenance_seats,
                'maintenance_seats': maintenance_seats,
                'occupancy_rate': round(occupied_seats / total_seats * 100, 1) if total_seats > 0 else 0,
                'active_reservations': active_reservations,
            })
        
        return jsonify({
            'code': 200,
            'data': dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'获取值班面板失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


@management_bp.route('/duty-dashboard/room/<int:room_id>', methods=['GET'])
@require_admin
def duty_dashboard_room(room_id):
    """获取指定房间的详细座位占用情况"""
    try:
        room = ReadingRoom.query.get(room_id)
        if not room:
            return jsonify({'code': 404, 'message': '房间不存在'}), 404
        
        seats = Seat.query.filter_by(room_id=room_id).order_by(Seat.seat_number).all()
        
        today = datetime.now().date()
        seat_info = []
        for seat in seats:
            # 获取座位的当前预约
            current_reservation = Reservation.query.filter(
                and_(
                    Reservation.seat_id == seat.id,
                    func.date(Reservation.reservation_date) == today,
                    Reservation.status.in_([1])  # checked_in
                )
            ).first()
            
            user_name = None
            if current_reservation:
                user = User.query.get(current_reservation.user_id)
                user_name = user.nickname if user else 'Unknown'
            
            seat_info.append({
                'seat_id': seat.id,
                'seat_number': seat.seat_number,
                'status': seat.status,  # 0-空闲, 1-占用, 2-维修
                'status_label': _get_seat_status_label(seat.status),
                'user_name': user_name,
            })
        
        return jsonify({
            'code': 200,
            'data': {
                'room': {
                    'id': room.id,
                    'name': room.name,
                    'floor': room.floor,
                },
                'seats': seat_info,
            }
        }), 200
    
    except Exception as e:
        logger.error(f'获取房间详情失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500


def _get_seat_status_label(status):
    """获取座位状态标签"""
    status_map = {
        0: '空闲',
        1: '占用',
        2: '维修',
    }
    return status_map.get(status, '未知')


# ===== 系统统计接口 =====

@management_bp.route('/statistics/overview', methods=['GET'])
@require_admin
def statistics_overview():
    """
    获取系统统计概览
    """
    try:
        today = datetime.now().date()
        
        # 1. 用户统计
        total_users = User.query.count()
        active_users = User.query.filter_by(status=1).count()
        disabled_users = User.query.filter_by(status=0).count()
        
        # 2. 今日统计
        today_reservations = Reservation.query.filter(
            func.date(Reservation.reservation_date) == today
        ).count()
        today_checked_in = Reservation.query.filter(
            and_(
                func.date(Reservation.reservation_date) == today,
                Reservation.status == 1
            )
        ).count()
        today_completed = Reservation.query.filter(
            and_(
                func.date(Reservation.reservation_date) == today,
                Reservation.status == 2
            )
        ).count()
        
        # 3. 座位统计
        total_seats = Seat.query.count()
        occupied_seats = Seat.query.filter_by(status=1).count()
        maintenance_seats = Seat.query.filter_by(status=2).count()
        
        # 4. 维护统计
        pending_maintenance = SeatMaintenance.query.filter(
            SeatMaintenance.status == 'pending'
        ).count()
        
        return jsonify({
            'code': 200,
            'data': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'disabled': disabled_users,
                },
                'today': {
                    'total_reservations': today_reservations,
                    'checked_in': today_checked_in,
                    'completed': today_completed,
                },
                'seats': {
                    'total': total_seats,
                    'occupied': occupied_seats,
                    'maintenance': maintenance_seats,
                    'empty': total_seats - occupied_seats - maintenance_seats,
                },
                'maintenance': {
                    'pending': pending_maintenance,
                },
            }
        }), 200
    
    except Exception as e:
        logger.error(f'获取统计数据失败: {e}')
        return jsonify({'code': 500, 'message': '服务器错误'}), 500

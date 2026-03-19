"""
房间相关接口
处理房间信息查询、占用率查询等功能
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import func
from app.models import db, ReadingRoom, Seat, Reservation
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
rooms_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')


@rooms_bp.route('/occupancy', methods=['GET'])
def get_rooms_occupancy():
    """
    获取所有房间的实时占用率
    """
    try:
        # 获取所有房间
        rooms = ReadingRoom.query.filter_by(status=1).all()
        
        occupancy_data = []
        
        for room in rooms:
            # 获取该房间的总座位数（所有座位，包括维修的）
            total_seats = Seat.query.filter_by(
                room_id=room.id
            ).count()
            
            # 获取维修中的座位数
            maintenance_seats = Seat.query.filter_by(
                room_id=room.id,
                status=2  # 维修中
            ).count()
            
            # 获取该房间当前被预约的座位数（今天）
            today = datetime.now().date()
            occupied_query = db.session.query(func.count(Reservation.id)).filter(
                Reservation.room_id == room.id,
                Reservation.reservation_date == today,
                Reservation.status == 0  # 有效预约（状态 0 = pending/active）
            )
            occupied_seats = occupied_query.scalar() or 0
            
            # 计算可用座位数 (总座位 - 维修座位 - 已占用座位)
            available_seats = total_seats - maintenance_seats - occupied_seats
            
            # 计算占用率（百分比，基于可用座位）
            available_total = total_seats - maintenance_seats
            occupancy_rate = 0
            if available_total > 0:
                occupancy_rate = round((occupied_seats / available_total) * 100, 2)
            
            occupancy_data.append({
                "room_id": room.id,
                "room_name": room.name,
                "floor": room.floor,
                "total_seats": total_seats,
                "occupied_seats": occupied_seats,
                "available_seats": available_seats,
                "occupancy_rate": occupancy_rate / 100  # 转换为小数形式 (0.0-1.0)
            })
        
        logger.info(f'[rooms.py] 获取房间占用率成功，共 {len(occupancy_data)} 个房间')
        
        return jsonify({
            "code": 0,
            "message": "success",
            "data": occupancy_data
        }), 200
    
    except Exception as e:
        logger.error(f'[rooms.py] 获取房间占用率失败: {str(e)}')
        return jsonify({
            "code": 500,
            "message": f"获取房间占用率失败: {str(e)}"
        }), 500

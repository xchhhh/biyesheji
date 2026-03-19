"""
Redis 并发控制工具 - 乐观锁、悲观锁、Lua 脚本防超卖
实现高并发座位预约的核心机制
"""

import redis
import time
import uuid
import json
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class RedisLockManager:
    """Redis 分布式锁管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        """
        初始化锁管理器
        
        Args:
            redis_client: Redis客户端实例
        """
        self.redis = redis_client
        # Lua脚本：原子性删除锁（防止误删其他线程的锁）
        self.unlock_script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
        """
        # Lua脚本：原子性获取锁（SET NX EX的替代品）
        self.lock_script = """
            if redis.call('setnx', KEYS[1], ARGV[1]) == 1 then
                redis.call('expire', KEYS[1], ARGV[2])
                return 1
            else
                return 0
            end
        """
        
    @contextmanager
    def lock(self, key: str, timeout: int = 30, lock_timeout: int = 10):
        """
        分布式锁上下文管理器
        
        Args:
            key: 锁的键名
            timeout: 最多等待时间（秒）
            lock_timeout: 锁的过期时间（秒）
        
        Yields:
            lock_id: 锁的唯一标识符
        
        Raises:
            TimeoutError: 获取锁超时
        """
        lock_id = str(uuid.uuid4())
        lock_key = f"lock:{key}"
        start_time = time.time()
        
        # 尝试获取锁
        while time.time() - start_time < timeout:
            try:
                # 使用 SET NX EX 原子操作
                if self.redis.set(lock_key, lock_id, nx=True, ex=lock_timeout):
                    logger.debug(f"获取锁成功: {lock_key}")
                    break
            except Exception as e:
                logger.error(f"获取锁失败: {e}")
            
            time.sleep(0.01)  # 避免忙轮询，节省CPU
        else:
            raise TimeoutError(f"获取锁超时: {lock_key}")
        
        try:
            yield lock_id
        finally:
            # 释放锁（原子性）
            try:
                self.redis.eval(self.unlock_script, 1, lock_key, lock_id)
                logger.debug(f"释放锁成功: {lock_key}")
            except Exception as e:
                logger.error(f"释放锁失败: {e}")
    
    def acquire_lock(self, key: str, timeout: int = 30) -> Optional[str]:
        """
        尝试获取锁（非阻塞）
        
        Args:
            key: 锁的键名
            timeout: 锁的过期时间（秒）
        
        Returns:
            锁的唯一标识符，获取失败返回None
        """
        lock_id = str(uuid.uuid4())
        lock_key = f"lock:{key}"
        
        try:
            if self.redis.set(lock_key, lock_id, nx=True, ex=timeout):
                logger.debug(f"获取锁成功: {lock_key}")
                return lock_id
        except Exception as e:
            logger.error(f"获取锁失败: {e}")
        
        return None
    
    def release_lock(self, key: str, lock_id: str) -> bool:
        """
        释放锁（原子性操作）
        
        Args:
            key: 锁的键名
            lock_id: 锁的唯一标识符
        
        Returns:
            是否释放成功
        """
        lock_key = f"lock:{key}"
        
        try:
            result = self.redis.eval(self.unlock_script, 1, lock_key, lock_id)
            if result:
                logger.debug(f"释放锁成功: {lock_key}")
                return True
        except Exception as e:
            logger.error(f"释放锁失败: {e}")
        
        return False


class RedisOptimisticLock:
    """Redis 乐观锁实现 - 用于座位库存检查"""
    
    def __init__(self, redis_client: redis.Redis):
        """
        初始化乐观锁
        
        Args:
            redis_client: Redis客户端实例
        """
        self.redis = redis_client
        # Lua脚本：乐观锁CAS操作（Compare And Swap）
        self.cas_script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('set', KEYS[1], ARGV[2])
            else
                return nil
            end
        """
    
    def get_version(self, key: str) -> Tuple[Optional[str], Optional[str]]:
        """
        获取键的值和版本号
        
        Args:
            key: 数据键名
        
        Returns:
            (值, 版本号)
        """
        try:
            data_key = f"data:{key}"
            version_key = f"version:{key}"
            
            value = self.redis.get(data_key)
            version = self.redis.get(version_key)
            
            if version is None:
                # 首次访问，初始化版本号为1
                version = "1"
                self.redis.set(version_key, version, ex=3600)
            
            return value, version
        except Exception as e:
            logger.error(f"获取版本号失败: {e}")
            return None, None
    
    def compare_and_swap(self, key: str, old_version: str, new_value: str) -> bool:
        """
        原子性的比较并交换
        
        Args:
            key: 数据键名
            old_version: 预期的版本号
            new_value: 新值
        
        Returns:
            是否更新成功
        """
        try:
            version_key = f"version:{key}"
            data_key = f"data:{key}"
            
            # 新版本号 = 旧版本号 + 1
            new_version = str(int(old_version) + 1)
            
            # 使用Lua脚本原子性地检查版本号并更新
            result = self.redis.eval(
                self.cas_script,
                1,
                version_key,
                old_version,
                new_version
            )
            
            if result is not None:
                # 同时更新数据
                self.redis.set(data_key, new_value, ex=86400)
                logger.info(f"乐观锁更新成功: {key}, 版本: {old_version} -> {new_version}")
                return True
        except Exception as e:
            logger.error(f"乐观锁CAS操作失败: {e}")
        
        return False


class ReservationLuaScript:
    """预约系统 Lua 脚本 - 防止座位超卖"""
    
    # Lua脚本：原子性地减少座位库存并记录预约
    # 防止多个线程同时预约同一座位
    RESERVE_SEAT_SCRIPT = """
        local seat_key = KEYS[1]  -- 座位库存键
        local reservation_key = KEYS[2]  -- 预约记录集合键

        local current_stock = redis.call('get', seat_key)

        -- 懒加载初始化库存：如果键不存在，默认座位初始库存为1
        if not current_stock then
            current_stock = 1
            -- 设置库存并给一个24小时过期时间，防止内存泄漏
            redis.call('set', seat_key, 1, 'EX', 86400)
        end

        -- 检查库存是否充足
        if tonumber(current_stock) <= 0 then
            return {0, "座位已满"}
        end
        
        -- 检查用户是否已预约此座位（防止重复预约）
        local user_reservation = ARGV[1]  -- 用户:座位ID组合
        if redis.call('sismember', reservation_key, user_reservation) == 1 then
            return {0, "用户已预约此座位"}
        end
        
        -- 原子性地减少库存
        redis.call('decr', seat_key)
        
        -- 添加预约记录
        redis.call('sadd', reservation_key, user_reservation)
        redis.call('expire', reservation_key, ARGV[2])  -- 设置过期时间
        
        -- 返回成功，新库存
        return {1, tonumber(current_stock) - 1}
    """
    
    # Lua脚本：原子性地增加座位库存（取消预约）
    CANCEL_RESERVATION_SCRIPT = """
        local seat_key = KEYS[1]
        local reservation_key = KEYS[2]
        local user_reservation = ARGV[1]
        
        -- 检查预约是否存在
        if redis.call('sismember', reservation_key, user_reservation) == 0 then
            return {0, "预约记录不存在"}
        end
        
        -- 原子性地增加库存
        redis.call('incr', seat_key)
        
        -- 移除预约记录
        redis.call('srem', reservation_key, user_reservation)
        
        local current_stock = redis.call('get', seat_key)
        return {1, tonumber(current_stock)}
    """
    
    @staticmethod
    def reserve_seat(redis_client: redis.Redis, seat_id: int, user_id: int, 
                    date: str, time_slot: str) -> Tuple[bool, str, Optional[int]]:
        """
        使用Lua脚本原子性地预约座位
        
        Args:
            redis_client: Redis客户端
            seat_id: 座位ID
            user_id: 用户ID
            date: 预约日期
            time_slot: 时间段
        
        Returns:
            (是否成功, 消息, 新库存)
        """
        try:
            seat_key = f"seat:stock:{date}:{time_slot}:{seat_id}"
            reservation_key = f"seats:reserved:{date}:{time_slot}"
            user_reservation = f"{user_id}:{seat_id}"
            
            result = redis_client.eval(
                ReservationLuaScript.RESERVE_SEAT_SCRIPT,
                2,
                seat_key,
                reservation_key,
                user_reservation,
                3600  # 预约过期时间（秒）
            )
            
            success = result[0] == 1
            message = result[1]
            stock = result[2] if len(result) > 2 else None
            
            if success:
                logger.info(f"座位预约成功: 用户ID={user_id}, 座位ID={seat_id}, 剩余库存={stock}")
            else:
                logger.warning(f"座位预约失败: {message}")
            
            return success, message, stock
        except Exception as e:
            logger.error(f"Lua脚本执行失败: {e}")
            return False, f"系统错误: {str(e)}", None
    
    @staticmethod
    def cancel_reservation(redis_client: redis.Redis, seat_id: int, user_id: int,
                          date: str, time_slot: str) -> Tuple[bool, str, Optional[int]]:
        """
        使用Lua脚本原子性地取消预约
        
        Args:
            redis_client: Redis客户端
            seat_id: 座位ID
            user_id: 用户ID
            date: 预约日期
            time_slot: 时间段
        
        Returns:
            (是否成功, 消息, 新库存)
        """
        try:
            seat_key = f"seat:stock:{date}:{time_slot}:{seat_id}"
            reservation_key = f"seats:reserved:{date}:{time_slot}"
            user_reservation = f"{user_id}:{seat_id}"
            
            result = redis_client.eval(
                ReservationLuaScript.CANCEL_RESERVATION_SCRIPT,
                2,
                seat_key,
                reservation_key,
                user_reservation
            )
            
            success = result[0] == 1
            message = result[1]
            stock = result[2] if len(result) > 2 else None
            
            if success:
                logger.info(f"预约取消成功: 用户ID={user_id}, 座位ID={seat_id}")
            else:
                logger.warning(f"预约取消失败: {message}")
            
            return success, message, stock
        except Exception as e:
            logger.error(f"Lua脚本执行失败: {e}")
            return False, f"系统错误: {str(e)}", None


class ReservationQueue:
    """预约队列管理 - 处理高并发排队"""
    
    def __init__(self, redis_client: redis.Redis):
        """初始化队列管理器"""
        self.redis = redis_client
    
    def add_to_queue(self, room_id: int, date: str, time_slot: str,
                     user_id: int, queue_position: Optional[int] = None) -> int:
        """
        添加用户到预约队列
        
        Args:
            room_id: 阅览室ID
            date: 预约日期
            time_slot: 时间段
            user_id: 用户ID
            queue_position: 优先级（可选，用于VIP用户）
        
        Returns:
            队列位置
        """
        try:
            queue_key = f"queue:reservation:{room_id}:{date}:{time_slot}"
            position = queue_position or time.time()
            
            self.redis.zadd(queue_key, {str(user_id): position})
            self.redis.expire(queue_key, 3600)
            
            # 获取当前排队位置
            rank = self.redis.zrank(queue_key, str(user_id))
            logger.info(f"用户加入预约队列: 用户ID={user_id}, 位置={rank + 1}")
            
            return rank + 1 if rank is not None else 0
        except Exception as e:
            logger.error(f"添加队列失败: {e}")
            return -1
    
    def get_queue_position(self, room_id: int, date: str, time_slot: str,
                          user_id: int) -> Optional[int]:
        """
        获取用户在队列中的位置
        
        Args:
            room_id: 阅览室ID
            date: 预约日期
            time_slot: 时间段
            user_id: 用户ID
        
        Returns:
            队列位置（1-based），如果不在队列中则返回None
        """
        try:
            queue_key = f"queue:reservation:{room_id}:{date}:{time_slot}"
            rank = self.redis.zrank(queue_key, str(user_id))
            return rank + 1 if rank is not None else None
        except Exception as e:
            logger.error(f"获取队列位置失败: {e}")
            return None
    
    def remove_from_queue(self, room_id: int, date: str, time_slot: str,
                         user_id: int) -> bool:
        """
        从队列中移除用户
        
        Args:
            room_id: 阅览室ID
            date: 预约日期
            time_slot: 时间段
            user_id: 用户ID
        
        Returns:
            是否移除成功
        """
        try:
            queue_key = f"queue:reservation:{room_id}:{date}:{time_slot}"
            result = self.redis.zrem(queue_key, str(user_id))
            return result > 0
        except Exception as e:
            logger.error(f"移除队列失败: {e}")
            return False

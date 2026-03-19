-- ========================================
-- 高校图书馆座位预约系统 - 数据库初始化脚本
-- ========================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `library_seat_booking`
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

USE `library_seat_booking`;

-- ========================================
-- 1. 用户表（users）
-- ========================================
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  `student_id` VARCHAR(20) UNIQUE NOT NULL COMMENT '学号',
  `name` VARCHAR(100) NOT NULL COMMENT '用户姓名',
  `phone` VARCHAR(11) COMMENT '手机号',
  `school` VARCHAR(100) COMMENT '所属学院',
  `major` VARCHAR(100) COMMENT '专业',
  `wechat_openid` VARCHAR(100) UNIQUE NOT NULL COMMENT '微信小程序openid',
  `credit_score` INT DEFAULT 100 COMMENT '信用积分（初始100分）',
  `total_violations` INT DEFAULT 0 COMMENT '总违规次数',
  `is_banned` TINYINT DEFAULT 0 COMMENT '是否被禁用（0=正常，1=禁用）',
  `banned_until` DATETIME COMMENT '封禁截止时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  KEY `idx_student_id` (`student_id`),
  KEY `idx_wechat_openid` (`wechat_openid`),
  KEY `idx_credit_score` (`credit_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';


-- ========================================
-- 2. 阅览室表（reading_rooms）
-- ========================================
CREATE TABLE IF NOT EXISTS `reading_rooms` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '阅览室ID',
  `room_code` VARCHAR(50) UNIQUE NOT NULL COMMENT '阅览室编码（如：A101）',
  `room_name` VARCHAR(100) NOT NULL COMMENT '阅览室名称',
  `total_seats` INT NOT NULL COMMENT '总座位数',
  `floor` INT COMMENT '楼层',
  `location` VARCHAR(200) COMMENT '具体位置描述',
  `open_time` TIME NOT NULL COMMENT '开放开始时间',
  `close_time` TIME NOT NULL COMMENT '关闭结束时间',
  `image_url` VARCHAR(255) COMMENT '阅览室示意图URL',
  `is_active` TINYINT DEFAULT 1 COMMENT '是否启用（0=禁用，1=启用）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_room_code` (`room_code`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='阅览室表';


-- ========================================
-- 3. 座位表（seats）
-- ========================================
CREATE TABLE IF NOT EXISTS `seats` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '座位ID',
  `room_id` INT NOT NULL COMMENT '阅览室ID',
  `seat_code` VARCHAR(50) NOT NULL COMMENT '座位编号（如：A-001）',
  `seat_row` VARCHAR(10) COMMENT '行（如：A、B、C）',
  `seat_col` INT COMMENT '列（如：1、2、3）',
  `x_coordinate` DECIMAL(10, 2) COMMENT '座位在热力图中的X坐标',
  `y_coordinate` DECIMAL(10, 2) COMMENT '座位在热力图中的Y坐标',
  `seat_type` ENUM('regular', 'window', 'quiet') DEFAULT 'regular' COMMENT '座位类型（普通、靠窗、安静区）',
  `is_active` TINYINT DEFAULT 1 COMMENT '是否启用（0=停用，1=启用）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY `uk_room_seat` (`room_id`, `seat_code`),
  KEY `idx_room_id` (`room_id`),
  KEY `idx_seat_type` (`seat_type`),
  CONSTRAINT `fk_seats_room_id` FOREIGN KEY (`room_id`) REFERENCES `reading_rooms` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='座位表';


-- ========================================
-- 4. 预约记录表（reservations）
-- ========================================
CREATE TABLE IF NOT EXISTS `reservations` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '预约ID',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `seat_id` INT NOT NULL COMMENT '座位ID',
  `room_id` INT NOT NULL COMMENT '阅览室ID',
  `reserve_date` DATE NOT NULL COMMENT '预约日期',
  `start_time` TIME NOT NULL COMMENT '开始时间',
  `end_time` TIME NOT NULL COMMENT '结束时间',
  `status` ENUM('pending', 'active', 'completed', 'cancelled', 'no_show') DEFAULT 'pending' COMMENT '状态（待确认、进行中、已完成、已取消、未签到）',
  `check_in_time` DATETIME COMMENT '签到时间',
  `check_out_time` DATETIME COMMENT '退座时间',
  `is_violation` TINYINT DEFAULT 0 COMMENT '是否违规（0=否，1=是：未签到）',
  `violation_reason` VARCHAR(255) COMMENT '违规原因描述',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  KEY `idx_user_id` (`user_id`),
  KEY `idx_seat_id` (`seat_id`),
  KEY `idx_room_id` (`room_id`),
  KEY `idx_reserve_date` (`reserve_date`),
  KEY `idx_status` (`status`),
  KEY `idx_user_date` (`user_id`, `reserve_date`),
  KEY `idx_seat_date` (`seat_id`, `reserve_date`),
  CONSTRAINT `fk_reservations_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reservations_seat_id` FOREIGN KEY (`seat_id`) REFERENCES `seats` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reservations_room_id` FOREIGN KEY (`room_id`) REFERENCES `reading_rooms` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预约记录表';


-- ========================================
-- 5. 信用积分流水表（credit_logs）
-- ========================================
CREATE TABLE IF NOT EXISTS `credit_logs` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '流水ID',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `operation_type` ENUM('deduction', 'recovery', 'manual_adjust') DEFAULT 'deduction' COMMENT '操作类型（扣分、恢复、手动调整）',
  `points_change` INT NOT NULL COMMENT '积分变化值（负数表示扣分）',
  `reason` VARCHAR(255) NOT NULL COMMENT '原因描述',
  `related_reservation_id` INT COMMENT '关联的预约ID',
  `balance_after` INT NOT NULL COMMENT '操作后的信用积分余额',
  `operator` VARCHAR(100) COMMENT '操作者（系统或管理员）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_operation_type` (`operation_type`),
  CONSTRAINT `fk_credit_logs_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='信用积分流水表';


-- ========================================
-- 6. 座位实时状态表（seat_status）
-- ========================================
CREATE TABLE IF NOT EXISTS `seat_status` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `seat_id` INT NOT NULL COMMENT '座位ID',
  `room_id` INT NOT NULL COMMENT '阅览室ID',
  `current_status` ENUM('free', 'reserved', 'occupied', 'occupied_pending') DEFAULT 'free' COMMENT '座位状态（空闲、已预约、被占用、被占用待确认）',
  `last_reservation_id` INT COMMENT '最后一条预约记录ID',
  `status_changed_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '状态最后更改时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_seat_id` (`seat_id`),
  KEY `idx_room_id` (`room_id`),
  KEY `idx_current_status` (`current_status`),
  CONSTRAINT `fk_seat_status_seat_id` FOREIGN KEY (`seat_id`) REFERENCES `seats` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='座位实时状态表';


-- ========================================
-- 7. 数据看板统计表（dashboard_stats）
-- ========================================
CREATE TABLE IF NOT EXISTS `dashboard_stats` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
  `stat_date` DATE NOT NULL COMMENT '统计日期',
  `stat_type` VARCHAR(50) NOT NULL COMMENT '统计类型（daily_total、hourly_peak等）',
  `room_id` INT COMMENT '阅览室ID（为NULL时表示全校数据）',
  `total_reservations` INT DEFAULT 0 COMMENT '总预约数',
  `completed_reservations` INT DEFAULT 0 COMMENT '已完成预约数',
  `cancelled_reservations` INT DEFAULT 0 COMMENT '已取消预约数',
  `violation_count` INT DEFAULT 0 COMMENT '违规次数',
  `occupancy_rate` DECIMAL(5, 2) COMMENT '座位占用率（百分比）',
  `peak_hour` INT COMMENT '高峰时段小时数',
  `peak_hour_occupancy` DECIMAL(5, 2) COMMENT '高峰时段占用率',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY `uk_stat_date_type` (`stat_date`, `stat_type`, `room_id`),
  KEY `idx_stat_date` (`stat_date`),
  KEY `idx_room_id` (`room_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据看板统计表';


-- ========================================
-- 8. 建立复合索引优化查询性能
-- ========================================

-- 预约表：查询用户在某日是否已有预约
ALTER TABLE `reservations` ADD UNIQUE KEY `uk_user_date_status` (`user_id`, `reserve_date`, `status`);

-- 预约表：查询座位在某时段的预约情况
ALTER TABLE `reservations` ADD KEY `idx_seat_date_time` (`seat_id`, `reserve_date`, `start_time`, `end_time`);


-- ========================================
-- 9. 初始化示例数据（可选）
-- ========================================

-- 插入示例阅览室
INSERT INTO `reading_rooms` (
  `room_code`, `room_name`, `total_seats`, `floor`, `location`, `open_time`, `close_time`, `is_active`
) VALUES
('A101', '主阅览室A区', 100, 1, '图书馆一楼西侧', '06:00:00', '22:00:00', 1),
('A102', '主阅览室B区', 100, 1, '图书馆一楼东侧', '06:00:00', '22:00:00', 1),
('B201', '二楼自习室1', 50, 2, '图书馆二楼', '07:00:00', '23:00:00', 1),
('C301', '安静区-三楼', 80, 3, '图书馆三楼', '08:00:00', '22:00:00', 1);

-- 插入示例座位（仅为A101阅览室插入前10个座位）
-- 实际生产中这里应该由管理系统批量导入
INSERT INTO `seats` (
  `room_id`, `seat_code`, `seat_row`, `seat_col`, `x_coordinate`, `y_coordinate`, `seat_type`, `is_active`
) SELECT 
  r.id, 
  CONCAT('A-', LPAD(n + (a.row_num - 1) * 10, 3, '0')),
  CHAR(64 + a.row_num),
  n,
  10 + (n - 1) * 3,
  10 + (a.row_num - 1) * 2.5,
  IF(n BETWEEN 8 AND 10, 'window', IF(a.row_num = 1, 'quiet', 'regular')),
  1
FROM reading_rooms r
CROSS JOIN (
  SELECT 1 as seat_type 
  UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
) a
CROSS JOIN (
  SELECT 1 as row_num UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
) b
CROSS JOIN (SELECT @n := 0) init, (SELECT @n := @n + 1 as n FROM (
  SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
) nm) seq
WHERE r.room_code = 'A101'
LIMIT 100;

-- 初始化座位状态
INSERT INTO `seat_status` (`seat_id`, `room_id`, `current_status`, `status_changed_at`)
SELECT s.id, s.room_id, 'free', NOW()
FROM seats s;


-- ========================================
-- 10. 创建视图（用于常用查询）
-- ========================================

-- 视图：用户预约详情
CREATE OR REPLACE VIEW `v_user_reservations` AS
SELECT 
  r.id as reservation_id,
  u.student_id,
  u.name,
  room.room_name,
  s.seat_code,
  r.reserve_date,
  r.start_time,
  r.end_time,
  r.status,
  r.check_in_time,
  r.check_out_time,
  r.is_violation,
  r.created_at
FROM reservations r
JOIN users u ON r.user_id = u.id
JOIN reading_rooms room ON r.room_id = room.id
JOIN seats s ON r.seat_id = s.id
ORDER BY r.reserve_date DESC, r.start_time DESC;

-- 视图：阅览室座位占用情况
CREATE OR REPLACE VIEW `v_room_occupancy` AS
SELECT 
  r.id as room_id,
  r.room_name,
  r.total_seats,
  COUNT(CASE WHEN ss.current_status = 'free' THEN 1 END) as free_seats,
  COUNT(CASE WHEN ss.current_status = 'reserved' THEN 1 END) as reserved_seats,
  COUNT(CASE WHEN ss.current_status = 'occupied' THEN 1 END) as occupied_seats,
  ROUND(
    (COUNT(CASE WHEN ss.current_status IN ('reserved', 'occupied') THEN 1 END) * 100.0 / r.total_seats),
    2
  ) as occupancy_rate_percent
FROM reading_rooms r
LEFT JOIN seats s ON r.id = s.room_id
LEFT JOIN seat_status ss ON s.id = ss.seat_id
WHERE r.is_active = 1
GROUP BY r.id, r.room_name, r.total_seats;

-- 视图：用户信用积分历史
CREATE OR REPLACE VIEW `v_user_credit_history` AS
SELECT 
  u.student_id,
  u.name,
  u.credit_score as current_score,
  cl.operation_type,
  cl.points_change,
  cl.reason,
  cl.balance_after,
  cl.created_at
FROM users u
LEFT JOIN credit_logs cl ON u.id = cl.user_id
ORDER BY u.student_id, cl.created_at DESC;


-- ========================================
-- 11. 创建存储过程（高效的操作）
-- ========================================

-- 存储过程：创建用户信用积分流水
DELIMITER $$

CREATE PROCEDURE `sp_record_credit_change` (
  IN p_user_id INT,
  IN p_operation_type VARCHAR(50),
  IN p_points_change INT,
  IN p_reason VARCHAR(255),
  IN p_reservation_id INT,
  IN p_operator VARCHAR(100),
  OUT p_result INT
)
BEGIN
  DECLARE v_current_score INT;
  DECLARE v_new_score INT;
  
  -- 开启事务
  START TRANSACTION;
  
  BEGIN
    -- 获取用户当前信用积分
    SELECT credit_score INTO v_current_score 
    FROM users 
    WHERE id = p_user_id 
    FOR UPDATE;
    
    -- 计算新的积分
    SET v_new_score = v_current_score + p_points_change;
    
    -- 检查最低积分（不能低于0）
    IF v_new_score < 0 THEN
      SET v_new_score = 0;
    END IF;
    
    -- 更新用户积分
    UPDATE users 
    SET credit_score = v_new_score,
        total_violations = CASE WHEN p_operation_type = 'deduction' THEN total_violations + 1 ELSE total_violations END
    WHERE id = p_user_id;
    
    -- 插入信用积分流水记录
    INSERT INTO credit_logs (
      user_id, operation_type, points_change, reason, 
      related_reservation_id, balance_after, operator
    ) VALUES (
      p_user_id, p_operation_type, p_points_change, p_reason,
      p_reservation_id, v_new_score, p_operator
    );
    
    -- 如果扣分后积分过低，自动禁用用户
    IF v_new_score < 20 THEN
      UPDATE users 
      SET is_banned = 1, banned_until = DATE_ADD(NOW(), INTERVAL 30 DAY)
      WHERE id = p_user_id;
    END IF;
    
    COMMIT;
    SET p_result = 1;  -- 成功
    
  END;
  
END$$

DELIMITER ;


-- 存储过程：标记违规预约
DELIMITER $$

CREATE PROCEDURE `sp_mark_violation` (
  IN p_reservation_id INT,
  IN p_reason VARCHAR(255)
)
BEGIN
  DECLARE v_user_id INT;
  
  START TRANSACTION;
  
  BEGIN
    -- 获取预约对应的用户
    SELECT user_id INTO v_user_id 
    FROM reservations 
    WHERE id = p_reservation_id;
    
    -- 更新预约记录为违规
    UPDATE reservations 
    SET is_violation = 1, 
        violation_reason = p_reason,
        status = 'no_show'
    WHERE id = p_reservation_id;
    
    -- 记录信用积分变化（扣10分）
    CALL sp_record_credit_change(
      v_user_id,
      'deduction',
      -10,
      p_reason,
      p_reservation_id,
      'System',
      @result
    );
    
    COMMIT;
    
  END;
  
END$$

DELIMITER ;


-- ========================================
-- 12. 创建触发器（自动化操作）
-- ========================================

-- 触发器：座位状态变更时更新时间戳
DELIMITER $$

CREATE TRIGGER `trg_seat_status_update` 
AFTER UPDATE ON `seat_status`
FOR EACH ROW
BEGIN
  UPDATE seat_status 
  SET status_changed_at = NOW() 
  WHERE id = NEW.id AND NEW.current_status != OLD.current_status;
END$$

DELIMITER ;

-- 触发器：插入预约时检查座位是否冲突
DELIMITER $$

CREATE TRIGGER `trg_check_reservation_conflict` 
BEFORE INSERT ON `reservations`
FOR EACH ROW
BEGIN
  DECLARE v_conflict_count INT;
  
  -- 检查是否已经存在相同座位、相同日期、时间重叠的预约
  SELECT COUNT(*) INTO v_conflict_count 
  FROM reservations 
  WHERE seat_id = NEW.seat_id 
    AND reserve_date = NEW.reserve_date
    AND status IN ('pending', 'active', 'completed')
    AND (
      (NEW.start_time < end_time AND NEW.end_time > start_time)
    );
  
  IF v_conflict_count > 0 THEN
    SIGNAL SQLSTATE '45000' 
    SET MESSAGE_TEXT = 'Seat reservation conflict: Time slot already booked';
  END IF;
END$$

DELIMITER ;


-- ========================================
-- 13. 权限管理（可选）
-- ========================================

-- 创建应用用户（生产环境应使用更强的密码）
-- 注意：删除 EXISTS 检查以简化，实际部署根据情况调整

CREATE USER IF NOT EXISTS 'lib_app'@'%' IDENTIFIED BY 'secure_password_123';
GRANT SELECT, INSERT, UPDATE ON library_seat_booking.* TO 'lib_app'@'%';

CREATE USER IF NOT EXISTS 'lib_admin'@'%' IDENTIFIED BY 'admin_password_456';
GRANT ALL PRIVILEGES ON library_seat_booking.* TO 'lib_admin'@'%';

FLUSH PRIVILEGES;


-- ========================================
-- 14. 输出完成信息
-- ========================================
SELECT '✅ 数据库初始化完成！' as status;
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'library_seat_booking' ORDER BY TABLE_NAME;

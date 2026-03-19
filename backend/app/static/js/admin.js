// 管理后台JavaScript

const API_BASE_URL = '/api/admin';
const ADMIN_TOKEN = 'admin_test_token';
let currentTab = 'dashboard';
let usersPagination = { page: 1, per_page: 20 };
let maintenancePagination = { page: 1, per_page: 20 };
let announcementsPagination = { page: 1, per_page: 20 };
let auditPagination = { page: 1, per_page: 50 };

// 实时更新定时器
let dutyDashboardRefreshTimer = null;
let roomOccupancyRefreshTimer = null;
const DUTY_DASHBOARD_REFRESH_INTERVAL = 5000; // 5秒刷新一次
const ROOM_OCCUPANCY_REFRESH_INTERVAL = 5000;  // 5秒刷新一次

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

function initApp() {
    // 更新当前时间
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    // 绑定选项卡切换
    document.querySelectorAll('[data-tab]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            switchTab(this.dataset.tab);
        });
    });

    // 加载数据看板
    loadDashboard();

    // 绑定过滤器事件
    document.getElementById('user-search').addEventListener('change', function() {
        usersPagination.page = 1;
        loadUsers();
    });

    document.getElementById('maintenance-status-filter').addEventListener('change', function() {
        maintenancePagination.page = 1;
        loadMaintenance();
    });

    document.getElementById('maintenance-severity-filter').addEventListener('change', function() {
        maintenancePagination.page = 1;
        loadMaintenance();
    });

    document.getElementById('audit-module-filter').addEventListener('change', function() {
        auditPagination.page = 1;
        loadAuditLogs();
    });

    document.getElementById('audit-status-filter').addEventListener('change', function() {
        auditPagination.page = 1;
        loadAuditLogs();
    });
}

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeString;
}

function switchTab(tabName) {
    currentTab = tabName;

    // 隐藏所有选项卡
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });

    // 显示选中的选项卡
    document.getElementById(tabName + '-tab').style.display = 'block';

    // 更新导航链接
    document.querySelectorAll('[data-tab]').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // 停止之前的定时器（如果有）
    if (dutyDashboardRefreshTimer) {
        clearInterval(dutyDashboardRefreshTimer);
        dutyDashboardRefreshTimer = null;
    }

    // 停止房间占用率定时器（仪表板切走时停止）
    if (tabName !== 'dashboard' && roomOccupancyRefreshTimer) {
        clearInterval(roomOccupancyRefreshTimer);
        roomOccupancyRefreshTimer = null;
    }

    // 加载相应的数据
    switch (tabName) {
        case 'dashboard':
            loadDashboard();
            // 加载并启动房间占用率实时更新
            loadRoomsOccupancy();
            if (!roomOccupancyRefreshTimer) {
                roomOccupancyRefreshTimer = setInterval(loadRoomsOccupancy, ROOM_OCCUPANCY_REFRESH_INTERVAL);
                console.log('✓ 已启动房间占用率实时更新（每5秒刷新一次）');
            }
            break;
        case 'duty':
            loadDutyDashboard();
            // 启动值班面板的实时更新
            dutyDashboardRefreshTimer = setInterval(loadDutyDashboard, DUTY_DASHBOARD_REFRESH_INTERVAL);
            console.log('✓ 已启动值班面板实时更新（每5秒刷新一次）');
            break;
        case 'users':
            loadUsers();
            break;
        case 'maintenance':
            loadMaintenance();
            break;
        case 'announcements':
            loadAnnouncements();
            break;
        case 'audit':
            loadAuditLogs();
            break;
    }
}

// ===== 数据看板 =====

function loadDashboard() {
    // 加载统计数据
    fetch(`${API_BASE_URL}/statistics/overview`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const stats = data.data;
                
                // 更新卡片数据
                document.getElementById('total-users').textContent = stats.users.total;
                document.getElementById('active-users').textContent = stats.users.active;
                document.getElementById('disabled-users').textContent = stats.users.disabled;
                
                document.getElementById('today-reservations').textContent = stats.today.total_reservations;
                document.getElementById('today-checked').textContent = stats.today.checked_in;
                document.getElementById('today-completed').textContent = stats.today.completed;
                
                document.getElementById('total-seats').textContent = stats.seats.total;
                document.getElementById('occupied-seats').textContent = stats.seats.occupied;
                document.getElementById('maintenance-seats').textContent = stats.seats.maintenance;
                
                document.getElementById('pending-maintenance').textContent = stats.maintenance.pending;
            }
        })
        .catch(e => console.error('加载统计数据失败:', e));

    // 加载最近日志
    loadRecentLogs();
    
    // 加载房间占用率
    loadRoomsOccupancy();
    
    // 如果在仪表板上，每10秒刷新一次数据
    if (currentTab === 'dashboard') {
        setTimeout(() => {
            if (currentTab === 'dashboard') {
                loadDashboard();
            }
        }, 10000);
    }
}

function loadRecentLogs() {
    fetch(`${API_BASE_URL}/audit-logs?page=1&per_page=10`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const logsHtml = data.data.map(log => `
                    <div class="log-item">
                        <div class="log-action">
                            <span class="badge badge-${log.status === 'success' ? 'success' : 'danger'}">
                                ${log.action === 'create' ? '创建' : log.action === 'update' ? '更新' : log.action === 'delete' ? '删除' : log.action}
                            </span>
                            ${log.description}
                        </div>
                        <div class="log-time">
                            ${new Date(log.created_at).toLocaleString('zh-CN')}
                            ${log.operator_name ? `by ${log.operator_name}` : ''}
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('recent-logs').innerHTML = logsHtml || '<p class="text-muted">暂无数据</p>';
            }
        })
        .catch(e => console.error('加载日志失败:', e));
}

// ===== 房间占用率 =====

function loadRoomsOccupancy() {
    fetch('/api/rooms/occupancy', {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 0 && data.data) {
                const rooms = data.data;
                const container = document.getElementById('rooms-occupancy-container');
                
                if (!container) {
                    console.error('找不到房间占用率容器');
                    return;
                }
                
                // 生成房间卡片HTML
                const roomsHtml = rooms.map(room => {
                    const occupancyRate = (room.occupancy_rate * 100).toFixed(0);
                    const occupancyPercent = room.occupancy_rate * 100;
                    
                    // 根据占用率确定状态和颜色
                    let statusText, statusClass, progressClass;
                    if (occupancyPercent >= 90) {
                        statusText = '已满';
                        statusClass = 'bg-danger';
                        progressClass = 'bg-danger';
                    } else if (occupancyPercent >= 70) {
                        statusText = '紧张';
                        statusClass = 'bg-warning';
                        progressClass = 'bg-warning';
                    } else if (occupancyPercent >= 50) {
                        statusText = '中等';
                        statusClass = 'bg-info';
                        progressClass = 'bg-info';
                    } else {
                        statusText = '充足';
                        statusClass = 'bg-success';
                        progressClass = 'bg-success';
                    }
                    
                    return `
                        <div class="col-md-6 col-lg-4 mb-3">
                            <div class="room-occupancy-card">
                                <div class="room-header">
                                    <h6 class="room-name">${room.room_name}</h6>
                                    <span class="badge ${statusClass}">${statusText}</span>
                                </div>
                                <div class="room-floor">
                                    <small class="text-muted">${room.floor}楼</small>
                                </div>
                                <div class="occupancy-rate mt-3 mb-2">
                                    <small class="d-flex justify-content-between align-items-center">
                                        <span>占用率</span>
                                        <strong>${occupancyRate}%</strong>
                                    </small>
                                    <div class="progress" style="height: 8px;">
                                        <div class="progress-bar ${progressClass}" role="progressbar" 
                                             style="width: ${occupancyPercent}%" 
                                             aria-valuenow="${occupancyPercent}" aria-valuemin="0" aria-valuemax="100">
                                        </div>
                                    </div>
                                </div>
                                <div class="room-stats mt-3">
                                    <div class="stat-item">
                                        <span class="stat-label">座位</span>
                                        <span class="stat-value">${room.occupied_seats}/${room.total_seats}</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-label">可用</span>
                                        <span class="stat-value text-success">${room.available_seats}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
                
                container.innerHTML = roomsHtml || '<p class="text-muted w-100">暂无房间数据</p>';
                
                // 更新时间戳
                const badge = document.getElementById('occupancy-update-badge');
                if (badge) {
                    const now = new Date();
                    badge.textContent = `最后更新: ${now.toLocaleTimeString('zh-CN', { 
                        hour: '2-digit', 
                        minute: '2-digit', 
                        second: '2-digit' 
                    })}`;
                    badge.classList.remove('bg-warning', 'bg-secondary');
                    badge.classList.add('bg-success');
                }
            }
        })
        .catch(e => {
            console.error('加载房间占用率失败:', e);
            const container = document.getElementById('rooms-occupancy-container');
            if (container) {
                container.innerHTML = '<p class="text-danger w-100">加载房间数据失败</p>';
            }
        });
}

// ===== 值班快查 =====

function loadDutyDashboard() {
    fetch(`${API_BASE_URL}/duty-dashboard`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const dashboard = data.data;
                const timestamp = new Date(data.timestamp);
                const timeStr = timestamp.toLocaleTimeString('zh-CN');
                
                const html = dashboard.map(room => `
                    <div class="col-md-4 mb-3">
                        <div class="duty-card">
                            <h5>${room.room_name} (${room.floor}楼)</h5>
                            <div class="duty-stat">
                                <label>总座位:</label>
                                <value>${room.total_seats}</value>
                            </div>
                            <div class="duty-stat">
                                <label>占用:</label>
                                <value>${room.occupied_seats}</value>
                            </div>
                            <div class="duty-stat">
                                <label>空闲:</label>
                                <value>${room.empty_seats}</value>
                            </div>
                            <div class="duty-stat">
                                <label>维修:</label>
                                <value>${room.maintenance_seats}</value>
                            </div>
                            <div class="duty-stat">
                                <label>占用率:</label>
                                <value>${room.occupancy_rate}%</value>
                            </div>
                            <button class="btn btn-sm btn-light" onclick="viewRoomDetails(${room.room_id})">
                                详细信息
                            </button>
                        </div>
                    </div>
                `).join('');
                
                // 在顶部显示更新时间
                const headerHtml = `
                    <div class="alert alert-info mb-3">
                        <i class="fas fa-sync-alt"></i> 数据最后更新于: <strong>${timeStr}</strong>
                        <span class="live-indicator" title="实时更新中"></span>
                    </div>
                `;
                
                document.getElementById('duty-dashboard').innerHTML = headerHtml + 
                    `<div class="row">${html}</div>`;
            }
        })
        .catch(e => console.error('加载值班面板失败:', e));
}

function viewRoomDetails(roomId) {
    fetch(`${API_BASE_URL}/duty-dashboard/room/${roomId}`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const { room, seats } = data.data;
                const seatGrid = seats.map(seat => {
                    let colorClass = 'bg-success';
                    if (seat.status === 1) colorClass = 'bg-warning';
                    else if (seat.status === 2) colorClass = 'bg-danger';
                    
                    return `
                        <div class="col-md-2 mb-2">
                            <div class="p-2 text-white text-center ${colorClass}" style="border-radius: 4px;">
                                <div class="small">${seat.seat_number}</div>
                                <div class="text-xs small">${seat.status_label}</div>
                                ${seat.user_name ? `<div class="text-xs">${seat.user_name}</div>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');

                alert(`
房间: ${room.name} (${room.floor}楼)

座位分布:
${seatGrid}
                `);
            }
        })
        .catch(e => console.error('加载房间详情失败:', e));
}

// ===== 用户管理 =====

function loadUsers() {
    const search = document.getElementById('user-search').value;
    const params = new URLSearchParams({
        page: usersPagination.page,
        per_page: usersPagination.per_page,
        status: -1,
        search: search
    });

    fetch(`${API_BASE_URL}/users?${params}`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const users = data.data;
                const html = users.map(user => `
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.nickname}</td>
                        <td>${user.phone}</td>
                        <td>${user.student_id}</td>
                        <td>${user.credit_score}</td>
                        <td>
                            <span class="status-indicator ${user.status === 1 ? 'status-active' : 'status-disabled'}"></span>
                            <span class="badge ${user.status === 1 ? 'badge-success' : 'badge-danger'}">
                                ${user.status_label}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="viewUserDetail(${user.id})">详情</button>
                            ${user.status === 1 ? 
                                `<button class="btn btn-sm btn-danger" onclick="disableUser(${user.id})">禁用</button>` :
                                `<button class="btn btn-sm btn-success" onclick="enableUser(${user.id})">启用</button>`
                            }
                            <button class="btn btn-sm btn-warning" onclick="forceCancelReservations(${user.id})">取消预约</button>
                        </td>
                    </tr>
                `).join('');

                document.getElementById('users-list').innerHTML = html;

                // 分页
                updatePagination(data.pagination, 'users-pagination', 'usersPagination', loadUsers);
            }
        })
        .catch(e => console.error('加载用户列表失败:', e));
}

function viewUserDetail(userId) {
    fetch(`${API_BASE_URL}/users/${userId}`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const user = data.data.user;
                const stats = data.data.statistics;
                alert(`
用户详情:
ID: ${user.id}
昵称: ${user.nickname}
电话: ${user.phone}
学号: ${user.student_id}
真名: ${user.real_name}
信用分: ${user.credit_score}
状态: ${user.status === 1 ? '正常' : '禁用'}

统计:
总预约: ${stats.total_reservations}
已完成: ${stats.completed_reservations}
已取消: ${stats.cancelled_reservations}
                `);
            }
        })
        .catch(e => console.error('加载用户详情失败:', e));
}

function disableUser(userId) {
    showUserActionModal('disable_user', userId, '禁用用户');
}

function enableUser(userId) {
    showUserActionModal('enable_user', userId, '启用用户');
}

function forceCancelReservations(userId) {
    showUserActionModal('force_cancel', userId, '强制取消预约');
}

function showUserActionModal(actionType, userId, title) {
    document.getElementById('userActionTitle').textContent = title;
    document.getElementById('actionUserId').value = userId;
    document.getElementById('actionType').value = actionType;
    document.getElementById('actionReason').value = '';
    const modal = new bootstrap.Modal(document.getElementById('userActionModal'));
    modal.show();
}

function submitUserAction() {
    const userId = document.getElementById('actionUserId').value;
    const actionType = document.getElementById('actionType').value;
    const reason = document.getElementById('actionReason').value;

    let endpoint = '';
    if (actionType === 'disable_user') {
        endpoint = `${API_BASE_URL}/users/${userId}/disable`;
    } else if (actionType === 'enable_user') {
        endpoint = `${API_BASE_URL}/users/${userId}/enable`;
    } else if (actionType === 'force_cancel') {
        endpoint = `${API_BASE_URL}/users/${userId}/cancel-reservations`;
    }

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'X-Admin-Token': ADMIN_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason: reason })
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                alert('操作成功!');
                bootstrap.Modal.getInstance(document.getElementById('userActionModal')).hide();
                loadUsers();
            } else {
                alert('操作失败: ' + data.message);
            }
        })
        .catch(e => console.error('操作失败:', e));
}

// ===== 座位维护 =====

function loadMaintenance() {
    const status = document.getElementById('maintenance-status-filter').value;
    const severity = document.getElementById('maintenance-severity-filter').value;
    
    const params = new URLSearchParams({
        page: maintenancePagination.page,
        per_page: maintenancePagination.per_page,
        status: status,
        severity: severity
    });

    fetch(`${API_BASE_URL}/seats/maintenance?${params}`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const maintenances = data.data;
                const html = maintenances.map(m => `
                    <tr>
                        <td>${m.seat_id}</td>
                        <td>${getIssueTypeLabel(m.issue_type)}</td>
                        <td>
                            <span class="badge ${getSeverityBadgeClass(m.severity)}">
                                ${getSeverityLabel(m.severity)}
                            </span>
                        </td>
                        <td>${m.description}</td>
                        <td>
                            <span class="badge ${getStatusBadgeClass(m.status)}">
                                ${getStatusLabel(m.status)}
                            </span>
                        </td>
                        <td>${m.reported_by_name || '-'}</td>
                        <td>
                            ${m.status === 'pending' || m.status === 'in_progress' ? 
                                `<button class="btn btn-sm btn-success" onclick="completeMaintenanceModal(${m.id})">完成</button>` : ''
                            }
                        </td>
                    </tr>
                `).join('');

                document.getElementById('maintenance-list').innerHTML = html;
                updatePagination(data.pagination, 'maintenance-pagination', 'maintenancePagination', loadMaintenance);
            }
        })
        .catch(e => console.error('加载维护列表失败:', e));
}

function showReportModal() {
    const modal = new bootstrap.Modal(document.getElementById('reportModal'));
    modal.show();
}

function submitReport() {
    const seatId = document.getElementById('reportSeatId').value;
    const issueType = document.getElementById('reportIssueType').value;
    const severity = document.getElementById('reportSeverity').value;
    const description = document.getElementById('reportDescription').value;

    if (!seatId || !issueType || !description) {
        alert('请填写所有必填字段');
        return;
    }

    fetch(`${API_BASE_URL}/seats/${seatId}/maintenance`, {
        method: 'POST',
        headers: {
            'X-Admin-Token': ADMIN_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            issue_type: issueType,
            severity: severity,
            description: description
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                alert('维护记录已创建');
                bootstrap.Modal.getInstance(document.getElementById('reportModal')).hide();
                loadMaintenance();
            } else {
                alert('创建失败: ' + data.message);
            }
        })
        .catch(e => console.error('创建维护记录失败:', e));
}

function completeMaintenanceModal(maintenanceId) {
    const notes = prompt('请输入维护备注:');
    if (notes !== null) {
        fetch(`${API_BASE_URL}/seats/maintenance/${maintenanceId}/complete`, {
            method: 'POST',
            headers: {
                'X-Admin-Token': ADMIN_TOKEN,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ notes: notes })
        })
            .then(r => r.json())
            .then(data => {
                if (data.code === 200) {
                    alert('维护已完成');
                    loadMaintenance();
                } else {
                    alert('操作失败: ' + data.message);
                }
            })
            .catch(e => console.error('完成维护失败:', e));
    }
}

// ===== 公告管理 =====

function loadAnnouncements() {
    const params = new URLSearchParams({
        page: announcementsPagination.page,
        per_page: announcementsPagination.per_page,
        status: -1
    });

    fetch(`${API_BASE_URL}/announcements?${params}`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const announcements = data.data;
                const html = announcements.map(a => `
                    <tr>
                        <td>${a.title}</td>
                        <td>${getAnnouncementTypeLabel(a.type)}</td>
                        <td>
                            <span class="badge ${getPriorityBadgeClass(a.priority)}">
                                ${getPriorityLabel(a.priority)}
                            </span>
                        </td>
                        <td>${a.author_name || 'System'}</td>
                        <td>${a.view_count}</td>
                        <td>
                            <span class="badge ${a.status === 1 ? 'badge-success' : 'badge-secondary'}">
                                ${a.status === 1 ? '已发布' : '已下架'}
                            </span>
                            ${a.is_pinned ? '<br><span class="badge badge-warning">置顶</span>' : ''}
                        </td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="editAnnouncement(${a.id})">编辑</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteAnnouncement(${a.id})">删除</button>
                        </td>
                    </tr>
                `).join('');

                document.getElementById('announcements-list').innerHTML = html;
                updatePagination(data.pagination, 'announcements-pagination', 'announcementsPagination', loadAnnouncements);
            }
        })
        .catch(e => console.error('加载公告失败:', e));
}

function showAnnouncementModal() {
    document.getElementById('announcementForm').reset();
    const modal = new bootstrap.Modal(document.getElementById('announcementModal'));
    modal.show();
}

function submitAnnouncement() {
    const title = document.getElementById('announcementTitle').value;
    const content = document.getElementById('announcementContent').value;
    const type = document.getElementById('announcementType').value;
    const priority = document.getElementById('announcementPriority').value;
    const isPinned = document.getElementById('announcementPinned').checked;

    if (!title || !content) {
        alert('请填写标题和内容');
        return;
    }

    fetch(`${API_BASE_URL}/announcements`, {
        method: 'POST',
        headers: {
            'X-Admin-Token': ADMIN_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: title,
            content: content,
            type: type,
            priority: parseInt(priority),
            is_pinned: isPinned
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                alert('公告已发布');
                bootstrap.Modal.getInstance(document.getElementById('announcementModal')).hide();
                loadAnnouncements();
            } else {
                alert('发布失败: ' + data.message);
            }
        })
        .catch(e => console.error('发布公告失败:', e));
}

function editAnnouncement(announcementId) {
    alert('编辑功能开发中...');
}

function deleteAnnouncement(announcementId) {
    if (confirm('确定要删除此公告吗?')) {
        fetch(`${API_BASE_URL}/announcements/${announcementId}`, {
            method: 'DELETE',
            headers: {
                'X-Admin-Token': ADMIN_TOKEN
            }
        })
            .then(r => r.json())
            .then(data => {
                if (data.code === 200) {
                    alert('公告已删除');
                    loadAnnouncements();
                } else {
                    alert('删除失败: ' + data.message);
                }
            })
            .catch(e => console.error('删除公告失败:', e));
    }
}

// ===== 审计日志 =====

function loadAuditLogs() {
    const module = document.getElementById('audit-module-filter').value;
    const status = document.getElementById('audit-status-filter').value;

    const params = new URLSearchParams({
        page: auditPagination.page,
        per_page: auditPagination.per_page,
        module: module,
        status: status
    });

    fetch(`${API_BASE_URL}/audit-logs?${params}`, {
        headers: {
            'X-Admin-Token': ADMIN_TOKEN
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.code === 200) {
                const logs = data.data;
                const html = logs.map(log => `
                    <tr>
                        <td>${new Date(log.created_at).toLocaleString('zh-CN')}</td>
                        <td>${log.operator_name || 'System'}</td>
                        <td>
                            <span class="badge ${getActionBadgeClass(log.action)}">
                                ${getActionLabel(log.action)}
                            </span>
                        </td>
                        <td>${log.module}</td>
                        <td>${log.resource_type} #${log.resource_id || '-'}</td>
                        <td>${log.description}</td>
                        <td>
                            <span class="badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}">
                                ${log.status === 'success' ? '成功' : '失败'}
                            </span>
                        </td>
                    </tr>
                `).join('');

                document.getElementById('audit-list').innerHTML = html;
                updatePagination(data.pagination, 'audit-pagination', 'auditPagination', loadAuditLogs);
            }
        })
        .catch(e => console.error('加载审计日志失败:', e));
}

// ===== 工具函数 =====

function updatePagination(pagination, elementId, paginationObjName, loadFunction) {
    const { total, page, per_page, pages } = pagination;
    const html = [];

    if (page > 1) {
        html.push(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage('${paginationObjName}', 1, ${loadFunction.name}); return false;">
                    首页
                </a>
            </li>
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage('${paginationObjName}', ${page - 1}, ${loadFunction.name}); return false;">
                    上一页
                </a>
            </li>
        `);
    }

    html.push(`<li class="page-item disabled"><span class="page-link">${page} / ${pages}</span></li>`);

    if (page < pages) {
        html.push(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage('${paginationObjName}', ${page + 1}, ${loadFunction.name}); return false;">
                    下一页
                </a>
            </li>
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage('${paginationObjName}', ${pages}, ${loadFunction.name}); return false;">
                    末页
                </a>
            </li>
        `);
    }

    document.getElementById(elementId).innerHTML = '<nav><ul class="pagination">' + html.join('') + '</ul></nav>';
}

function changePage(objName, page, loadFunction) {
    window[objName].page = page;
    loadFunction();
}

function getIssueTypeLabel(type) {
    const map = {
        'broken': '破坏',
        'dirty': '脏污',
        'furniture': '家具问题',
        'electrical': '电气问题',
        'other': '其他'
    };
    return map[type] || type;
}

function getSeverityLabel(severity) {
    const map = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'critical': '严重'
    };
    return map[severity] || severity;
}

function getSeverityBadgeClass(severity) {
    const map = {
        'low': 'badge-info',
        'medium': 'badge-warning',
        'high': 'badge-danger',
        'critical': 'badge-danger'
    };
    return map[severity] || 'badge-secondary';
}

function getStatusLabel(status) {
    const map = {
        'pending': '待处理',
        'in_progress': '处理中',
        'completed': '已完成',
        'cancelled': '已取消'
    };
    return map[status] || status;
}

function getStatusBadgeClass(status) {
    const map = {
        'pending': 'badge-warning',
        'in_progress': 'badge-info',
        'completed': 'badge-success',
        'cancelled': 'badge-secondary'
    };
    return map[status] || 'badge-secondary';
}

function getAnnouncementTypeLabel(type) {
    const map = {
        'general': '一般',
        'maintenance': '维护',
        'emergency': '紧急'
    };
    return map[type] || type;
}

function getPriorityLabel(priority) {
    const map = {
        0: '低',
        1: '中',
        2: '高'
    };
    return map[priority] || '中';
}

function getPriorityBadgeClass(priority) {
    const map = {
        0: 'badge-info',
        1: 'badge-warning',
        2: 'badge-danger'
    };
    return map[priority] || 'badge-secondary';
}

function getActionLabel(action) {
    const map = {
        'create': '创建',
        'update': '更新',
        'delete': '删除',
        'enable': '启用',
        'disable': '禁用',
        'force_cancel': '强制取消'
    };
    return map[action] || action;
}

function getActionBadgeClass(action) {
    const map = {
        'create': 'badge-success',
        'update': 'badge-info',
        'delete': 'badge-danger',
        'enable': 'badge-success',
        'disable': 'badge-warning',
        'force_cancel': 'badge-danger'
    };
    return map[action] || 'badge-secondary';
}

function logout() {
    if (confirm('确定要退出吗?')) {
        window.location.href = '/';
    }
}

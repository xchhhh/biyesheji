const api = require('../../utils/api');
const config = require('../../utils/config');

Page({
  data: {
    userInfo: null,
    hasUserInfo: false,
    reservations: [],
    activeTab: 0,  // 0=当前预约, 1=历史预约
    isLoading: false
  },

  onLoad() {
    this.getUserInfo();
    
    // ✅ 优化: 先显示缓存预约
    this.loadCachedReservations();
    
    // ✅ 后台加载最新预约
    this.loadReservations();
    
    this.isFirstLoad = true;
  },

  onShow() {
    // 每次显示页面时重新检查登录状态
    this.getUserInfo();
    
    // 检查是否需要刷新预约列表（从座位预约页面返回时）
    const needRefresh = wx.getStorageSync('need_refresh_reservations');
    if (needRefresh) {
      console.log('[my.js] 检测到需要刷新，重新加载预约列表');
      wx.removeStorageSync('need_refresh_reservations');
      this.loadReservations();
    } else if (!this.isFirstLoad) {
      // 第二次进入此页面时，使用缓存优先策略
      console.log('[my.js] 使用缓存预约数据');
      this.loadCachedReservations();
      // 后台更新
      this.loadReservations();
    }
  },

  /**
   * ✅ 优化: 从缓存快速加载预约
   */
  loadCachedReservations() {
    const cachedReservations = wx.getStorageSync('cached_reservations');
    if (cachedReservations && cachedReservations.length > 0) {
      console.log('[my.js] 从缓存加载预约数据，共', cachedReservations.length, '条');
      
      // 为每个预约添加状态显示字段
      const reservations = cachedReservations.map(r => ({
        ...r,
        statusText: this.getStatusText(r.status),
        statusColor: this.getStatusColor(r.status)
      }));
      
      // 整理数据
      const currentReservations = reservations.filter(r => r.status === 0 || r.status === 1);
      const historyReservations = reservations.filter(r => r.status === 2 || r.status === 3 || r.status === 4);
      const displayReservations = this.data.activeTab === 0 ? currentReservations : historyReservations;
      
      this.setData({
        reservations: displayReservations,
        isLoading: false
      });
      return true;
    }
    return false;
  },

  getUserInfo() {
    // 检查token是否存在（最可靠的登录判断）
    const token = wx.getStorageSync('auth_token');
    const phone = wx.getStorageSync('phone_number');
    
    console.log('[my.js] 检查登录状态 - token:', token ? '存在' : '不存在', 'phone:', phone);
    
    if (!token || !phone) {
      console.log('[my.js] 用户未登录');
      this.setData({ hasUserInfo: false });
      return;
    }

    // 构造用户信息对象
    const userInfo = {
      user_id: wx.getStorageSync('user_id') || 'N/A',
      phone_number: phone,
      real_name: wx.getStorageSync('real_name') || '用户',
      student_id: wx.getStorageSync('student_id') || 'N/A',
      created_at: new Date().toISOString(),
      createdDate: new Date().toISOString().split('T')[0],
      avatarChar: (wx.getStorageSync('real_name') || '用户').charAt(0)
    };
    
    console.log('[my.js] 用户已登录，信息:', userInfo);
    
    this.setData({
      userInfo,
      hasUserInfo: true
    });
  },

  // 加载预约列表 - 增强版，含网络状态检查和错误处理
  loadReservations() {
    const network = require('../../utils/network');
    this.setData({ isLoading: true });
    
    // 从后端API获取真实数据
    const token = wx.getStorageSync('auth_token');
    
    if (!token) {
      this.setData({ isLoading: false, reservations: [] });
      console.warn('[my.js] 用户未登录');
      return;
    }

    // 先检查网络连接
    network.getNetworkStatus().then(status => {
      if (!status.isOnline) {
        console.warn('[my.js] 网络未连接');
        this.setData({ isLoading: false });
        
        // 尝试使用缓存数据
        const cachedReservations = wx.getStorageSync('cached_reservations');
        if (cachedReservations) {
          this.setData({ 
            reservations: cachedReservations,
            isLoading: false 
          });
          wx.showToast({
            title: '显示缓存预约',
            icon: 'none',
            duration: 1500
          });
        } else {
          wx.showToast({
            title: '网络未连接，无缓存数据',
            icon: 'none',
            duration: 2000
          });
        }
        return;
      }

      // 调用后端API获取预约列表
      api.getMyReservations()
        .then(response => {
          console.log('[my.js] 获取预约列表响应:', response);
          
          // 处理标准化后的响应 - response已经是data内容
          let reservations = [];
          if (response.reservations && Array.isArray(response.reservations)) {
            // 如果是分页格式：{total, pages, page, per_page, reservations: [...]}
            reservations = response.reservations;
          }
          // 如果是直接数组
          else if (Array.isArray(response)) {
            reservations = response;
          }
          
          console.log('[my.js] 获取到预约数据:', reservations);
          
          // 为每个预约添加状态显示字段
          if (Array.isArray(reservations)) {
            reservations = reservations.map(r => ({
              ...r,
              statusText: this.getStatusText(r.status),
              statusColor: this.getStatusColor(r.status)
            }));
          }
          
          // 缓存预约数据
          wx.setStorageSync('cached_reservations', reservations);
          
          // 整理数据 - 根据当前activeTab选择要显示的数据
          let displayReservations = [];
          const currentReservations = reservations.filter(r => r.status === 0 || r.status === 1);
          const historyReservations = reservations.filter(r => r.status === 2 || r.status === 3 || r.status === 4);
          
          // 根据activeTab显示对应的预约列表
          displayReservations = this.data.activeTab === 0 ? currentReservations : historyReservations;
          
          console.log('[my.js] 当前预约:', currentReservations.length, '历史预约:', historyReservations.length, '显示tab:', this.data.activeTab, '显示预约:', displayReservations.length);
          
          this.setData({
            reservations: displayReservations,
            isLoading: false
          });
        })
        .catch(error => {
          console.error('[my.js] 获取预约列表失败:', error);
          this.setData({ isLoading: false });
          
          // 尝试使用缓存数据
          const cachedReservations = wx.getStorageSync('cached_reservations');
          if (cachedReservations) {
            let displayReservations = [];
            const currentReservations = cachedReservations.filter(r => r.status === 0 || r.status === 1);
            const historyReservations = cachedReservations.filter(r => r.status === 2 || r.status === 3 || r.status === 4);
            displayReservations = this.data.activeTab === 0 ? currentReservations : historyReservations;
            
            this.setData({ 
              reservations: displayReservations,
              isLoading: false 
            });
            wx.showToast({
              title: '显示缓存预约',
              icon: 'none',
              duration: 1500
            });
          } else {
            let errorMsg = error.message || '获取预约列表失败';
            if (error.tip) {
              errorMsg = error.tip;
            }
            wx.showToast({
              title: errorMsg,
              icon: 'error',
              duration: 2000
            });
          }
        });
    }).catch(error => {
      console.error('[my.js] 检查网络状态失败:', error);
      this.setData({ isLoading: false });
    });
  },

  // 获取状态文本
  getStatusText(status) {
    const statusMap = {
      0: '预约中',
      1: '已签到',
      2: '已完成',
      3: '已取消',
      4: '已迟到'
    };
    return statusMap[status] || '未知';
  },

  // 获取状态颜色
  getStatusColor(status) {
    const colorMap = {
      0: '#3c6fda',  // 蓝色 - 预约中
      1: '#52c41a',  // 绿色 - 已签到
      2: '#999999',  // 灰色 - 已完成
      3: '#ff4d4f',  // 红色 - 已取消
      4: '#ff7a45'   // 橙色 - 已迟到
    };
    return colorMap[status] || '#000000';
  },

  // 切换标签
  switchTab(e) {
    const index = parseInt(e.currentTarget.dataset.index);
    if (isNaN(index)) {
      console.error('Invalid tab index:', e.currentTarget.dataset.index);
      return;
    }
    
    this.setData({ activeTab: index }, () => {
      // setData回调中加载数据，确保activeTab已更新
      this.loadReservations();
    });
  },

  // 取消预约
  onCancelReservation(e) {
    const reservationId = e.currentTarget.dataset.id;
    const token = wx.getStorageSync('auth_token');
    
    if (!token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    
    wx.showModal({
      title: '确认取消',
      content: '确定要取消这个预约吗？',
      confirmText: '取消预约',
      cancelText: '保留',
      success: (res) => {
        if (res.confirm) {
          api.cancelReservation(reservationId)
            .then(response => {
              console.log('[my.js] 取消预约响应:', response);
              
              wx.showToast({
                title: '预约已取消',
                icon: 'success',
                duration: 2000
              });
              setTimeout(() => this.loadReservations(), 500);
            })
            .catch(error => {
              console.error('[my.js] 取消预约失败:', error);
              wx.showToast({
                title: error.message || '取消失败，请重试',
                icon: 'error',
                duration: 2000
              });
            });
        }
      }
    });
  },

  // 签到
  onCheckIn(e) {
    const reservationId = e.currentTarget.dataset.id;
    const reservation = e.currentTarget.dataset.reservation;
    
    console.log('[my.js] onCheckIn 原始事件:', e);
    console.log('[my.js] 提取的 reservationId:', reservationId);
    console.log('[my.js] 类型:', typeof reservationId, '值是否为空:', !reservationId);
    
    const token = wx.getStorageSync('auth_token');
    
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'error'
      });
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    
    // 校验 reservationId
    if (!reservationId) {
      wx.showToast({
        title: '预约ID无效',
        icon: 'error',
        duration: 2000
      });
      console.error('[my.js] reservationId 为空:', reservationId);
      return;
    }

    // 显示确认对话框
    wx.showModal({
      title: '确认签到',
      content: '确认要签到吗？',
      success: (res) => {
        if (res.confirm) {
          this.submitCheckIn(reservationId, token);
        }
      }
    });
  },

  submitCheckIn(reservationId, token) {
    this.setData({ isLoading: true });
    
    console.log('[my.js] 发送签到请求:', {
      reservationId: reservationId,
      token: token ? '存在' : '不存在'
    });
    
    api.checkIn(reservationId)
      .then(response => {
        console.log('[my.js] 签到响应:', response);
        this.setData({ isLoading: false });
        
        wx.showToast({
          title: '签到成功',
          icon: 'success',
          duration: 2000
        });
        setTimeout(() => this.loadReservations(), 500);
      })
      .catch(error => {
        console.error('[my.js] 签到请求失败:', error);
        this.setData({ isLoading: false });
        wx.showToast({
          title: error.message || '签到失败，请重试',
          icon: 'error',
          duration: 2000
        });
      });
  },

  // 前往个人统计页面
  onGoToStatistics() {
    wx.navigateTo({
      url: '/pages/my/statistics/statistics'
    });
  },

  // 前往我的账户页面
  onGoToAccount() {
    wx.navigateTo({
      url: '/pages/my/account/account'
    });
  },

  // 前往座位维修申请页面
  onGoToMaintenance() {
    wx.navigateTo({
      url: '/pages/maintenance/maintenance'
    });
  },

  // 登出
  onLogout() {
    wx.showModal({
      title: '确认登出',
      content: '确定要登出账户吗？',
      confirmText: '登出',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('auth_token');
          wx.removeStorageSync('user_info');
          wx.navigateTo({
            url: '/pages/login/login'
          });
        }
      }
    });
  }
});

// 座位选择页面 - 逻辑文件
const api = require('../../utils/api');
const app = getApp();
const AnnouncementManager = require('../../utils/announcement');

Page({
  data: {
    // 阅览室列表
    roomList: [
      { id: 1, name: '一楼自习室' },
      { id: 2, name: '二楼阅读室' },
      { id: 3, name: '三楼研讨室' }
    ],
    selectedRoomIndex: 0,

    // 座位相关
    rows: [], // 15行座位数据 (A-O行，每行10个座位)
    colNumbers: Array.from({ length: 10 }, (_, i) => i + 1), // [1,2,3...10]
    rowLetters: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O'],
    totalSeats: 150,
    occupiedCount: 0,
    availableCount: 150,
    selectedSeat: null,
    
    // 热力表相关
    showHeatmap: true,
    heatmapExpanded: false,    // 热力图是否展开
    showAllSeats: true,         // 是否显示所有座位列表 ✅ 默认为true
    heatmapData: {},
    maxHeat: 0,
    topHotSeats: [],     // Top 3最热座位
    topColdSeats: [],    // Top 3最冷座位

    // 模态框相关
    showModal: false,
    isSubmitting: false,
    isLoading: true,

    // 预约相关
    reservedDate: '', // 格式: YYYY-MM-DD
    today: '', // 今天日期
    maxDate: '', // 最大可预约日期 (MAX_ADVANCE_DAYS后)
    selectedTimeSlot: 0, // 默认选择第一个时间段
    timeSlots: [
      '08:00-10:00',
      '10:00-12:00',
      '13:00-15:00',
      '15:00-17:00',
      '17:00-19:00',
      '19:00-21:00'
    ],

    // 座位状态映射
    seatStatusMap: {
      0: { status: 0, class: 'seat-available', text: '可选' },    // 可选
      1: { status: 1, class: 'seat-reserved', text: '已预约' },    // 已预约
      2: { status: 2, class: 'seat-maintenance', text: '维护中' },  // 维护中
      3: { status: 3, class: 'seat-my-reserved', text: '我的预约' } // 我的预约
    },

    // 推荐座位相关
    showRecommendModal: false,
    isLoadingRecommendations: false,
    recommendations: [],
    recommendationReason: ''
  },

  onLoad() {
    // 首先检查用户是否已登录
    const token = wx.getStorageSync('auth_token');
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'error',
        duration: 2000
      });
      setTimeout(() => {
        wx.navigateTo({
          url: '/pages/login/login'
        });
      }, 1000);
      return;
    }

    // 初始化页面
    this.initializeDate();
    
    // ✅ 优化1: 先显示缓存数据（秒级显示）
    this.loadCachedSeats();
    
    // ✅ 优化2: 后台加载最新数据（不阻塞UI）
    this.loadSeats();
    
    // 启动座位实时轮询刷新
    this.startSeatPolling();
    
    // ✅ 优化3: 异步加载公告（不阻塞主流程）
    this.loadAnnouncementsAsync();
    
    // 标记首次加载完成
    this.isFirstLoad = true;
  },

  onShow() {
    // ✅ 优化4: 只在需要时刷新（避免重复加载）
    const needRefresh = wx.getStorageSync('need_refresh_reservations');
    if (needRefresh) {
      wx.removeStorageSync('need_refresh_reservations');
      this.loadSeats();
    } else if (this.isFirstLoad) {
      // 页面已加载过，仅在必要时刷新
      // 这里不调用loadSeats，只依赖轮询和手动下拉刷新
      console.log('[seats.js] 页面已缓存，跳过重复加载');
    }
  },
  
  onUnload() {
    // 页面卸载时停止座位轮询刷新
    this.stopSeatPolling();
  },

  /**
   * 下拉刷新事件处理
   */
  onPullDownRefresh() {
    console.log('[seats.js] 用户下拉刷新座位列表');
    this.loadSeats();
    
    // 刷新完成后停止下拉刷新动画
    setTimeout(() => {
      wx.stopPullDownRefresh({
        success: () => {
          console.log('[seats.js] 下拉刷新完成');
        }
      });
    }, 500);
  },

  /**
   * 页面滚动到底部事件
   */
  onReachBottom() {
    console.log('[seats.js] 滚动到底部');
    // 这里可以用于加载更多数据或其他操作
  },

  /**
   * 初始化日期
   */
  initializeDate() {
    const config = require('../../utils/config');
    const today = new Date();
    const todayStr = this.formatDate(today);
    
    // 计算最大可预约日期（最多提前MAX_ADVANCE_DAYS天）
    const maxDateObj = new Date(today);
    maxDateObj.setDate(maxDateObj.getDate() + config.APP_CONFIG.RESERVATION.MAX_ADVANCE_DAYS);
    const maxDateStr = this.formatDate(maxDateObj);
    
    this.setData({
      today: todayStr,
      maxDate: maxDateStr,
      reservedDate: todayStr
    });
  },

  /**
   * 日期格式化 (YYYY-MM-DD)
   */
  formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },

  /**
   * 启动座位实时轮询刷新 - 智能轮询策略
   */
  startSeatPolling() {
    // 智能轮询间隔：
    // - 当前预约中(activeTab=0)时：15秒
    // - 历史预约(activeTab=1)时：30秒
    const basePollInterval = 20000; // 基础间隔 20秒
    
    if (this.seatPollingTimer) {
      clearInterval(this.seatPollingTimer);
    }
    
    this.seatPollingTimer = setInterval(() => {
      console.log('[seats.js] 执行定时座位刷新...');
      this.loadSeats();
    }, basePollInterval);
    
    console.log('[seats.js] 座位轮询刷新已启动，间隔:', basePollInterval / 1000 + '秒');
  },

  /**
   * 停止座位实时轮询刷新
   */
  stopSeatPolling() {
    if (this.seatPollingTimer) {
      clearInterval(this.seatPollingTimer);
      this.seatPollingTimer = null;
      console.log('[seats.js] 座位轮询刷新已停止');
    }
  },

  /**
   * ✅ 优化: 从缓存快速加载座位（秒级显示）
   */
  loadCachedSeats() {
    const cachedSeats = wx.getStorageSync('cached_seats');
    if (cachedSeats && cachedSeats.length > 0) {
      console.log('[seats.js] 从缓存加载座位数据，共', cachedSeats.length, '个');
      this.processSeatData(cachedSeats);
      this.setData({ isLoading: false });
      return true;
    }
    return false;
  },

  /**
   * ✅ 优化: 异步加载公告（不阻塞主流程）
   */
  loadAnnouncementsAsync() {
    // 使用setTimeout模拟异步，避免阻塞主UI线程
    setTimeout(() => {
      try {
        const AnnouncementManager = require('../../utils/announcement');
        AnnouncementManager.loadAndShowAnnouncement()
          .then(result => {
            if (result) {
              console.log('[seats.js] 公告加载成功');
            }
          })
          .catch(error => {
            console.warn('[seats.js] 公告加载失败:', error);
            // 不影响主流程
          });
      } catch (error) {
        console.warn('[seats.js] 加载公告工具失败:', error);
      }
    }, 500); // 延迟500ms后加载公告
  },

  /**
   * 手动刷新座位信息
   */
  onRefreshSeats() {
    console.log('[seats.js] 用户手动刷新座位信息');
    this.setData({ isLoading: true });
    this.loadSeats();
  },

  /**
   * 加载座位列表 - 增强版，含网络状态检查
   */
  loadSeats() {
    const network = require('../../utils/network');
    this.setData({ isLoading: true });

    // 首先检查网络连接
    network.getNetworkStatus().then(status => {
      if (!status.isOnline) {
        console.warn('[seats.js] 网络未连接');
        this.setData({ isLoading: false });
        
        // 使用演示数据作为备选
        wx.showToast({
          title: '网络未连接，显示缓存数据',
          icon: 'none',
          duration: 2000
        });
        
        // 如果有本地缓存的座位数据，就使用缓存，否则生成演示数据
        const cachedSeats = wx.getStorageSync('cached_seats');
        if (cachedSeats) {
          this.processSeatData(cachedSeats);
        } else {
          this.generateMockSeats();
        }
        return;
      }

      const token = wx.getStorageSync('auth_token');
      if (!token) {
        wx.showToast({
          title: '请先登录',
          icon: 'error',
          duration: 2000
        });
        this.setData({ isLoading: false });
        setTimeout(() => {
          wx.navigateTo({ url: '/pages/login/login' });
        }, 1000);
        return;
      }

      const { selectedRoomIndex, roomList, reservedDate } = this.data;
      const room = roomList[selectedRoomIndex];
      
      // 调用API获取座位列表
      api.getSeats(room.id, reservedDate)
        .then(response => {
          console.log('[seats.js] 获取座位列表成功:', response);
          
          // 处理API响应数据
          const seats = response && response.seats ? response.seats : [];
          this.processSeatData(seats);
          
          // 缓存座位数据，以便离线使用
          wx.setStorageSync('cached_seats', seats);
          
          // 更新统计数据
          if (response) {
            this.setData({
              occupiedCount: response.occupied_seats || 0,
              availableCount: response.available_seats || 0,
              totalSeats: response.total_seats || 100
            });
          }
          
          this.setData({ isLoading: false });
          
          // 停止下拉刷新动画
          wx.stopPullDownRefresh();
        })
        .catch(error => {
          console.error('[seats.js] 获取座位列表失败:', error);
          
          // 显示具体的错误信息
          let errorMsg = '加载座位信息失败';
          let showCache = false;
          
          if (error.code === 404) {
            errorMsg = error.tip || '资源不存在';
          } else if (error.code === 401) {
            errorMsg = '登录已过期，请重新登录';
          } else if (error.code === -1) {
            errorMsg = error.tip || '网络连接失败';
            showCache = true;
          } else if (error.tip) {
            errorMsg = error.tip;
            showCache = true;
          }
          
          // 如果网络错误，使用缓存数据
          if (showCache) {
            const cachedSeats = wx.getStorageSync('cached_seats');
            if (cachedSeats) {
              console.log('[seats.js] 使用缓存座位数据');
              this.processSeatData(cachedSeats);
              wx.showToast({
                title: '显示缓存数据',
                icon: 'none',
                duration: 2000
              });
            } else {
              // 使用演示数据作为最后备选方案
              console.log('[seats.js] 使用演示座位数据作为备选');
              this.generateMockSeats();
              wx.showToast({
                title: errorMsg,
                icon: 'error',
                duration: 2000
              });
            }
          } else {
            wx.showToast({
              title: errorMsg,
              icon: 'error',
              duration: 2000
            });
          }
          
          this.setData({ isLoading: false });
          
          // 停止下拉刷新动画
          wx.stopPullDownRefresh();
        });
    }).catch(error => {
      console.error('[seats.js] 检查网络状态失败:', error);
      this.setData({ isLoading: false });
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 处理座位数据
   * 将一维数组转换为二维数组（15行 × 10列 = 150座位）
   */
  processSeatData(seats) {
    const rows = [];
    // 15行座位：A-O行
    const rowLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O'];
    const colNumbers = Array.from({ length: 10 }, (_, i) => i + 1);
    
    // 计算热力表数据
    const heatmapData = {};
    let maxHeat = 0;

    // 改为15行×10列=150个座位
    for (let row = 0; row < 15; row++) {
      const rowSeats = [];
      for (let col = 0; col < 10; col++) {
        const seatIndex = row * 10 + col;
        const seatData = seats[seatIndex] || this.createDefaultSeat(row, col);

        const seatId = seatData.id || (row * 10 + col + 100);
        
        // 组织座位数据
        const seat = {
          seatId: seatId,
          seatNumber: `${rowLetters[row]}-${String(col + 1).padStart(2, '0')}`,  // 格式改为 A-01, A-02等
          status: seatData.status || 0,
          statusClass: this.data.seatStatusMap[seatData.status || 0].class,
          row: row,
          col: col,
          rowLabel: rowLetters[row],
          colLabel: colNumbers[col],
          heat: seatData.heat || 0
        };
        
        // 记录热力数据用于热力表显示
        const heat = seatData.heat || Math.random() * 5;
        heatmapData[seatId] = heat;
        maxHeat = Math.max(maxHeat, heat);

        rowSeats.push(seat);
      }
      rows.push(rowSeats);
    }

    // 计算热力排行 (Top 3热门和冷门)
    const heatmapRanking = this.calculateHeatmapRanking(rows, heatmapData, maxHeat);

    // 也生成列号数据供WXML使用
    this.setData({ 
      rows,
      colNumbers: colNumbers,
      rowLetters: rowLetters,
      heatmapData: heatmapData,
      maxHeat: Math.max(maxHeat, 1),
      topHotSeats: heatmapRanking.topHot,
      topColdSeats: heatmapRanking.topCold
    });
  },

  /**
   * 计算热力排行 - 找出Top 3最热和最冷的座位
   */
  calculateHeatmapRanking(rows, heatmapData, maxHeat) {
    const seatArray = [];
    
    // 收集所有座位的热度数据
    for (let row of rows) {
      for (let seat of row) {
        const heat = heatmapData[seat.seatId] || 0;
        seatArray.push({
          seatNumber: seat.seatNumber,
          seatId: seat.seatId,
          heat: heat,
          percentHeat: maxHeat > 0 ? Math.round((heat / maxHeat) * 100) : 0
        });
      }
    }
    
    // 按热度排序
    seatArray.sort((a, b) => b.heat - a.heat);
    
    // 获取Top 3最热和最冷
    const topHot = seatArray.slice(0, 3);
    const topCold = seatArray.slice(-3).reverse();
    
    return {
      topHot,
      topCold
    };
  },

  /**
   * 生成默认座位
   */
  createDefaultSeat(row, col) {
    // 模拟一些已占用的座位
    const occupiedSeats = [
      [0, 0], [0, 3], [1, 2], [1, 5], [2, 1], [2, 8],
      [3, 4], [3, 7], [4, 2], [5, 9], [6, 0], [7, 5], [8, 3]
    ];

    let status = 0; // 默认可选
    
    // 标记已占用座位
    if (occupiedSeats.some(([r, c]) => r === row && c === col)) {
      status = 1; // 已预约
    }

    // 模拟维护座位
    if ((row + col) % 13 === 0) {
      status = 2; // 维护中
    }

    return {
      id: row * 10 + col + 100,  // 数字格式
      status: status
    };
  },

  /**
   * 生成模拟座位数据 (15行 × 10列 = 150个座位)
   */
  generateMockSeats() {
    const seats = [];
    for (let i = 0; i < 150; i++) {
      seats.push(this.createDefaultSeat(Math.floor(i / 10), i % 10));
    }
    this.processSeatData(seats);

    // 更新统计数据
    const occupied = seats.filter(s => s.status === 1).length;
    this.setData({
      occupiedCount: occupied,
      availableCount: 150 - occupied,
      totalSeats: 150
    });
  },

  /**
   * 根据座位ID查找座位
   */
  findSeatById(seatId) {
    for (let row of this.data.rows) {
      for (let seat of row) {
        if (seat.seatId === seatId) {
          return seat;
        }
      }
    }
    return null;
  },

  /**
   * 取消模态框
   */
  onCancelModal() {
    this.setData({
      showModal: false,
      selectedSeat: null
    });
  },

  /**
   * 从热力图选择座位
   */
  onSelectHeatmapSeat(event) {
    const seatId = parseInt(event.currentTarget.dataset.seatId);
    
    // 查找选中的座位
    const selectedSeat = this.findSeatById(seatId);
    if (!selectedSeat) {
      wx.showToast({
        title: '座位未找到',
        icon: 'error',
        duration: 2000
      });
      return;
    }

    // 检查座位是否可选
    if (selectedSeat.status !== 0) {
      wx.showToast({
        title: '该座位不可选，请选择其他座位',
        icon: 'none',
        duration: 2000
      });
      return;
    }

    console.log('从热力图选中座位:', selectedSeat);

    // 打开模态框
    this.setData({
      selectedSeat: selectedSeat,
      showModal: true
    });
  },

  /**
   * 选择预约日期
   */
  onSelectDate(event) {
    const date = event.detail.value;
    const { today, maxDate } = this.data;
    
    // 验证日期范围
    if (date < today) {
      wx.showToast({
        title: '不能选择今天之前的日期',
        icon: 'error',
        duration: 2000
      });
      this.setData({ reservedDate: today });
      return;
    }
    
    if (date > maxDate) {
      const config = require('../../utils/config');
      const maxDays = config.APP_CONFIG.RESERVATION.MAX_ADVANCE_DAYS;
      wx.showToast({
        title: `最多只能提前${maxDays}天预约`,
        icon: 'error',
        duration: 2000
      });
      this.setData({ reservedDate: maxDate });
      return;
    }
    
    this.setData({ reservedDate: date });
    console.log('选中日期:', date);
    
    // 日期改变时重新加载座位列表
    this.loadSeats();
  },

  /**
   * 选择时间段
   */
  onSelectTimeSlot(event) {
    // 支持两种触发方式：picker的change事件和列表项的tap事件
    let index;
    
    if (event.detail !== undefined && event.detail.value !== undefined) {
      // picker的change事件
      index = parseInt(event.detail.value);
    } else if (event.currentTarget && event.currentTarget.dataset && event.currentTarget.dataset.index !== undefined) {
      // 列表项tap事件
      index = parseInt(event.currentTarget.dataset.index);
    } else {
      // 默认使用当前值
      index = this.data.selectedTimeSlot;
    }
    
    // 确保index是有效的数字
    if (isNaN(index) || index < 0 || index >= this.data.timeSlots.length) {
      index = 0;
    }
    
    this.setData({ selectedTimeSlot: index });
    console.log('选中时间段:', index, '时间:', this.data.timeSlots[index]);
  },

  /**
   * 本地更新座位状态（预约成功后立即改变颜色）
   */
  updateLocalSeatStatus(seatId, newStatus, userId) {
    const { rows } = this.data;
    
    // 找到被预约的座位并更新其状态
    for (let row of rows) {
      for (let seat of row) {
        if (seat.seatId === seatId) {
          // 更新座位状态
          seat.status = newStatus;
          
          // 根据新状态更新 CSS 类
          const statusInfo = this.data.seatStatusMap[newStatus];
          if (statusInfo) {
            seat.statusClass = statusInfo.class;
          }
          
          console.log(`座位 ${seat.seatNumber} 状态已更新为 ${newStatus} (${statusInfo?.text})`);
          
          // 触发页面重新渲染
          this.setData({ rows });
          return;
        }
      }
    }
  },

  /**
   * 确认预约
   */
  onConfirmReservation() {
    const { selectedSeat, reservedDate, selectedTimeSlot, roomList, selectedRoomIndex, timeSlots } = this.data;

    // 验证数据
    if (!selectedSeat) {
      wx.showToast({
        title: '请选择座位',
        icon: 'error'
      });
      return;
    }

    if (!reservedDate) {
      wx.showToast({
        title: '请选择预约日期',
        icon: 'error'
      });
      return;
    }

    // 确保selectedTimeSlot是有效的数字
    let timeSlotIndex = selectedTimeSlot;
    if (isNaN(timeSlotIndex) || timeSlotIndex < 0 || timeSlotIndex >= timeSlots.length) {
      timeSlotIndex = 0;
    }
    
    const room = roomList[selectedRoomIndex];
    const timeSlot = timeSlots[timeSlotIndex];

    // 准备请求数据
    const reservationData = {
      seat_id: selectedSeat.seatId,
      room_id: room.id,
      reservation_date: reservedDate,
      reservation_time: timeSlot
    };

    console.log('提交预约:', reservationData);

    // 调用后端API提交预约
    this.setData({ isSubmitting: true });

    api.submitReservation(reservationData)
      .then(response => {
        console.log('预约成功:', response);

        // 预约成功后，立即更新前端座位状态为"我的预约"(状态 3)
        const userId = wx.getStorageSync('user_id');
        this.updateLocalSeatStatus(selectedSeat.seatId, 3, userId);
        
        this.setData({
          isSubmitting: false,
          showModal: false,
          selectedSeat: null,
          selectedTimeSlot: 0
        });

        // 保存预约信息到本地（用于快速显示）
        const reservationInfo = {
          reservationId: response.reservation_id,
          seatNumber: selectedSeat.seatNumber,
          roomName: room.name,
          roomId: room.id,
          date: reservedDate,
          timeSlot: timeSlot,
          timestamp: Date.now()
        };
        wx.setStorageSync('last_reservation', reservationInfo);

        wx.showToast({
          title: '预约成功！',
          icon: 'success',
          duration: 2000
        });

        // 稍后刷新座位列表（争取最新数据）
        setTimeout(() => {
          this.loadSeats();
          
          // 也要通知"我的预约"页面刷新数据（如果页面已打开）
          // 通过事件系统或全局变量标记需要刷新
          wx.setStorageSync('need_refresh_reservations', true);
        }, 500);
        
        // 弹出提示，询问是否查看预约详情
        setTimeout(() => {
          wx.showModal({
            title: '预约成功',
            content: `座位 ${selectedSeat.seatNumber} 已预约成功\\n${reservedDate} ${timeSlot}\\n\\n点击"查看预约"可查看详情`,
            confirmText: '查看预约',
            cancelText: '继续预约',
            success: (res) => {
              if (res.confirm) {
                // 跳转到"我的预约"页面
                wx.switchTab({
                  url: '/pages/my/my'
                });
              }
            }
          });
        }, 1500);
      })
      .catch(error => {
        console.error('预约失败:', error);
        this.setData({ isSubmitting: false });

        let errorMsg = '预约失败，请重试';
        let errorTip = '';
        
        if (error.code === 409) {
          errorMsg = error.message || '该座位已被他人预约';
          errorTip = '座位已被锁定，请选择其他座位';
        } else if (error.data && error.data.message) {
          errorMsg = error.data.message;
        } else if (error.message) {
          errorMsg = error.message;
        }
        
        if (error.tip) {
          errorTip = error.tip;
        }

        wx.showToast({
          title: errorMsg,
          icon: 'error',
          duration: 2000
        });
        
        // 如果有额外提示，延迟显示
        if (errorTip) {
          setTimeout(() => {
            wx.showModal({
              title: '提示',
              content: errorTip,
              confirmText: '确定',
              showCancel: false
            });
          }, 2500);
        }
      });
  },

  // ========== 座位推荐功能 ==========

  /**
   * 打开推荐座位弹窗
   */
  onGetRecommendations() {
    const token = wx.getStorageSync('auth_token');
    const roomId = this.data.roomList[this.data.selectedRoomIndex].id;

    this.setData({
      showRecommendModal: true,
      isLoadingRecommendations: true
    });

    const requestData = {
      room_id: roomId,
      date: this.data.reservedDate,
      time_slot: this.data.timeSlots[this.data.selectedTimeSlot],
      count: 5
    };

    api.getRecommendedSeats(requestData)
      .then(response => {
        console.log('[seats.js] 获取推荐座位成功:', response);
        
        this.setData({ isLoadingRecommendations: false });
        
        // 处理标准化的响应
        const recommendData = response.recommendations ? response : response.data;
        const { recommendations, recommendation_reason } = recommendData;
        
        if (recommendations && Array.isArray(recommendations)) {
          // 为每个推荐项添加预计算的百分比
          const processedRecommendations = recommendations.map(item => ({
            ...item,
            crowdingPercent: Math.round(item.crowding_level * 100)
          }));
          
          this.setData({
            recommendations: processedRecommendations,
            recommendationReason: recommendation_reason
          });
        } else {
          wx.showToast({
            title: '获取推荐失败',
            icon: 'error'
          });
          this.setData({ showRecommendModal: false });
        }
      })
      .catch(error => {
        console.error('[seats.js] 获取推荐座位失败:', error);
        this.setData({ isLoadingRecommendations: false });
        wx.showToast({
          title: error.message || '网络错误，请重试',
          icon: 'error'
        });
        console.error('[seats.js] 获取推荐座位失败:', error);
        this.setData({ isLoadingRecommendations: false });
        wx.showToast({
          title: error.message || '网络错误，请重试',
          icon: 'error'
        });
        this.setData({ showRecommendModal: false });
      });
  },

  /**
   * 关闭推荐座位弹窗
   */
  onCloseRecommendModal() {
    this.setData({ showRecommendModal: false });
  },

  /**
   * 选择推荐的座位
   */
  onSelectRecommendedSeat(event) {
    const { seatId, roomId } = event.currentTarget.dataset;
    
    // 关闭推荐弹窗
    this.setData({ showRecommendModal: false });

    // 立即打开预约确认弹窗，设置选中的座位
    const seat = this.findSeatById(seatId);
    
    if (seat) {
      this.setData({
        selectedSeat: seat,
        showModal: true
      });
    } else {
      wx.showToast({
        title: '座位信息加载失败',
        icon: 'error'
      });
    }
  },

  /**
   * 根据seatId查找座位对象
   */
  findSeatById(seatId) {
    const { rows } = this.data;
    
    for (let row of rows) {
      for (let seat of row) {
        if (seat.seatId === seatId) {
          return seat;
        }
      }
    }
    
    return null;
  },

  /**
   * 切换显示所有座位列表
   */
  /**
   * 切换热力图展开/折叠
   */
  toggleHeatmap() {
    this.setData({
      heatmapExpanded: !this.data.heatmapExpanded
    });
  },

  /**
   * 切换显示所有座位列表
   */
  toggleAllSeats() {
    this.setData({
      showAllSeats: !this.data.showAllSeats
    });
  },

  /**
   * 楼层选择 - 切换房间
   */
  onSelectRoom(event) {
    const { index } = event.currentTarget.dataset;
    
    if (this.data.selectedRoomIndex === index) {
      // 同一楼层，直接返回
      return;
    }

    // 更新选中的房间索引
    this.setData({ 
      selectedRoomIndex: index,
      isLoading: true,
      selectedSeat: null  // 清除之前选中的座位
    });

    // 重新加载该楼层的座位
    this.loadSeats();

    // 显示切换提示
    wx.showToast({
      title: `已切换到${this.data.roomList[index].name}`,
      icon: 'success',
      duration: 1500
    });
  },

  /**
   * 选择座位 - 打开预约确认弹窗
   */
  onSelectSeat(event) {
    const { seatId, disabled } = event.currentTarget.dataset;
    
    if (disabled) {
      wx.showToast({
        title: '该座位不可选',
        icon: 'error'
      });
      return;
    }

    const seat = this.findSeatById(seatId);
    
    if (seat) {
      this.setData({
        selectedSeat: seat,
        showModal: true
      });
    }
  },

  /**
   * 从热力图选择座位
   */
  onSelectHeatmapSeat(event) {
    const { seatId } = event.currentTarget.dataset;
    const seat = this.findSeatById(seatId);
    
    if (seat && seat.status === 0) {
      this.setData({
        selectedSeat: seat,
        showModal: true
      });
    } else {
      wx.showToast({
        title: '该座位不可选',
        icon: 'error'
      });
    }
  },

  /**
   * 打开我的预约页面 - 使用switchTab而不是navigateTo（因为my是tabbar页）
   */
  onMyReservations() {
    wx.switchTab({
      url: '/pages/my/my',
      fail: (error) => {
        console.error('导航失败:', error);
        wx.showToast({
          title: '页面加载失败',
          icon: 'error'
        });
      }
    });
  },

  /**
   * 加载并显示公告
   * 在用户登录进入页面时，获取最新的公告并显示弹窗
   */
  async loadAnnouncements() {
    try {
      console.log('[Seats] 开始加载公告');
      const announcementShown = await AnnouncementManager.loadAndShowAnnouncement();
      
      if (announcementShown) {
        console.log('[Seats] 公告加载并显示成功');
      } else {
        console.log('[Seats] 没有可显示的新公告');
      }
    } catch (error) {
      console.error('[Seats] 加载公告出错:', error);
      // 不影响主流程，继续正常使用
    }
  }
});
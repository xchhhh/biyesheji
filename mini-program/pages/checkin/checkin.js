// 签到页面 - 逻辑文件
const api = require('../../utils/api');
const config = require('../../utils/config');
const app = getApp();

Page({
  data: {
    // 页面状态
    activeTab: 'qr',  // 'qr' 或 'manual'
    isLoading: false,
    isSubmitting: false,
    errorMessage: '',
    successMessage: '',

    // QR扫描
    showQRScanner: false,
    scannedQRCode: '',

    // 手动输入
    reservationId: '',
    reservationCode: '',

    // 预约信息显示
    showReservationInfo: false,
    reservationInfo: {
      id: '',
      room_name: '',
      seat_number: '',
      reservation_date: '',
      time_slot: '',
      status: '',
      check_in_deadline: ''
    },

    // UI配置
    colors: config.APP_CONFIG.UI.COLORS,
    toastDuration: config.APP_CONFIG.UI.TOAST_DURATION
  },

  onLoad() {
    // 检查用户是否已登录
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

    // 检查是否从其他页面传来预约ID
    if (this.options.reservationId) {
      this.setData({
        reservationId: this.options.reservationId,
        activeTab: 'manual'
      });
    }

    console.log('[checkin.js] 签到页面加载完成');
  },

  /**
   * 切换标签页
   */
  onTabChange(e) {
    const activeTab = e.currentTarget.dataset.tab;
    this.clearMessages();
    this.setData({ activeTab });
    
    if (activeTab === 'qr') {
      this.startQRScanner();
    } else {
      this.stopQRScanner();
    }
  },

  /**
   * 启动QR扫描
   */
  startQRScanner() {
    wx.scanCode({
      onlyFromCamera: true,
      scanType: ['qrCode'],
      success: (res) => {
        console.log('[checkin.js] QR码扫描成功:', res.result);
        this.setData({ scannedQRCode: res.result });
        this.handleQRCodeScan(res.result);
      },
      fail: (error) => {
        console.error('[checkin.js] QR码扫描失败:', error);
        if (error.errMsg !== 'scanCode:fail cancel') {
          this.setData({
            errorMessage: '扫描失败，请重试'
          });
        }
      }
    });
  },

  /**
   * 停止QR扫描
   */
  stopQRScanner() {
    // 微信小程序的扫描是一个性质的操作，不需要停止
  },

  /**
   * 处理QR码扫描结果
   */
  handleQRCodeScan(qrCode) {
    if (!qrCode || qrCode.trim() === '') {
      this.setData({
        errorMessage: '二维码内容为空'
      });
      return;
    }

    // 调用签到，标记为QR码扫描
    this.performCheckIn(qrCode, true);
  },

  /**
   * 手动输入预约号
   */
  onReservationIdInput(e) {
    this.setData({
      reservationId: e.detail.value
    });
    this.clearMessages();
  },

  /**
   * 手动输入预约代码
   */
  onReservationCodeInput(e) {
    this.setData({
      reservationCode: e.detail.value
    });
    this.clearMessages();
  },

  /**
   * 手动签到
   */
  onManualCheckIn() {
    const { reservationId } = this.data;

    if (!reservationId || reservationId.trim() === '') {
      this.setData({
        errorMessage: '请输入预约号'
      });
      return;
    }

    // 调用签到，标记为手动输入（不是QR码）
    this.performCheckIn(reservationId, false);
  },

  /**
   * 执行签到操作
   */
  performCheckIn(reservationIdOrQRCode, isQRCode = false) {
    this.setData({ isSubmitting: true, errorMessage: '', successMessage: '' });

    // 根据输入类型选择合适的API调用
    const apiCall = isQRCode 
      ? api.checkInWithQR(reservationIdOrQRCode)
      : api.checkIn(parseInt(reservationIdOrQRCode));

    apiCall
      .then(response => {
        console.log('[checkin.js] 签到成功:', response);

        // 显示成功提示
        this.setData({
          successMessage: '签到成功！',
          showReservationInfo: true,
          reservationInfo: response,
          isSubmitting: false
        });

        wx.showToast({
          title: '签到成功',
          icon: 'success',
          duration: 2000
        });

        // 显示预约信息3秒后返回首页
        setTimeout(() => {
          wx.switchTab({
            url: '/pages/index/index'
          });
        }, 3000);
      })
      .catch(error => {
        console.error('[checkin.js] 签到失败:', error);
        
        const errorMsg = error.message || '签到失败，请检查预约号是否正确';
        this.setData({
          errorMessage: errorMsg,
          isSubmitting: false,
          showReservationInfo: false
        });

        wx.showToast({
          title: errorMsg,
          icon: 'error',
          duration: 2000
        });
      });
  },

  /**
   * 清除消息
   */
  clearMessages() {
    this.setData({
      errorMessage: '',
      successMessage: ''
    });
  },

  /**
   * 返回首页
   */
  onBackToHome() {
    wx.switchTab({
      url: '/pages/index/index'
    });
  },

  /**
   * 返回座位选择页面
   */
  onBackToSeats() {
    wx.switchTab({
      url: '/pages/seats/seats'
    });
  }
});

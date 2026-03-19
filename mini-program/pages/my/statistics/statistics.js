const config = require('../../../utils/config');

Page({
  data: {
    stats: null,
    hasStats: false,
    isLoading: true,
    Math: Math  // 使得Math对象在模板中可用
  },

  onLoad() {
    this.loadStatistics();
  },

  onShow() {
    // 每次显示时刷新统计数据
    this.loadStatistics();
  },

  // 加载统计数据
  loadStatistics() {
    const token = wx.getStorageSync('auth_token');
    const userId = wx.getStorageSync('user_id');

    if (!token || !userId) {
      this.setData({ 
        hasStats: false, 
        isLoading: false 
      });
      return;
    }

    this.setData({ isLoading: true });

    wx.request({
      url: `${config.API_BASE_URL}/user/statistics`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        days: 90  // 获取90天的统计数据
      },
      success: (response) => {
        console.log('[statistics.js] 获取统计数据成功', response);
        
        this.setData({ isLoading: false });
        
        if (response.statusCode === 200 && response.data.data) {
          const stats = response.data.data;
          
          this.setData({
            stats,
            hasStats: true
          });
        } else {
          this.setData({ hasStats: false });
          wx.showToast({
            title: response.data.message || '加载统计数据失败',
            icon: 'error'
          });
        }
      },
      fail: (error) => {
        console.error('[statistics.js] 获取统计数据失败', error);
        this.setData({ 
          isLoading: false, 
          hasStats: false 
        });
        wx.showToast({
          title: '网络错误，请重试',
          icon: 'error'
        });
      }
    });
  },

  // 刷新数据
  onRefresh() {
    this.loadStatistics();
    wx.showToast({
      title: '数据已刷新',
      icon: 'success',
      duration: 1500
    });
  }
});

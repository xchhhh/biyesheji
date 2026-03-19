const config = require('./utils/config');

App({
  onLaunch() {
    // 应用启动
    console.log('App launched');
  },

  globalData: {
    baseUrl: config.API_BASE_URL  // 从中心化配置导入
  },

  getToken() {
    return wx.getStorageSync('auth_token') || null;
  },

  setToken(token) {
    wx.setStorageSync('auth_token', token);
  },

  clearToken() {
    wx.removeStorageSync('auth_token');
  }
});

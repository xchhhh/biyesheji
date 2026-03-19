// 网络状态监听工具
const app = getApp();

let networkListener = null;
let isOnline = true;

/**
 * 启动网络状态监听
 * @param {Function} callback - 网络状态变化时的回调函数，参数为 {isOnline, type}
 */
function startNetworkListener(callback) {
  try {
    // 监听网络状态变化
    wx.onNetworkStatusChange(function(res) {
      console.log('[network.js] 网络状态变化:', res);
      
      const wasOnline = isOnline;
      isOnline = res.isConnected;
      
      // 只在状态改变时执行回调
      if (wasOnline !== isOnline && callback) {
        callback({
          isOnline: isOnline,
          type: res.networkType,
          wasOnline: wasOnline
        });
      }
    });
    
    networkListener = callback;
    console.log('[network.js] 网络状态监听已启动');
  } catch (error) {
    console.error('[network.js] 启动网络监听失败:', error);
  }
}

/**
 * 获取当前网络状态
 */
function getNetworkStatus() {
  return new Promise((resolve, reject) => {
    wx.getNetworkType({
      success(networkType) {
        console.log('[network.js] 当前网络类型:', networkType);
        resolve({
          type: networkType.networkType, // wifi | 4g | 3g | 2g | none
          isOnline: networkType.networkType !== 'none',
          typeText: getNetworkTypeText(networkType.networkType)
        });
      },
      fail(error) {
        console.error('[network.js] 获取网络状态失败:', error);
        reject(error);
      }
    });
  });
}

/**
 * 获取网络类型的文本描述
 */
function getNetworkTypeText(type) {
  const typeMap = {
    'wifi': 'WiFi',
    '4g': '4G',
    '3g': '3G',
    '2g': '2G',
    '5g': '5G',
    'unknown': '未知网络',
    'none': '无网络连接'
  };
  return typeMap[type] || type;
}

/**
 * 显示网络状态提示
 * @param {Object} options - 配置选项
 *   - title: 提示标题
 *   - message: 提示内容
 *   - duration: 显示时长（ms）
 *   - showNetworkType: 是否显示网络类型
 */
function showNetworkStatus(options = {}) {
  const {
    title = '网络状态',
    message = '',
    duration = 2000,
    showNetworkType = true
  } = options;

  // 先获取网络状态
  getNetworkStatus().then(status => {
    if (!status.isOnline) {
      wx.showToast({
        title: '网络未连接',
        icon: 'none',
        duration: duration,
        mask: false
      });
    } else {
      // 显示当前网络信息的Toast
      const content = showNetworkType 
        ? `${message || title} (${status.typeText})`
        : (message || title);
        
      wx.showToast({
        title: content,
        icon: 'success',
        duration: duration,
        mask: false
      });
    }
  }).catch(error => {
    console.error('[network.js] 显示网络状态时出错:', error);
  });
}

/**
 * 检查网络连接，如果没有网络则显示提示
 * @param {Function} callback - 有网络时执行的回调
 * @param {boolean} showMessage - 是否显示提示消息
 */
function checkNetworkAndExecute(callback, showMessage = true) {
  getNetworkStatus().then(status => {
    if (!status.isOnline) {
      if (showMessage) {
        wx.showToast({
          title: '网络未连接，请检查网络设置',
          icon: 'error',
          duration: 2000
        });
      }
      return;
    }
    
    if (callback && typeof callback === 'function') {
      callback(status);
    }
  }).catch(error => {
    console.error('[network.js] 检查网络失败:', error);
    if (showMessage) {
      wx.showToast({
        title: '无法检查网络状态',
        icon: 'error',
        duration: 1500
      });
    }
  });
}

/**
 * 停止网络状态监听
 */
function stopNetworkListener() {
  try {
    wx.offNetworkStatusChange();
    networkListener = null;
    console.log('[network.js] 网络状态监听已停止');
  } catch (error) {
    console.error('[network.js] 停止网络监听失败:', error);
  }
}

/**
 * 获取是否在线状态
 */
function isConnected() {
  return isOnline;
}

module.exports = {
  startNetworkListener,
  stopNetworkListener,
  getNetworkStatus,
  getNetworkTypeText,
  showNetworkStatus,
  checkNetworkAndExecute,
  isConnected
};

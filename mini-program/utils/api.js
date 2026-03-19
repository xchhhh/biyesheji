// API 调用工具
const config = require('./config');
const app = getApp();
let isRelogging = false; // 防重入标识，解决并发401时循环压栈问题

/**
 * 标准化API响应格式
 * 将不同来源的响应转换为统一格式
 * @param {object} responseData - 原始响应数据
 * @returns {object} 标准化的响应数据
 */
function normalizeResponse(responseData) {
  if (!responseData) {
    return {};
  }
  
  // 如果响应已经有data属性，直接返回data内容
  if (responseData.data !== undefined) {
    return responseData.data;
  }
  
  // 如果响应本身就是数组或对象，直接返回
  if (typeof responseData === 'object') {
    return responseData;
  }
  
  return responseData;
}

/**
 * HTTP 请求封装
 */
function request(method, endpoint, data = null) {
  return new Promise((resolve, reject) => {
    // 获取token
    const token = app.getToken();

    // 构造完整URL
    const url = config.API_BASE_URL + endpoint;

    // 构造请求头
    const header = {
      'Content-Type': 'application/json'
    };

    // 如果有token，添加到请求头
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }

    console.log(`[${method}] ${url}`, data);

    // 发送请求
    wx.request({
      url: url,
      method: method,
      data: data,
      header: header,
      timeout: 10000, // 10秒超时

      success(response) {
        const { statusCode, data: responseData } = response;

        console.log(`Response (${statusCode}):`, responseData);

        // 处理响应
        if (statusCode === 200 || statusCode === 201) {
          // 成功响应 (statusCode 2xx 表示成功)
          // 标准化响应格式
          const normalizedData = normalizeResponse(responseData);
          resolve(normalizedData);
        } else if (statusCode === 401) {
          // 未授权，清除token并防抖控制跳转登录
          app.clearToken();
          if (!isRelogging) {
            isRelogging = true;
            wx.showToast({
              title: '登录已过期',
              icon: 'error',
              duration: 2000
            });
            // 延迟跳转，给用户看到提示的时间
            setTimeout(() => {
              // 使用 reLaunch 确保清空历史栈，使用户无法返回
              wx.reLaunch({
                url: '/pages/login/login',
                success: () => {
                  isRelogging = false;
                },
                fail: () => {
                  isRelogging = false;
                }
              });
            }, 1500);
          }
          reject({
            code: 401,
            message: '登录已过期，请重新登录'
          });
        } else if (statusCode === 403) {
          // 禁止访问
          reject({
            code: 403,
            message: responseData.message || '没有权限访问'
          });
        } else if (statusCode === 404) {
          // 资源不存在 - 提供更详细的错误信息
          console.warn('[API 404]', endpoint, responseData);
          let errorMsg = '请求的资源不存在';
          
          // 根据不同端点提供更具体的提示
          if (endpoint.includes('/reservations/')) {
            errorMsg = '该预约信息不存在，可能已被删除';
          } else if (endpoint.includes('/seats')) {
            errorMsg = '座位信息加载失败，请检查网络或稍后重试';
          } else if (endpoint.includes('/admin')) {
            errorMsg = '管理资源不存在';
          }
          
          reject({
            code: 404,
            message: errorMsg,
            tip: '如果问题持续存在，请尝试刷新页面或重新登录'
          });
        } else if (statusCode === 409) {
          // 冲突（如座位已被他人预约）
          reject({
            code: 409,
            message: responseData.message || '操作冲突，请重试',
            data: normalizeResponse(responseData)
          });
        } else if (statusCode === 500) {
          // 服务器错误
          reject({
            code: 500,
            message: '服务器错误，请稍后重试'
          });
        } else {
          // 其他错误
          reject({
            code: statusCode,
            message: `请求失败 (${statusCode})`
          });
        }
      },

      fail(error) {
        // 网络请求失败 - 提供更详细的诊断信息
        console.error('Network error:', error);
        
        let errorMsg = '网络连接失败';
        let errorTip = '请检查网络连接';
        
        // 根据不同的错误类型提供更具体的提示
        if (error.errMsg) {
          if (error.errMsg.includes('timeout')) {
            errorMsg = '请求超时';
            errorTip = '网络不稳定，请检查网络连接并重试';
          } else if (error.errMsg.includes('abort')) {
            errorMsg = '请求被中断';
            errorTip = '请稍后重试';
          } else if (error.errMsg.includes('ERR_INVALID_ARG_TYPE')) {
            errorMsg = '请求参数错误';
            errorTip = '如果问题持续，请刷新页面';
          } else if (error.errMsg.includes('ENOTFOUND')) {
            errorMsg = '无法连接到服务器';
            errorTip = '请确保网络连接正常';
          }
        }
        
        reject({
          code: -1,
          message: errorMsg,
          tip: errorTip,
          error: error,
          errMsg: error.errMsg
        });
      },

      complete() {
        // 请求完成（无论成功还是失败）
        console.log(`Request completed: ${method} ${endpoint}`);
      }
    });
  });
}

/**
 * 获取座位列表
 * @param {number} roomId - 阅览室ID
 * @param {string} date - 预约日期 (YYYY-MM-DD)
 */
function getSeats(roomId, date) {
  const params = `?room_id=${roomId}&date=${date || ''}`;
  return request('GET', '/reservations/seats/' + roomId + params);
}

/**
 * 提交预约
 * @param {object} data - 预约数据
 *   - seat_id: 座位ID
 *   - room_id: 阅览室ID
 *   - reservation_date: 预约日期 (YYYY-MM-DD)
 *   - time_slot: 时间段 (HH:MM-HH:MM)
 */
function submitReservation(data) {
  return request('POST', '/reservations/reserve', data);
}

/**
 * 获取用户的预约列表
 * @param {object} params - 查询参数
 *   - status: 预约状态 (0=pending, 1=checked-in, 2=completed, 3=cancelled)
 *   - start_date: 开始日期
 *   - end_date: 结束日期
 */
function getMyReservations(params = {}) {
  let queryStr = '';
  if (Object.keys(params).length > 0) {
    queryStr = '?' + Object.keys(params)
      .map(key => `${key}=${params[key]}`)
      .join('&');
  }
  return request('GET', '/reservations/my-reservations' + queryStr);
}

/**
 * 签到
 * @param {number} reservationId - 预约ID
 */
function checkIn(reservationId) {
  return request('POST', '/reservations/check-in', {
    reservation_id: reservationId
  });
}

/**
 * 签退
 * @param {number} reservationId - 预约ID
 */
function checkOut(reservationId) {
  return request('POST', '/reservations/check-out', {
    reservation_id: reservationId
  });
}

/**
 * 取消预约
 * @param {number} reservationId - 预约ID
 */
function cancelReservation(reservationId) {
  return request('POST', `/reservations/cancel/${reservationId}`, {});
}

/**
 * 扫描QR码签到
 * @param {string} qrCode - QR码内容
 */
function checkInWithQR(qrCode) {
  return request('POST', '/reservations/check-in-qr', {
    qr_code: qrCode
  });
}

/**
 * 报告座位维修问题
 * @param {object} data - 维修申报数据
 *   - seat_id: 座位ID
 *   - issue_type: 问题类型 (broken, dirty, furniture, electrical, other)
 *   - severity: 严重程度 (low, medium, high, critical)
 *   - description: 问题描述
 *   - phone: 联系电话 (可选)
 */
function reportMaintenance(data) {
  return request('POST', '/reservations/maintenance/report', data);
}

/**
 * 获取维修申报状态列表
 * @param {object} params - 查询参数
 *   - page: 页码 (默认1)
 *   - per_page: 每页数量 (默认10)
 *   - status: 筛选状态 (pending, in_progress, completed, cancelled)
 */
function getMaintenanceStatus(params = {}) {
  let queryStr = '';
  if (Object.keys(params).length > 0) {
    queryStr = '?' + Object.keys(params)
      .map(key => `${key}=${params[key]}`)
      .join('&');
  }
  return request('GET', '/reservations/maintenance/status' + queryStr);
}

/**
 * 获取推荐座位
 * @param {object} data - 请求数据
 *   - room_id: 阅览室ID
 *   - date: 日期 (YYYY-MM-DD)
 *   - time_slot: 时间段 (HH:MM-HH:MM)
 *   - count: 推荐数量 (默认5)
 */
function getRecommendedSeats(data) {
  return request('GET', '/reservations/recommend', data);
}

/**
 * 通用 GET 请求
 * @param {string} endpoint - 端点路径
 * @param {object} params - 查询参数
 */
function get(endpoint, params = {}) {
  let queryStr = '';
  
  // 构建查询字符串，跳过headers等特殊参数
  const queryParams = {};
  for (const key in params) {
    if (key !== 'headers' && params.hasOwnProperty(key)) {
      queryParams[key] = params[key];
    }
  }
  
  if (Object.keys(queryParams).length > 0) {
    queryStr = '?' + Object.keys(queryParams)
      .map(key => `${key}=${encodeURIComponent(queryParams[key])}`)
      .join('&');
  }
  
  return request('GET', endpoint + queryStr);
}

/**
 * 通用 POST 请求
 * @param {string} endpoint - 端点路径
 * @param {object} data - 请求数据
 */
function post(endpoint, data = {}) {
  return request('POST', endpoint, data);
}

/**
 * 通用 PUT 请求
 * @param {string} endpoint - 端点路径
 * @param {object} data - 请求数据
 */
function put(endpoint, data = {}) {
  return request('PUT', endpoint, data);
}

/**
 * 通用 DELETE 请求
 * @param {string} endpoint - 端点路径
 * @param {object} data - 请求数据
 */
function del(endpoint, data = {}) {
  return request('DELETE', endpoint, data);
}

// 导出接口
module.exports = {
  request,
  get,
  post,
  put,
  del,
  getSeats,
  submitReservation,
  getMyReservations,
  checkIn,
  checkOut,
  cancelReservation,
  checkInWithQR,
  reportMaintenance,
  getMaintenanceStatus,
  getRecommendedSeats,
  normalizeResponse
};

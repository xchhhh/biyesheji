/**
 * 灏忕▼搴忛厤缃枃浠?
 */

// API 鍩虹URL锛堝紑鍙戞椂浣跨敤鏈湴鍦板潃锛岀敓浜ф椂鏀逛负瀹為檯鏈嶅姟鍣ㄥ湴鍧€锛?
// 鏀寔鐜鍙橀噺鎴栨湰鍦板瓨鍌ㄧ殑閰嶇疆锛岄粯璁ゅ€间负鏈湴寮€鍙戝湴鍧€
const API_BASE_URL = wx.getStorageSync('apiBaseUrl') || 'http://192.168.10.6:5000/api';

// 搴旂敤閰嶇疆
const APP_CONFIG = {
  // 搴т綅鐩稿叧閰嶇疆
  SEAT: {
    ROWS: 15,      // 琛屾暟 (A-O琛?
    COLS: 10,      // 鍒楁暟
    TOTAL: 150,    // 鎬诲骇浣嶆暟 (15脳10)
  },

  // 棰勭害鐩稿叧閰嶇疆
  RESERVATION: {
    MAX_ADVANCE_DAYS: 7,  // 鏈€澶氭彁鍓嶉绾﹀ぉ鏁?
    CHECK_IN_TIMEOUT: 30, // 澶氬皯鍒嗛挓鍐呭繀椤荤鍒?(鍒嗛挓)
    MAX_DURATION: 480,    // 鏈€闀块绾︽椂闀?(鍒嗛挓)
    MIN_DURATION: 60,     // 鏈€鐭绾︽椂闀?(鍒嗛挓)
  },

  // 搴т綅鐘舵€佸€?
  SEAT_STATUS: {
    AVAILABLE: 0,      // 鍙€?
    OCCUPIED: 1,       // 宸插崰鐢?
    MAINTENANCE: 2,    // 缁存姢涓?
    MY_RESERVED: 3,    // 鎴戠殑棰勭害
  },

  // 棰勭害鐘舵€佸€?
  RESERVATION_STATUS: {
    PENDING: 0,        // 寰呯鍒?
    CHECKED_IN: 1,     // 宸茬鍒?
    COMPLETED: 2,      // 宸插畬鎴?
    CANCELLED: 3,      // 宸插彇娑?
    NO_SHOW: 4,        // 鏈嚭鐜?
  },

  // 淇＄敤绉垎閰嶇疆
  CREDIT: {
    NO_SHOW_PENALTY: -5,      // 缂虹害鎵ｅ垎
    CANCELLATION_PENALTY: -2, // 鍙栨秷棰勭害鎵ｅ垎
    COMPLETED_REWARD: 1,      // 瀹屾垚棰勭害鍔犲垎
  },

  // UI 鐩稿叧
  UI: {
    COLORS: {
      PRIMARY: '#3c6fda',
      SUCCESS: '#09bb07',
      ERROR: '#e64141',
      WARNING: '#ff9500',
      GRAY: '#999999',
    },
    TOAST_DURATION: 2000,
  },

  // 鏃堕棿娈甸厤缃?
  TIME_SLOTS: [
    { label: '08:00-10:00', start: '08:00', end: '10:00' },
    { label: '10:00-12:00', start: '10:00', end: '12:00' },
    { label: '13:00-15:00', start: '13:00', end: '15:00' },
    { label: '15:00-17:00', start: '15:00', end: '17:00' },
    { label: '17:00-19:00', start: '17:00', end: '19:00' },
    { label: '19:00-21:00', start: '19:00', end: '21:00' },
  ],
};

// 缂撳瓨閿?
const CACHE_KEYS = {
  TOKEN: 'token',
  USER_INFO: 'userInfo',
  SEATS_CACHE: 'seatsCache',
  RESERVATIONS_CACHE: 'reservationsCache',
};

// 瀛樺偍鐩稿叧鎿嶄綔
const storage = {
  /**
   * 璁剧疆缂撳瓨
   */
  set(key, value, ttl = null) {
    const data = {
      value: value,
      timestamp: Date.now(),
      ttl: ttl // null琛ㄧず姘镐箙瀛樺偍
    };
    wx.setStorageSync(key, JSON.stringify(data));
  },

  /**
   * 鑾峰彇缂撳瓨
   */
  get(key) {
    const data = wx.getStorageSync(key);
    if (!data) return null;

    try {
      const parsed = JSON.parse(data);
      
      // 妫€鏌ユ槸鍚﹁繃鏈?
      if (parsed.ttl && Date.now() - parsed.timestamp > parsed.ttl) {
        wx.removeStorageSync(key);
        return null;
      }

      return parsed.value;
    } catch (error) {
      console.error('缂撳瓨璇诲彇閿欒:', error);
      return null;
    }
  },

  /**
   * 绉婚櫎缂撳瓨
   */
  remove(key) {
    wx.removeStorageSync(key);
  },

  /**
   * 娓呯┖鎵€鏈夌紦瀛?
   */
  clear() {
    wx.clearStorageSync();
  }
};

module.exports = {
  API_BASE_URL,
  APP_CONFIG,
  CACHE_KEYS,
  storage
};

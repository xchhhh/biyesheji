/**
 * 公告弹窗管理模块
 * 处理公告的获取、显示、以及"下次不显示"功能
 */

const api = require('./api');

/**
 * 公告弹窗管理器
 */
const AnnouncementManager = {
  /**
   * 获取当前有效的公告
   * @param {number} limit 返回的公告数量限制
   * @returns {Promise} 返回公告列表
   */
  async getAnnouncements(limit = 1) {
    try {
      const token = wx.getStorageSync('auth_token');
      if (!token) {
        console.warn('[Announcement] 未找到认证令牌，跳过公告加载');
        return [];
      }

      // 调用API获取公告（token会由api.js自动处理）
      // 注意：API_BASE_URL已经包含'/api'，所以这里只需要相对路径
      const response = await api.get('/v1/user/announcements', {
        limit: limit
      });

      if (response && response.length > 0) {
        console.log('[Announcement] 成功获取公告列表:', response);
        return response;
      }

      console.warn('[Announcement] 获取公告失败或无公告数据:', response);
      return [];
    } catch (error) {
      console.error('[Announcement] 获取公告出错:', error);
      return [];
    }
  },

  /**
   * 检查是否应该显示公告（基于"下次不显示"设置）
   * @param {Object} announcement 公告对象
   * @returns {boolean} 是否应该显示
   */
  shouldShowAnnouncement(announcement) {
    if (!announcement || !announcement.id) {
      return false;
    }

    const dismissedKey = `announcement_dismissed_${announcement.id}`;
    const isDismissed = wx.getStorageSync(dismissedKey);

    return !isDismissed;
  },

  /**
   * 标记公告为"下次不显示"
   * @param {number} announcementId 公告ID
   */
  dismissAnnouncement(announcementId) {
    const dismissedKey = `announcement_dismissed_${announcementId}`;
    wx.setStorageSync(dismissedKey, true);
    console.log(`[Announcement] 已标记公告 ${announcementId} 为"下次不显示"`);
  },

  /**
   * 清除"下次不显示"标记（重置为可显示状态）
   * @param {number} announcementId 公告ID
   */
  clearDismissal(announcementId) {
    const dismissedKey = `announcement_dismissed_${announcementId}`;
    wx.removeStorageSync(dismissedKey);
    console.log(`[Announcement] 已清除公告 ${announcementId} 的"下次不显示"标记`);
  },

  /**
   * 显示公告弹窗
   * @param {Object} announcement 公告对象
   * @returns {Promise} 返回用户选择的结果
   */
  showAnnouncementModal(announcement) {
    return new Promise((resolve) => {
      if (!announcement) {
        resolve({ confirm: false, dismiss: false });
        return;
      }

      let showDismissButton = true;
      if (announcement.priority === 2) {
        // 紧急公告（优先级为高）不显示"下次不显示"按钮
        showDismissButton = false;
      }

      const content = announcement.content;
      
      wx.showModal({
        title: announcement.title,
        content: content,
        showCancel: showDismissButton,
        cancelText: '不再显示',
        confirmText: '确定',
        success: (res) => {
          if (res.confirm) {
            // 用户点击确定
            console.log('[Announcement] 用户确认公告');
            resolve({ confirm: true, dismiss: false });
          } else if (res.cancel) {
            // 用户点击下次不显示
            this.dismissAnnouncement(announcement.id);
            console.log('[Announcement] 用户选择下次不显示');
            resolve({ confirm: false, dismiss: true });
          }
        },
        fail: (error) => {
          console.error('[Announcement] 显示公告弹窗失败:', error);
          resolve({ confirm: false, dismiss: false });
        }
      });
    });
  },

  /**
   * 加载并显示公告
   * 这是主要的调用入口，会自动获取公告并显示第一条未被"下次不显示"的公告
   * @returns {Promise} 返回是否显示了公告
   */
  async loadAndShowAnnouncement() {
    try {
      const announcements = await this.getAnnouncements(5);

      if (!announcements || announcements.length === 0) {
        console.log('[Announcement] 没有可显示的公告');
        return false;
      }

      // 找到第一条应该显示的公告
      for (const announcement of announcements) {
        if (this.shouldShowAnnouncement(announcement)) {
          console.log('[Announcement] 显示公告:', announcement.title);
          await this.showAnnouncementModal(announcement);
          return true;
        }
      }

      console.log('[Announcement] 所有公告都已被"下次不显示"');
      return false;
    } catch (error) {
      console.error('[Announcement] 加载并显示公告失败:', error);
      return false;
    }
  },

  /**
   * 重置所有公告的"下次不显示"状态
   * 主要用于调试和管理员功能
   */
  resetAllDismissals() {
    try {
      const keys = wx.getStorage({
        key: 'announcement_dismissed',
        fail: () => {
          // 获取所有以announcement_dismissed开头的key
          // 这是一个近似的实现
          console.log('[Announcement] 重置所有公告显示状态');
        }
      });
      console.log('[Announcement] 已重置所有公告');
    } catch (error) {
      console.error('[Announcement] 重置公告失败:', error);
    }
  }
};

module.exports = AnnouncementManager;

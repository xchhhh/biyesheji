const config = require('../../../utils/config');

Page({
  data: {
    userInfo: null,
    hasUserInfo: false,
    showPasswordModal: false,
    showDeactivateModal: false,
    isChangingPassword: false,
    isDeactivating: false,
    passwordForm: {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    },
    deactivatePassword: ''
  },

  onLoad() {
    this.loadUserProfile();
  },

  onShow() {
    this.loadUserProfile();
  },

  // 加载用户信息
  loadUserProfile() {
    const token = wx.getStorageSync('auth_token');
    const userId = wx.getStorageSync('user_id');

    if (!token || !userId) {
      this.setData({ hasUserInfo: false });
      return;
    }

    wx.request({
      url: `${config.API_BASE_URL}/user/profile`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (response) => {
        console.log('[account.js] 获取用户信息成功', response);
        
        if (response.statusCode === 200 && response.data.data) {
          const userData = response.data.data;
          const avatarChar = (userData.real_name || '用户').charAt(0);
          
          this.setData({
            userInfo: {
              ...userData,
              avatarChar,
              created_at: this.formatDate(userData.created_at)
            },
            hasUserInfo: true
          });
        }
      },
      fail: (error) => {
        console.error('[account.js] 获取用户信息失败', error);
        wx.showToast({
          title: '加载用户信息失败',
          icon: 'error'
        });
      }
    });
  },

  // 打开修改密码弹窗
  onChangePassword() {
    this.setData({
      showPasswordModal: true,
      passwordForm: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    });
  },

  // 关闭修改密码弹窗
  closePasswordModal() {
    this.setData({ showPasswordModal: false });
  },

  // 处理密码输入
  onPasswordInput(event) {
    const { field } = event.currentTarget.dataset;
    const { value } = event.detail;
    
    const passwordForm = this.data.passwordForm;
    passwordForm[field] = value;
    
    this.setData({ passwordForm });
  },

  // 提交修改密码
  submitPasswordChange() {
    const { passwordForm } = this.data;
    
    // 验证
    if (!passwordForm.oldPassword) {
      wx.showToast({
        title: '请输入旧密码',
        icon: 'error'
      });
      return;
    }

    if (!passwordForm.newPassword) {
      wx.showToast({
        title: '请输入新密码',
        icon: 'error'
      });
      return;
    }

    if (passwordForm.newPassword.length < 6) {
      wx.showToast({
        title: '新密码至少6个字符',
        icon: 'error'
      });
      return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      wx.showToast({
        title: '两次输入的密码不一致',
        icon: 'error'
      });
      return;
    }

    const token = wx.getStorageSync('auth_token');
    
    this.setData({ isChangingPassword: true });

    wx.request({
      url: `${config.API_BASE_URL}/user/change-password`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        old_password: passwordForm.oldPassword,
        new_password: passwordForm.newPassword,
        confirm_password: passwordForm.confirmPassword
      },
      success: (response) => {
        this.setData({ isChangingPassword: false });
        
        if (response.statusCode === 200) {
          wx.showToast({
            title: '密码修改成功',
            icon: 'success'
          });
          this.closePasswordModal();
        } else {
          wx.showToast({
            title: response.data.message || '修改失败',
            icon: 'error'
          });
        }
      },
      fail: (error) => {
        this.setData({ isChangingPassword: false });
        console.error('[account.js] 修改密码请求失败', error);
        wx.showToast({
          title: '网络错误，请重试',
          icon: 'error'
        });
      }
    });
  },

  // 打开注销确认弹窗
  onDeactivate() {
    wx.showModal({
      title: '注意',
      content: '注销账户是不可逆的操作，确定要继续吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            showDeactivateModal: true,
            deactivatePassword: ''
          });
        }
      }
    });
  },

  // 关闭注销弹窗
  closeDeactivateModal() {
    this.setData({ showDeactivateModal: false });
  },

  // 处理注销密码输入
  onDeactivatePasswordInput(event) {
    this.setData({
      deactivatePassword: event.detail.value
    });
  },

  // 确认注销
  confirmDeactivate() {
    const { deactivatePassword } = this.data;
    
    if (!deactivatePassword) {
      wx.showToast({
        title: '请输入密码',
        icon: 'error'
      });
      return;
    }

    const token = wx.getStorageSync('auth_token');
    
    this.setData({ isDeactivating: true });

    wx.request({
      url: `${config.API_BASE_URL}/user/deactivate`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        password: deactivatePassword
      },
      success: (response) => {
        this.setData({ isDeactivating: false });
        
        if (response.statusCode === 200) {
          wx.showToast({
            title: '账户已注销',
            icon: 'success'
          });
          
          // 清除本地存储
          wx.clearStorageSync();
          
          // 返回登录页面
          setTimeout(() => {
            wx.redirectTo({
              url: '/pages/login/login'
            });
          }, 1500);
        } else {
          wx.showToast({
            title: response.data.message || '注销失败',
            icon: 'error'
          });
        }
      },
      fail: (error) => {
        this.setData({ isDeactivating: false });
        console.error('[account.js] 注销请求失败', error);
        wx.showToast({
          title: '网络错误，请重试',
          icon: 'error'
        });
      }
    });
  },

  // 查看统计
  onCheckStatistics() {
    wx.navigateTo({
      url: '/pages/my/statistics/statistics'
    });
  },

  // 格式化日期
  formatDate(dateStr) {
    if (!dateStr) return '--';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN');
  }
});

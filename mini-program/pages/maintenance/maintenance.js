// 座位维修申请页面
const api = require('../../utils/api');
const app = getApp();

Page({
  data: {
    // 页面状态
    activeTab: 0,  // 0=申报维修, 1=申报历史
    isLoading: false,
    isSubmitting: false,
    
    // 申报维修表单数据
    seatInput: '',
    issueType: 'broken',  // 问题类型
    severity: 'medium',    // 严重程度
    description: '',
    phone: '',
    
    // 问题类型选项
    issueTypes: [
      { value: 'broken', label: '座位损坏', icon: '🔨' },
      { value: 'dirty', label: '座位脏污', icon: '🧹' },
      { value: 'furniture', label: '家具问题', icon: '🪑' },
      { value: 'electrical', label: '电气问题', icon: '⚡' },
      { value: 'other', label: '其他问题', icon: '❓' }
    ],
    
    // 严重程度选项
    severities: [
      { value: 'low', label: '低' },
      { value: 'medium', label: '中' },
      { value: 'high', label: '高' },
      { value: 'critical', label: '严重' }
    ],
    
    // 维修申报历史
    maintenanceList: [],
    currentPage: 1,
    totalPages: 1,
    
    // 筛选条件
    statusFilter: '',
    statusOptions: [
      { value: '', label: '全部' },
      { value: 'pending', label: '待处理' },
      { value: 'in_progress', label: '处理中' },
      { value: 'completed', label: '已完成' }
    ]
  },

  onLoad() {
    // 检查登录状态
    const token = wx.getStorageSync('auth_token');
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'error'
      });
      setTimeout(() => {
        wx.navigateTo({
          url: '/pages/login/login'
        });
      }, 1000);
      return;
    }
    
    // 获取用户电话号码作为默认值
    const phone = wx.getStorageSync('phone_number');
    this.setData({ phone });
  },

  onShow() {
    // 每次显示页面时刷新维修申报历史
    this.loadMaintenanceHistory();
  },

  /**
   * 切换标签页
   */
  onTabChange(e) {
    const activeTab = e.currentTarget.dataset.tab;
    this.setData({ activeTab });
    
    if (activeTab === 1) {
      this.loadMaintenanceHistory();
    }
  },

  /**
   * 获取焦点时更新手机号
   */
  onInputFocus() {
    const phone = wx.getStorageSync('phone_number');
    this.setData({ phone });
  },

  /**
   * 输入框变化处理
   */
  onInput(e) {
    const { field } = e.currentTarget.dataset;
    const value = e.detail.value;
    this.setData({ [field]: value });
  },

  /**
   * 问题类型选择
   */
  onIssueTypeChange(e) {
    const issueType = e.currentTarget.dataset.type;
    this.setData({ issueType });
  },

  /**
   * 严重程度选择
   */
  onSeverityChange(e) {
    const severity = e.currentTarget.dataset.severity;
    this.setData({ severity });
  },

  /**
   * 扫描二维码获取座位号
   */
  onScanQRCode() {
    wx.scanCode({
      onlyFromCamera: true,
      scanType: ['qrCode'],
      success: (res) => {
        // 从二维码数据中提取座位号
        // 假设格式为: seat:seat_id:date:time_slot 或 seat-001 等
        let seatNumber = res.result;
        
        // 尝试从不同格式中提取座位号
        if (seatNumber.includes(':')) {
          const parts = seatNumber.split(':');
          seatNumber = parts[0];
        }
        
        this.setData({ seatInput: seatNumber });
        
        wx.showToast({
          title: '扫描成功',
          icon: 'success'
        });
      },
      fail: () => {
        wx.showToast({
          title: '扫描失败',
          icon: 'error'
        });
      }
    });
  },

  /**
   * 提交维修申报
   */
  onSubmit() {
    const { seatInput, issueType, severity, description, phone } = this.data;
    
    // 输入验证
    if (!seatInput.trim()) {
      wx.showToast({
        title: '请输入座位号',
        icon: 'error'
      });
      return;
    }
    
    if (!description.trim()) {
      wx.showToast({
        title: '请描述问题',
        icon: 'error'
      });
      return;
    }
    
    if (description.length < 5) {
      wx.showToast({
        title: '问题描述至少需要5个字符',
        icon: 'error'
      });
      return;
    }
    
    // 准备提交数据
    const submitData = {
      seat_id: this.parseSeatsId(seatInput),
      issue_type: issueType,
      severity: severity,
      description: description.trim(),
      phone: phone.trim()
    };
    
    // 验证座位ID是否有效
    if (!submitData.seat_id || submitData.seat_id <= 0) {
      wx.showToast({
        title: '座位号格式不正确',
        icon: 'error'
      });
      return;
    }
    
    this.submitMaintenance(submitData);
  },

  /**
   * 解析座位号为座位ID
   * 支持的格式: A-001, A001, 1100等
   */
  parseSeatsId(seatInput) {
    const input = seatInput.toUpperCase().trim();
    
    // 如果是纯数字，直接返回
    if (/^\d+$/.test(input)) {
      return parseInt(input);
    }
    
    // 如果是座位号格式 (A-001 或 A001)
    const match = input.match(/^([A-O])[-]?(\d+)$/);
    if (match) {
      const row = match[1].charCodeAt(0) - 'A'.charCodeAt(0);  // A=0, B=1...O=14
      const col = parseInt(match[2]);
      
      // 按照150座位布局计算座位ID（以1100开始作为base）
      // 假设座位ID: row * 10 + col + 1100
      const seatId = row * 10 + col + 1100;
      return seatId;
    }
    
    return null;
  },

  /**
   * 提交维修申报到后端
   */
  submitMaintenance(data) {
    this.setData({ isSubmitting: true });
    
    const token = wx.getStorageSync('auth_token');
    
    api.reportMaintenance(data)
      .then(response => {
        console.log('[maintenance.js] 维修申报响应:', response);
        
        // 申报成功
        wx.showToast({
          title: '申报成功',
            icon: 'success',
            duration: 2000
          });
          
          // 清空表单
          this.setData({
            seatInput: '',
            issueType: 'broken',
            severity: 'medium',
            description: '',
            isSubmitting: false,
            activeTab: 1  // 切换到历史记录主页
          });
          
          // 延迟加载历史记录
          setTimeout(() => {
            this.loadMaintenanceHistory();
          }, 1000);
      })
      .catch(error => {
        console.error('[maintenance.js] 维修申报失败:', error);
        let errorMsg = error.message || '申报失败，请重试';
        
        if (error.code === -1 && error.message?.includes('timeout')) {
          errorMsg = '请求超时，请检查网络';
        }
        
        wx.showToast({
          title: errorMsg,
          icon: 'error'
        });
        
        this.setData({ isSubmitting: false });
      });
  },

  /**
   * 加载维修申报历史
   */
  loadMaintenanceHistory() {
    this.setData({ isLoading: true });
    
    const token = wx.getStorageSync('auth_token');
    const { currentPage, statusFilter } = this.data;
    
    // 构建查询参数
    const params = {
      page: currentPage,
      per_page: 10
    };
    if (statusFilter) {
      params.status = statusFilter;
    }
    
    api.getMaintenanceStatus(params)
      .then(response => {
        console.log('[maintenance.js] 维修申报历史响应:', response);
        
        const listData = response?.maintenance_requests || [];
        const pagination = response || {};
        
        this.setData({
          maintenanceList: this.formatMaintenanceData(listData),
          totalPages: pagination.pages || 1,
          isLoading: false
        });
      })
      .catch(error => {
        console.error('[maintenance.js] 加载维修申报历史失败:', error);
        this.setData({ isLoading: false });
        
        wx.showToast({
          title: error.message || '加载失败',
          icon: 'error'
        });
      });
  },

  /**
   * 格式化维修数据用于显示
   */
  formatMaintenanceData(data) {
    return data.map(item => ({
      ...item,
      // 添加状态颜色和图标
      statusColor: this.getStatusColor(item.status),
      statusIcon: this.getStatusIcon(item.status),
      severityColor: this.getSeverityColor(item.severity),
      createdAt: this.formatDate(item.created_at)
    }));
  },

  /**
   * 获取状态颜色
   */
  getStatusColor(status) {
    const colorMap = {
      'pending': '#FF9800',      // 橙色
      'in_progress': '#2196F3',  // 蓝色
      'completed': '#4CAF50',    // 绿色
      'cancelled': '#999999'     // 灰色
    };
    return colorMap[status] || '#999999';
  },

  /**
   * 获取状态图标
   */
  getStatusIcon(status) {
    const iconMap = {
      'pending': '⏳',
      'in_progress': '🔧',
      'completed': '✅',
      'cancelled': '❌'
    };
    return iconMap[status] || '❓';
  },

  /**
   * 获取严重程度颜色
   */
  getSeverityColor(severity) {
    const colorMap = {
      'low': '#4CAF50',      // 绿色
      'medium': '#FF9800',   // 橙色
      'high': '#F44336',     // 红色
      'critical': '#9C27B0'  // 紫色
    };
    return colorMap[severity] || '#999999';
  },

  /**
   * 格式化日期
   */
  formatDate(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    // 计算时间差
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor(diff / (1000 * 60));
    
    if (days > 0) {
      return `${days}天前`;
    } else if (hours > 0) {
      return `${hours}小时前`;
    } else if (minutes > 0) {
      return `${minutes}分钟前`;
    } else {
      return '刚刚';
    }
  },

  /**
   * 筛选状态变化
   */
  onStatusFilterChange(e) {
    const status = e.currentTarget.dataset.status;
    this.setData({
      statusFilter: status,
      currentPage: 1
    });
    
    // 重新加载
    this.loadMaintenanceHistory();
  },

  /**
   * 点击维修申报卡片查看详情
   */
  onMaintenanceCardTap(e) {
    const { id } = e.currentTarget.dataset;
    const maintenance = this.data.maintenanceList.find(m => m.id === id);
    
    if (!maintenance) return;
    
    // 显示详情对话框
    wx.showModal({
      title: `座位 ${maintenance.seat_number} 维修详情`,
      content: `
问题类型: ${maintenance.issue_type_text}
严重程度: ${maintenance.severity_text}
当前状态: ${maintenance.status_text}
描述: ${maintenance.description}
申报时间: ${maintenance.created_at}
${maintenance.assigned_to_name ? `处理人: ${maintenance.assigned_to_name}` : ''}
${maintenance.notes ? `处理备注: ${maintenance.notes}` : ''}
      `,
      showCancel: false,
      confirmText: '关闭'
    });
  },

  /**
   * 分页加载 - 上拉加载
   */
  onReachBottom() {
    const { currentPage, totalPages } = this.data;
    
    if (currentPage < totalPages) {
      this.setData({
        currentPage: currentPage + 1
      });
      
      this.loadMoreMaintenanceHistory();
    }
  },

  /**
   * 加载更多维修申报历史
   */
  loadMoreMaintenanceHistory() {
    const token = wx.getStorageSync('auth_token');
    const { currentPage, statusFilter, maintenanceList } = this.data;
    
    const params = {
      page: currentPage,
      per_page: 10
    };
    if (statusFilter) {
      params.status = statusFilter;
    }
    
    api.getMaintenanceStatus(params)
      .then(response => {
        const listData = response?.maintenance_requests || [];
        
        this.setData({
          maintenanceList: maintenanceList.concat(
            this.formatMaintenanceData(listData)
          )
        });
      })
      .catch(error => {
        console.error('[maintenance.js] 加载更多历史失败:', error);
      });
  }
});

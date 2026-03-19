Page({
  data: {
    phoneNumber: '',
    password: '',
    isLoading: false,
    errorMessage: '',
    rememberMe: false
  },

  onLoad() {
    // 检查是否已保存的登录信息
    const savedPhone = wx.getStorageSync('savedPhone')
    if (savedPhone) {
      this.setData({
        phoneNumber: savedPhone,
        rememberMe: true
      })
    }
    console.log('登录页面加载完成')
  },

  // 手机号输入
  onPhoneInput(e) {
    this.setData({
      phoneNumber: e.detail.value
    })
    this.setData({ errorMessage: '' })
  },

  // 密码输入
  onPasswordInput(e) {
    this.setData({
      password: e.detail.value
    })
    this.setData({ errorMessage: '' })
  },

  // 记住我 toggle
  onRememberMeChange(e) {
    this.setData({
      rememberMe: e.detail.value
    })
  },

  // 表单验证
  validateForm() {
    const { phoneNumber, password } = this.data

    if (!phoneNumber) {
      this.setData({ errorMessage: '请输入手机号码' })
      return false
    }

    if (!/^1[3-9]\d{9}$/.test(phoneNumber)) {
      this.setData({ errorMessage: '请输入有效的手机号码' })
      return false
    }

    if (!password) {
      this.setData({ errorMessage: '请输入密码' })
      return false
    }

    return true
  },

  // 登录处理
  onLogin() {
    if (!this.validateForm()) {
      console.log('表单验证失败')
      return
    }

    this.setData({ isLoading: true })
    const { phoneNumber, password, rememberMe } = this.data
    const config = require('../../utils/config')
    const baseUrl = config.API_BASE_URL

    console.log('开始登录，URL:', `${baseUrl}/auth/login`)
    console.log('请求数据:', { phone_number: phoneNumber, password: password })
    console.log('当前时间:', new Date().toLocaleString())

    wx.request({
      url: `${baseUrl}/auth/login`,
      method: 'POST',
      data: {
        phone_number: phoneNumber,
        password: password
      },
      header: {
        'Content-Type': 'application/json'
      },
      timeout: 15000,  // 增加超时时间到15秒
      success: (response) => {
        console.log('登录响应状态:', response.statusCode)
        console.log('登录响应数据:', response.data)
        const { statusCode, data: responseData } = response

        if (statusCode === 200) {
          // 后端返回的data结构: { code, message, data: { access_token, user_id, ... } }
          const { data } = responseData
          
          // 保存token和用户信息
          if (data && data.access_token) {
            console.log('开始保存登录数据...')
            wx.setStorageSync('auth_token', data.access_token)
            wx.setStorageSync('user_id', data.user_id)
            wx.setStorageSync('phone_number', phoneNumber)
            wx.setStorageSync('real_name', data.user?.real_name || '用户')
            wx.setStorageSync('student_id', data.user?.student_id || '')
            
            // 验证保存是否成功
            const savedToken = wx.getStorageSync('auth_token')
            const savedPhone = wx.getStorageSync('phone_number')
            console.log('保存验证 - token保存成功:', !!savedToken, '- phone保存成功:', !!savedPhone)
          }

          // 记住手机号
          if (rememberMe) {
            wx.setStorageSync('savedPhone', phoneNumber)
          } else {
            wx.removeStorageSync('savedPhone')
          }

          console.log('登录成功，保存数据...')
          this.setData({ isLoading: false })

          // 延迟200ms后跳转，给storage保存时间
          setTimeout(() => {
            console.log('跳转到座位页面...')
            wx.switchTab({
              url: '/pages/seats/seats'
            })
          }, 200)
        } else {
          const errorMsg = responseData.message || responseData.error || `登录失败(${statusCode})，请重试`
          console.log('登录失败:', errorMsg)
          this.setData({ errorMessage: errorMsg, isLoading: false })
        }
      },
      fail: (error) => {
        console.error('登录网络错误:', error)
        this.setData({ errorMessage: '网络连接失败，请检查网络并重试', isLoading: false })
      }
    })
  },

  // 忘记密码
  onForgotPassword() {
    wx.showModal({
      title: '忘记密码',
      content: '请联系管理员重置密码',
      showCancel: false,
      confirmText: '我知道了'
    })
  },

  // 跳转到注册页
  onGoToRegister() {
    wx.navigateTo({
      url: '/pages/register/register'
    })
  },

  // 页面卸载
  onUnload() {
    console.log('登录页面已卸载')
  }
})

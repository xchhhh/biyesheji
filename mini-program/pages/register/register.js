Page({
  data: {
    currentStep: 1,
    phoneNumber: '',
    password: '',
    confirmPassword: '',
    studentId: '',
    realName: '',
    isLoading: false,
    errorMessage: '',
    successMessage: '',
    passwordStrength: '',
    passwordStrengthText: ''
  },

  onLoad() {
    // 页面加载时的初始化
    console.log('注册页面已加载')
  },

  // 步骤控制
  onNextStep() {
    this.setData({ errorMessage: '' });
    
    // 验证当前步骤
    if (this.data.currentStep === 1) {
      if (!this.data.realName) {
        this.setData({ errorMessage: '请输入真实姓名' });
        return;
      }
      if (!this.data.studentId) {
        this.setData({ errorMessage: '请输入学号' });
        return;
      }
    } else if (this.data.currentStep === 2) {
      if (!this.data.phoneNumber) {
        this.setData({ errorMessage: '请输入手机号码' });
        return;
      }
      if (!/^1[3-9]\d{9}$/.test(this.data.phoneNumber)) {
        this.setData({ errorMessage: '手机号格式不正确' });
        return;
      }
    }

    this.setData({ 
      currentStep: this.data.currentStep + 1
    });
  },

  onPrevStep() {
    this.setData({ 
      currentStep: this.data.currentStep - 1,
      errorMessage: ''
    });
  },

  // 密码强度检测
  calculatePasswordStrength(password) {
    if (!password) {
      this.setData({ passwordStrength: '', passwordStrengthText: '' });
      return;
    }
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-zA-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    if (password.length < 6 || strength <= 1) {
      this.setData({ passwordStrength: 'weak', passwordStrengthText: '弱' });
    } else if (strength === 2) {
      this.setData({ passwordStrength: 'medium', passwordStrengthText: '中' });
    } else {
      this.setData({ passwordStrength: 'strong', passwordStrengthText: '强' });
    }
  },

  // 输入框绑定
  onPhoneInput(e) {
    this.setData({
      phoneNumber: e.detail.value,
      errorMessage: ''
    })
  },

  onPasswordInput(e) {
    const pwd = e.detail.value;
    this.setData({
      password: pwd,
      errorMessage: ''
    });
    this.calculatePasswordStrength(pwd);
  },

  onConfirmPasswordInput(e) {
    this.setData({
      confirmPassword: e.detail.value
    })
    this.setData({ errorMessage: '' })
  },

  onStudentIdInput(e) {
    this.setData({
      studentId: e.detail.value
    })
    this.setData({ errorMessage: '' })
  },

  onRealNameInput(e) {
    this.setData({
      realName: e.detail.value
    })
    this.setData({ errorMessage: '' })
  },

  // 表单验证
  validateForm() {
    const { phoneNumber, password, confirmPassword, studentId, realName } = this.data

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

    if (password.length < 6) {
      this.setData({ errorMessage: '密码长度至少为6位' })
      return false
    }

    if (!confirmPassword) {
      this.setData({ errorMessage: '请确认密码' })
      return false
    }

    if (password !== confirmPassword) {
      this.setData({ errorMessage: '两次输入的密码不一致' })
      return false
    }

    if (!studentId) {
      this.setData({ errorMessage: '请输入学号' })
      return false
    }

    if (!realName) {
      this.setData({ errorMessage: '请输入真实姓名' })
      return false
    }

    return true
  },

  // 注册按钮
  async onRegister() {
    if (!this.validateForm()) {
      return
    }

    this.setData({ isLoading: true })

    try {
      const config = require('../../utils/config');
      const { phoneNumber, password, studentId, realName } = this.data
      const baseUrl = config.API_BASE_URL

      const response = await new Promise((resolve, reject) => {
        wx.request({
          url: `${baseUrl}/auth/register`,
          method: 'POST',
          data: {
            phone_number: phoneNumber,
            password: password,
            student_id: studentId,
            real_name: realName
          },
          header: {
            'Content-Type': 'application/json'
          },
          success: (res) => resolve(res),
          fail: (err) => reject(err)
        })
      })

      if (response.statusCode === 201 || response.statusCode === 200) {
        const { data: responseData } = response
        const { data } = responseData
        
        this.setData({
          successMessage: '注册成功！',
          phoneNumber: '',
          password: '',
          confirmPassword: '',
          studentId: '',
          realName: ''
        })

        // 保存token
        if (data && data.access_token) {
          wx.setStorageSync('auth_token', data.access_token)
          wx.setStorageSync('user_id', data.user_id)
          wx.setStorageSync('phone_number', phoneNumber)
          wx.setStorageSync('real_name', data.user?.real_name || '用户')
          wx.setStorageSync('student_id', data.user?.student_id || '')
        }

        // 2秒后跳转到登录页或首页
        setTimeout(() => {
          wx.navigateTo({
            url: '/pages/seats/seats'
          })
        }, 2000)
      } else {
        const errorMsg = response.data.message || response.data.error || '注册失败，请重试'
        this.setData({ errorMessage: errorMsg })
      }
    } catch (error) {
      console.error('注册请求失败:', error)
      this.setData({ errorMessage: '网络连接失败，请检查网络并重试' })
    } finally {
      this.setData({ isLoading: false })
    }
  },

  // 跳转到登录页
  onGoToLogin() {
    wx.navigateTo({
      url: '/pages/login/login'
    })
  },

  // 页面卸载
  onUnload() {
    console.log('注册页面已卸载')
  }
})

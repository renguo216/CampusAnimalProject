const api = require('../../utils/api.js');

Page({
  data: {
    userInfo: null,
    loading: false,
    applyContent: '',
    isAgreed: false,
    isAlreadyVolunteer: false
  },

  onLoad: function() {
    this.checkUserRole();
  },

  goBack: function() {
    wx.navigateBack();
  },

  checkUserRole: function() {
    const userInfo = wx.getStorageSync('userInfo');
    console.log('当前用户信息:', userInfo);
    if (!userInfo || !userInfo.user_id) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    
    this.setData({ userInfo: userInfo });
    
    // 检查用户角色：role=2 表示志愿者
    if (userInfo.role === 2) {
      this.setData({ isAlreadyVolunteer: true });
      wx.showModal({
        title: '已是志愿者',
        content: '您已经是志愿者，无需重复申请。',
        showCancel: false,
        success: () => {
          wx.navigateBack();
        }
      });
      return;
    }
    
    // role=3 表示管理员
    if (userInfo.role === 3) {
      wx.showModal({
        title: '提示',
        content: '管理员身份无需申请志愿者。',
        showCancel: false,
        success: () => {
          wx.navigateBack();
        }
      });
      return;
    }
  },

  loadUserInfo: function() {
    const userInfo = wx.getStorageSync('userInfo');
    console.log('当前用户信息:', userInfo);
    if (userInfo) {
      this.setData({ userInfo: userInfo });
    }
  },

  submitApplication: async function() {
    console.log('=== 提交志愿者申请 ===');
    console.log('当前数据:', this.data);
    
    const { userInfo } = this.data;
    
    if (!userInfo || !userInfo.user_id) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    console.log('申请理由:', this.data.applyContent);
    if (!this.data.applyContent || this.data.applyContent.trim().length === 0) {
      wx.showToast({ title: '请输入申请理由', icon: 'none' });
      return;
    }

    console.log('是否同意协议:', this.data.isAgreed);
    if (!this.data.isAgreed) {
      wx.showToast({ title: '请先阅读并同意相关协议', icon: 'none' });
      return;
    }

    try {
      this.setData({ loading: true });
      wx.showLoading({ title: '提交中...' });
      
      const applicationData = {
        user_id: userInfo.user_id,
        nickname: userInfo.nickname || '',
        phone_number: userInfo.phone_number || '',
        apply_content: this.data.applyContent
      };

      console.log('准备提交的数据:', applicationData);
      const result = await api.applyVolunteer(applicationData);
      console.log('API 返回结果:', result);
      wx.hideLoading();

      if (result.success) {
        wx.showModal({
          title: '提交成功',
          content: '您的志愿者申请已提交，请耐心等待审核。',
          showCancel: false,
          success: () => {
            wx.navigateBack();
          }
        });
      } else {
        wx.showToast({ title: result.message || '提交失败', icon: 'none' });
      }
    } catch (error) {
      wx.hideLoading();
      console.error('提交异常:', error);
      wx.showToast({ title: '提交失败，请重试', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  onContentInput: function(e) {
    this.setData({ applyContent: e.detail.value });
  },

  onAgreementChange: function(e) {
    console.log('协议勾选变更:', e.detail.value);
    const isAgreed = e.detail.value && e.detail.value.includes('agree');
    this.setData({ isAgreed: isAgreed });
    console.log('更新后的 isAgreed:', isAgreed);
  }
});

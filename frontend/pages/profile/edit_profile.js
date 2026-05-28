const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userInfo: {
      nickname: '',
      avatarUrl: '',
      phone: '',
      identityNo: '',
      gender: 0
    },
    tempAvatarUrl: '',
    showPhoneInput: false,
    showIdentityInput: false
  },

  onLoad: function() {
    this.loadUserInfo();
  },

  onShow: function() {
    this.loadUserInfo();
  },

  loadUserInfo: function() {
    const userInfo = app.globalData.userInfo || {};
    this.setData({
      userInfo: {
        nickname: userInfo.nickname || '',
        avatarUrl: userInfo.avatarUrl || '',
        phone: userInfo.phone || '',
        identityNo: userInfo.identityNo || '',
        gender: userInfo.gender || 0
      },
      tempAvatarUrl: userInfo.avatarUrl || ''
    });
  },

  chooseAvatar: function() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({
          tempAvatarUrl: res.tempFilePaths[0]
        });
      }
    });
  },

  onNicknameInput: function(e) {
    this.setData({
      'userInfo.nickname': e.detail.value
    });
  },

  onPhoneInput: function(e) {
    this.setData({
      'userInfo.phone': e.detail.value
    });
  },

  onIdentityInput: function(e) {
    this.setData({
      'userInfo.identityNo': e.detail.value
    });
  },

  saveUserInfo: function() {
    const userInfo = this.data.userInfo;
    
    if (!userInfo.nickname || userInfo.nickname.trim() === '') {
      wx.showToast({
        title: '请输入昵称',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({ title: '保存中...' });

    const updateData = {
      nickname: userInfo.nickname,
      avatarURL: this.data.tempAvatarUrl || userInfo.avatarUrl,
      phone: userInfo.phone,
      identityNo: userInfo.identityNo,
      gender: userInfo.gender
    };

    api.updateUserInfo(updateData).then(res => {
      wx.hideLoading();
      if (res.success) {
        app.globalData.userInfo = {
          ...app.globalData.userInfo,
          ...updateData
        };
        
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });
        
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        wx.showToast({
          title: res.message || '保存失败',
          icon: 'none'
        });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('保存用户信息失败:', err);
      wx.showToast({
        title: '网络错误，请重试',
        icon: 'none'
      });
    });
  },

  goBack: function() {
    wx.navigateBack();
  }
});
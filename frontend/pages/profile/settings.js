const app = getApp();

Page({
  data: {
    version: '1.0.0',
    notificationEnabled: true,
    locationEnabled: true
  },

  onLoad: function() {
    this.checkVersion();
  },

  checkVersion: function() {
    wx.request({
      url: 'http://192.168.85.73:3000/api/v1/version',
      method: 'GET',
      success: (res) => {
        if (res.data.success && res.data.version) {
          this.setData({ version: res.data.version });
        }
      }
    });
  },

  toggleNotification: function(e) {
    const enabled = e.detail.value;
    this.setData({ notificationEnabled: enabled });
    wx.showToast({
      title: enabled ? '已开启通知' : '已关闭通知',
      icon: 'none'
    });
  },

  toggleLocation: function(e) {
    const enabled = e.detail.value;
    this.setData({ locationEnabled: enabled });
    wx.showToast({
      title: enabled ? '已开启位置权限' : '已关闭位置权限',
      icon: 'none'
    });
  },

  clearCache: function() {
    wx.showModal({
      title: '提示',
      content: '确定要清除缓存吗？',
      success: (res) => {
        if (res.confirm) {
          wx.clearStorageSync();
          wx.showToast({
            title: '缓存已清除',
            icon: 'success'
          });
        }
      }
    });
  },

  checkUpdate: function() {
    wx.showToast({
      title: '已是最新版本',
      icon: 'success'
    });
  },

  aboutUs: function() {
    wx.showModal({
      title: '关于我们',
      content: '校园宠物平台 v1.0.0\n\n我们致力于帮助流浪动物，为校园内的宠物提供一个温暖的家园。\n\n联系我们：support@campus-pets.com',
      showCancel: false
    });
  },

  logout: function() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.globalData.token = null;
          app.globalData.userInfo = null;
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      }
    });
  }
});

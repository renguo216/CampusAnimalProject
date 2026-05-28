const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userInfo: {},
    stats: {
      likes: 0,
      following: 0,
      fans: 0
    }
  },

  onShow: function() {
    this.setData({
      userInfo: app.globalData.userInfo || {}
    });
    this.loadStats();
  },

  loadStats: function() {
    setTimeout(() => {
      this.setData({
        stats: {
          likes: 128,
          following: 45,
          fans: 67
        }
      });
    }, 500);
  },

  goToEditProfile: function() {
    wx.navigateTo({
      url: '/pages/profile/edit_profile'
    });
  },

  viewLikes: function() {
    wx.showToast({ title: '我的获赞', icon: 'none' });
  },

  viewFollowing: function() {
    wx.showToast({ title: '我的关注', icon: 'none' });
  },

  viewFans: function() {
    wx.showToast({ title: '我的粉丝', icon: 'none' });
  },

  goToMyReports: function() {
    wx.showToast({ title: '我上报的救助记录', icon: 'none' });
  },

  goToMyHelps: function() {
    wx.showToast({ title: '我参与帮助的救助', icon: 'none' });
  },

  goToMyAdoptions: function() {
    wx.showToast({ title: '我的领养记录', icon: 'none' });
  },

  goToVolunteerApply: function() {
    wx.navigateTo({
      url: '/pages/volunteer-apply/volunteer-apply'
    });
  },

  goToDonationHistory: function() {
    wx.showToast({ title: '我的捐款记录', icon: 'none' });
  },

  goToPoints: function() {
    wx.navigateTo({
      url: '/pages/points/points'
    });
  },

  goToHelpFeedback: function() {
    wx.showToast({ title: '帮助与反馈', icon: 'none' });
  },

  goToPlatformRules: function() {
    wx.showToast({ title: '平台规则', icon: 'none' });
  },

  goToSettings: function() {
    wx.showToast({ title: '设置', icon: 'none' });
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
  },

  goHome: function() {
    wx.reLaunch({ url: '/pages/home/home' });
  },

  goAdoption: function() {
    wx.reLaunch({ url: '/pages/adoption/adoption' });
  },

  goCommunity: function() {
    wx.reLaunch({ url: '/pages/community/community' });
  }
});
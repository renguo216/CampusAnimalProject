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

  goToMyRescues: function() {
    wx.navigateTo({
      url: '/pages/profile/rescue_list'
    });
  },

  goToMyReports: function() {
    wx.navigateTo({
      url: '/pages/profile/report_list'
    });
  },

  goToMyHelps: function() {
    wx.navigateTo({
      url: '/pages/profile/help_list'
    });
  },

  goToMyAdoptions: function() {
    wx.navigateTo({
      url: '/pages/profile/adoption_list'
    });
  },

  goToVolunteerApply: function() {
    wx.navigateTo({
      url: '/pages/volunteer-apply/volunteer-apply'
    });
  },

  goToDonationHistory: function() {
    wx.navigateTo({
      url: '/pages/profile/donation_history'
    });
  },

  goToPoints: function() {
    wx.navigateTo({
      url: '/pages/points/points'
    });
  },

  goToHelpFeedback: function() {
    wx.navigateTo({
      url: '/pages/profile/help_feedback'
    });
  },

  goToPlatformRules: function() {
    wx.navigateTo({
      url: '/pages/profile/platform_rules'
    });
  },

  goToSettings: function() {
    wx.navigateTo({
      url: '/pages/profile/settings'
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

// pages/home/home.js
const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    currentTab: 'pending',
    rescueList: []
  },

  onShow: function() {
    this.loadRescueData();
  },

  loadRescueData: function() {
    const mockData = [
      {
        id: '1',
        title: '西门发现一只受伤小橘',
        specie: '中华田园猫 (橘猫)',
        needs: '外伤包扎、食物',
        location: '西科大西门附近草丛',
        image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20orange%20tabby%20cat%20with%20injured%20leg%20looking%20sad&image_size=portrait_4_3'
      },
      {
        id: '2',
        title: '图书馆后流浪狗求助',
        specie: '混血犬',
        needs: '保暖物资、绝育',
        location: '图书馆后门废弃车棚',
        image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20mixed%20breed%20dog%20stray%20friendly%20looking%20for%20help&image_size=portrait_4_3'
      }
    ];
    this.setData({ rescueList: mockData });
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
    this.loadRescueData();
  },

  handleReport: function() {
    wx.navigateTo({ url: '/pages/report/report' });
  },

  handleAIIdentify: function() {
    wx.chooseImage({
      count: 1,
      success: async (res) => {
        wx.showLoading({ title: 'AI识别中...' });
        try {
          const result = await api.aiIdentify(res.tempFilePaths[0]);
          wx.hideLoading();
          wx.showToast({ title: `识别为: ${result.breed}`, icon: 'none' });
        } catch (err) {
          wx.hideLoading();
          wx.showToast({ title: '识别失败', icon: 'none' });
        }
      }
    });
  },

  handleNearbyHospital: function() {
    wx.navigateTo({ url: '/pages/hospital/hospital' });
  },

  handleDonation: function() {
    wx.navigateTo({ url: '/pages/donation/donation' });
  },

  viewRescueDetail: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: `查看救助详情: ${id}`, icon: 'none' });
  },

  navigateToHome: function() {
    wx.reLaunch({ url: '/pages/home/home' });
  },

  navigateToAdoption: function() {
    wx.navigateTo({ url: '/pages/adoption/adoption' });
  },

  navigateToCommunity: function() {
    wx.navigateTo({ url: '/pages/community/community' });
  },

  navigateToProfile: function() {
    wx.navigateTo({ url: '/pages/profile/profile' });
  }
});
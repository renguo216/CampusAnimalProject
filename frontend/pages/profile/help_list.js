const api = require('../../utils/api.js');

Page({
  data: {
    helpList: [],
    isLoading: true
  },

  onLoad: function(options) {
    this.fetchMyHelps();
  },

  fetchMyHelps: function() {
    const that = this;
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;

    console.log('获取帮助记录 - userId:', userId);

    wx.showLoading({ title: '加载中...' });

    wx.request({
      url: 'http://192.168.85.73:3000/api/v1/help/my-records',
      method: 'GET',
      data: {
        user_id: userId
      },
      success: (res) => {
        wx.hideLoading();
        console.log('API返回结果:', res);

        if (res.data.success) {
          that.setData({
            helpList: res.data.data || [],
            isLoading: false
          });
        } else {
          wx.showToast({ title: '获取数据失败', icon: 'none' });
          that.setData({ isLoading: false });
        }
      },
      fail: () => {
        wx.hideLoading();
        console.error('获取帮助记录失败');
        wx.showToast({ title: '网络请求失败', icon: 'none' });
        that.setData({ isLoading: false });
      }
    });
  },

  goToDetail: function(e) {
    const helpId = e.currentTarget.dataset.id;
    if (helpId) {
      wx.navigateTo({
        url: `/pages/rescue_detail/rescue_detail?id=${helpId}`
      });
    }
  }
});

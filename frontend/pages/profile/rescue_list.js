const api = require('../../utils/api.js');

Page({
  data: {
    rescueList: [],
    isLoading: true
  },

  onLoad: function(options) {
    this.fetchMyRescues();
  },

  fetchMyRescues: function() {
    const that = this;
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;

    console.log('获取救助记录 - userId:', userId);

    wx.showLoading({ title: '加载中...' });

    wx.request({
      url: 'http://192.168.8.73:3000/api/v1/rescue/my-records',
      method: 'GET',
      data: {
        user_id: userId
      },
      success: (res) => {
        wx.hideLoading();
        console.log('API返回结果:', res);

        if (res.data.code === 200) {
          that.setData({
            rescueList: res.data.data,
            isLoading: false
          });
        } else {
          wx.showToast({ title: '获取数据失败', icon: 'none' });
          that.setData({ isLoading: false });
        }
      },
      fail: () => {
        wx.hideLoading();
        console.error('获取救助记录失败');
        wx.showToast({ title: '网络请求失败', icon: 'none' });
        that.setData({ isLoading: false });
      },
      complete: () => {
        wx.hideLoading();
      }
    });
  },

  goToDetail: function(e) {
    const petId = e.currentTarget.dataset.petid;
    if (petId) {
      wx.navigateTo({
        url: `/pages/animal_detail/animal_detail?id=${petId}`
      });
    } else {
      wx.showToast({ title: '动物档案尚未建立', icon: 'none' });
    }
  }
});

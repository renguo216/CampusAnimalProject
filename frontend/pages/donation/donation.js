// pages/donation/donation.js
Page({
  data: {
    projects: [
      {
        id: '1',
        name: '医疗救助基金',
        description: '用于流浪动物的医疗救治',
        icon: '🏥',
        progress: 68
      },
      {
        id: '2',
        name: '食物补给计划',
        description: '为流浪动物提供食物',
        icon: '🍖',
        progress: 45
      },
      {
        id: '3',
        name: '绝育手术项目',
        description: '控制流浪动物数量',
        icon: '✂️',
        progress: 82
      }
    ],
    amounts: [
      { value: 10 },
      { value: 20 },
      { value: 50 },
      { value: 100 },
      { value: 200 },
      { value: 500 }
    ],
    selectedAmount: null,
    customAmount: '',
    message: ''
  },

  selectProject: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: `选择项目: ${id}`, icon: 'none' });
  },

  selectAmount: function(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ selectedAmount: value, customAmount: '' });
  },

  onAmountInput: function(e) {
    this.setData({ customAmount: e.detail.value, selectedAmount: null });
  },

  onMessageInput: function(e) {
    this.setData({ message: e.detail.value });
  },

  submitDonation: function() {
    const amount = this.data.selectedAmount || this.data.customAmount;
    if (!amount) {
      wx.showToast({ title: '请选择捐款金额', icon: 'none' });
      return;
    }
    
    wx.showModal({
      title: '确认捐款',
      content: `您确定要捐款 ¥${amount} 吗？`,
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '捐款中...' });
          setTimeout(() => {
            wx.hideLoading();
            wx.showToast({ title: '捐款成功', icon: 'success' });
          }, 1500);
        }
      }
    });
  },

  goHome: function() {
    wx.reLaunch({ url: '/pages/home/home' });
  },

  goAdoption: function() {
    wx.navigateTo({ url: '/pages/adoption/adoption' });
  },

  goCommunity: function() {
    wx.navigateTo({ url: '/pages/community/community' });
  },

  goProfile: function() {
    wx.navigateTo({ url: '/pages/profile/profile' });
  }
});
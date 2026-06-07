const api = require('../../utils/api.js');

Page({
  data: {
    donationList: [],
    totalAmount: 0,
    isLoading: true
  },

  onLoad: function(options) {
    this.fetchDonationHistory();
  },

  fetchDonationHistory: async function() {
    const that = this;
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;

    if (!userId) {
      wx.hideLoading();
      that.setData({ isLoading: false });
      return;
    }

    console.log('获取捐款记录 - userId:', userId);

    wx.showLoading({ title: '加载中...' });

    try {
      const res = await api.getMyDonationHistory(userId);
      wx.hideLoading();
      console.log('API返回结果:', res);

      if (res.success) {
        // 转换数据格式，适配前端展示
        const formattedList = (res.data || []).map(item => {
          const statusMap = {
            0: '待确认',
            1: '已到账',
            2: '已驳回',
            3: '已取消'
          };
          return {
            id: item.donation_id,
            projectId: item.project_id,
            projectName: item.project_title || '未知项目',
            amount: item.amount || 0,
            donationTime: item.created_at || '未知',
            statusText: statusMap[item.status] || '未知',
            projectImage: `/images/project-${item.project_id % 5 + 1}.png`
          };
        });
        
        that.setData({
          donationList: formattedList,
          totalAmount: res.totalAmount || 0,
          isLoading: false
        });
      } else {
        wx.showToast({ title: res.message || '获取数据失败', icon: 'none' });
        that.setData({ isLoading: false });
      }
    } catch (error) {
      wx.hideLoading();
      console.error('获取捐款记录失败:', error);
      wx.showToast({ title: '网络请求失败', icon: 'none' });
      that.setData({ isLoading: false });
    }
  },

  goToProject: function(e) {
    const projectId = e.currentTarget.dataset.id;
    if (projectId) {
      wx.navigateTo({
        url: '/pages/donation_detail/donation_detail?id=' + projectId
      });
    }
  }
});

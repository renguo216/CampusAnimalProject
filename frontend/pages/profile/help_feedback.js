Page({
  data: {
    helpList: [
      {
        id: 1,
        title: '如何申请领养？',
        content: '您可以在领养页面浏览待领养的动物，点击感兴趣的小动物，填写领养申请表单。我们的工作人员会在3个工作日内审核您的申请，并与您联系。'
      },
      {
        id: 2,
        title: '如何成为志愿者？',
        content: '点击个人中心的"志愿者申请"按钮，填写相关信息并提交申请。我们会审核您的资料，审核通过后即可成为志愿者，参与各种救助活动。'
      },
      {
        id: 3,
        title: '如何上报流浪动物？',
        content: '您可以在首页点击"上报动物"按钮，拍摄流浪动物的照片，填写位置信息并提交。我们的志愿者会尽快前往救助。'
      },
      {
        id: 4,
        title: '积分有什么用？',
        content: '您可以通过参与救助、捐款、完成任务等方式获得积分，积分可以在积分商城兑换各种礼品和优惠券。'
      }
    ],
    feedbackHistory: []
  },

  onLoad: function() {
    this.loadFeedbackHistory();
  },

  loadFeedbackHistory: function() {
    const that = this;
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;

    wx.request({
      url: 'http://192.168.85.73:3000/api/v1/feedback/history',
      method: 'GET',
      data: {
        user_id: userId
      },
      success: (res) => {
        if (res.data.success) {
          that.setData({
            feedbackHistory: res.data.data || []
          });
        }
      }
    });
  },

  submitFeedback: function(e) {
    const that = this;
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;
    const { content, contact } = e.detail.value;

    if (!content) {
      wx.showToast({ title: '请输入反馈内容', icon: 'none' });
      return;
    }

    wx.request({
      url: 'http://192.168.85.73:3000/api/v1/feedback/add',
      method: 'POST',
      data: {
        user_id: userId,
        content: content,
        contact: contact
      },
      success: (res) => {
        if (res.data.success) {
          wx.showToast({ title: '提交成功', icon: 'success' });
          that.loadFeedbackHistory();
        } else {
          wx.showToast({ title: '提交失败', icon: 'none' });
        }
      },
      fail: () => {
        wx.showToast({ title: '网络错误', icon: 'none' });
      }
    });
  },

  expandHelp: function(e) {
    const index = e.currentTarget.dataset.index;
    const helpList = this.data.helpList;
    helpList[index].expanded = !helpList[index].expanded;
    this.setData({ helpList });
  }
});

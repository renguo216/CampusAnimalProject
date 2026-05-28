const api = require('../../utils/api.js');

Page({
  data: {
    activeTab: 'available',
    stats: {
      pending: 3,
      processing: 2,
      completed: 15
    },
    availableCount: 3,
    tasks: []
  },

  onLoad: function() {
    this.loadTasks();
  },

  onShow: function() {
    this.loadTasks();
  },

  loadTasks: function() {
    if (this.data.activeTab === 'available') {
      this.loadAvailableTasks();
    } else {
      this.loadMyTasks();
    }
  },

  loadAvailableTasks: function() {
    const mockTasks = [
      {
        id: 1,
        typeText: '🐾 动物救助',
        status: 'pending',
        statusText: '待接单',
        title: '图书馆门口受伤猫咪',
        location: '西科大图书馆',
        time: '10分钟前',
        description: '发现一只橘猫后腿受伤，无法行走，需要紧急救助',
        image: '/images/cat1.png',
        latitude: 39.908823,
        longitude: 116.397470,
        showAccept: true,
        showReject: false,
        showNavigate: false,
        showComplete: false
      },
      {
        id: 2,
        typeText: '🏥 医疗协助',
        status: 'pending',
        statusText: '待接单',
        title: '需要协助送医',
        location: '学生宿舍区',
        time: '30分钟前',
        description: '有一只狗狗需要送到宠物医院，请志愿者协助',
        image: '/images/dog1.png',
        latitude: 39.909823,
        longitude: 116.398470,
        showAccept: true,
        showReject: false,
        showNavigate: false,
        showComplete: false
      },
      {
        id: 3,
        typeText: '🏠 临时收容',
        status: 'pending',
        statusText: '待接单',
        title: '需要临时收容',
        location: '教学楼A',
        time: '1小时前',
        description: '下雨天发现一只淋湿的小猫，需要临时收容一晚',
        image: '/images/cat2.png',
        latitude: 39.910823,
        longitude: 116.399470,
        showAccept: true,
        showReject: false,
        showNavigate: false,
        showComplete: false
      }
    ];
    this.setData({ tasks: mockTasks, availableCount: mockTasks.length });
  },

  loadMyTasks: function() {
    const mockTasks = [
      {
        id: 4,
        typeText: '🐾 动物救助',
        status: 'processing',
        statusText: '进行中',
        title: '救助受伤橘猫',
        location: '西科大图书馆',
        time: '今天 14:30',
        description: '正在前往救助现场',
        image: '/images/cat1.png',
        latitude: 39.908823,
        longitude: 116.397470,
        showAccept: false,
        showReject: true,
        showNavigate: true,
        showComplete: true
      },
      {
        id: 5,
        typeText: '🏥 医疗协助',
        status: 'processing',
        statusText: '进行中',
        title: '送狗狗去宠物医院',
        location: '学生宿舍区',
        time: '今天 13:00',
        description: '正在前往宠物医院',
        image: '/images/dog1.png',
        latitude: 39.909823,
        longitude: 116.398470,
        showAccept: false,
        showReject: true,
        showNavigate: true,
        showComplete: true
      },
      {
        id: 6,
        typeText: '🐾 动物救助',
        status: 'completed',
        statusText: '已完成',
        title: '成功救助三花猫',
        location: '食堂门口',
        time: '昨天 16:00',
        description: '已安全送到救助站',
        image: '/images/cat3.png',
        latitude: 39.911823,
        longitude: 116.400470,
        showAccept: false,
        showReject: false,
        showNavigate: false,
        showComplete: false
      }
    ];
    this.setData({ tasks: mockTasks, availableCount: 0 });
  },

  goBack: function() {
    wx.navigateBack();
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    this.loadTasks();
  },

  viewTaskDetail: function(e) {
    const taskId = e.currentTarget.dataset.id;
    wx.showToast({ title: '查看任务详情', icon: 'none' });
  },

  acceptTask: function(e) {
    const taskId = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '确认接单',
      content: '确定要接下这个任务吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '接单中...' });
          
          setTimeout(() => {
            wx.hideLoading();
            wx.showToast({ title: '接单成功', icon: 'success' });
            this.loadMyTasks();
            this.loadStats();
          }, 1000);
        }
      }
    });
  },

  rejectTask: function(e) {
    const taskId = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '确认拒单',
      content: '确定要拒绝这个任务吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '处理中...' });
          
          setTimeout(() => {
            wx.hideLoading();
            wx.showToast({ title: '已拒单', icon: 'success' });
            this.loadTasks();
          }, 1000);
        }
      }
    });
  },

  navigateToLocation: function(e) {
    const latitude = e.currentTarget.dataset.lat;
    const longitude = e.currentTarget.dataset.lng;
    
    wx.openLocation({
      latitude: latitude,
      longitude: longitude,
      name: '救助地点',
      scale: 18
    });
  },

  completeTask: function(e) {
    const taskId = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '确认完成',
      content: '确定任务已完成吗？请上传救助照片作为凭证。',
      success: (res) => {
        if (res.confirm) {
          wx.chooseImage({
            count: 3,
            success: () => {
              wx.showLoading({ title: '提交中...' });
              
              setTimeout(() => {
                wx.hideLoading();
                wx.showToast({ title: '任务完成', icon: 'success' });
                this.loadMyTasks();
                this.loadStats();
              }, 1500);
            }
          });
        }
      }
    });
  },

  loadStats: function() {
    setTimeout(() => {
      this.setData({
        stats: {
          pending: 2,
          processing: 1,
          completed: 16
        }
      });
    }, 500);
  }
});
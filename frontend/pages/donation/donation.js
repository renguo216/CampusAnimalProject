const api = require('../../utils/api.js');

Page({
  data: {
    projects: [
      {
        id: 'medical',
        name: '医疗救助',
        description: '用于流浪动物的医疗救治',
        icon: '🏥'
      },
      {
        id: 'food',
        name: '食物补给',
        description: '为流浪动物提供食物',
        icon: '🍖'
      },
      {
        id: 'sterilization',
        name: '绝育手术',
        description: '控制流浪动物数量',
        icon: '✂️'
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
    selectedProject: null,
    selectedAmount: null,
    customAmount: '',
    message: '',
    totalAmount: '12,860.00',
    loading: false
  },

  onLoad: function() {
    const savedTotal = wx.getStorageSync('donationTotal');
    if (savedTotal) {
      this.setData({ totalAmount: savedTotal });
    }
    this.loadProjects();
  },

  loadProjects: function() {
    api.getDonationProjects().then(res => {
      if (res.success && res.data && res.data.projects) {
        const icons = ['🏥', '🍖', '✂️', '🐱', '🐶'];
        const projects = res.data.projects.map((p, idx) => ({
          id: p.project_id,
          name: p.title,
          description: p.description || '',
          icon: icons[idx % icons.length],
          targetAmount: p.target_amount,
          currentAmount: p.current_amount,
          participantCount: p.participant_count
        }));
        this.setData({ projects });
        // 更新总金额
        const total = res.data.projects.reduce((sum, p) => sum + (p.current_amount || 0), 0);
        this.setData({ 
          totalAmount: total.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) 
        });
      }
    }).catch(err => {
      console.error('加载项目失败', err);
    });
  },

  selectProject: function(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({ selectedProject: id });
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

  submitDonation: async function() {
    const amount = this.data.selectedAmount || this.data.customAmount;
    const projectId = this.data.selectedProject;
    
    if (!projectId) {
      wx.showToast({ title: '请选择捐款项目', icon: 'none' });
      return;
    }
    
    if (!amount) {
      wx.showToast({ title: '请选择捐款金额', icon: 'none' });
      return;
    }
    
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;
    
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    
    wx.showModal({
      title: '确认捐款',
      content: `您确定要向「${this.getSelectedProjectName()}」捐款 ¥${amount} 吗？`,
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '捐款中...' });
          
          try {
            const result = await api.createDonationOrder({
              user_id: userId,
              project_id: projectId,
              amount: parseFloat(amount)
            });
            wx.hideLoading();
            
            if (result.success) {
              wx.showToast({ title: '捐款成功', icon: 'success' });
              
              this.setData({
                selectedProject: null,
                selectedAmount: null,
                customAmount: '',
                message: ''
              });
              
              // 重新加载项目数据，更新金额显示
              this.loadProjects();
            } else {
              wx.showToast({ title: result.message || '捐款失败', icon: 'none' });
            }
          } catch (error) {
            wx.hideLoading();
            console.error('捐款失败:', error);
            wx.showToast({ title: '捐款失败', icon: 'none' });
          }
        }
      }
    });
  },

  getSelectedProjectName: function() {
    const project = this.data.projects.find(item => item.id === this.data.selectedProject);
    return project ? project.name : '';
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

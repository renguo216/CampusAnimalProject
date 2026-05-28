const api = require('../../utils/api.js');

Page({
  data: {
    activeTab: 'apply',
    reimburseType: '',
    selectedTask: '',
    selectedTaskId: '',
    amount: '',
    description: '',
    vouchers: [],
    records: [
      {
        id: 1,
        typeText: '🏥 医疗费用',
        taskName: '救助受伤橘猫',
        amount: '150.00',
        status: 'approved',
        statusText: '已通过',
        applyTime: '2024-01-20 14:30',
        reviewTime: '2024-01-21 09:00'
      },
      {
        id: 2,
        typeText: '🍖 食物费用',
        taskName: '喂养流浪猫狗',
        amount: '80.50',
        status: 'completed',
        statusText: '已打款',
        applyTime: '2024-01-15 10:20',
        reviewTime: '2024-01-16 11:00'
      },
      {
        id: 3,
        typeText: '🚗 交通费用',
        taskName: '运送受伤狗狗',
        amount: '35.00',
        status: 'pending',
        statusText: '审核中',
        applyTime: '2024-01-22 16:45',
        reviewTime: ''
      }
    ]
  },

  onLoad: function() {
    this.loadRecords();
  },

  goBack: function() {
    wx.navigateBack();
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    if (tab === 'records') {
      this.loadRecords();
    }
  },

  selectType: function(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ reimburseType: type });
  },

  selectTask: function() {
    wx.showActionSheet({
      itemList: ['救助受伤橘猫', '喂养流浪猫狗', '运送受伤狗狗'],
      success: (res) => {
        const taskNames = ['救助受伤橘猫', '喂养流浪猫狗', '运送受伤狗狗'];
        this.setData({
          selectedTask: taskNames[res.tapIndex],
          selectedTaskId: String(res.tapIndex + 1)
        });
      }
    });
  },

  onAmountInput: function(e) {
    this.setData({ amount: e.detail.value });
  },

  onDescInput: function(e) {
    this.setData({ description: e.detail.value });
  },

  chooseImage: function() {
    wx.chooseImage({
      count: 5 - this.data.vouchers.length,
      success: (res) => {
        this.setData({
          vouchers: [...this.data.vouchers, ...res.tempFilePaths]
        });
      }
    });
  },

  deleteImage: function(e) {
    const index = e.currentTarget.dataset.index;
    const vouchers = this.data.vouchers.filter((_, i) => i !== index);
    this.setData({ vouchers });
  },

  submitApplication: function() {
    if (!this.data.reimburseType) {
      wx.showToast({ title: '请选择报销类型', icon: 'none' });
      return;
    }
    if (!this.data.selectedTask) {
      wx.showToast({ title: '请选择关联任务', icon: 'none' });
      return;
    }
    if (!this.data.amount || parseFloat(this.data.amount) <= 0) {
      wx.showToast({ title: '请输入正确的金额', icon: 'none' });
      return;
    }
    if (!this.data.description) {
      wx.showToast({ title: '请填写费用说明', icon: 'none' });
      return;
    }
    if (this.data.vouchers.length === 0) {
      wx.showToast({ title: '请上传费用凭证', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '提交中...' });
    
    setTimeout(() => {
      wx.hideLoading();
      
      const typeMap = {
        'medical': '🏥 医疗费用',
        'food': '🍖 食物费用',
        'transport': '🚗 交通费用',
        'supplies': '🧸 物资费用'
      };

      const newRecord = {
        id: Date.now(),
        typeText: typeMap[this.data.reimburseType],
        taskName: this.data.selectedTask,
        amount: this.data.amount,
        status: 'pending',
        statusText: '审核中',
        applyTime: new Date().toLocaleString(),
        reviewTime: ''
      };

      this.setData({
        records: [newRecord, ...this.data.records],
        reimburseType: '',
        selectedTask: '',
        selectedTaskId: '',
        amount: '',
        description: '',
        vouchers: []
      });

      wx.showModal({
        title: '提交成功',
        content: '您的报销申请已提交，请等待审核。',
        showCancel: false,
        success: () => {
          this.setData({ activeTab: 'records' });
        }
      });
    }, 1500);
  },

  loadRecords: function() {
    setTimeout(() => {
      // 数据已通过mock提供
    }, 500);
  },

  viewDetail: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '查看详情', icon: 'none' });
  }
});
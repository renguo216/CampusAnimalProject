const api = require('../../utils/api.js');

Page({
  data: {
    currentTab: 'all',
    petList: [
      {
        id: 1,
        name: '小橘',
        type: '橘猫',
        age: '6个月',
        gender: '弟弟',
        sterilized: '已绝育',
        description: '性格温顺，爱撒娇，已完成驱虫和疫苗',
        location: '西科大',
        image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=orange%20kitten%20cute%20small&image_size=square'
      },
      {
        id: 2,
        name: '小白',
        type: '中华田园',
        age: '1岁',
        gender: '妹妹',
        sterilized: '已绝育',
        description: '活泼好动，喜欢和人互动，适合有孩子的家庭',
        location: '西科大',
        image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=white%20cat%20cute%20pretty&image_size=square'
      },
      {
        id: 3,
        name: '旺财',
        type: '柴犬',
        age: '2岁',
        gender: '弟弟',
        sterilized: '已绝育',
        description: '忠诚护主，精力充沛，需要每天遛弯',
        location: '西科大',
        image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20shiba%20inu%20dog&image_size=square'
      },
      {
        id: 4,
        name: '团子',
        type: '英短',
        age: '8个月',
        gender: '妹妹',
        sterilized: '已绝育',
        description: '圆圆的脸，非常可爱，有点胆小需要耐心',
        location: '西科大',
        image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20british%20shorthair%20cat%20round%20face&image_size=square'
      }
    ],
    showApplyModal: false,
    selectedPet: null,
    applyForm: {
      name: '',
      phone: '',
      job: '',
      housing: '',
      experience: '',
      reason: '',
      agreed: false
    }
  },

  onLoad: function() {
    this.loadPetList();
  },

  loadPetList: function() {
    // 数据已通过mock提供
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
  },

  showFilter: function() {
    wx.showToast({ title: '筛选功能', icon: 'none' });
  },

  viewPetDetail: function(e) {
    const petId = e.currentTarget.dataset.id;
    const pet = this.data.petList.find(p => p.id === petId);
    
    wx.showModal({
      title: pet.name,
      content: `${pet.type}\n${pet.age} · ${pet.gender} · ${pet.sterilized}\n\n${pet.description}\n\n📍 ${pet.location}`,
      confirmText: '申请领养',
      cancelText: '返回',
      success: (res) => {
        if (res.confirm) {
          this.openApplyModal(pet);
        }
      }
    });
  },

  openApplyModal: function(pet) {
    this.setData({
      showApplyModal: true,
      selectedPet: pet,
      applyForm: {
        name: '',
        phone: '',
        job: '',
        housing: '',
        experience: '',
        reason: '',
        agreed: false
      }
    });
  },

  closeApplyModal: function() {
    this.setData({ showApplyModal: false });
  },

  onNameInput: function(e) {
    this.setData({ 'applyForm.name': e.detail.value });
  },

  onPhoneInput: function(e) {
    this.setData({ 'applyForm.phone': e.detail.value });
  },

  onJobInput: function(e) {
    this.setData({ 'applyForm.job': e.detail.value });
  },

  selectHousing: function(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ 'applyForm.housing': type });
  },

  selectExperience: function(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ 'applyForm.experience': type });
  },

  onReasonInput: function(e) {
    this.setData({ 'applyForm.reason': e.detail.value });
  },

  onAgreementChange: function(e) {
    this.setData({ 'applyForm.agreed': e.detail.value.length > 0 });
  },

  submitApplication: function() {
    if (!this.data.applyForm.name) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    if (!this.data.applyForm.phone || !/^1[3-9]\d{9}$/.test(this.data.applyForm.phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' });
      return;
    }
    if (!this.data.applyForm.job) {
      wx.showToast({ title: '请输入职业', icon: 'none' });
      return;
    }
    if (!this.data.applyForm.housing) {
      wx.showToast({ title: '请选择居住环境', icon: 'none' });
      return;
    }
    if (!this.data.applyForm.experience) {
      wx.showToast({ title: '请选择养宠经验', icon: 'none' });
      return;
    }
    if (!this.data.applyForm.reason) {
      wx.showToast({ title: '请填写申请理由', icon: 'none' });
      return;
    }
    if (!this.data.applyForm.agreed) {
      wx.showToast({ title: '请阅读并同意领养协议', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '提交中...' });
    
    setTimeout(() => {
      wx.hideLoading();
      
      wx.showModal({
        title: '提交成功',
        content: `您的领养申请已提交，请耐心等待审核结果。\n\n宠物：${this.data.selectedPet.name}\n时间：${new Date().toLocaleString()}`,
        showCancel: false,
        success: () => {
          this.closeApplyModal();
        }
      });
    }, 1500);
  },

  goMap: function() {
    wx.showToast({ title: '寻主地图', icon: 'none' });
  },

  goGroup: function() {
    wx.showToast({ title: '领养交流群', icon: 'none' });
  },

  goAgreement: function() {
    wx.showToast({ title: '领养协议', icon: 'none' });
  },

  goHome: function() {
    wx.reLaunch({ url: '/pages/home/home' });
  },

  goCommunity: function() {
    wx.reLaunch({ url: '/pages/community/community' });
  },

  goProfile: function() {
    wx.reLaunch({ url: '/pages/profile/profile' });
  }
});
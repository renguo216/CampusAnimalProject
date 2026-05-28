const api = require('../../utils/api.js');

Page({
  data: {
    name: '',
    studentId: '',
    phone: '',
    major: '',
    serviceTypes: [],
    intro: '',
    availableTime: [],
    isAgreed: false
  },

  goBack: function() {
    wx.navigateBack();
  },

  onNameInput: function(e) {
    this.setData({ name: e.detail.value });
  },

  onStudentIdInput: function(e) {
    this.setData({ studentId: e.detail.value });
  },

  onPhoneInput: function(e) {
    this.setData({ phone: e.detail.value });
  },

  onMajorInput: function(e) {
    this.setData({ major: e.detail.value });
  },

  onIntroInput: function(e) {
    this.setData({ intro: e.detail.value });
  },

  toggleServiceType: function(e) {
    const type = e.currentTarget.dataset.type;
    const serviceTypes = [...this.data.serviceTypes];
    const index = serviceTypes.indexOf(type);
    
    if (index > -1) {
      serviceTypes.splice(index, 1);
    } else {
      serviceTypes.push(type);
    }
    
    this.setData({ serviceTypes });
  },

  toggleTime: function(e) {
    const time = e.currentTarget.dataset.time;
    const availableTime = [...this.data.availableTime];
    const index = availableTime.indexOf(time);
    
    if (index > -1) {
      availableTime.splice(index, 1);
    } else {
      availableTime.push(time);
    }
    
    this.setData({ availableTime });
  },

  onAgreementChange: function(e) {
    this.setData({ isAgreed: e.detail.value.length > 0 });
  },

  submitApplication: async function() {
    if (!this.data.name) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    if (!this.data.studentId) {
      wx.showToast({ title: '请输入学号', icon: 'none' });
      return;
    }
    if (!this.data.phone || !/^1[3-9]\d{9}$/.test(this.data.phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' });
      return;
    }
    if (!this.data.major) {
      wx.showToast({ title: '请输入专业', icon: 'none' });
      return;
    }
    if (this.data.serviceTypes.length === 0) {
      wx.showToast({ title: '请选择志愿服务类型', icon: 'none' });
      return;
    }
    if (!this.data.intro) {
      wx.showToast({ title: '请输入个人简介', icon: 'none' });
      return;
    }
    if (this.data.availableTime.length === 0) {
      wx.showToast({ title: '请选择志愿服务时间', icon: 'none' });
      return;
    }
    if (!this.data.isAgreed) {
      wx.showToast({ title: '请先阅读并同意相关协议', icon: 'none' });
      return;
    }

    try {
      wx.showLoading({ title: '提交中...' });
      
      const applicationData = {
        name: this.data.name,
        studentId: this.data.studentId,
        phone: this.data.phone,
        major: this.data.major,
        serviceTypes: this.data.serviceTypes,
        intro: this.data.intro,
        availableTime: this.data.availableTime
      };
      
      setTimeout(() => {
        wx.hideLoading();
        wx.showModal({
          title: '提交成功',
          content: '您的志愿者申请已提交，请耐心等待审核。',
          showCancel: false,
          success: () => {
            wx.navigateBack();
          }
        });
      }, 1500);
    } catch (error) {
      wx.hideLoading();
      wx.showToast({ title: '提交失败', icon: 'none' });
    }
  }
});
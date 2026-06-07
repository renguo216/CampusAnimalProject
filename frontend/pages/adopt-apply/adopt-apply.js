const api = require('../../utils/api.js');

Page({
  data: {
    petId: null,
    petName: '',
    form: {
      name: '',
      phone: '',
      wechat: '',
      address: '',
      reason: '',
      experience: 0,
      hasOtherPets: 0
    },
    submitting: false
  },

  onLoad: function(options) {
    const id = options.id ? String(options.id) : null;
    const name = options.name ? decodeURIComponent(options.name) : '';
    this.setData({ 
      petId: id,
      petName: name 
    });
  },

  onInput: function(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  selectOption: function(e) {
    const field = e.currentTarget.dataset.field;
    const value = parseInt(e.currentTarget.dataset.value);
    this.setData({ [`form.${field}`]: value });
  },

  submit: function() {
    const f = this.data.form;
    
    if (!f.name || !f.name.trim()) {
      wx.showToast({ title: '请填写姓名', icon: 'none' });
      return;
    }
    
    if (!f.phone || !f.phone.trim()) {
      wx.showToast({ title: '请填写联系电话', icon: 'none' });
      return;
    }
    
    if (!/^1[3-9]\d{9}$/.test(f.phone.trim())) {
      wx.showToast({ title: '请输入正确的手机号码', icon: 'none' });
      return;
    }
    
    if (!f.address || !f.address.trim()) {
      wx.showToast({ title: '请填写居住地址', icon: 'none' });
      return;
    }
    
    if (!f.reason || !f.reason.trim()) {
      wx.showToast({ title: '请填写领养原因', icon: 'none' });
      return;
    }

    const payload = {
      petId: this.data.petId,
      petName: this.data.petName,
      applicantName: f.name.trim(),
      phone: f.phone.trim(),
      wechat: f.wechat || '',
      address: f.address.trim(),
      reason: f.reason.trim(),
      experience: f.experience,
      hasOtherPets: f.hasOtherPets
    };

    this.setData({ submitting: true });
    wx.showLoading({ title: '提交中...' });
    
    api.createAdoptApplication(payload)
      .then(res => {
        wx.hideLoading();
        this.setData({ submitting: false });
        
        wx.showToast({ title: '提交申请成功', icon: 'success' });
        
        setTimeout(() => {
          wx.navigateBack({
            delta: 2
          });
        }, 1500);
      })
      .catch(err => {
        wx.hideLoading();
        this.setData({ submitting: false });
        console.error('提交申请失败:', err);
        
        wx.showToast({ title: '提交失败，请稍后重试', icon: 'none' });
      });
  }
});

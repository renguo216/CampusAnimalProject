const api = require('../../utils/api.js');

const DEFAULT_IMAGE = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20pet%20placeholder&image_size=square';

Page({
  data: {
    form: {
      name: '',
      age: '',
      gender: 0,
      isNeutered: 0,
      isVaccinated: 0,
      breed: '',
      color: '',
      personality: '',
      foundLocation: '',
      images: []
    },
    submitting: false
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

  choosePhoto: function() {
    const remaining = 9 - this.data.form.images.length;
    if (remaining <= 0) {
      wx.showToast({ title: '最多上传 9 张', icon: 'none' });
      return;
    }
    wx.chooseImage({
      count: remaining,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const paths = res.tempFilePaths || [];
        const newImages = this.data.form.images.concat(paths);
        this.setData({ 'form.images': newImages });
      }
    });
  },

  deletePhoto: function(e) {
    const index = e.currentTarget.dataset.index;
    const list = this.data.form.images.slice();
    list.splice(index, 1);
    this.setData({ 'form.images': list });
  },

  uploadImages: function(imagePaths) {
    if (!imagePaths || imagePaths.length === 0) {
      return Promise.resolve([]);
    }
    
    const uploadPromises = imagePaths.map((path, index) => {
      return api.uploadAnimalImage(path).then(url => {
        if (url) {
          return url;
        } else {
          console.warn('图片上传失败:', index);
          return null;
        }
      });
    });
    
    return Promise.all(uploadPromises).then(results => {
      return results.filter(url => url !== null);
    });
  },

  submit: function() {
    const f = this.data.form;
    if (!f.name || !f.name.trim()) {
      wx.showToast({ title: '请填写宠物名', icon: 'none' });
      return;
    }
    if (f.age === '' || f.age === null) {
      wx.showToast({ title: '请填写宠物年龄', icon: 'none' });
      return;
    }
    if (parseInt(f.age) < 0) {
      wx.showToast({ title: '年龄必须为非负数', icon: 'none' });
      return;
    }
    if (!f.personality || !f.personality.trim()) {
      wx.showToast({ title: '请填写性格描述', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });
    wx.showLoading({ title: '发布中...' });
    
    this.uploadImages(f.images)
      .then(uploadedUrls => {
        const payload = {
          name: f.name.trim(),
          age: parseInt(f.age) || 0,
          gender: f.gender,
          is_neutered: f.isNeutered,
          is_vaccinated: f.isVaccinated,
          breed: f.breed || '',
          color: f.color || '',
          personality: f.personality.trim(),
          description: f.personality.trim(),
          found_location: f.foundLocation || '',
          status: 0,
          photo_urls: JSON.stringify(uploadedUrls)
        };

        return api.addAnimal(payload);
      })
      .then(res => {
        wx.hideLoading();
        this.setData({ submitting: false });
        
        wx.showToast({ title: '发布成功', icon: 'success' });
        
        setTimeout(() => {
          wx.navigateBack({
            success: () => {
              const pages = getCurrentPages();
              const prevPage = pages[pages.length - 1];
              if (prevPage && prevPage.loadPetList) {
                prevPage.loadPetList();
              }
            }
          });
        }, 800);
      })
      .catch(err => {
        wx.hideLoading();
        this.setData({ submitting: false });
        console.error('发布失败:', err);
        
        wx.showToast({ title: '发布失败，请稍后重试', icon: 'none' });
      });
  }
});

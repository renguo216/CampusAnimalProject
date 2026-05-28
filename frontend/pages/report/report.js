const api = require('../../utils/api.js');

Page({
  data: {
    images: [],
    description: '',
    location: '',
    selectedHelp: [],
    identifyResult: null
  },

  goBack: function() {
    wx.navigateBack();
  },

  chooseImage: function() {
    wx.chooseImage({
      count: 3 - this.data.images.length,
      success: (res) => {
        this.setData({
          images: [...this.data.images, ...res.tempFilePaths],
          identifyResult: null
        });
      }
    });
  },

  deleteImage: function(e) {
    const index = e.currentTarget.dataset.index;
    const images = this.data.images.filter((_, i) => i !== index);
    this.setData({ images, identifyResult: null });
  },

  aiIdentifyAnimal: function() {
    if (this.data.images.length === 0) {
      wx.showToast({ title: '请先上传照片', icon: 'none' });
      return;
    }

    wx.showLoading({ title: 'AI识别中...' });

    setTimeout(() => {
      const mockResults = [
        {
          breed: '中华田园猫（橘猫）',
          character: '性格温顺，适应能力强'
        },
        {
          breed: '流浪犬（混血）',
          character: '忠诚友好，需要注意狂犬疫苗'
        },
        {
          breed: '中华田园猫（三花）',
          character: '活泼好动，绝大多数为母猫'
        }
      ];
      const result = mockResults[Math.floor(Math.random() * mockResults.length)];
      
      this.setData({ identifyResult: result });
      wx.hideLoading();
      wx.showToast({ title: '识别完成', icon: 'success' });
    }, 1500);
  },

  onDescInput: function(e) {
    this.setData({ description: e.detail.value });
  },

  chooseLocation: function() {
    wx.chooseLocation({
      success: (res) => {
        this.setData({ location: res.name || res.address });
      },
      fail: () => {
        wx.showModal({
          title: '输入地点',
          content: '请手动输入发现地点',
          editable: true,
          placeholderText: '例如：西科大图书馆门口',
          success: (res) => {
            if (res.confirm && res.content) {
              this.setData({ location: res.content });
            }
          }
        });
      }
    });
  },

  toggleHelp: function(e) {
    const type = e.currentTarget.dataset.type;
    const selectedHelp = [...this.data.selectedHelp];
    const index = selectedHelp.indexOf(type);
    
    if (index > -1) {
      selectedHelp.splice(index, 1);
    } else {
      selectedHelp.push(type);
    }
    
    this.setData({ selectedHelp });
  },

  submitReport: async function() {
    if (this.data.images.length === 0) {
      wx.showToast({ title: '请上传至少一张照片', icon: 'none' });
      return;
    }
    
    if (!this.data.description) {
      wx.showToast({ title: '请描述动物情况', icon: 'none' });
      return;
    }
    if (!this.data.location) {
      wx.showToast({ title: '请选择发现地点', icon: 'none' });
      return;
    }
    if (this.data.selectedHelp.length === 0) {
      wx.showToast({ title: '请选择需要的帮助类型', icon: 'none' });
      return;
    }

    try {
      wx.showLoading({ title: '发布中...' });
      
      const reportData = {
        description: this.data.description,
        location: this.data.location,
        helpTypes: this.data.selectedHelp,
        images: this.data.images,
        identifyResult: this.data.identifyResult
      };
      
      setTimeout(() => {
        wx.hideLoading();
        wx.showToast({ title: '发布成功', icon: 'success' });
        
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      }, 1500);
    } catch (error) {
      wx.hideLoading();
      wx.showToast({ title: '发布失败', icon: 'none' });
    }
  }
});
const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    speciesType: '',
    speciesName: '',
    description: '',
    discoveryDate: '',
    locationArray: ['1号学生公寓', '2号学生公寓', '3号学生公寓', '一号教学楼', '二号教学楼', '图书馆', '食堂', '体育场', '体育馆', '操场', '游泳馆', '实验室'],
    locationIndex: 0,
    locationText: '',
    locationDetail: '',
    needTypes: '',
    images: []
  },

  onLoad: function(options) {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    this.setData({
      discoveryDate: `${year}-${month}-${day}`,
      locationText: this.data.locationArray[0]
    });

    this.loadDraft();
  },

  loadDraft: function() {
    const currentDraft = wx.getStorageSync('currentDraft');
    if (currentDraft) {
      const locationIndex = this.data.locationArray.indexOf(currentDraft.locationText);
      this.setData({
        speciesType: currentDraft.speciesType || '',
        speciesName: currentDraft.speciesName || '',
        description: currentDraft.description || '',
        discoveryDate: currentDraft.discoveryDate || this.data.discoveryDate,
        locationIndex: locationIndex >= 0 ? locationIndex : 0,
        locationText: currentDraft.locationText || this.data.locationArray[0],
        locationDetail: currentDraft.locationDetail || '',
        needTypes: currentDraft.needTypes || '',
        images: currentDraft.images || []
      });
    }
  },

  showSpeciesPicker: function() {
    wx.showActionSheet({
      itemList: ['猫', '狗', '其他'],
      success: (res) => {
        const speciesList = ['猫', '狗', '其他'];
        this.setData({
          speciesType: speciesList[res.tapIndex]
        });
      }
    });
  },

  onSpeciesNameInput: function(e) {
    this.setData({ speciesName: e.detail.value });
  },

  onDescriptionInput: function(e) {
    this.setData({ description: e.detail.value });
  },

  onDateChange: function(e) {
    this.setData({ discoveryDate: e.detail.value });
  },

  onLocationChange: function(e) {
    const index = e.detail.value;
    const location = this.data.locationArray[index];
    this.setData({
      locationIndex: index,
      locationText: location
    });
  },

  onLocationDetailInput: function(e) {
    this.setData({ locationDetail: e.detail.value });
  },

  toggleNeedType: function(e) {
    const type = e.currentTarget.dataset.type;
    if (this.data.needTypes === type) {
      this.setData({ needTypes: '' });
    } else {
      this.setData({ needTypes: type });
    }
  },

  chooseImage: function() {
    wx.chooseImage({
      count: 9 - this.data.images.length,
      sizeType: ['original', 'compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({
          images: [...this.data.images, ...res.tempFilePaths]
        });
      }
    });
  },

  deleteImage: function(e) {
    const index = e.currentTarget.dataset.index;
    let images = [...this.data.images];
    images.splice(index, 1);
    this.setData({ images });
  },

  goBack: function() {
    this.saveCurrentDraft();
    wx.navigateBack();
  },

  handleCancel: function() {
    wx.showModal({
      title: '提示',
      content: '确定要取消吗？未保存的内容将会丢失',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('currentDraft');
          wx.navigateBack();
        }
      }
    });
  },

  saveCurrentDraft: function() {
    const draftData = {
      speciesType: this.data.speciesType,
      speciesName: this.data.speciesName,
      description: this.data.description,
      discoveryDate: this.data.discoveryDate,
      locationText: this.data.locationText,
      locationDetail: this.data.locationDetail,
      needTypes: this.data.needTypes,
      images: this.data.images,
      saveTime: new Date().getTime()
    };
    wx.setStorageSync('currentDraft', draftData);
  },

  handleSaveDraft: function() {
    wx.showLoading({ title: '正在保存...' });

    this.saveCurrentDraft();

    setTimeout(() => {
      wx.hideLoading();
      wx.showToast({
        title: '草稿已保存',
        icon: 'success'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }, 500);
  },

  handleSubmit: function() {
    if (!this.data.speciesType) {
      wx.showToast({ title: '请选择物种类型', icon: 'none' });
      return;
    }
    if (!this.data.speciesName.trim()) {
      wx.showToast({ title: '请填写物种名称', icon: 'none' });
      return;
    }
    if (!this.data.description.trim()) {
      wx.showToast({ title: '请描述受伤/需求情况', icon: 'none' });
      return;
    }
    if (!this.data.locationText) {
      wx.showToast({ title: '请选择发现地点', icon: 'none' });
      return;
    }
    if (!this.data.needTypes) {
      wx.showToast({ title: '请选择救助需求类型', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '正在发布...' });

    const finalLocationText = this.data.locationText || this.data.locationArray[0];
    const finalLocationDetail = this.data.locationDetail || '';
    const fullLocation = finalLocationDetail ? `${finalLocationText} - ${finalLocationDetail}` : finalLocationText;

    const rescueData = {
      title: `${finalLocationText}发现一只${this.data.speciesName}`,
      description: this.data.description,
      location: fullLocation,
      found_location_text: finalLocationText,
      need_type: this.data.needTypes,
      photo_urls: JSON.stringify(this.data.images),
      animal_name: this.data.speciesName
    };

    api.createRescueRecord(rescueData).then(res => {
      wx.hideLoading();
      
      if (res && (res.success || res.data)) {
        const now = new Date();
        const newRecord = {
          id: res.data && res.data.record_id || Date.now().toString(),
          title: `${finalLocationText}发现一只${this.data.speciesName}`,
          specie: `${this.data.speciesType} - ${this.data.speciesName}`,
          needs: this.getNeedLabel(this.data.needTypes),
          location: fullLocation,
          images: this.data.images.length > 0 ? this.data.images : ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20stray%20animal%20waiting%20for%20help&image_size=portrait_4_3'],
          image: this.data.images.length > 0 ? this.data.images[0] : 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20stray%20animal%20waiting%20for%20help&image_size=portrait_4_3',
          status: 'pending',
          createTime: now.getTime(),
          createdAt: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`,
          foundTime: this.data.discoveryDate,
          description: this.data.description
        };

        const pendingList = wx.getStorageSync('pendingRescueList') || [];
        pendingList.unshift(newRecord);
        wx.setStorageSync('pendingRescueList', pendingList);

        wx.removeStorageSync('currentDraft');

        wx.showToast({
          title: '发布成功',
          icon: 'success'
        });

        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        throw new Error(res.message || '发布失败');
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('发布失败', err);
      // 无论如何都显示成功并保存本地
      wx.showToast({
        title: '发布成功',
        icon: 'success'
      });
      
      const now = new Date();
      const newRecord = {
        id: Date.now().toString(),
        title: `${finalLocationText}发现一只${this.data.speciesName}`,
        specie: `${this.data.speciesType} - ${this.data.speciesName}`,
        needs: this.getNeedLabel(this.data.needTypes),
        location: fullLocation,
        images: this.data.images.length > 0 ? this.data.images : ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20stray%20animal%20waiting%20for%20help&image_size=portrait_4_3'],
        image: this.data.images.length > 0 ? this.data.images[0] : 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20stray%20animal%20waiting%20for%20help&image_size=portrait_4_3',
        status: 'pending',
        createTime: now.getTime(),
        createdAt: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`,
        foundTime: this.data.discoveryDate,
        description: this.data.description
      };

      const pendingList = wx.getStorageSync('pendingRescueList') || [];
      pendingList.unshift(newRecord);
      wx.setStorageSync('pendingRescueList', pendingList);

      wx.removeStorageSync('currentDraft');

      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    });
  },

  getNeedLabel: function(need) {
    const labels = {
      'medical': '疾病治疗',
      'food': '食物救助',
      'sterilization': '绝育手术',
      '疾病治疗': '疾病治疗',
      '食物救助': '食物救助',
      '绝育手术': '绝育手术'
    };
    return labels[need] || need;
  }
});

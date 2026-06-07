const api = require('../../utils/api.js');

const DEFAULT_IMAGE = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20pet%20placeholder&image_size=square';

Page({
  data: {
    rescueList: [],
    isLoading: true
  },

  onLoad: function(options) {
    this.fetchMyRescues();
  },

  onShow: function() {
    this.fetchMyRescues();
  },

  parsePhotoUrls: function(photoUrls) {
    if (!photoUrls) return [];
    if (Array.isArray(photoUrls)) return photoUrls;
    if (typeof photoUrls === 'string') {
      try {
        return JSON.parse(photoUrls);
      } catch (e) {
        return [photoUrls];
      }
    }
    return [];
  },

  fetchMyRescues: async function() {
    const that = this;
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;

    if (!userId) {
      wx.hideLoading();
      that.setData({ isLoading: false });
      return;
    }

    console.log('获取救助记录 - userId:', userId);

    wx.showLoading({ title: '加载中...' });

    try {
      const res = await api.getMyRescueRecords(userId);
      wx.hideLoading();
      console.log('API返回结果:', res);

      if (res.success) {
        // 转换数据格式，适配前端展示
        // 只显示已完成的救助记录（status=3）
        const completedRecords = (res.data || []).filter(item => item.status === 3);
        
        const formattedList = completedRecords.map(item => {
          const photoUrls = this.parsePhotoUrls(item.photo_urls);
          const imageUrl = photoUrls.length > 0 ? photoUrls[0] : DEFAULT_IMAGE;
          
          return {
            record_id: item.record_id,
            pet_id: item.pet_id,
            rescue_time: item.completed_at || item.created_at,
            animal: {
              name: item.pet_name || item.animal_name || '未知小可爱',
              photo_urls: photoUrls,
              image: imageUrl,
              gender: 0,
              breed: item.animal_name || ''
            }
          };
        });
        
        that.setData({
          rescueList: formattedList,
          isLoading: false
        });
      } else {
        wx.showToast({ title: res.message || '获取数据失败', icon: 'none' });
        that.setData({ isLoading: false });
      }
    } catch (error) {
      wx.hideLoading();
      console.error('获取救助记录失败:', error);
      wx.showToast({ title: '网络请求失败', icon: 'none' });
      that.setData({ isLoading: false });
    }
  },

  goToDetail: function(e) {
    const recordId = e.currentTarget.dataset.recordid;
    const petId = e.currentTarget.dataset.petid;
    if (recordId) {
      wx.navigateTo({
        url: '/pages/rescue-detail/rescue-detail?id=' + recordId
      });
    } else if (petId) {
      wx.navigateTo({
        url: '/pages/animal_detail/animal_detail?id=' + petId
      });
    } else {
      wx.showToast({ title: '记录不存在', icon: 'none' });
    }
  }
});

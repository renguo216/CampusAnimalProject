const api = require('../../utils/api.js');

const BASE_URL = 'http://192.168.40.73:5000';
const DEFAULT_IMAGE = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20pet%20placeholder&image_size=square';

Page({
  data: {
    adoptionList: [],
    isLoading: true
  },

  onLoad: function(options) {
    this.fetchMyAdoptions();
  },

  onShow: function() {
    this.fetchMyAdoptions();
  },

  parsePhotoUrls: function(photoUrls) {
    if (!photoUrls) return [];
    if (Array.isArray(photoUrls)) {
      // 将相对路径转换为完整URL
      return photoUrls.map(url => {
        if (typeof url === 'string') {
          url = url.replace(/`/g, '').trim();
          // 如果是相对路径，添加BASE_URL
          if (url.startsWith('/')) {
            return BASE_URL + url;
          }
          return url;
        }
        return url;
      });
    }
    if (typeof photoUrls === 'string') {
      try {
        // 去除可能存在的反引号
        const cleaned = photoUrls.replace(/`/g, '');
        const parsed = JSON.parse(cleaned);
        if (Array.isArray(parsed)) {
          // 将相对路径转换为完整URL
          return parsed.map(url => {
            if (typeof url === 'string') {
              url = url.replace(/`/g, '').trim();
              // 如果是相对路径，添加BASE_URL
              if (url.startsWith('/')) {
                return BASE_URL + url;
              }
              return url;
            }
            return url;
          });
        }
        // 单条URL
        const singleUrl = cleaned.trim();
        if (singleUrl.startsWith('/')) {
          return [BASE_URL + singleUrl];
        }
        return [singleUrl];
      } catch (e) {
        // 如果不是 JSON 数组，去除反引号后直接作为单个 URL
        const singleUrl = photoUrls.replace(/`/g, '').trim();
        if (singleUrl.startsWith('/')) {
          return [BASE_URL + singleUrl];
        }
        return [singleUrl];
      }
    }
    return [];
  },

  fetchMyAdoptions: async function() {
    const that = this;
    const userInfo = wx.getStorageSync('userInfo');
    const userId = userInfo ? userInfo.user_id : null;

    if (!userId) {
      wx.hideLoading();
      that.setData({ isLoading: false });
      return;
    }

    console.log('获取领养记录 - userId:', userId);

    wx.showLoading({ title: '加载中...' });

    try {
      const res = await api.getMyAdoptionRecords(userId);
      wx.hideLoading();
      console.log('API返回结果:', res);

      if (res.success) {
        // 转换数据格式，适配前端展示
        // 只显示审核通过的领养申请（status=1）
        const statusMap = {
          0: '审核中',
          1: '已通过',
          2: '已驳回'
        };
        
        // 过滤出审核通过的领养申请
        const approvedRecords = (res.data || []).filter(item => item.status === 1);
        
        const formattedList = approvedRecords.map(item => {
          const photoUrls = this.parsePhotoUrls(item.pet_photo_urls);
          const photoUrl = photoUrls.length > 0 ? photoUrls[0] : DEFAULT_IMAGE;
          
          return {
            apply_id: item.apply_id,
            pet_id: item.pet_id,
            petName: item.pet_name || '未知小可爱',
            photoUrl: photoUrl,
            gender: item.gender || 0,
            breed: item.pet_breed || '',
            applyTime: item.created_at || '未知',
            status: item.status || 0,
            statusText: statusMap[item.status] || '审核中'
          };
        });
        
        that.setData({
          adoptionList: formattedList,
          isLoading: false
        });
      } else {
        wx.showToast({ title: res.message || '获取数据失败', icon: 'none' });
        that.setData({ isLoading: false });
      }
    } catch (error) {
      wx.hideLoading();
      console.error('获取领养记录失败:', error);
      wx.showToast({ title: '网络请求失败', icon: 'none' });
      that.setData({ isLoading: false });
    }
  },

  goToDetail: function(e) {
    const petId = e.currentTarget.dataset.petid;
    if (petId) {
      wx.navigateTo({
        url: '/pages/animal_detail/animal_detail?id=' + petId
      });
    } else {
      wx.showToast({ title: '动物档案尚未建立', icon: 'none' });
    }
  }
});
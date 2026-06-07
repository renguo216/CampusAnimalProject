const api = require('../../utils/api.js');

const DEFAULT_IMAGE = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20pet%20placeholder&image_size=square';

Page({
  data: {
    petId: null,
    pet: null,
    defaultImage: DEFAULT_IMAGE,
    loading: true,
    canAdopt: false
  },

  onLoad: function(options) {
    const id = options.id ? String(options.id) : null;
    if (!id) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 800);
      return;
    }
    this.setData({ petId: id });
    this.loadPetDetail(id);
  },

  formatAge: function(month) {
    const m = parseInt(month) || 0;
    if (m <= 0) return '未知';
    if (m < 12) return m + '个月';
    const years = Math.floor(m / 12);
    const rest = m % 12;
    return rest > 0 ? years + '岁' + rest + '个月' : years + '岁';
  },

  formatDateTime: function(value) {
    if (!value) return '';
    const d = new Date(value);
    if (isNaN(d.getTime())) return value;
    const pad = n => (n < 10 ? '0' + n : '' + n);
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  },

  loadPetDetail: function(id) {
    this.setData({ loading: true });
    
    return api.getAnimalListAll({})
      .then(res => {
        const list = (res && res.data && res.data.animals) || [];
        const pet = list.find(p => String(p.pet_id) === String(id) || String(p.id) === String(id));
        if (!pet) {
          this.setData({ pet: null, loading: false });
          wx.showToast({ title: '未找到该动物', icon: 'none' });
          return;
        }
        
        const formatted = this.formatPetData(pet);
        
        this.setData({
          pet: formatted,
          loading: false,
          canAdopt: formatted.status === 0
        });
      })
      .catch(err => {
        console.error('加载动物详情失败:', err);
        this.setData({ pet: null, loading: false });
        wx.showToast({ title: '加载失败', icon: 'none' });
      });
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

  formatPetData: function(pet) {
    const petId = pet.pet_id || pet.id;
    const status = typeof pet.status === 'number' ? pet.status : 0;
    const statusMap = { 0: '可领养', 1: '已领养', 2: '需医疗' };
    const statusClassMap = { 0: 'available', 1: 'adopted', 2: 'medical' };
    const genderMap = { 0: '未知', 1: '弟弟', 2: '妹妹' };
    const neuteredMap = { 0: '未知', 1: '已绝育', 2: '未绝育' };
    const vaccinatedMap = { 0: '未知', 1: '已疫苗', 2: '未疫苗' };
    
    const storedImages = this.parsePhotoUrls(pet.photo_urls);
    const images = (pet.images && pet.images.length > 0)
      ? pet.images
      : (storedImages.length > 0 ? storedImages : [DEFAULT_IMAGE]);

    return {
      ...pet,
      id: petId,
      images,
      image: images[0],
      statusText: statusMap[status] || '可领养',
      statusClass: statusClassMap[status] || 'available',
      ageText: this.formatAge(pet.age),
      genderText: genderMap[pet.gender] || '未知',
      neuteredText: neuteredMap[pet.is_neutered || pet.isNeutered] || '未知',
      vaccinatedText: vaccinatedMap[pet.is_vaccinated || pet.isVaccinated] || '未知',
      createTimeText: this.formatDateTime(pet.created_at || pet.createTime),
      foundLocation: pet.found_location || pet.foundLocation
    };
  },

  goToAdoptApply: function() {
    const pet = this.data.pet;
    if (!pet) return;
    
    wx.navigateTo({
      url: `/pages/adopt-apply/adopt-apply?id=${pet.id}&name=${encodeURIComponent(pet.name)}`
    });
  }
});
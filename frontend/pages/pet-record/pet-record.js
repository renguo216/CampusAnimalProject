const api = require('../../utils/api.js');

const DEFAULT_IMAGE = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20pet%20placeholder&image_size=square';
const BASE_URL = 'http://192.168.40.73:5000';

Page({
  data: {
    petList: [],
    loading: false,
    refreshing: false,
    defaultImage: DEFAULT_IMAGE,
    stats: { total: 0, available: 0, adopted: 0 }
  },

  onLoad: function() {
    this.loadPetList();
  },

  onShow: function() {
    this.loadPetList();
  },

  onRefresh: function() {
    this.setData({ refreshing: true });
    this.loadPetList().then(() => {
      this.setData({ refreshing: false });
    }).catch(() => {
      this.setData({ refreshing: false });
    });
  },

  formatAge: function(month) {
    const m = parseInt(month) || 0;
    if (m <= 0) return '年龄未知';
    if (m < 12) return m + '个月';
    const years = Math.floor(m / 12);
    const rest = m % 12;
    return rest > 0 ? years + '岁' + rest + '个月' : years + '岁';
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

  formatPet: function(p) {
    const petId = p.pet_id || p.id;
    const genderMap = { 0: '未知性别', 1: '弟弟', 2: '妹妹' };
    const neuteredMap = { 0: '绝育未知', 1: '已绝育', 2: '未绝育' };
    const vaccinatedMap = { 0: '疫苗未知', 1: '已疫苗', 2: '未疫苗' };
    const statusMap = { 0: '可领养', 1: '已领养', 2: '需医疗' };
    const statusClassMap = { 0: 'available', 1: 'adopted', 2: 'medical' };
    const status = typeof p.status === 'number' ? p.status : 0;
    
    const storedImages = this.parsePhotoUrls(p.photo_urls);
    const images = (p.images && p.images.length > 0)
      ? p.images
      : (storedImages.length > 0 ? storedImages : [DEFAULT_IMAGE]);
      
    return {
      ...p,
      id: petId,
      adopted: status === 1,
      image: p.image || images[0],
      images: images,
      ageText: this.formatAge(p.age),
      genderText: genderMap[p.gender] || '未知性别',
      neuteredText: neuteredMap[p.is_neutered || p.isNeutered] || '绝育未知',
      vaccinatedText: vaccinatedMap[p.is_vaccinated || p.isVaccinated] || '疫苗未知',
      statusText: statusMap[status] || '可领养',
      statusClass: statusClassMap[status] || 'available',
      foundLocation: p.found_location || p.foundLocation
    };
  },

  loadPetList: function() {
    this.setData({ loading: true });
    
    return api.getAnimalListAll({})
      .then(res => {
        console.log('动物档案API返回:', res);
        const list = (res && res.data && res.data.animals) || [];
        console.log('动物列表:', list);
        
        const serverFormatted = list.map(p => {
          console.log('原始动物数据:', p);
          console.log('photo_urls:', p.photo_urls, '类型:', typeof p.photo_urls);
          const formatted = this.formatPet(p);
          console.log('格式化后:', formatted);
          return formatted;
        });
        
        const stats = { total: serverFormatted.length, available: 0, adopted: 0 };
        serverFormatted.forEach(p => {
          if (p.adopted) stats.adopted++;
          else stats.available++;
        });
        
        this.setData({ petList: serverFormatted, stats, loading: false });
      })
      .catch(err => {
        console.error('加载动物档案失败:', err);
        this.setData({ petList: [], stats: { total: 0, available: 0, adopted: 0 }, loading: false });
        wx.showToast({ title: '加载失败', icon: 'none' });
      });
  }
});
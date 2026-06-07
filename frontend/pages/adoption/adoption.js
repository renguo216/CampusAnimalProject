const api = require('../../utils/api.js');

const DEFAULT_IMAGE = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20pet%20placeholder&image_size=square';
const BASE_URL = 'http://192.168.40.73:5000';
const STICKY_POST_ID = 'sticky_post_how_to_save_money';

const stickyPost = {
  id: STICKY_POST_ID,
  isSticky: true,
  author: '校园宠物之家',
  title: '如何科学省钱养宠？新手必看流程',
  content: '很多同学第一次养宠都会担心开销问题，其实只要做好规划，花得少也能养得好。下面给大家整理一份新手省钱养宠流程👇\n\n一、领养代替购买\n校内流浪猫狗大多已绝育、驱虫、疫苗，到校医院或救助站免费领养，体检费一般在 50 元以内。\n\n二、必备物资一次买齐\n猫粮 / 狗粮、饭盆水盆、猫砂盆、牵引绳、基础玩具，总共 200 元左右可以搞定。\n\n三、饮食与驱虫\n主粮选正规平价品牌，月均 80–120 元；驱虫每月一次，自购驱虫药 10 元/次。\n\n四、医疗省钱小技巧\n小毛病先到校医院，挂号费便宜；需要疫苗绝育可关注平台定期义诊活动，名单会发到领养交流群。\n\n五、积分与任务兑换\n完成平台日常签到、分享领养经验，就能攒积分，兑换主粮、驱虫药、玩具等物资。\n\n科学养宠不是靠花得多，而是靠用心。遇到问题随时在社区提问，志愿者和资深宠主都会来帮忙～',
  createTime: '置顶 · 1 周前'
};

Page({
  data: {
    petList: [],
    loading: false,
    refreshing: false
  },

  onLoad: function() {
    this.ensureStickyPost();
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
    const genderMap = { 0: '未知', 1: '公', 2: '母' };
    const neuteredMap = { 0: '未知', 1: '已绝育', 2: '未绝育' };
    const vaccinatedMap = { 0: '未知', 1: '已疫苗', 2: '未疫苗' };
    
    console.log('=== formatPet ===');
    console.log('原始数据:', p);
    console.log('photo_urls:', p.photo_urls);
    
    const storedImages = this.parsePhotoUrls(p.photo_urls);
    console.log('解析后的图片数组:', storedImages);
    
    const images = (p.images && p.images.length > 0)
      ? p.images
      : (storedImages.length > 0 ? storedImages : [DEFAULT_IMAGE]);
    console.log('最终图片列表:', images);
      
    const result = {
      ...p,
      id: petId,
      image: p.image || images[0],
      images: images,
      ageText: p.ageText || this.formatAge(p.age),
      genderText: p.genderText || (genderMap[p.gender] || '未知'),
      neuteredText: p.neuteredText || (neuteredMap[p.is_neutered || p.isNeutered] || '未知'),
      vaccinatedText: p.vaccinatedText || (vaccinatedMap[p.is_vaccinated || p.isVaccinated] || '未知'),
      foundLocation: p.found_location || p.foundLocation
    };
    
    console.log('格式化结果:', result);
    return result;
  },

  ensureStickyPost: function() {
    const allPosts = wx.getStorageSync('communityPosts') || [];
    const index = allPosts.findIndex(p => p.id === STICKY_POST_ID);
    if (index === -1) {
      allPosts.unshift({ ...stickyPost });
    } else {
      allPosts[index] = { ...stickyPost };
    }
    wx.setStorageSync('communityPosts', allPosts);
  },

  goPublishAdoption: function() {
    wx.navigateTo({ url: '/pages/publish-adoption/publish-adoption' });
  },

  goAddAnimal: function() {
    wx.navigateTo({ url: '/pages/add-animal/add-animal' });
  },

  goPetRecord: function() {
    wx.navigateTo({ url: '/pages/pet-record/pet-record' });
  },

  goStickyPost: function() {
    this.ensureStickyPost();
    wx.navigateTo({
      url: '/pages/post_detail/post_detail?id=' + STICKY_POST_ID
    });
  },

  loadPetList: function() {
    this.setData({ loading: true });
    
    return api.getAnimalListAll({})
      .then(res => {
        const list = (res && res.data && res.data.animals) || [];
        // 只显示 status=0 的可领养动物
        const availableList = list.filter(p => p.status === 0);
        const formatted = availableList.map(p => this.formatPet(p));
        
        this.setData({ petList: formatted, loading: false });
      })
      .catch(err => {
        console.error('加载待领养列表失败:', err);
        this.setData({ petList: [], loading: false });
        wx.showToast({ title: '加载失败', icon: 'none' });
      });
  },

  viewPetDetail: function(e) {
    const petId = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/pet-detail/pet-detail?id=' + petId });
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

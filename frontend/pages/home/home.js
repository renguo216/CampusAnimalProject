const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    currentTab: 'pending',
    rescueList: []
  },

  onShow: function() {
    this.loadRescueData();
  },

  loadRescueData: function() {
    const tab = this.data.currentTab;
    
    api.getRescueRecords().then(res => {
      console.log('获取救助记录结果:', res);
      if (res.success && res.data && res.data.records) {
        let records = res.data.records;
        console.log('筛选前记录数:', records.length);
        // 根据状态筛选
        if (tab === 'pending') {
          records = records.filter(r => r.status === 0);
        } else if (tab === 'processing') {
          records = records.filter(r => r.status === 1 || r.status === 2);
        } else if (tab === 'resolved') {
          records = records.filter(r => r.status === 3 || r.status === 4);
        }
        console.log('筛选后记录数:', records.length);
        // 转换格式
        const rescueList = records.map(r => {
          let photoUrl = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20stray%20animal%20waiting%20for%20help&image_size=portrait_4_3';
          if (r.photo_urls) {
            try {
              const urls = JSON.parse(r.photo_urls);
              if (urls && urls.length > 0) {
                photoUrl = urls[0];
              }
            } catch (e) {}
          }
          return {
            id: r.record_id,
            title: r.title || '救助记录',
            specie: r.animal_name || '流浪动物',
            needs: this.getNeedLabel(r.need_type) || '救助',
            location: r.location || r.found_location_text || '未知位置',
            image: photoUrl,
            status: this.getStatusText(r.status),
            createdAt: r.created_at ? r.created_at.substring(0, 10) : '',
            description: r.description || ''
          };
        });
        console.log('最终要显示的列表:', rescueList);
        this.setData({ rescueList });
      } else {
        console.log('没有获取到记录，使用本地存储');
        // 使用本地存储作为后备
        this.loadFromStorage(tab);
      }
    }).catch(err => {
      console.error('加载救助记录失败', err);
      this.loadFromStorage(tab);
    });
  },

  loadFromStorage: function(tab) {
    let rescueList = [];
    if (tab === 'pending') {
      rescueList = wx.getStorageSync('pendingRescueList') || [];
    } else if (tab === 'processing') {
      rescueList = wx.getStorageSync('processingRescueList') || [];
    } else if (tab === 'resolved') {
      rescueList = wx.getStorageSync('resolvedRescueList') || [];
    }
    
    if (rescueList.length === 0 && tab === 'pending') {
      rescueList = [
        {
          id: '1',
          title: '西门发现一只受伤小橘',
          specie: '中华田园猫 (橘猫)',
          needs: '疾病治疗',
          location: '西科大西门附近草丛',
          image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20orange%20tabby%20cat%20with%20injured%20leg%20looking%20sad&image_size=portrait_4_3',
          status: 'pending',
          createdAt: '2024-02-15',
          description: '在图书馆门口发现一只受伤的橘猫，腿好像断了，需要紧急救助。猫咪很亲人，希望好心人能帮帮它。'
        },
        {
          id: '2',
          title: '图书馆后流浪狗求助',
          specie: '混血犬',
          needs: '食物救助',
          location: '图书馆后门废弃车棚',
          image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20mixed%20breed%20dog%20stray%20friendly%20looking%20for%20help&image_size=portrait_4_3',
          status: 'pending',
          createdAt: '2024-02-14',
          description: '图书馆后面发现一只流浪狗，瘦弱不堪，急需食物和救助。'
        }
      ];
      wx.setStorageSync('pendingRescueList', rescueList);
    }
    
    this.setData({ rescueList });
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
    this.loadRescueData();
  },

  handleReport: function() {
    wx.navigateTo({ url: '/pages/create-rescue/create-rescue' });
  },

  handleAIIdentify: function() {
    wx.chooseImage({
      count: 1,
      success: async (res) => {
        wx.showLoading({ title: 'AI识别中...' });
        try {
          const result = await api.aiIdentify(res.tempFilePaths[0]);
          wx.hideLoading();
          
          if (result.success) {
            const data = result.data || result;
            const breed = data.breed || data.species || '未知';
            const confidence = data.confidence || 0;
            const suggestion = data.suggestion || '';
            
            let content = `🐾 识别结果：${breed}\n`;
            content += `置信度：${(confidence * 100).toFixed(1)}%\n`;
            if (suggestion) {
              content += `\n建议：${suggestion}`;
            }
            
            wx.showModal({
              title: 'AI识别完成',
              content: content,
              showCancel: false,
              confirmText: '知道了',
              success: () => {}
            });
            
            setTimeout(() => {
              wx.hideModal();
            }, 10000);
          } else {
            wx.showToast({ 
              title: result.message || '识别失败', 
              icon: 'none',
              duration: 2000 
            });
          }
        } catch (err) {
          wx.hideLoading();
          wx.showToast({ 
            title: '识别失败，请重试', 
            icon: 'none',
            duration: 2000 
          });
          console.error('AI识别错误:', err);
        }
      },
      fail: (err) => {
        console.error('选择图片失败:', err);
        wx.showToast({ title: '选择图片失败', icon: 'none' });
      }
    });
  },

  handleNearbyHospital: function() {
    wx.navigateTo({ url: '/pages/hospital/hospital' });
  },

  handleDonation: function() {
    wx.navigateTo({ url: '/pages/donation/donation' });
  },

  viewRescueDetail: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/rescue-detail/rescue-detail?id=${id}`
    });
  },

  navigateToHome: function() {
    wx.reLaunch({ url: '/pages/home/home' });
  },

  navigateToAdoption: function() {
    wx.navigateTo({ url: '/pages/adoption/adoption' });
  },

  navigateToCommunity: function() {
    wx.navigateTo({ url: '/pages/community/community' });
  },

  navigateToProfile: function() {
    wx.navigateTo({ url: '/pages/profile/profile' });
  },

  getStatusText: function(status) {
    const statusMap = {
      0: 'pending',
      1: 'processing',
      2: 'processing',
      3: 'resolved',
      4: 'resolved'
    };
    return statusMap[status] || 'pending';
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
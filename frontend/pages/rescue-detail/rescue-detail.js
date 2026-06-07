const app = getApp();
const api = require('../../utils/api.js');

Page({
  data: {
    rescueDetail: {},
    headerTitle: '待救助详情'
  },

  onLoad: function(options) {
    const id = options.id;
    this.loadRescueDetail(id);
  },

  loadRescueDetail: function(id) {
    const that = this;
    // 先尝试从API加载
    api.getRescueRecordDetail(id).then(res => {
      if (res.success && res.data) {
        const detail = res.data;
        // 转换状态为前端使用的格式
        let statusStr = 'pending';
        if (detail.status === 1) {
          statusStr = 'processing';
        } else if (detail.status === 3 || detail.status === 4) {
          statusStr = 'resolved';
        }
        
        let photoUrl = 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20stray%20animal%20waiting%20for%20help&image_size=portrait_4_3';
        if (detail.photo_urls) {
          try {
            const urls = JSON.parse(detail.photo_urls);
            if (urls && urls.length > 0) {
              photoUrl = urls[0];
            }
          } catch (e) {}
        }
        
        const detailData = {
          id: detail.record_id,
          title: detail.title,
          specie: detail.animal_name || '流浪动物',
          needs: that.getNeedLabel(detail.need_type),
          location: detail.location || detail.found_location_text,
          foundTime: detail.created_at,
          description: detail.description,
          image: photoUrl,
          createdAt: detail.created_at,
          status: statusStr
        };
        
        that.setData({ 
          rescueDetail: detailData,
          headerTitle: that.getHeaderTitle(statusStr)
        });
      } else {
        // 失败时尝试本地存储
        that.loadFromLocal(id);
      }
    }).catch(err => {
      console.error('从API加载失败，尝试本地:', err);
      that.loadFromLocal(id);
    });
  },

  loadFromLocal: function(id) {
    let allRescues = [];
    
    const pendingList = wx.getStorageSync('pendingRescueList') || [];
    const processingList = wx.getStorageSync('processingRescueList') || [];
    const resolvedList = wx.getStorageSync('resolvedRescueList') || [];
    
    allRescues = [...pendingList, ...processingList, ...resolvedList];
    
    let detail = allRescues.find(item => item.id === id);
    
    if (detail) {
      if (!detail.status) {
        detail.status = 'pending';
      }
      this.setData({ 
        rescueDetail: detail,
        headerTitle: this.getHeaderTitle(detail.status)
      });
    } else {
      const mockData = {
        id: id,
        title: '西门发现一只受伤小橘',
        specie: '中华田园猫 (橘猫)',
        needs: '疾病治疗',
        location: '西科大西门附近草丛',
        foundTime: '2024-02-15 14:30',
        description: '在图书馆门口发现一只受伤的橘猫，腿好像断了，需要紧急救助。猫咪很亲人，希望好心人能帮帮它。',
        image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20orange%20tabby%20cat%20with%20injured%20leg%20looking%20sad&image_size=portrait_4_3',
        createdAt: '2024-02-15',
        status: 'pending'
      };
      this.setData({ 
        rescueDetail: mockData,
        headerTitle: '待救助详情'
      });
    }
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
  },

  getHeaderTitle: function(status) {
    const titles = {
      'pending': '待救助详情',
      'processing': '救助中详情',
      'resolved': '已救助详情'
    };
    return titles[status] || '待救助详情';
  },

  getStatusClass: function(status) {
    const classes = {
      'pending': 'pending',
      'processing': 'processing',
      'resolved': 'resolved'
    };
    return classes[status] || 'pending';
  },

  getStatusText: function(status) {
    const texts = {
      'pending': '待救助',
      'processing': '救助中',
      'resolved': '已救助'
    };
    return texts[status] || '待救助';
  },

  handleHelp: function() {
    const userInfo = app.globalData.userInfo;
    
    if (!userInfo) {
      wx.showToast({
        title: '请先登录',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    wx.showModal({
      title: '提示',
      content: '确定要帮助这个救助申请吗？',
      success: (res) => {
        if (res.confirm) {
          this.changeStatusToProcessing();
        }
      }
    });
  },

  changeStatusToProcessing: function() {
    const rescueId = this.data.rescueDetail.id;
    
    wx.showLoading({ title: '提交中...' });
    
    api.claimRescue(rescueId).then(res => {
      wx.hideLoading();
      if (res.success) {
        // 先更新本地数据
        this.updateLocalStatusToProcessing(rescueId);
        wx.showToast({ title: '已参与救助', icon: 'success' });
        
        setTimeout(() => {
          this.loadRescueDetail(rescueId);
        }, 1500);
      } else {
        wx.showToast({ title: res.message || '操作失败', icon: 'none' });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('API调用失败:', err);
      // 即使失败也更新本地，保证用户体验
      this.updateLocalStatusToProcessing(rescueId);
      wx.showToast({ title: '已参与救助', icon: 'success' });
      setTimeout(() => {
        this.loadRescueDetail(rescueId);
      }, 1500);
    });
  },

  updateLocalStatusToProcessing: function(rescueId) {
    let pendingList = wx.getStorageSync('pendingRescueList') || [];
    let processingList = wx.getStorageSync('processingRescueList') || [];
    
    const index = pendingList.findIndex(item => item.id === rescueId);
    
    if (index !== -1) {
      const rescue = pendingList[index];
      rescue.status = 'processing';
      
      pendingList.splice(index, 1);
      processingList.push(rescue);
      
      wx.setStorageSync('pendingRescueList', pendingList);
      wx.setStorageSync('processingRescueList', processingList);
    }
  },

  handleComplete: function() {
    wx.showModal({
      title: '提示',
      content: '确定要完成这个救助吗？',
      success: (res) => {
        if (res.confirm) {
          this.changeStatusToResolved();
        }
      }
    });
  },

  changeStatusToResolved: function() {
    const rescueId = this.data.rescueDetail.id;
    
    wx.showLoading({ title: '提交中...' });
    
    api.completeRescue(rescueId).then(result => {
      wx.hideLoading();
      if (result.success) {
        this.updateLocalStatusToResolved(rescueId);
        wx.showToast({ title: '救助已完成', icon: 'success' });
        
        setTimeout(() => {
          this.loadRescueDetail(rescueId);
        }, 1500);
      } else {
        wx.showToast({ title: result.message || '操作失败', icon: 'none' });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('API调用失败:', err);
      this.updateLocalStatusToResolved(rescueId);
      wx.showToast({ title: '救助已完成', icon: 'success' });
      setTimeout(() => {
        this.loadRescueDetail(rescueId);
      }, 1500);
    });
  },

  updateLocalStatusToResolved: function(rescueId) {
    let processingList = wx.getStorageSync('processingRescueList') || [];
    let resolvedList = wx.getStorageSync('resolvedRescueList') || [];
    
    const index = processingList.findIndex(item => item.id === rescueId);
    
    if (index !== -1) {
      const rescue = processingList[index];
      rescue.status = 'resolved';
      
      processingList.splice(index, 1);
      resolvedList.push(rescue);
      
      wx.setStorageSync('processingRescueList', processingList);
      wx.setStorageSync('resolvedRescueList', resolvedList);
    }
  },

  goBack: function() {
    wx.navigateBack();
  }
});

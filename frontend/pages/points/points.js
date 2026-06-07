const api = require('../../utils/api.js');

Page({
  data: {
    myPoints: 0,
    activeTab: 'products',
    products: [],
    exchangeRecords: [],
    loading: false,
    productsLoading: false,
    recordsLoading: false
  },

  onLoad: function() {
    this.loadMyPoints();
    this.loadProducts();
    this.loadExchangeRecords();
  },

  onShow: function() {
    this.loadMyPoints();
  },

  loadMyPoints: async function() {
    try {
      const userInfo = wx.getStorageSync('userInfo');
      const userId = userInfo ? userInfo.user_id : '';
      
      if (!userId) {
        this.setData({ myPoints: 0 });
        return;
      }
      
      console.log('从数据库获取用户积分，userId:', userId);
      const result = await api.getMyPoints(userId);
      console.log('积分API返回:', result);
      
      if (result.success) {
        // 处理不同的返回数据结构
        let points = 0;
        if (result.data && result.data.points !== undefined) {
          points = result.data.points;
        } else if (result.points !== undefined) {
          points = result.points;
        }
        
        this.setData({ myPoints: points });
        
        // 更新本地Storage中的积分
        const updatedUserInfo = { ...userInfo, points: points };
        wx.setStorageSync('userInfo', updatedUserInfo);
        console.log('积分已更新:', points);
      }
    } catch (error) {
      console.error('获取积分失败:', error);
      const userInfo = wx.getStorageSync('userInfo');
      if (userInfo && userInfo.points !== undefined) {
        this.setData({ myPoints: userInfo.points });
      }
    }
  },

  loadProducts: async function() {
    try {
      console.log('开始加载积分商品...');
      this.setData({ productsLoading: true });
      const result = await api.getPointProducts();
      console.log('积分商品API返回结果:', result);
      
      if (result.success && result.data) {
        this.setData({ products: result.data });
        console.log('成功设置商品数据:', result.data);
      } else {
        console.log('API返回失败或数据为空');
        this.setData({ products: [] });
        wx.showToast({ title: '加载商品失败', icon: 'none' });
      }
    } catch (error) {
      console.error('加载积分商品失败:', error);
      this.setData({ products: [] });
      wx.showToast({ title: '网络错误', icon: 'none' });
    } finally {
      this.setData({ productsLoading: false });
    }
  },

  loadExchangeRecords: async function() {
    try {
      this.setData({ recordsLoading: true });
      const userInfo = wx.getStorageSync('userInfo');
      const userId = userInfo ? userInfo.user_id : '';
      console.log('加载兑换记录，userId:', userId);
      const result = await api.getExchangeRecords(userId);
      console.log('兑换记录API返回结果:', result);
      
      if (result.success && result.data) {
        this.setData({ exchangeRecords: result.data });
      } else {
        console.log('暂无兑换记录');
        this.setData({ exchangeRecords: [] });
      }
    } catch (error) {
      console.error('加载兑换记录失败:', error);
      this.setData({ exchangeRecords: [] });
    } finally {
      this.setData({ recordsLoading: false });
    }
  },

  goBack: function() {
    wx.navigateBack();
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },

  exchangeProduct: async function(e) {
    const productId = e.currentTarget.dataset.id;
    const product = this.data.products.find(p => p.id === productId);
    
    if (!product) {
      wx.showToast({ title: '商品不存在', icon: 'none' });
      return;
    }
    
    if (this.data.myPoints < product.points) {
      wx.showToast({ title: '积分不足', icon: 'none' });
      return;
    }
    
    if (product.stock <= 0) {
      wx.showToast({ title: '库存不足', icon: 'none' });
      return;
    }
    
    wx.showModal({
      title: '确认兑换',
      content: `确定要兑换 ${product.name} 吗？将消耗 ${product.points} 积分`,
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '兑换中...' });
            const userInfo = wx.getStorageSync('userInfo');
            const userId = userInfo ? userInfo.user_id : '';
            
            const result = await api.exchangeProduct(userId, productId);
            wx.hideLoading();
            
            if (result.success) {
              wx.showToast({ title: '兑换成功', icon: 'success' });
              
              // 重新从数据库加载积分
              this.loadMyPoints();
              
              // 重新加载商品和兑换记录
              this.loadProducts();
              this.loadExchangeRecords();
            } else {
              wx.showToast({ title: result.message || '兑换失败', icon: 'none' });
            }
          } catch (error) {
            wx.hideLoading();
            console.error('兑换失败:', error);
            wx.showToast({ title: '兑换失败', icon: 'none' });
          }
        }
      }
    });
  }
});
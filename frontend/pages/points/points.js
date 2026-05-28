const api = require('../../utils/api.js');

Page({
  data: {
    myPoints: 0,
    activeTab: 'products',
    products: [
      {
        id: 1,
        name: '宠物罐头零食',
        description: '优质鸡肉配方，营养均衡',
        points: 500,
        image: '/images/product1.png'
      },
      {
        id: 2,
        name: '猫咪逗猫棒',
        description: '彩色羽毛，增添乐趣',
        points: 300,
        image: '/images/product2.png'
      },
      {
        id: 3,
        name: '宠物饮水机',
        description: '循环过滤，保持水质新鲜',
        points: 2000,
        image: '/images/product3.png'
      },
      {
        id: 4,
        name: '宠物清洁湿巾',
        description: '温和配方，清洁护肤',
        points: 400,
        image: '/images/product4.png'
      },
      {
        id: 5,
        name: '动物救助徽章',
        description: '限量版纪念徽章',
        points: 1000,
        image: '/images/product5.png'
      }
    ],
    exchangeRecords: [
      {
        id: 1,
        productName: '宠物罐头零食',
        exchangeTime: '2024-01-15 14:30',
        points: 500,
        status: 'completed',
        statusText: '已完成'
      },
      {
        id: 2,
        productName: '猫咪逗猫棒',
        exchangeTime: '2024-01-10 09:20',
        points: 300,
        status: 'pending',
        statusText: '配送中'
      }
    ]
  },

  onLoad: function() {
    this.loadMyPoints();
  },

  loadMyPoints: function() {
    setTimeout(() => {
      this.setData({ myPoints: 2580 });
    }, 500);
  },

  goBack: function() {
    wx.navigateBack();
  },

  goToExchangeRecords: function() {
    this.setData({ activeTab: 'records' });
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },

  exchangeProduct: function(e) {
    const productId = e.currentTarget.dataset.id;
    const productPoints = e.currentTarget.dataset.points;
    const product = this.data.products.find(p => p.id === productId);

    wx.showModal({
      title: '确认兑换',
      content: `确定要兑换"${product.name}"吗？需要消耗${productPoints}积分。`,
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '兑换中...' });
          
          setTimeout(() => {
            wx.hideLoading();
            
            this.setData({
              myPoints: this.data.myPoints - productPoints,
              exchangeRecords: [
                {
                  id: Date.now(),
                  productName: product.name,
                  exchangeTime: new Date().toLocaleString(),
                  points: productPoints,
                  status: 'pending',
                  statusText: '配送中'
                },
                ...this.data.exchangeRecords
              ]
            });

            wx.showToast({
              title: '兑换成功',
              icon: 'success'
            });
          }, 1500);
        }
      }
    });
  }
});
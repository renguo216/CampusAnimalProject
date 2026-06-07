// pages/hospital/hospital.js
const api = require('../../utils/api.js');

Page({
  data: {
    hospitals: [],
    filteredHospitals: [],
    selectedDistance: 'all'
  },

  onLoad: function() {
    this.loadHospitals();
  },

  onShow: function() {
    this.loadHospitals();
  },

  loadHospitals: function() {
    wx.showLoading({ title: '加载中...' });

    api.getHospitals().then(res => {
      wx.hideLoading();
      if (res.success && res.data && res.data.hospitals) {
        const hospitals = res.data.hospitals.map(h => ({
          id: h.hospital_id,
          name: h.name,
          address: h.address,
          tags: h.services ? JSON.parse(h.services) : [],
          services: h.services ? JSON.parse(h.services) : [],
          distance: h.distance,
          phone: h.phone
        }));
        this.setData({
          hospitals: hospitals,
          filteredHospitals: hospitals
        });
      } else {
        wx.showToast({ title: '加载失败', icon: 'none' });
        this.setMockData();
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('获取医院列表失败:', err);
      // 使用模拟数据作为后备
      this.setMockData();
    });
  },

  setMockData: function() {
    const mockHospitals = [
      {
        id: '1',
        name: '瑞鹏宠物医院',
        address: '临潼区人民路中段168号',
        tags: ['24小时', '全科', '疫苗接种'],
        services: ['24小时', '全科', '疫苗接种'],
        distance: '1.2',
        phone: '029-81366666'
      },
      {
        id: '2',
        name: '爱诺动物医院',
        address: '临潼区文化路西段23号',
        tags: ['骨科', '眼科', '住院部'],
        services: ['骨科', '眼科', '住院部'],
        distance: '2.1',
        phone: '029-81388888'
      },
      {
        id: '3',
        name: '美联众合宠物医院',
        address: '临潼区秦唐大道88号',
        tags: ['牙科', '皮肤科', '绝育手术'],
        services: ['牙科', '皮肤科', '绝育手术'],
        distance: '2.8',
        phone: '029-81399999'
      }
    ];
    this.setData({
      hospitals: mockHospitals,
      filteredHospitals: mockHospitals
    });
  },

  selectDistance: function(e) {
    const distance = e.currentTarget.dataset.distance;
    this.setData({ selectedDistance: distance });
    this.filterHospitals(distance);
  },

  filterHospitals: function(distance) {
    const hospitals = this.data.hospitals;

    if (distance === 'all') {
      this.setData({ filteredHospitals: hospitals });
      return;
    }

    const filtered = hospitals.filter(item => {
      const hospitalDistance = parseFloat(item.distance);
      return hospitalDistance * 1000 <= distance;
    });

    this.setData({ filteredHospitals: filtered });
  },

  viewHospital: function(e) {
    const id = e.currentTarget.dataset.id;
    const hospital = this.data.filteredHospitals.find(h => h.id == id);
    if (hospital) {
      wx.showModal({
        title: hospital.name,
        content: `地址：${hospital.address}\n电话：${hospital.phone}\n服务：${(hospital.services || hospital.tags || []).join('、')}`,
        showCancel: true,
        cancelText: '关闭',
        confirmText: '拨打电话',
        success: (res) => {
          if (res.confirm) {
            wx.makePhoneCall({ phoneNumber: hospital.phone });
          }
        }
      });
    }
  },

  callHospital: function(e) {
    const phone = e.currentTarget.dataset.phone;
    wx.makePhoneCall({ phoneNumber: phone });
  },

  goHome: function() {
    wx.reLaunch({ url: '/pages/home/home' });
  },

  goAdoption: function() {
    wx.navigateTo({ url: '/pages/adoption/adoption' });
  },

  goCommunity: function() {
    wx.navigateTo({ url: '/pages/community/community' });
  },

  goProfile: function() {
    wx.navigateTo({ url: '/pages/profile/profile' });
  }
});

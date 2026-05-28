// pages/hospital/hospital.js
Page({
  data: {
    hospitals: [
      {
        id: '1',
        name: '瑞鹏宠物医院',
        address: '临潼区人民路中段168号',
        tags: ['24小时', '全科', '疫苗接种'],
        distance: '1.2km',
        phone: '029-81366666'
      },
      {
        id: '2',
        name: '爱诺动物医院',
        address: '临潼区文化路西段23号',
        tags: ['骨科', '眼科', '住院部'],
        distance: '2.1km',
        phone: '029-81388888'
      },
      {
        id: '3',
        name: '美联众合宠物医院',
        address: '临潼区秦唐大道88号',
        tags: ['牙科', '皮肤科', '绝育手术'],
        distance: '2.8km',
        phone: '029-81399999'
      }
    ]
  },

  viewHospital: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: `查看医院: ${id}`, icon: 'none' });
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
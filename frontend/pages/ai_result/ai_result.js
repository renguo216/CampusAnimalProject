// pages/ai_result/ai_result.js
Page({
  data: {
    result: {
      image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=calico%20cat%20beautiful%20fluffy%20portrait&image_size=portrait_4_3',
      breed: '中华田园猫',
      englishName: 'Dragon Li / Calico Variant',
      character: '中华田园猫性格独立而温顺，具有极强的生存能力。它们聪明伶俐，对主人忠诚，同时也保留了敏捷的狩猎天性。三花猫（Calico）更是以其独特的色彩分布和偶尔的"小脾气"深受喜爱。',
      intelligence: '极高 (Highly Active)',
      lifespan: '12 - 18 年',
      tips: [
        '它们适应力强，但需要定期驱虫和疫苗接种以保持健康。',
        '喜欢攀爬，建议在室内提供猫爬架等垂直活动空间。',
        '毛发易于打理，每周梳理一次即可保持光泽。'
      ]
    }
  },

  goBack: function() {
    wx.navigateBack();
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
  },

  shareResult: function() {
    wx.showToast({ title: '分享功能', icon: 'none' });
  }
});
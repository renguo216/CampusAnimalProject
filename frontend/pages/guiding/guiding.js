// pages/guiding/guiding.js
Page({
  data: {
    slogan: "让每一只校园流浪动物都有家可归",
    illustration: "/assets/images/cat_illustration.png"
  },
  
  // 绑定“开始探索”按钮动作，跳转到首页
  handleStartExplore: function() {
    wx.switchTab({
      url: '/pages/home/home'
    });
  }
});
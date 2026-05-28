// app.js
App({
  // 全局共享数据状态
  globalData: {
    // 映射自 T-User 类/表结构
    userInfo: {
      userId: '',       // 微信 OpenID 
      nickname: '',     // 用户昵称 
      avatarUrl: '',    // 头像路径 
      role: 1,          // 角色定义：1-普通用户，2-志愿者，3-管理员 
      points: 0,        // 志愿积分 (仅对志愿者有效) 
      identityNo: '',   // 校园学号/工号 (实名认证) 
      level: 0          // 管理员等级 
    },
    token: '',          // JWT 鉴权令牌，后续存储于 Redis 缓存中配合网关校验 
    currentLocation: null // 实时 LBS 定位坐标数据 [cite: 1, 3]
  },

  onLaunch: function () {
    // 启动时初始化定位，为首页及紧急救援提供支持
    this.getSystemLocation();
  },

  // 全局 LBS 定位获取函数
  getSystemLocation: function() {
    wx.getLocation({
      type: 'wgs84',
      success: (res) => {
        this.globalData.currentLocation = {
          latitude: res.latitude,
          longitude: res.longitude
        };
      },
      fail: () => {
        console.warn("LBS定位失败，部分位置服务将受限");
      }
    });
  }
});
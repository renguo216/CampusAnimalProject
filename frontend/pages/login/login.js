const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    isAgreed: false
  },

  handleAgreementChange: function(e) {
    this.setData({ isAgreed: e.detail.value.length > 0 });
  },

  handleWeChatLogin: function() {
    if (!this.data.isAgreed) {
      wx.showToast({ title: '请先阅读并同意相关服务协议与公约', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '登录中...' });

    // 获取用户信息
    wx.getUserProfile({
      desc: '用于完善用户资料',
      success: async (userRes) => {
        console.log('获取用户信息成功:', userRes.userInfo);
        
        // 登录
        wx.login({
          success: async (loginRes) => {
            if (loginRes.code) {
              try {
                const loginResult = await api.login(loginRes.code, {
                  rawData: userRes.rawData,
                  userInfo: userRes.userInfo
                });
                
                app.globalData.token = loginResult.token;
                app.globalData.userInfo = {
                  user_id: loginResult.user.user_id,
                  nickname: loginResult.user.nickname,
                  avatarUrl: loginResult.user.avatarURL,
                  role: loginResult.user.role,
                  points: loginResult.user.points || 0,
                  phone_number: loginResult.user.phone_number || ''
                };
                
                // 保存到本地storage
                wx.setStorageSync('userInfo', app.globalData.userInfo);
                wx.setStorageSync('token', loginResult.token);

                wx.hideLoading();
                wx.showToast({ title: '登录成功', icon: 'success' });
                
                setTimeout(() => {
                  wx.reLaunch({ url: '/pages/home/home' });
                }, 1500);
              } catch (error) {
                wx.hideLoading();
                console.error('登录API调用失败:', error);
                wx.showToast({ title: '网络连接失败，请检查网络', icon: 'none' });
              }
            } else {
              wx.hideLoading();
              console.error('微信登录失败:', loginRes.errMsg);
              wx.showToast({ title: '微信登录失败: ' + loginRes.errMsg, icon: 'none' });
            }
          },
          fail: (err) => {
            wx.hideLoading();
            console.error('wx.login调用失败:', err);
            wx.showToast({ title: '无法连接微信，请检查网络', icon: 'none' });
          }
        });
      },
      fail: (err) => {
        wx.hideLoading();
        console.error('获取用户信息失败:', err);
        wx.showToast({ title: '获取用户信息失败，请重试', icon: 'none' });
      }
    });
  }
});

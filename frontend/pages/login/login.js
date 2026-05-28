const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    isAgreed: false
  },

  handleAgreementChange: function(e) {
    this.setData({ isAgreed: e.detail.value.length > 0 });
  },

  handleWeChatLogin: async function() {
    if (!this.data.isAgreed) {
      wx.showToast({ title: '请先阅读并同意相关服务协议与公约', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '登录中...' });

    try {
      // 获取微信用户信息
      const userProfile = await new Promise((resolve, reject) => {
        wx.getUserProfile({
          desc: '用于完善用户资料',
          success: resolve,
          fail: reject
        });
      });

      // 获取登录凭证
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        });
      });

      if (loginRes.code) {
        // 将用户信息和登录凭证发送到后端
        const loginResult = await api.login(loginRes.code, {
          encryptedData: userProfile.encryptedData,
          iv: userProfile.iv,
          rawData: userProfile.rawData,
          signature: userProfile.signature
        });
        
        app.globalData.token = loginResult.token;
        app.globalData.userInfo = {
          userId: loginResult.user.user_id,
          nickname: loginResult.user.nickname,
          avatarUrl: loginResult.user.avatarURL,
          role: loginResult.user.role,
          points: loginResult.user.points || 0,
          identityNo: loginResult.user.identityNo || '',
          // 保存微信原始用户信息
          wechatUserInfo: {
            nickName: userProfile.userInfo.nickName,
            avatarUrl: userProfile.userInfo.avatarUrl,
            gender: userProfile.userInfo.gender,
            country: userProfile.userInfo.country,
            province: userProfile.userInfo.province,
            city: userProfile.userInfo.city
          }
        };

        wx.hideLoading();
        wx.showToast({ title: '登录成功', icon: 'success' });
        
        setTimeout(() => {
          wx.reLaunch({ url: '/pages/home/home' });
        }, 1500);
      } else {
        wx.hideLoading();
        console.error('微信登录失败:', loginRes.errMsg);
        wx.showToast({ title: '微信登录失败: ' + loginRes.errMsg, icon: 'none' });
      }
    } catch (error) {
      wx.hideLoading();
      console.error('登录过程出错:', error);
      if (error.errMsg && error.errMsg.includes('auth deny')) {
        wx.showToast({ title: '您拒绝了授权请求', icon: 'none' });
      } else {
        wx.showToast({ title: '网络连接失败，请检查网络', icon: 'none' });
      }
    }
  }
});
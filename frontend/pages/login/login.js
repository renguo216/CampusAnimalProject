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
                
                console.log('登录API返回结果:', loginResult);
                
                // 处理后端返回的数据格式
                if (loginResult.success) {
                  // 成功，需要获取完整的用户信息
                  let userData = loginResult.data;
                  console.log('登录接口返回的userData:', userData);
                  
                  // 如果注册成功只返回了user_id，需要重新获取用户信息
                  if (userData && !userData.nickname && userData.user_id) {
                    try {
                      console.log('需要重新获取用户详情，user_id:', userData.user_id);
                      const userDetail = await api.getUser(userData.user_id);
                      console.log('用户详情返回:', userDetail);
                      if (userDetail.success && userDetail.data) {
                        userData = userDetail.data;
                      }
                    } catch (e) {
                      console.log('获取用户详情失败:', e);
                    }
                  }
                  
                  console.log('最终的userData:', userData);
                  
                  // 使用后端返回的user_id作为token
                  const token = userData.user_id;
                  console.log('使用的token:', token);
                  
                  app.globalData.token = token;
                  app.globalData.userInfo = {
                    user_id: userData.user_id,
                    nickname: userData.nickname || userRes.userInfo.nickName,
                    avatarUrl: userData.avatarURL || userRes.userInfo.avatarUrl,
                    role: userData.role || 1,
                    points: userData.points || 0,
                    phone_number: userData.phone_number || ''
                  };
                  
                  console.log('保存的用户信息:', app.globalData.userInfo);
                  
                  // 保存到本地storage
                  wx.setStorageSync('userInfo', app.globalData.userInfo);
                  wx.setStorageSync('token', token);

                  wx.hideLoading();
                  wx.showToast({ title: '登录成功', icon: 'success' });
                  
                  setTimeout(() => {
                    wx.reLaunch({ url: '/pages/home/home' });
                  }, 1500);
                } else {
                  // 后端返回失败
                  wx.hideLoading();
                  console.error('登录失败:', loginResult.message);
                  wx.showToast({ 
                    title: loginResult.message || '登录失败，请重试', 
                    icon: 'none' 
                  });
                }
              } catch (error) {
                wx.hideLoading();
                console.error('登录API调用失败:', error);
                let errorMsg = '网络连接失败，请检查网络';
                if (error && error.message) {
                  errorMsg = error.message;
                } else if (typeof error === 'string') {
                  errorMsg = error;
                }
                wx.showToast({ title: errorMsg, icon: 'none' });
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

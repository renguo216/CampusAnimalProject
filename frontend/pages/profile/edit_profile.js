const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userInfo: {
      user_id: '',
      nickname: '',
      avatarUrl: '',
      phone_number: ''
    },
    tempAvatarUrl: ''
  },

  onLoad: function() {
    this.loadUserInfo();
  },

  onShow: function() {
    this.loadUserInfo();
  },

  loadUserInfo: function() {
    const userInfo = app.globalData.userInfo || {};
    this.setData({
      userInfo: {
        user_id: userInfo.user_id || '',
        nickname: userInfo.nickname || '',
        avatarUrl: userInfo.avatarUrl || '',
        phone_number: userInfo.phone_number || userInfo.phone || ''
      },
      tempAvatarUrl: userInfo.avatarUrl || ''
    });
  },

  chooseAvatar: function() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFilePath = res.tempFilePaths[0];
        
        wx.showLoading({ title: '上传头像中...' });
        
        wx.getFileSystemManager().readFile({
          filePath: tempFilePath,
          encoding: 'base64',
          success: (fileRes) => {
            const base64Image = 'data:image/jpeg;base64,' + fileRes.data;
            
            api.uploadAvatar(base64Image).then(uploadRes => {
              wx.hideLoading();
              
              if (uploadRes.success) {
                const newAvatarUrl = uploadRes.avatarUrl;
                
                this.setData({
                  tempAvatarUrl: newAvatarUrl
                });
                
                // 同时更新globalData
                app.globalData.userInfo.avatarUrl = newAvatarUrl;
                wx.setStorageSync('userInfo', app.globalData.userInfo);
                
                wx.showToast({
                  title: '头像上传成功',
                  icon: 'success'
                });
              } else {
                wx.showToast({
                  title: uploadRes.message || '上传失败',
                  icon: 'none'
                });
              }
            }).catch(err => {
              wx.hideLoading();
              console.error('上传头像失败:', err);
              wx.showToast({
                title: '上传失败，请重试',
                icon: 'none'
              });
            });
          },
          fail: (err) => {
            wx.hideLoading();
            console.error('读取图片失败:', err);
            wx.showToast({
              title: '读取图片失败',
              icon: 'none'
            });
          }
        });
      }
    });
  },

  onNicknameInput: function(e) {
    this.setData({
      'userInfo.nickname': e.detail.value
    });
  },

  onPhoneInput: function(e) {
    this.setData({
      'userInfo.phone_number': e.detail.value
    });
  },

  saveUserInfo: function() {
    const userInfo = this.data.userInfo;
    
    if (!userInfo.nickname || userInfo.nickname.trim() === '') {
      wx.showToast({
        title: '请输入昵称',
        icon: 'none'
      });
      return;
    }

    console.log('准备保存的用户信息:', userInfo);
    console.log('当前token:', app.globalData.token);

    wx.showLoading({ title: '保存中...' });

    const updateData = {
      nickname: userInfo.nickname,
      avatarURL: this.data.tempAvatarUrl || userInfo.avatarUrl,
      phone_number: userInfo.phone_number
    };

    console.log('发送到后端的数据:', updateData);

    api.updateUserInfo(updateData).then(res => {
      console.log('后端返回结果:', res);
      wx.hideLoading();
      if (res.success) {
        // 更新globalData和storage
        app.globalData.userInfo = {
          ...app.globalData.userInfo,
          ...updateData
        };
        wx.setStorageSync('userInfo', app.globalData.userInfo);
        
        console.log('更新后的用户信息:', app.globalData.userInfo);
        
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });
        
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        wx.showToast({
          title: res.message || '保存失败',
          icon: 'none'
        });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('保存用户信息失败:', err);
      console.error('错误详情:', JSON.stringify(err));
      
      let errorMsg = '网络错误，请重试';
      if (err && err.errMsg) {
        errorMsg = err.errMsg;
      } else if (typeof err === 'string') {
        errorMsg = err;
      }
      
      wx.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 3000
      });
    });
  }
});
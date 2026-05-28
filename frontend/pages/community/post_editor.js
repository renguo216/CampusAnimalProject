// pages/community/post_editor.js
const api = require('../../utils/api.js');

Page({
  data: {
    postTitle: '',
    postContent: ''
  },

  handleInput: function(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [field]: e.detail.value });
  },

  // 触发表单递交与敏感词前置审核用例流程 
  handleSubmitPost: async function() {
    if (!this.data.postContent.trim()) {
      wx.showToast({ title: '内容不能为空', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '正在提交审核...' });
    try {
      const payload = {
        title: this.data.postTitle,
        content: this.data.postContent
      };
      
      // 发送网络请求，后端逻辑层自动调用过滤构件 
      const response = await api.createPost(payload);
      wx.hideLoading();

      if (response.is_valid === false) {
        // 匹配安全拦截设计：若含违规信息，实时反馈给UI要求修改 
        wx.showModal({
          title: '发布失败',
          content: `内容包含敏感词 [${response.sensitive_word}]，请修改后重新提交。`,
          showCancel: false
        });
      } else {
        wx.showToast({ title: '发布成功', icon: 'success' });
        
        // 取得唯一的 PostId 并通过事件通道告知父页面刷新 
        const eventChannel = this.getOpenerEventChannel();
        eventChannel.emit('postSuccessRefresh');
        
        wx.navigateBack();
      }
    } catch(err) {
      wx.hideLoading();
      wx.showToast({ title: '服务器开小差了，请稍后再试', icon: 'none' });
    }
  }
});
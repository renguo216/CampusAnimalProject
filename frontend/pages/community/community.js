const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userAvatar: '',
    userNickname: '',
    searchKeyword: '',
    posts: [],
    allPosts: [],
    loading: false,
    hasMore: true,
    pageNum: 1,
    
    showPostModal: false,
    postContent: '',
    postImages: [],
    selectedTag: '',
    
    showCommentModal: false,
    currentPostId: null,
    currentComments: [],
    commentText: ''
  },

  onLoad: function() {
    this.loadUserInfo();
    this.loadPosts();
  },

  onShow: function() {
    this.loadUserInfo();
  },

  loadUserInfo: function() {
    const userInfo = app.globalData.userInfo || {};
    this.setData({
      userAvatar: userInfo.avatarUrl || userInfo.avatarURL || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=young%20person%20avatar%20friendly&image_size=square',
      userNickname: userInfo.nickname || '用户'
    });
  },

  transformPost: function(post) {
    let images = [];
    if (post.image_urls) {
      try {
        images = typeof post.image_urls === 'string' ? JSON.parse(post.image_urls) : post.image_urls;
      } catch (e) {
        images = [];
      }
    }
    
    const now = new Date();
    let createTime = '未知';
    if (post.created_at) {
      const postDate = new Date(post.created_at.replace(' ', 'T'));
      const diff = now.getTime() - postDate.getTime();
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);
      
      if (minutes < 1) createTime = '刚刚';
      else if (minutes < 60) createTime = `${minutes}分钟前`;
      else if (hours < 24) createTime = `${hours}小时前`;
      else if (days < 30) createTime = `${days}天前`;
      else createTime = postDate.toLocaleDateString();
    }
    
    return {
      id: post.post_id || post.id || Date.now(),
      author: post.author || post.nickname || '用户',
      avatar: post.avatar || post.avatar_url || post.avatarURL || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=friendly%20avatar&image_size=square',
      content: post.content || '',
      images: images,
      likes: post.like_count || post.likes || 0,
      comments: post.comment_count || post.comments || 0,
      isLiked: post.is_liked || post.isLiked || false,
      createTime: createTime
    };
  },

  loadPosts: function(isRefresh = false) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    const page = isRefresh ? 1 : this.data.page;
    
    api.getPosts(page).then(res => {
      let newPosts = [];
      if (res.success && res.data && res.data.posts) {
        newPosts = res.data.posts.map(p => this.transformPost(p));
      }
      
      let allPosts = isRefresh ? newPosts : [...this.data.allPosts, ...newPosts];
      
      const filteredPosts = this.data.searchKeyword 
        ? allPosts.filter(p => p.content.includes(this.data.searchKeyword) || p.author.includes(this.data.searchKeyword))
        : allPosts;
      
      wx.setStorageSync('communityPosts', allPosts);
      
      this.setData({
        allPosts: allPosts,
        posts: filteredPosts,
        loading: false,
        page: isRefresh ? 2 : this.data.page + 1,
        hasMore: res.data && res.data.has_more !== undefined ? res.data.has_more : (newPosts.length >= 10)
      });
    }).catch(err => {
      console.error('获取帖子失败:', err);
      this.setData({ 
        loading: false,
        hasMore: false 
      });
    });
  },

  onSearchInput: function(e) {
    const keyword = e.detail.value;
    this.setData({ searchKeyword: keyword });
    
    if (keyword.trim()) {
      this.performSearch(keyword);
    } else {
      this.setData({ posts: this.data.allPosts });
    }
  },

  performSearch: function(keyword) {
    if (!keyword.trim()) {
      this.setData({ posts: this.data.allPosts });
      return;
    }
    
    const filteredPosts = this.data.allPosts.filter(post => 
      post.content.includes(keyword) || post.author.includes(keyword)
    );
    
    this.setData({ posts: filteredPosts });
  },

  doSearch: function() {
    if (!this.data.searchKeyword.trim()) {
      wx.showToast({ title: '请输入搜索关键词', icon: 'none' });
      return;
    }
    this.performSearch(this.data.searchKeyword);
  },

  focusSearch: function() {},

  loadMore: function() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ pageNum: this.data.pageNum + 1 });
      this.loadPosts();
    }
  },

  viewPostDetail: function(e) {
    const postId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/post_detail/post_detail?id=' + postId
    });
  },

  showPostMenu: function(e) {
    const postId = e.currentTarget.dataset.id;
    const postAuthor = e.currentTarget.dataset.author;
    const currentUser = this.data.userNickname;
    
    if (postAuthor === currentUser) {
      wx.showActionSheet({
        itemList: ['删除', '举报'],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.deletePost(postId);
          } else if (res.tapIndex === 1) {
            wx.showToast({ title: '已举报', icon: 'none' });
          }
        }
      });
    } else {
      wx.showActionSheet({
        itemList: ['举报', '屏蔽'],
        success: (res) => {
          if (res.tapIndex === 0) {
            wx.showToast({ title: '已举报', icon: 'none' });
          } else {
            wx.showToast({ title: '已屏蔽', icon: 'none' });
          }
        }
      });
    }
  },

  deletePost: function(postId) {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条帖子吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          
          api.deletePost(postId).then(result => {
            wx.hideLoading();
            
            const newAllPosts = this.data.allPosts.filter(post => post.id !== postId);
            const newPosts = this.data.posts.filter(post => post.id !== postId);
            
            this.setData({
              allPosts: newAllPosts,
              posts: newPosts
            });
            
            let localPosts = wx.getStorageSync('communityPosts') || [];
            localPosts = localPosts.filter(post => post.id !== postId);
            wx.setStorageSync('communityPosts', localPosts);
            
            wx.showToast({ title: '删除成功', icon: 'success' });
          }).catch(err => {
            wx.hideLoading();
            console.error('删除失败:', err);
            
            const newAllPosts = this.data.allPosts.filter(post => post.id !== postId);
            const newPosts = this.data.posts.filter(post => post.id !== postId);
            
            this.setData({
              allPosts: newAllPosts,
              posts: newPosts
            });
            
            let localPosts = wx.getStorageSync('communityPosts') || [];
            localPosts = localPosts.filter(post => post.id !== postId);
            wx.setStorageSync('communityPosts', localPosts);
            
            wx.showToast({ title: '删除成功', icon: 'success' });
          });
        }
      }
    });
  },

  likePost: function(e) {
    const postId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/post_detail/post_detail?id=' + postId
    });
  },

  commentPost: function(e) {
    const postId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/post_detail/post_detail?id=' + postId
    });
  },

  sharePost: function(e) {
    const postId = e.currentTarget.dataset.id;
    wx.showShareMenu({
      withShareTicket: true
    });
    wx.showToast({ title: '请点击右上角分享', icon: 'none' });
  },

  previewImage: function(e) {
    const images = e.currentTarget.dataset.images;
    const index = e.currentTarget.dataset.index;
    wx.previewImage({
      urls: images,
      current: images[index]
    });
  },

  createPost: function() {
    this.setData({
      showPostModal: true,
      postContent: '',
      postImages: [],
      selectedTag: ''
    });
  },

  closePostModal: function() {
    this.setData({ showPostModal: false });
  },

  onPostContentInput: function(e) {
    this.setData({ postContent: e.detail.value });
  },

  chooseImages: function() {
    wx.chooseImage({
      count: 9 - this.data.postImages.length,
      success: (res) => {
        this.setData({
          postImages: [...this.data.postImages, ...res.tempFilePaths]
        });
      }
    });
  },

  deletePostImage: function(e) {
    const index = e.currentTarget.dataset.index;
    const postImages = this.data.postImages.filter((_, i) => i !== index);
    this.setData({ postImages });
  },

  selectTag: function(e) {
    const tag = e.currentTarget.dataset.tag;
    this.setData({ selectedTag: tag });
  },

  submitPost: function() {
    if (!this.data.postContent.trim()) {
      wx.showToast({ title: '请输入内容', icon: 'none' });
      return;
    }

    const tagLabels = {
      'rescue': '#救助故事',
      'find': '#寻宠/寻主',
      'adoption': '#领养信息',
      'experience': '#经验分享'
    };

    let finalContent = this.data.postContent;
    if (this.data.selectedTag && tagLabels[this.data.selectedTag]) {
      finalContent = finalContent + ' ' + tagLabels[this.data.selectedTag];
    }

    wx.showLoading({ title: '发布中...' });
    
    api.createPost({
      content: finalContent,
      image_urls: JSON.stringify(this.data.postImages)
    }).then(res => {
      wx.hideLoading();
      
      if (res.success && res.data) {
        const newPost = this.transformPost(res.data);
        let localPosts = wx.getStorageSync('communityPosts') || [];
        localPosts.unshift(newPost);
        wx.setStorageSync('communityPosts', localPosts);
        
        const newAllPosts = [newPost, ...this.data.allPosts];
        const newPosts = this.data.searchKeyword 
          ? newAllPosts.filter(p => p.content.includes(this.data.searchKeyword) || p.author.includes(this.data.searchKeyword))
          : newAllPosts;
        
        this.setData({
          allPosts: newAllPosts,
          posts: newPosts,
          showPostModal: false,
          postContent: '',
          postImages: [],
          selectedTag: ''
        });
        
        wx.showToast({ title: '发布成功', icon: 'success' });
      } else {
        wx.showToast({ title: '发布失败', icon: 'none' });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('发布帖子失败:', err);
      wx.showToast({ title: '发布失败', icon: 'none' });
    });
  },

  closeCommentModal: function() {
    this.setData({ showCommentModal: false, commentText: '' });
  },

  onCommentInput: function(e) {
    this.setData({ commentText: e.detail.value });
  },

  submitComment: function() {
    if (!this.data.commentText.trim()) {
      wx.showToast({ title: '请输入评论内容', icon: 'none' });
      return;
    }

    api.commentPost(this.data.currentPostId, this.data.commentText).then(res => {
      if (res.success) {
        const userInfo = app.globalData.userInfo || {};
        const newComment = {
          id: Date.now(),
          author: userInfo.nickname || '用户',
          avatar: userInfo.avatarUrl || userInfo.avatarURL || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=default%20avatar&image_size=square',
          content: this.data.commentText,
          time: '刚刚'
        };

        this.setData({
          currentComments: [...this.data.currentComments, newComment],
          commentText: ''
        });

        const posts = this.data.posts.map(post => {
          if (post.id === this.data.currentPostId) {
            return { ...post, comments: post.comments + 1 };
          }
          return post;
        });
        
        let allPosts = this.data.allPosts.map(post => {
          if (post.id === this.data.currentPostId) {
            return { ...post, comments: post.comments + 1 };
          }
          return post;
        });
        
        this.setData({ posts, allPosts });
        
        let localPosts = wx.getStorageSync('communityPosts') || [];
        localPosts = localPosts.map(post => {
          if (post.id === this.data.currentPostId) {
            return { ...post, comments: post.comments + 1 };
          }
          return post;
        });
        wx.setStorageSync('communityPosts', localPosts);
        
        wx.showToast({ title: '评论成功', icon: 'success' });
      }
    }).catch(err => {
      console.error('评论失败:', err);
      const userInfo = app.globalData.userInfo || {};
      const newComment = {
        id: Date.now(),
        author: userInfo.nickname || '用户',
        avatar: userInfo.avatarUrl || userInfo.avatarURL || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=default%20avatar&image_size=square',
        content: this.data.commentText,
        time: '刚刚'
      };

      this.setData({
        currentComments: [...this.data.currentComments, newComment],
        commentText: ''
      });

      const posts = this.data.posts.map(post => {
        if (post.id === this.data.currentPostId) {
          return { ...post, comments: post.comments + 1 };
        }
        return post;
      });
      
      let allPosts = this.data.allPosts.map(post => {
        if (post.id === this.data.currentPostId) {
          return { ...post, comments: post.comments + 1 };
        }
        return post;
      });
      
      this.setData({ posts, allPosts });
      
      let localPosts = wx.getStorageSync('communityPosts') || [];
      localPosts = localPosts.map(post => {
        if (post.id === this.data.currentPostId) {
          return { ...post, comments: post.comments + 1 };
        }
        return post;
      });
      wx.setStorageSync('communityPosts', localPosts);
      
      wx.showToast({ title: '评论成功', icon: 'success' });
    });
  },

  goHome: function() {
    wx.reLaunch({ url: '/pages/home/home' });
  },

  goAdoption: function() {
    wx.reLaunch({ url: '/pages/adoption/adoption' });
  },

  goProfile: function() {
    wx.reLaunch({ url: '/pages/profile/profile' });
  }
});

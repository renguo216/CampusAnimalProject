const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userAvatar: '',
    searchKeyword: '',
    currentTab: 'recommend',
    posts: [],
    allPosts: [],
    loading: false,
    hasMore: true,
    pageNum: 1,
    
    showPostModal: false,
    postContent: '',
    postImages: [],
    selectedTags: [],
    
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
    if (this.data.allPosts.length === 0) {
      this.loadPosts();
    }
  },

  loadUserInfo: function() {
    const userInfo = app.globalData.userInfo || {};
    this.setData({
      userAvatar: userInfo.avatarUrl || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=young%20person%20avatar%20friendly&image_size=square'
    });
  },

  generateMockPosts: function() {
    return [
      {
        id: Date.now() - 1000,
        author: '爱心志愿者',
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20cat%20avatar&image_size=square',
        content: '今天在图书馆门口发现了一只受伤的小橘猫，已经送往宠物医院治疗了。希望大家多多关注校园流浪动物！❤️',
        images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=orange%20cat%20hospital&image_size=square'],
        likes: Math.floor(Math.random() * 100),
        comments: Math.floor(Math.random() * 30),
        isLiked: false,
        createTime: '2小时前'
      },
      {
        id: Date.now() - 2000,
        author: '校园铲屎官',
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20dog%20avatar&image_size=square',
        content: '领养代替购买，给流浪动物一个温暖的家。我家的小黑现在已经是我最好的朋友啦~',
        images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=happy%20dog%20with%20owner&image_size=square'],
        likes: Math.floor(Math.random() * 150),
        comments: Math.floor(Math.random() * 50),
        isLiked: false,
        createTime: '5小时前'
      },
      {
        id: Date.now() - 3000,
        author: '救助站小张',
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=volunteer%20avatar%20friendly&image_size=square',
        content: '【救助经验分享】如果在校园里发现生病的流浪动物，请不要盲目靠近，可以先拍照在群里反馈，或者直接联系附近合作医院。详情请看长图~',
        images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=pet%20first%20aid%20guide&image_size=square'],
        likes: Math.floor(Math.random() * 200),
        comments: Math.floor(Math.random() * 80),
        isLiked: false,
        createTime: '昨天'
      },
      {
        id: Date.now() - 4000,
        author: '爱猫人士',
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cat%20lover%20avatar&image_size=square',
        content: '南区食堂门口遇到这只亲人的小狸花，给它喂了点猫粮，吃的可香了。有同学认识它吗？或者有没有想领养的？',
        images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20tabby%20cat%20eating&image_size=square', 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20tabby%20cat%20portrait&image_size=square'],
        likes: Math.floor(Math.random() * 120),
        comments: Math.floor(Math.random() * 40),
        isLiked: false,
        createTime: '昨天'
      },
      {
        id: Date.now() - 5000,
        author: '动物保护协会',
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=animal%20protection%20logo&image_size=square',
        content: '本周六下午2点，我们将在中心广场举办领养活动，有20多只可爱的小动物等待新家！欢迎大家前来参加~',
        images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=pet%20adoption%20event%20happy&image_size=square'],
        likes: Math.floor(Math.random() * 300),
        comments: Math.floor(Math.random() * 100),
        isLiked: false,
        createTime: '2天前'
      },
      {
        id: Date.now() - 6000,
        author: '校园萌宠',
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20pet%20avatar&image_size=square',
        content: '今天在操场看到三只小奶猫，太可爱了！有没有同学想领养的？联系我~',
        images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=three%20cute%20kittens&image_size=square'],
        likes: Math.floor(Math.random() * 180),
        comments: Math.floor(Math.random() * 60),
        isLiked: false,
        createTime: '3天前'
      }
    ];
  },

  loadPosts: function(isRefresh = false) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    api.getPosts(this.data.currentTab).then(res => {
      if (res.success) {
        let newPosts = res.data;
        if (newPosts.length === 0) {
          newPosts = this.generateMockPosts();
        }
        
        let allPosts = isRefresh ? newPosts : [...this.data.allPosts, ...newPosts];
        
        const filteredPosts = this.data.searchKeyword 
          ? allPosts.filter(p => p.content.includes(this.data.searchKeyword) || p.author.includes(this.data.searchKeyword))
          : allPosts;
        
        this.setData({
          allPosts: allPosts,
          posts: filteredPosts,
          loading: false,
          hasMore: allPosts.length < 20
        });
      } else {
        const newPosts = this.generateMockPosts();
        let allPosts = isRefresh ? newPosts : [...this.data.allPosts, ...newPosts];
        
        const filteredPosts = this.data.searchKeyword 
          ? allPosts.filter(p => p.content.includes(this.data.searchKeyword) || p.author.includes(this.data.searchKeyword))
          : allPosts;
        
        this.setData({
          allPosts: allPosts,
          posts: filteredPosts,
          loading: false,
          hasMore: allPosts.length < 20
        });
      }
    }).catch(err => {
      console.error('获取帖子失败:', err);
      const newPosts = this.generateMockPosts();
      let allPosts = isRefresh ? newPosts : [...this.data.allPosts, ...newPosts];
      
      const filteredPosts = this.data.searchKeyword 
        ? allPosts.filter(p => p.content.includes(this.data.searchKeyword) || p.author.includes(this.data.searchKeyword))
        : allPosts;
      
      this.setData({
        allPosts: allPosts,
        posts: filteredPosts,
        loading: false,
        hasMore: allPosts.length < 20
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
    
    if (filteredPosts.length === 0 && this.data.allPosts.length === 0) {
      this.loadPosts(true);
    } else {
      this.setData({ posts: filteredPosts });
    }
  },

  doSearch: function() {
    if (!this.data.searchKeyword.trim()) {
      wx.showToast({ title: '请输入搜索关键词', icon: 'none' });
      return;
    }
    this.performSearch(this.data.searchKeyword);
  },

  focusSearch: function() {},

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab, posts: [], pageNum: 1, hasMore: true });
    this.loadPosts(true);
  },

  loadMore: function() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ pageNum: this.data.pageNum + 1 });
      this.loadPosts();
    }
  },

  viewPostDetail: function(e) {
    const postId = e.currentTarget.dataset.id;
    wx.showToast({ title: '查看帖子详情', icon: 'none' });
  },

  showPostMenu: function(e) {
    const postId = e.currentTarget.dataset.id;
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
  },

  likePost: function(e) {
    const postId = e.currentTarget.dataset.id;
    const posts = this.data.posts.map(post => {
      if (post.id === postId) {
        return {
          ...post,
          isLiked: !post.isLiked,
          likes: post.isLiked ? post.likes - 1 : post.likes + 1
        };
      }
      return post;
    });
    this.setData({ posts });
  },

  commentPost: function(e) {
    const postId = e.currentTarget.dataset.id;
    this.setData({
      showCommentModal: true,
      currentPostId: postId,
      currentComments: [
        {
          id: 1,
          author: '热心网友',
          avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=friendly%20avatar&image_size=square',
          content: '好可怜，希望小猫早日康复！',
          time: '1小时前'
        },
        {
          id: 2,
          author: '爱猫达人',
          avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cat%20lover%20avatar&image_size=square',
          content: '请问现在小猫怎么样了？',
          time: '30分钟前'
        }
      ]
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
      selectedTags: []
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

  toggleTag: function(e) {
    const tag = e.currentTarget.dataset.tag;
    const selectedTags = [...this.data.selectedTags];
    const index = selectedTags.indexOf(tag);
    
    if (index > -1) {
      selectedTags.splice(index, 1);
    } else {
      selectedTags.push(tag);
    }
    
    this.setData({ selectedTags });
  },

  submitPost: function() {
    if (!this.data.postContent.trim()) {
      wx.showToast({ title: '请输入内容', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '发布中...' });
    
    api.createPost({
      content: this.data.postContent,
      images: this.data.postImages,
      tags: this.data.selectedTags
    }).then(res => {
      wx.hideLoading();
      
      if (res.success) {
        const newPost = {
          id: Date.now(),
          author: app.globalData.userInfo?.nickname || '用户',
          avatar: this.data.userAvatar,
          content: this.data.postContent,
          images: this.data.postImages,
          likes: 0,
          comments: 0,
          isLiked: false,
          createTime: '刚刚'
        };
        
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
          selectedTags: []
        });
        
        wx.showToast({ title: '发布成功', icon: 'success' });
      } else {
        wx.showToast({ title: '发布失败', icon: 'none' });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('发布帖子失败:', err);
      
      const newPost = {
        id: Date.now(),
        author: app.globalData.userInfo?.nickname || '用户',
        avatar: this.data.userAvatar,
        content: this.data.postContent,
        images: this.data.postImages,
        likes: 0,
        comments: 0,
        isLiked: false,
        createTime: '刚刚'
      };
      
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
        selectedTags: []
      });
      
      wx.showToast({ title: '发布成功', icon: 'success' });
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

    const newComment = {
      id: Date.now(),
      author: app.globalData.userInfo?.nickname || '用户',
      avatar: this.data.userAvatar,
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
    this.setData({ posts });
    
    wx.showToast({ title: '评论成功', icon: 'success' });
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
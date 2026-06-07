const api = require('../../utils/api.js');
const app = getApp();

const STICKY_POST_ID = 'sticky_post_how_to_save_money';
const stickyPost = {
  id: STICKY_POST_ID,
  isSticky: true,
  author: '校园宠物之家',
  title: '如何科学省钱养宠？新手必看流程',
  content: '很多同学第一次养宠都会担心开销问题，其实只要做好规划，花得少也能养得好。下面给大家整理一份新手省钱养宠流程👇\n\n一、领养代替购买\n校内流浪猫狗大多已绝育、驱虫、疫苗，到校医院或救助站免费领养，体检费一般在 50 元以内。\n\n二、必备物资一次买齐\n猫粮 / 狗粮、饭盆水盆、猫砂盆、牵引绳、基础玩具，总共 200 元左右可以搞定。\n\n三、饮食与驱虫\n主粮选正规平价品牌，月均 80–120 元；驱虫每月一次，自购驱虫药 10 元/次。\n\n四、医疗省钱小技巧\n小毛病先到校医院，挂号费便宜；需要疫苗绝育可关注平台定期义诊活动，名单会发到领养交流群。\n\n五、积分与任务兑换\n完成平台日常签到、分享领养经验，就能攒积分，兑换主粮、驱虫药、玩具等物资。\n\n科学养宠不是靠花得多，而是靠用心。遇到问题随时在社区提问，志愿者和资深宠主都会来帮忙～',
  createTime: '置顶 · 1 周前'
};

Page({
  data: {
    post: {},
    comments: [],
    commentText: '',
    commentFocused: false
  },

  onLoad: function(options) {
    const postId = options.id;
    
    if (postId === STICKY_POST_ID) {
      const post = {
        id: stickyPost.id,
        author: stickyPost.author,
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=friendly%20avatar%20cat%20face&image_size=square',
        content: stickyPost.content,
        images: [],
        likes: 0,
        comments: 0,
        isLiked: false,
        createTime: stickyPost.createTime,
        title: stickyPost.title
      };
      this.setData({ post: post, comments: [] });
      return;
    }
    
    this.loadPostDetail(postId);
  },

  loadPostDetail: function(postId) {
    wx.showLoading({ title: '加载中...' });
    
    api.getPostDetail(postId).then(res => {
      wx.hideLoading();
      
      if (res.success && res.data) {
        let images = [];
        if (res.data.image_urls) {
          try {
            images = typeof res.data.image_urls === 'string' ? JSON.parse(res.data.image_urls) : res.data.image_urls;
          } catch (e) {
            images = [];
          }
        }
        
        const now = new Date();
        let createTime = '未知';
        if (res.data.created_at) {
          const postDate = new Date(res.data.created_at.replace(' ', 'T'));
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
        
        const post = {
          id: res.data.post_id || res.data.id || postId,
          author: res.data.author || res.data.nickname || '用户',
          avatar: res.data.avatar || res.data.avatar_url || res.data.avatarURL || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=friendly%20avatar&image_size=square',
          content: res.data.content || '',
          images: images,
          likes: res.data.like_count || res.data.likes || 0,
          comments: res.data.comment_count || res.data.comments || 0,
          isLiked: res.data.is_liked_by_current_user || res.data.is_liked || res.data.isLiked || false,
          createTime: createTime
        };
        
        if (res.data.comments) {
          const formattedComments = res.data.comments.map(c => {
            let time = '未知';
            if (c.created_at) {
              const now = new Date();
              const commentDate = new Date(c.created_at.replace(' ', 'T'));
              const diff = now.getTime() - commentDate.getTime();
              const minutes = Math.floor(diff / 60000);
              const hours = Math.floor(diff / 3600000);
              const days = Math.floor(diff / 86400000);
              
              if (minutes < 1) time = '刚刚';
              else if (minutes < 60) time = `${minutes}分钟前`;
              else if (hours < 24) time = `${hours}小时前`;
              else if (days < 30) time = `${days}天前`;
              else time = commentDate.toLocaleDateString();
            }
            
            return {
              id: c.comment_id || c.id,
              author: c.nickname || c.author || '用户',
              avatar: c.avatar_url || c.avatar || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=friendly%20avatar&image_size=square',
              content: c.content,
              time: time
            };
          });
          this.setData({ comments: formattedComments });
        } else {
          this.setData({ comments: [] });
        }
        
        this.setData({ post: post });
      } else {
        const mockPost = {
          id: postId,
          author: '用户',
          avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=default%20avatar&image_size=square',
          content: '帖子内容不存在或已被删除',
          images: [],
          likes: 0,
          comments: 0,
          isLiked: false,
          createTime: '未知'
        };
        this.setData({ 
          post: mockPost,
          comments: []
        });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('获取帖子详情失败:', err);
      const mockPost = {
        id: postId,
        author: '用户',
        avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=default%20avatar&image_size=square',
        content: '帖子内容不存在或已被删除',
        images: [],
        likes: 0,
        comments: 0,
        isLiked: false,
        createTime: '未知'
      };
      this.setData({ 
        post: mockPost,
        comments: []
      });
    });
  },

  toggleLike: function() {
    const post = this.data.post;
    let newIsLiked = !post.isLiked;
    let newLikes = newIsLiked ? post.likes + 1 : post.likes - 1;
    
    api.likePost(post.id).then(res => {
      if (res.success) {
        const updatedPost = {
          ...post,
          isLiked: res.data.is_liked !== undefined ? res.data.is_liked : newIsLiked,
          likes: res.data.is_liked !== undefined ? (res.data.is_liked ? post.likes + 1 : post.likes - 1) : newLikes
        };
        this.setData({ post: updatedPost });
      } else {
        wx.showToast({ title: res.message || '操作失败', icon: 'none' });
      }
    }).catch(err => {
      console.error('点赞失败:', err);
      wx.showToast({ title: '操作失败', icon: 'none' });
    });
  },

  focusComment: function() {
    this.setData({ commentFocused: true });
  },

  onCommentInput: function(e) {
    this.setData({ commentText: e.detail.value });
  },

  submitComment: function() {
    const commentText = this.data.commentText.trim();
    if (!commentText) {
      wx.showToast({ title: '请输入评论内容', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '发布中...' });

    api.commentPost(this.data.post.id, commentText).then(res => {
      wx.hideLoading();
      
      if (res.success) {
        const userInfo = app.globalData.userInfo || {};
        const newComment = {
          id: res.data.comment_id || Date.now(),
          author: userInfo.nickname || '用户',
          avatar: userInfo.avatarUrl || userInfo.avatarURL || 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=default%20avatar&image_size=square',
          content: commentText,
          time: '刚刚'
        };

        let comments = [...this.data.comments, newComment];
        let post = { ...this.data.post, comments: comments.length };

        this.setData({ 
          comments: comments,
          post: post,
          commentText: '',
          commentFocused: false
        });

        wx.showToast({ title: '评论成功', icon: 'success' });
      } else {
        wx.showToast({ title: res.message || '评论失败', icon: 'none' });
      }
    }).catch(err => {
      wx.hideLoading();
      console.error('评论失败:', err);
      wx.showToast({ title: '评论失败', icon: 'none' });
    });
  },

  previewImage: function(e) {
    const images = e.currentTarget.dataset.images;
    const index = e.currentTarget.dataset.index;
    wx.previewImage({
      urls: images,
      current: images[index]
    });
  },

  goBack: function() {
    wx.navigateBack();
  }
});

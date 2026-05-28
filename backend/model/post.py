class Post:
    def __init__(self, post_id, user_id, content=None, image_urls=None,
                 like_count=0, comment_count=0, share_count=0, status=1,
                 created_at=None):
        self.post_id = post_id          # 帖子编号
        self.user_id = user_id          # 发帖人ID
        self.content = content          # 帖子内容
        self.image_urls = image_urls    # 图片链接（JSON数组）
        self.like_count = like_count    # 点赞数
        self.comment_count = comment_count  # 评论数
        self.share_count = share_count  # 转发/分享数
        self.status = status            # 审核状态：0-待审核，1-已通过，2-驳回
        self.created_at = created_at    # 创建时间
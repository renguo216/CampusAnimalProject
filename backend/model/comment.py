class Comment:
    def __init__(self, comment_id, post_id, user_id, content, parent_comment_id=None, like_count=0, created_at=None):
        self.comment_id = comment_id              # 评论ID
        self.post_id = post_id                    # 关联帖子ID
        self.user_id = user_id                    # 评论人ID
        self.content = content                    # 评论内容
        self.parent_comment_id = parent_comment_id  # 父评论ID（楼中楼回复）
        self.like_count = like_count              # 点赞数
        self.created_at = created_at              # 评论时间

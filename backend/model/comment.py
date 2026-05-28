class Comment:
    def __init__(self, comment_id, post_id, user_id, content, created_at=None):
        self.comment_id = comment_id    # 评论ID
        self.post_id = post_id          # 关联帖子ID
        self.user_id = user_id          # 评论人ID
        self.content = content          # 评论内容
        self.created_at = created_at    # 评论时间
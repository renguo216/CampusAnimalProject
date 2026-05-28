class Like:
    def __init__(self, like_id, user_id, post_id=None, comment_id=None, created_at=None):
        self.like_id = like_id          # 点赞记录ID
        self.user_id = user_id          # 点赞人ID
        self.post_id = post_id          # 帖子ID（可空）
        self.comment_id = comment_id    # 评论ID（可空）
        self.created_at = created_at    # 点赞时间
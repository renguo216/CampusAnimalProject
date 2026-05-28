class Follow:
    def __init__(self, follow_id, from_user_id, to_user_id, created_at=None):
        self.follow_id = follow_id          # 关注记录ID
        self.from_user_id = from_user_id    # 关注者ID
        self.to_user_id = to_user_id        # 被关注者ID
        self.created_at = created_at        # 关注时间
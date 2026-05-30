class Like:
    def __init__(self, like_id, target_type, target_id, user_id, target_owner_id=None, is_deleted=0, created_at=None):
        self.like_id = like_id              # 点赞记录ID
        self.target_type = target_type      # 点赞目标类型：post-帖子，comment-评论
        self.target_id = target_id          # 点赞目标ID（对应帖子或评论的ID）
        self.user_id = user_id              # 点赞人ID
        self.target_owner_id = target_owner_id  # 目标作者ID（冗余存储，用于性能优化）
        self.is_deleted = is_deleted        # 逻辑删除标记：0-未删除，1-已删除
        self.created_at = created_at        # 点赞时间
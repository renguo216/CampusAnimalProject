class Exchange:
    def __init__(self, exchange_id, user_id, product_id, points_used,
                 status=0, created_at=None, updated_at=None,
                 reviewed_by=None, reviewed_at=None, review_comment=None,
                 contact_info=None):
        self.exchange_id = exchange_id      # 兑换记录ID
        self.user_id = user_id              # 用户ID
        self.product_id = product_id        # 兑换商品ID
        self.points_used = points_used      # 消耗积分数
        self.status = status                # 状态：0-待发货，1-已完成，2-已取消
        self.created_at = created_at        # 兑换时间
        self.updated_at = updated_at        # 最后更新时间
        self.reviewed_by = reviewed_by      # 审核人ID
        self.reviewed_at = reviewed_at      # 审核时间
        self.review_comment = review_comment  # 审核意见/拒绝原因
        self.contact_info = contact_info    # 用户联系方式
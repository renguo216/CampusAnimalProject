class Exchange:
    def __init__(self, exchange_id, user_id, product_id, points_used,
                 status=0, created_at=None):
        self.exchange_id = exchange_id    # 兑换记录ID
        self.user_id = user_id            # 用户ID
        self.product_id = product_id      # 兑换商品ID
        self.points_used = points_used    # 消耗积分数
        self.status = status              # 状态：0-待发货，1-已完成，2-已取消
        self.created_at = created_at      # 兑换时间
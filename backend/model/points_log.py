class PointsLog:
    def __init__(self, log_id, user_id, delta, before_points, after_points,
                 reason=None, created_at=None):
        self.log_id = log_id                # 日志ID
        self.user_id = user_id              # 用户ID
        self.delta = delta                  # 积分变动值
        self.before_points = before_points  # 变动前积分
        self.after_points = after_points    # 变动后积分
        self.reason = reason                # 变动原因
        self.created_at = created_at        # 变动时间
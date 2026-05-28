class User:
    def __init__(self, user_id, nickname, avatarURL=None, role=1, points=0,
                 volunteer_id=None, admin_id=None, level=1, phone_number=None,
                 like_count=0, follower_count=0, following_count=0,
                 is_active=1, created_at=None):
        self.user_id = user_id          # 用户唯一ID (微信OpenID)
        self.nickname = nickname        # 用户昵称
        self.avatarURL = avatarURL      # 头像URL
        self.role = role                # 角色：1-普通用户，2-志愿者，3-管理员
        self.points = points            # 积分
        self.volunteer_id = volunteer_id  # 志愿者编号（仅志愿者）
        self.admin_id = admin_id        # 管理员工号（仅管理员）
        self.level = level              # 等级（仅志愿者有）
        self.phone_number = phone_number  # 手机号（预留）
        self.like_count = like_count    # 获赞总数
        self.follower_count = follower_count  # 粉丝数
        self.following_count = following_count  # 关注数
        self.is_active = is_active      # 账号是否激活：0-封禁，1-正常
        self.created_at = created_at    # 注册时间
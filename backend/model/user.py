class User:
    def __init__(self, user_id, nickname, role, avatarURL=None, points=0, identityNo=None, level=None):
        self.user_id = user_id          # 微信OpenID
        self.nickname = nickname        # 昵称
        self.avatarURL = avatarURL      # 头像链接
        self.role = role                # 1-普通用户，2-志愿者，3-管理员
        self.points = points            # 志愿者积分
        self.identityNo = identityNo    # 学号/工号
        self.level = level              # 管理等级
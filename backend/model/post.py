class Post:
    def __init__(self, post_id, content, like_count=0):
        self.post_id = post_id          # 帖子编号
        self.content = content          # 帖子内容
        self.like_count = like_count    # 点赞数
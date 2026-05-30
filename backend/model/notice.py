class Notice:
    def __init__(self, notice_id, title, content=None, is_top=0, created_at=None):
        self.notice_id = notice_id      # 公告编号
        self.title = title              # 公告标题
        self.content = content          # 公告内容
        self.is_top = is_top            # 是否置顶: 0-普通, 1-置顶
        self.created_at = created_at    # 发布时间
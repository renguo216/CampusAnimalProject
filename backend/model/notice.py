class Notice:
    def __init__(self, notice_id, title, content=None, created_at=None):
        self.notice_id = notice_id      # 公告编号
        self.title = title              # 公告标题
        self.content = content          # 公告内容
        self.created_at = created_at    # 发布时间
class DonationProject:
    def __init__(self, project_id, title, description=None,
                 target_amount=0.0, current_amount=0.0,
                 participant_count=0, status=1, created_at=None):
        self.project_id = project_id        # 项目ID
        self.title = title                  # 项目标题
        self.description = description      # 项目描述
        self.target_amount = target_amount  # 目标金额
        self.current_amount = current_amount  # 已筹金额
        self.participant_count = participant_count  # 参与人数
        self.status = status                # 状态：0-已结束，1-进行中
        self.created_at = created_at        # 创建时间
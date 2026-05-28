class Donation:
    def __init__(self, donation_id, user_id, project_id, amount, created_at=None):
        self.donation_id = donation_id  # 捐赠单号
        self.user_id = user_id          # 捐款人ID
        self.project_id = project_id    # 募捐项目ID
        self.amount = amount            # 捐赠金额
        self.created_at = created_at    # 捐款时间
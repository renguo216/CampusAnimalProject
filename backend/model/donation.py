class Donation:
    def __init__(self, donation_id, user_id, project_id, amount, 
                 status=0, reviewed_by=None, reviewed_at=None, review_comment=None, 
                 created_at=None):
        self.donation_id = donation_id      # 捐赠单号
        self.user_id = user_id              # 捐款人ID
        self.project_id = project_id        # 募捐项目ID
        self.amount = amount                # 捐赠金额
        self.status = status                # 捐赠状态：0-待确认，1-已到账，2-已驳回，3-已取消
        self.reviewed_by = reviewed_by      # 审核人ID
        self.reviewed_at = reviewed_at      # 审核时间
        self.review_comment = review_comment  # 审核意见/驳回原因
        self.created_at = created_at        # 捐款时间
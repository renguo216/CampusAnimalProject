class VolunteerApplication:
    def __init__(self, application_id, user_id, status=0,
                 apply_content=None, review_comment=None, created_at=None):
        self.application_id = application_id  # 申请ID
        self.user_id = user_id                # 申请人ID
        self.status = status                  # 状态：0-待审核，1-通过，2-驳回
        self.apply_content = apply_content    # 申请理由
        self.review_comment = review_comment  # 审核意见
        self.created_at = created_at          # 申请时间
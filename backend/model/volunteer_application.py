class VolunteerApplication:
    def __init__(self, application_id, user_id, status=0,
                 apply_content=None, review_comment=None,
                 reviewed_by=None, reviewed_at=None, updated_at=None,
                 created_at=None):
        self.application_id = application_id  # 申请ID
        self.user_id = user_id                # 申请人ID
        self.status = status                  # 状态：0-待审核，1-通过，2-驳回
        self.apply_content = apply_content    # 申请理由
        self.review_comment = review_comment  # 审核意见
        self.reviewed_by = reviewed_by        # 审核人ID
        self.reviewed_at = reviewed_at        # 审核时间
        self.updated_at = updated_at          # 最后修改时间
        self.created_at = created_at          # 申请时间
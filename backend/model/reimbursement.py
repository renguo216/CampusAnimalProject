class Reimbursement:
    def __init__(self, reimb_id, user_id, amount, status=0,
                 type=None, description=None, receipt_urls=None,
                 review_comment=None, reviewed_by=None, reviewed_at=None,
                 updated_at=None, pet_id=None, project_id=None,
                 created_at=None):
        self.reimb_id = reimb_id          # 报销单号
        self.user_id = user_id            # 申请人ID
        self.amount = amount              # 申请金额
        self.status = status              # 状态：0-待审，1-通过，2-驳回，3-已撤销
        self.type = type                  # 报销类型
        self.description = description    # 报销说明
        self.receipt_urls = receipt_urls  # 收据图片链接
        self.review_comment = review_comment  # 审核意见
        self.reviewed_by = reviewed_by    # 审核人ID
        self.reviewed_at = reviewed_at    # 审核时间
        self.updated_at = updated_at      # 最后修改时间
        self.pet_id = pet_id              # 关联动物ID
        self.project_id = project_id      # 关联募捐项目ID
        self.created_at = created_at      # 申请时间
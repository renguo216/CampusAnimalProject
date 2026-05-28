class Reimbursement:
    def __init__(self, reimb_id, user_id, amount, status=0,
                 type=None, description=None, receipt_urls=None,
                 review_comment=None, created_at=None):
        self.reimb_id = reimb_id        # 报销单号
        self.user_id = user_id          # 申请人ID
        self.amount = amount            # 申请金额
        self.status = status            # 状态：0-待审，1-通过，2-驳回
        self.type = type                # 报销类型
        self.description = description  # 报销说明
        self.receipt_urls = receipt_urls  # 收据图片链接
        self.review_comment = review_comment  # 审核意见
        self.created_at = created_at    # 申请时间
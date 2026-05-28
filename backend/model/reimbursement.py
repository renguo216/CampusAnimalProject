class Reimbursement:
    def __init__(self, reimb_id, amount, status=0):
        self.reimb_id = reimb_id        # 报销单号
        self.amount = amount            # 金额
        self.status = status            # 0-待审，1-通过，2-驳回
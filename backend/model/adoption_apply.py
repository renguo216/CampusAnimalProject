class AdoptionApply:
    def __init__(self, apply_id, pet_id, user_id, status=0, content=""):
        self.apply_id = apply_id        # 申请单号
        self.pet_id = pet_id            # 领养宠物ID
        self.user_id = user_id          # 申请人ID
        self.status = status            # 0-审核中，1-通过，2-驳回
        self.content = content          # 申请理由
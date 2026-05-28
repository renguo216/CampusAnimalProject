class Donation:
    def __init__(self, donation_id, amount, target_pet_id=None):
        self.donation_id = donation_id      # 捐赠单号
        self.amount = amount                # 金额
        self.target_pet_id = target_pet_id  # 目标宠物ID（可选）
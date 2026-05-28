class Animal:
    def __init__(self, pet_id, name, breed, vector=None, status=0):
        self.pet_id = str(pet_id).zfill(8) #8位数字ID
        self.name = name                # 名字 
        self.breed = breed              # 品种
        self.vector = vector            # 特征向量（JSON字符串）
        self.status = status            # 0-在校，1-已领养，2-需医疗
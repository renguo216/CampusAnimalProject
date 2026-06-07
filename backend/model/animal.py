class Animal:
    def __init__(self, pet_id, name, breed=None, color=None, vector=None,
                 status=0, age=0, gender=0, is_neutered=0, is_vaccinated=0,
                 personality=None, description=None, photo_urls=None,
                 found_location=None, created_at=None):
        self.pet_id = pet_id            # 宠物档案ID
        self.name = name                # 宠物名字
        self.breed = breed              # 品种
        self.color = color              # 毛色
        self.vector = vector            # 特征向量（JSON格式）
        self.status = status            # 状态：0-在校，1-已领养，2-需医疗
        self.age = age                  # 年龄（单位：月）
        self.gender = gender            # 性别：0-未知，1-弟弟，2-妹妹
        self.is_neutered = is_neutered  # 是否绝育：0-未知，1-是，2-否
        self.is_vaccinated = is_vaccinated  # 是否疫苗：0-未知，1-是，2-否
        self.personality = personality  # 性格描述（简短）
        self.description = description  # 详细描述（故事）
        self.photo_urls = photo_urls    # 照片链接（JSON数组）
        self.found_location = found_location  # 发现地点
        self.created_at = created_at    # 档案创建时间

    def to_dict(self):
        import json
        # 确保 photo_urls 是正确的格式 - 如果是字符串且是 JSON 数组，保持原样
        processed_photo_urls = self.photo_urls
        
        return {
            "pet_id": self.pet_id,
            "name": self.name,
            "breed": self.breed,
            "color": self.color,
            "vector": self.vector,
            "status": self.status,
            "age": self.age,
            "gender": self.gender,
            "is_neutered": self.is_neutered,
            "is_vaccinated": self.is_vaccinated,
            "personality": self.personality,
            "description": self.description,
            "photo_urls": processed_photo_urls,
            "found_location": self.found_location,
            "created_at": self.created_at
        }
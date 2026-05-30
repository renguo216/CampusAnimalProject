from backend.utils.db_manager import DatabaseManager
from backend.model.animal import Animal
import json
import math


class AnimalLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    # ========== 基础增删改查 ==========

    def add_animal(self, name, breed='未知', status=0, vector=None,
                   color=None, age=0, gender=0, is_neutered=0, is_vaccinated=0,
                   personality=None, description=None, photo_urls=None, found_location=None):
        """
        添加新动物档案
        """
        # 校验
        if not name or len(name.strip()) == 0:
            print("错误：动物名字不能为空")
            return False
        if status not in (0, 1, 2):
            print("错误：状态值必须是 0, 1 或 2")
            return False
        if gender not in (0, 1, 2):
            print("错误：性别值必须是 0, 1 或 2")
            return False
        if is_neutered not in (0, 1, 2):
            print("错误：绝育状态必须是 0, 1 或 2")
            return False
        if is_vaccinated not in (0, 1, 2):
            print("错误：疫苗状态必须是 0, 1 或 2")
            return False

        data = {
            'name': name,
            'breed': breed,
            'status': status,
            'vector': vector,
            'color': color,
            'age': age,
            'gender': gender,
            'is_neutered': is_neutered,
            'is_vaccinated': is_vaccinated,
            'personality': personality,
            'description': description,
            'photo_urls': photo_urls,
            'found_location': found_location
        }

        if not self.db.open_database():
            return False

        success = self.db.insert('t_animal', data)
        pet_id = self.db.get_last_insert_id() if success else None
        self.db.close_database()
        return pet_id if success else False

    def get_animal_by_id(self, pet_id):
        """根据 pet_id 精确查询"""
        if not self.db.open_database():
            return None
        data = self.db.get_by_id('t_animal', 'pet_id', pet_id)
        self.db.close_database()
        if data:
            return Animal(**data)
        return None

    def get_animal_by_name(self, name):
        """根据名字模糊查询"""
        if not self.db.open_database():
            return []
        sql = "SELECT * FROM t_animal WHERE name LIKE %s"
        results = self.db.execute_raw_sql(sql, (f'%{name}%',))
        self.db.close_database()
        return [Animal(**row) for row in results] if results else []

    def get_animals_by_status(self, status, page=1, page_size=20):
        """
        按状态筛选（分页）
        返回: {"animals": [...], "total": N, "page": page, "page_size": page_size}
        """
        if status not in (0, 1, 2):
            return {"animals": [], "total": 0, "page": page, "page_size": page_size}

        if not self.db.open_database():
            return {"animals": [], "total": 0, "page": page, "page_size": page_size}

        result = self.db.get_paginated(
            't_animal',
            page=page,
            page_size=page_size,
            where_clause="status = %s",
            params=(status,),
            order_by="created_at DESC"
        )
        self.db.close_database()

        if not result:
            return {"animals": [], "total": 0, "page": page, "page_size": page_size}

        animals = [Animal(**row) for row in result.get("data", [])]
        return {
            "animals": animals,
            "total": result.get("total", 0),
            "page": page,
            "page_size": page_size
        }

    def get_all_animals(self, page=1, page_size=20):
        """
        获取所有动物档案（分页）
        返回: {"animals": [...], "total": N, "page": page, "page_size": page_size}
        """
        if not self.db.open_database():
            return {"animals": [], "total": 0, "page": page, "page_size": page_size}

        result = self.db.get_paginated(
            't_animal',
            page=page,
            page_size=page_size,
            order_by="created_at DESC"
        )
        self.db.close_database()

        if not result:
            return {"animals": [], "total": 0, "page": page, "page_size": page_size}

        animals = [Animal(**row) for row in result.get("data", [])]
        return {
            "animals": animals,
            "total": result.get("total", 0),
            "page": page,
            "page_size": page_size
        }

    def update_animal(self, pet_id, update_data):
        """
        通用更新动物档案
        白名单限制：禁止修改 pet_id, created_at
        """
        # 检查动物是否存在
        if not self.get_animal_by_id(pet_id):
            return False

        # 白名单过滤
        forbidden_fields = {'pet_id', 'created_at'}
        clean_data = {k: v for k, v in update_data.items() if k not in forbidden_fields}

        # 枚举字段校验
        if 'status' in clean_data and clean_data['status'] not in (0, 1, 2):
            return False
        if 'gender' in clean_data and clean_data['gender'] not in (0, 1, 2):
            return False
        if 'is_neutered' in clean_data and clean_data['is_neutered'] not in (0, 1, 2):
            return False
        if 'is_vaccinated' in clean_data and clean_data['is_vaccinated'] not in (0, 1, 2):
            return False

        if not clean_data:
            return False

        if not self.db.open_database():
            return False
        success = self.db.update('t_animal', 'pet_id', pet_id, clean_data)
        self.db.close_database()
        return success

    def update_animal_status(self, pet_id, new_status):
        """专门更新动物状态"""
        if new_status not in (0, 1, 2):
            return False
        return self.update_animal(pet_id, {'status': new_status})

    def update_animal_vector(self, pet_id, vector):
        """更新动物特征向量"""
        return self.update_animal(pet_id, {'vector': vector})

    def delete_animal(self, pet_id):
        """删除动物档案"""
        if not self.get_animal_by_id(pet_id):
            return False
        if not self.db.open_database():
            return False
        success = self.db.delete('t_animal', 'pet_id', pet_id)
        self.db.close_database()
        return success

    # ========== 照片管理 ==========

    def add_photo(self, pet_id, photo_url):
        """
        为动物添加一张照片
        :param photo_url: 照片URL
        """
        animal = self.get_animal_by_id(pet_id)
        if not animal:
            return False

        photos = []
        if animal.photo_urls:
            try:
                photos = json.loads(animal.photo_urls)
                if not isinstance(photos, list):
                    photos = []
            except:
                photos = []

        if photo_url not in photos:
            photos.append(photo_url)

        return self.update_animal(pet_id, {'photo_urls': json.dumps(photos)})

    def remove_photo(self, pet_id, photo_url):
        """
        删除动物的某张照片
        """
        animal = self.get_animal_by_id(pet_id)
        if not animal or not animal.photo_urls:
            return False

        try:
            photos = json.loads(animal.photo_urls)
            if not isinstance(photos, list):
                return False
        except:
            return False

        if photo_url not in photos:
            return False

        photos.remove(photo_url)
        return self.update_animal(pet_id, {'photo_urls': json.dumps(photos)})

    # ========== 查询扩展 ==========

    def search_animals_by_location(self, keyword, page=1, page_size=20):
        """
        按发现地点模糊搜索
        """
        if not self.db.open_database():
            return {"animals": [], "total": 0, "page": page, "page_size": page_size}

        result = self.db.get_paginated(
            't_animal',
            page=page,
            page_size=page_size,
            where_clause="found_location LIKE %s",
            params=(f'%{keyword}%',),
            order_by="created_at DESC"
        )
        self.db.close_database()

        if not result:
            return {"animals": [], "total": 0, "page": page, "page_size": page_size}

        animals = [Animal(**row) for row in result.get("data", [])]
        return {
            "animals": animals,
            "total": result.get("total", 0),
            "page": page,
            "page_size": page_size
        }

    def get_animal_statistics(self):
        """
        获取动物档案统计汇总
        """
        if not self.db.open_database():
            return None

        sql = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as on_campus,
                SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as adopted,
                SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as medical_needed
            FROM t_animal
        """
        results = self.db.execute_raw_sql(sql)
        self.db.close_database()

        if not results:
            return None

        row = results[0]
        return {
            "total": int(row.get("total", 0)),
            "on_campus": int(row.get("on_campus", 0)),
            "adopted": int(row.get("adopted", 0)),
            "medical_needed": int(row.get("medical_needed", 0))
        }

    # ========== AI 识别桥梁（待优化） ==========

    def search_similar_animals(self, query_vector, limit=5):
        """
        根据特征向量查找最相似的动物
        TODO: 当前为内存计算，动物数量超过1000时建议改用向量数据库
        """
        if not self.db.open_database():
            return []

        sql = "SELECT * FROM t_animal WHERE vector IS NOT NULL"
        results = self.db.execute_raw_sql(sql)
        self.db.close_database()

        if not results:
            return []

        if isinstance(query_vector, str):
            try:
                query_vector = json.loads(query_vector)
            except:
                return []

        animals = []
        for row in results:
            try:
                db_vector = json.loads(row['vector'])
                similarity = self._cosine_similarity(query_vector, db_vector)
                animals.append((Animal(**row), similarity))
            except:
                continue

        animals.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in animals[:limit]]

    def _cosine_similarity(self, vec1, vec2):
        """计算两个向量的余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
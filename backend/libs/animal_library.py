# ===== backend/libs/animal_library.py =====
"""
动物档案管理业务逻辑层
提供动物档案增删改查、AI识别、以图搜图、失踪动物找回等功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from backend.utils.db_manager import DatabaseManager
from backend.model.animal import Animal
from backend.utils.response import success_response, error_response
import json
import math
from typing import Optional
from backend.utils.ai_http_client import detect_species, extract_features, identify_animal, add_animal_to_ai_db


class AnimalLibrary:
    """
    动物档案业务逻辑库（组合模式）
    持有 DatabaseManager、UserLibrary、AnimalLibrary 实例
    """

    def __init__(self):
        self.db = DatabaseManager()

    # ========== 内部方法（返回原始类型，供本类内部使用） ==========

    def _get_animal_by_id(self, pet_id) -> Optional[Animal]:
        """内部方法：返回 Animal 对象或 None"""
        if not self.db.open_database():
            return None
        data = self.db.get_by_id('t_animal', 'pet_id', pet_id)
        self.db.close_database()
        return Animal(**data) if data else None

    def _cosine_similarity(self, vec1, vec2):
        """内部方法：计算余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    # ========== 公共方法（统一返回格式） ==========

    def add_animal(self, name, breed='未知', status=0, vector=None,
                   color=None, age=0, gender=0, is_neutered=0, is_vaccinated=0,
                   personality=None, description=None, photo_urls=None, found_location=None) -> dict:
        """
        添加新动物档案
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        if not name or len(name.strip()) == 0:
            return error_response("动物名字不能为空")
        if status not in (0, 1, 2):
            return error_response("状态值必须是 0, 1 或 2")
        if gender not in (0, 1, 2):
            return error_response("性别值必须是 0, 1 或 2")
        if is_neutered not in (0, 1, 2):
            return error_response("绝育状态必须是 0, 1 或 2")
        if is_vaccinated not in (0, 1, 2):
            return error_response("疫苗状态必须是 0, 1 或 2")
<<<<<<< HEAD

        # 处理 photo_urls - 如果是列表，转换为 JSON 字符串
        import json
        processed_photo_urls = photo_urls
        if photo_urls and isinstance(photo_urls, list):
            processed_photo_urls = json.dumps(photo_urls)
=======
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706

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
            'photo_urls': processed_photo_urls,
            'found_location': found_location
        }

        if not self.db.open_database():
            return error_response("数据库连接失败")

        success = self.db.insert('t_animal', data)
        pet_id = self.db.get_last_insert_id() if success else None
        self.db.close_database()

        if success and pet_id:
            return success_response("添加成功", data={"pet_id": pet_id})
        return error_response("添加失败")

    def add_animal_with_ai(self, photo_bytes: bytes, name, status=0,
                           color=None, age=0, gender=0, is_neutered=0, is_vaccinated=0,
                           personality=None, description=None, found_location=None) -> dict:
        """
        通过AI识别品种和特征向量后添加动物档案
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        breed = "未知"
        category = "unknown"
        vector = None

        try:
            species_result = detect_species(photo_bytes)
            if species_result.get('success'):
                breed = species_result.get('breed_name', '未知')
                category = species_result.get('category', 'unknown')
        except Exception as e:
            print(f"AI识别品种失败: {e}")

        try:
            features_result = extract_features(photo_bytes)
            if features_result.get('success'):
                vector = json.dumps(features_result.get('features'))
        except Exception as e:
            print(f"AI提取特征失败: {e}")

        result = self.add_animal(
            name=name,
            breed=breed,
            status=status,
            vector=vector,
            color=color,
            age=age,
            gender=gender,
            is_neutered=is_neutered,
            is_vaccinated=is_vaccinated,
            personality=personality,
            description=description,
            found_location=found_location
        )

        if not result["success"]:
            return result

        pet_id = result["data"]["pet_id"]

        try:
            add_animal_to_ai_db(
                image_bytes=photo_bytes,
                species=category,
                location=found_location or "unknown",
                breed=breed
            )
        except Exception as e:
            print(f"同步AI数据库失败: {e}")

        return success_response("添加成功", data={"pet_id": pet_id})

    def get_animal_by_id(self, pet_id) -> dict:
        """
        根据ID查询动物详情
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        animal = self._get_animal_by_id(pet_id)
        if not animal:
            return error_response("动物不存在")
        return success_response(
            message="成功",
            data=animal.to_dict() if hasattr(animal, 'to_dict') else {
                "pet_id": animal.pet_id,
                "name": animal.name,
                "breed": animal.breed,
                "status": animal.status,
                "vector": animal.vector,
                "color": animal.color,
                "age": animal.age,
                "gender": animal.gender,
                "is_neutered": animal.is_neutered,
                "is_vaccinated": animal.is_vaccinated,
                "personality": animal.personality,
                "description": animal.description,
                "photo_urls": animal.photo_urls,
                "found_location": animal.found_location
            }
        )

    def get_animal_by_name(self, name) -> dict:
        """
        根据名字模糊查询动物
        :return: dict {"success": bool, "message": str, "data": {"animals": list}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = "SELECT * FROM t_animal WHERE name LIKE %s"
        results = self.db.execute_raw_sql(sql, (f'%{name}%',))
        self.db.close_database()

        if not results:
            return success_response("成功", data={"animals": []})

        animals = []
        for row in results:
            animal = Animal(**row)
            animals.append(animal.to_dict() if hasattr(animal, 'to_dict') else {
                "pet_id": animal.pet_id,
                "name": animal.name,
                "breed": animal.breed,
                "status": animal.status,
                "color": animal.color,
                "photo_urls": animal.photo_urls,
                "found_location": animal.found_location
            })

        return success_response("成功", data={"animals": animals})

    def get_animals_by_status(self, status, page=1, page_size=20) -> dict:
        """
        按状态分页查询动物列表
        :return: dict {"success": bool, "message": str, "data": {"animals": list, "total": int, "page": int, "page_size": int}}
        """
        if status not in (0, 1, 2):
            return error_response("状态值必须是 0, 1 或 2")
        if not self.db.open_database():
            return error_response("数据库连接失败")

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
            return success_response("成功", data={"animals": [], "total": 0, "page": page, "page_size": page_size})

        animals = []
        for row in result.get("data", []):
            animal = Animal(**row)
            animals.append(animal.to_dict() if hasattr(animal, 'to_dict') else {
                "pet_id": animal.pet_id,
                "name": animal.name,
                "breed": animal.breed,
                "status": animal.status,
                "color": animal.color,
                "photo_urls": animal.photo_urls,
                "found_location": animal.found_location
            })

        return success_response(
            "成功",
            data={
                "animals": animals,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
        )

    def get_all_animals(self, page=1, page_size=20) -> dict:
        """
        获取所有动物列表（分页）
        :return: dict {"success": bool, "message": str, "data": {"animals": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        result = self.db.get_paginated(
            't_animal',
            page=page,
            page_size=page_size,
            order_by="created_at DESC"
        )
        self.db.close_database()

        if not result:
            return success_response("成功", data={"animals": [], "total": 0, "page": page, "page_size": page_size})

        animals = []
        for row in result.get("data", []):
            animal = Animal(**row)
            animals.append(animal.to_dict() if hasattr(animal, 'to_dict') else {
                "pet_id": animal.pet_id,
                "name": animal.name,
                "breed": animal.breed,
                "status": animal.status,
                "color": animal.color,
                "photo_urls": animal.photo_urls,
                "found_location": animal.found_location
            })

        return success_response(
            "成功",
            data={
                "animals": animals,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
        )

    def update_animal(self, pet_id, update_data) -> dict:
        """
        更新动物信息
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        animal = self._get_animal_by_id(pet_id)
        if not animal:
            return error_response("动物不存在")

        forbidden_fields = {'pet_id', 'created_at'}
        clean_data = {k: v for k, v in update_data.items() if k not in forbidden_fields}
        if 'status' in clean_data and clean_data['status'] not in (0, 1, 2):
            return error_response("状态值必须是 0, 1 或 2")
        if 'gender' in clean_data and clean_data['gender'] not in (0, 1, 2):
            return error_response("性别值必须是 0, 1 或 2")
        if 'is_neutered' in clean_data and clean_data['is_neutered'] not in (0, 1, 2):
            return error_response("绝育状态必须是 0, 1 或 2")
        if 'is_vaccinated' in clean_data and clean_data['is_vaccinated'] not in (0, 1, 2):
            return error_response("疫苗状态必须是 0, 1 或 2")
        if not clean_data:
            return error_response("没有需要更新的字段")

        if not self.db.open_database():
            return error_response("数据库连接失败")
        success = self.db.update('t_animal', 'pet_id', pet_id, clean_data)
        self.db.close_database()

        if success:
            return success_response("更新成功", data={"pet_id": pet_id})
        return error_response("更新失败")

    def update_animal_status(self, pet_id, new_status) -> dict:
        """
        更新动物状态
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        if new_status not in (0, 1, 2):
            return error_response("状态值必须是 0, 1 或 2")
        return self.update_animal(pet_id, {'status': new_status})

    def update_animal_vector(self, pet_id, vector) -> dict:
        """
        更新动物特征向量
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        return self.update_animal(pet_id, {'vector': vector})

    def delete_animal(self, pet_id) -> dict:
        """
        删除动物档案
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        animal = self._get_animal_by_id(pet_id)
        if not animal:
            return error_response("动物不存在")
        if not self.db.open_database():
            return error_response("数据库连接失败")
        success = self.db.delete('t_animal', 'pet_id', pet_id)
        self.db.close_database()

        if success:
            return success_response("删除成功", data={"pet_id": pet_id})
        return error_response("删除失败")

    # ========== 照片管理 ==========

    def add_photo(self, pet_id, photo_url) -> dict:
        """
        添加动物照片
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        animal = self._get_animal_by_id(pet_id)
        if not animal:
            return error_response("动物不存在")

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

        result = self.update_animal(pet_id, {'photo_urls': json.dumps(photos)})
        return result

    def remove_photo(self, pet_id, photo_url) -> dict:
        """
        移除动物照片
        :return: dict {"success": bool, "message": str, "data": {"pet_id": int} or None}
        """
        animal = self._get_animal_by_id(pet_id)
        if not animal or not animal.photo_urls:
            return error_response("动物不存在或无照片")

        try:
            photos = json.loads(animal.photo_urls)
            if not isinstance(photos, list):
                return error_response("照片数据格式错误")
        except:
            return error_response("照片数据格式错误")

        if photo_url not in photos:
            return error_response("照片不存在")

        photos.remove(photo_url)
        return self.update_animal(pet_id, {'photo_urls': json.dumps(photos)})

    # ========== 查询扩展 ==========

    def search_animals_by_location(self, keyword, page=1, page_size=20) -> dict:
        """
        按发现位置搜索动物
        :return: dict {"success": bool, "message": str, "data": {"animals": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

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
            return success_response("成功", data={"animals": [], "total": 0, "page": page, "page_size": page_size})

        animals = []
        for row in result.get("data", []):
            animal = Animal(**row)
            animals.append(animal.to_dict() if hasattr(animal, 'to_dict') else {
                "pet_id": animal.pet_id,
                "name": animal.name,
                "breed": animal.breed,
                "status": animal.status,
                "color": animal.color,
                "photo_urls": animal.photo_urls,
                "found_location": animal.found_location
            })

        return success_response(
            "成功",
            data={
                "animals": animals,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
        )

    def get_animal_statistics(self) -> dict:
        """
        获取动物统计信息
        :return: dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

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
            return error_response("统计查询失败")

        row = results[0]
        return success_response(
            "成功",
            data={
                "total": int(row.get("total", 0)),
                "on_campus": int(row.get("on_campus", 0)),
                "adopted": int(row.get("adopted", 0)),
                "medical_needed": int(row.get("medical_needed", 0))
            }
        )

    # ========== AI 识别桥梁 ==========

    def search_similar_animals(self, query_vector, limit=5) -> dict:
        """
        根据特征向量查找最相似的动物
        :return: dict {"success": bool, "message": str, "data": [{"animal": dict, "similarity": float}]}
        """
        def search_similar_animals(self, query_vector, limit=5):
            # 1. 严格校验输入：必须是列表，且不为空
            if not isinstance(query_vector, list) or len(query_vector) == 0:
                return error_response("无效的查询向量格式")
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = "SELECT * FROM t_animal WHERE vector IS NOT NULL"
        results = self.db.execute_raw_sql(sql)
        self.db.close_database()

        if not results:
            return success_response("成功", data={"similar_animals": []})

        if isinstance(query_vector, str):
            try:
                query_vector = json.loads(query_vector)
            except:
                return error_response("特征向量格式错误")

        animals = []
        for row in results:
            try:
                db_vector = json.loads(row['vector'])
                similarity = self._cosine_similarity(query_vector, db_vector)
                animal = Animal(**row)
                animals.append((animal, similarity))
            except:
                continue

        animals.sort(key=lambda x: x[1], reverse=True)

        similar_animals = []
        for animal, sim in animals[:limit]:
            similar_animals.append({
                "animal": animal.to_dict() if hasattr(animal, 'to_dict') else {
                    "pet_id": animal.pet_id,
                    "name": animal.name,
                    "breed": animal.breed,
                    "color": animal.color,
                    "photo_urls": animal.photo_urls,
                    "found_location": animal.found_location,
                    "status": animal.status,
                },
                "similarity": round(sim, 4)
            })

        return success_response("成功", data={"similar_animals": similar_animals})

    # ========== 以图搜猫 / 失踪动物找回 ==========

    def search_by_image(self, photo_bytes: bytes) -> dict:
        """
        以图搜图：先AI识别个体，再在库中找相似
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        identify_result = identify_animal(photo_bytes)
        if not identify_result.get("success"):
            return error_response("AI识别失败")
        if identify_result.get("is_new"):
            return success_response("未找到相似动物", data={"animals": []})

        confidence = identify_result.get("confidence", 0)

        features_result = extract_features(photo_bytes)
        if not features_result.get("success"):
            return error_response("提取特征失败")

        similar_result = self.search_similar_animals(features_result["features"], limit=5)
        if not similar_result["success"]:
            return similar_result

        return success_response(
            "匹配成功",
            data={
                "confidence": confidence,
                "animals": similar_result["data"]["similar_animals"]
            }
        )

    def find_lost_animal(self, photo_bytes: bytes) -> dict:
        """
        失踪动物找回，内部调用 search_by_image
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        return self.search_by_image(photo_bytes)
# backend/tests/test_animal_library.py
"""
AnimalLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_animal_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_animal 表已存在
    - AI 服务（可选）：python -m backend.ai_module.flask_api
    - 测试图片：backend/tests/test_data/ 目录下存在：
        虎斑猫.jpg, 金毛寻回犬.jpg, 边境牧羊犬.jpg, 猎豹.jpg
"""

import json
import os
import sys
import unittest
import uuid
import requests
from unittest.mock import patch

# 将项目根目录加入路径，确保 backend 包可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.animal_library import AnimalLibrary


# ==================== 测试配置 ====================

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
CAT_IMG = os.path.join(TEST_DATA_DIR, "虎斑猫.jpg")
DOG_IMG = os.path.join(TEST_DATA_DIR, "金毛寻回犬.jpg")
DOG2_IMG = os.path.join(TEST_DATA_DIR, "边境牧羊犬.jpg")
CHEETAH_IMG = os.path.join(TEST_DATA_DIR, "猎豹.jpg")

AI_BASE_URL = "http://localhost:8001"


def _ai_service_available() -> bool:
    """检查 AI 服务是否可访问"""
    try:
        r = requests.get(f"{AI_BASE_URL}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ==================== 基础功能 + Mock AI 测试 ====================

class TestAnimalLibrary(unittest.TestCase):
    """AnimalLibrary 基础功能 + Mock AI 测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = AnimalLibrary()
        cls._cleanup_all_test_data()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all_test_data()

    def setUp(self):
        self.created_pet_ids = []
        self.created_names = []

    def tearDown(self):
        self._cleanup_created_data()

    # ---------- 内部辅助 ----------

    @classmethod
    def _cleanup_all_test_data(cls):
        """清理所有测试数据（按 name 前缀）"""
        if cls.lib.db.open_database():
            prefixes = [
                'test_animal_%', 'test_adopted_%', 'similar_%',
                'to_be_deleted_%', 'photo_test_%', 'location_test_%',
                'updated_%', 'test_ai_%', 'test_fallback_%', 'real_%',
                'mock_%', 'vector_%', 'search_%'
            ]
            for prefix in prefixes:
                cls.lib.db.execute_raw_sql(
                    "DELETE FROM t_animal WHERE name LIKE %s", (prefix,)
                )
            cls.lib.db.close_database()

    def _cleanup_created_data(self):
        """清理本测试方法创建的数据"""
        if not self.created_pet_ids and not self.created_names:
            return
        if self.lib.db.open_database():
            for pet_id in self.created_pet_ids:
                self.lib.db.execute_raw_sql(
                    "DELETE FROM t_animal WHERE pet_id = %s", (pet_id,)
                )
            for name in self.created_names:
                self.lib.db.execute_raw_sql(
                    "DELETE FROM t_animal WHERE name = %s", (name,)
                )
            self.lib.db.close_database()

    def _track(self, result: dict) -> dict:
        """追踪创建的动物 ID，便于 tearDown 清理"""
        if result.get("success") and result.get("data", {}).get("pet_id"):
            self.created_pet_ids.append(result["data"]["pet_id"])
        return result

    def _add_test_animal(self, **kwargs) -> dict:
        """快速添加测试动物并追踪"""
        defaults = {
            "name": f"test_animal_{uuid.uuid4().hex[:8]}",
            "breed": "中华田园猫",
            "status": 0,
            "color": "橘色",
            "age": 6,
            "gender": 1,
            "is_neutered": 0,
            "is_vaccinated": 1,
            "personality": "温顺",
            "description": "测试用",
            "photo_urls": json.dumps(["http://example.com/cat1.jpg"]),
            "found_location": "图书馆南门"
        }
        defaults.update(kwargs)
        result = self.lib.add_animal(**defaults)
        self._track(result)
        if defaults.get("name"):
            self.created_names.append(defaults["name"])
        return result

    # ==================== 1. add_animal ====================

    def test_add_animal_success(self):
        """正常添加动物"""
        result = self._add_test_animal()
        self.assertTrue(result["success"], f"添加失败：{result}")
        self.assertIn("pet_id", result["data"])
        self.assertIsInstance(result["data"]["pet_id"], int)

    def test_add_animal_empty_name(self):
        """空名字应失败"""
        result = self.lib.add_animal("", "测试", 0)
        self.assertFalse(result["success"])
        self.assertIn("名字", result["message"])

    def test_add_animal_invalid_status(self):
        """非法状态应失败"""
        result = self.lib.add_animal("测试", "测试", status=5)
        self.assertFalse(result["success"])
        self.assertIn("状态", result["message"])

    def test_add_animal_invalid_gender(self):
        """非法性别应失败"""
        result = self.lib.add_animal("测试", "测试", gender=99)
        self.assertFalse(result["success"])
        self.assertIn("性别", result["message"])

    def test_add_animal_invalid_neutered(self):
        """非法绝育状态应失败"""
        result = self.lib.add_animal("测试", "测试", is_neutered=99)
        self.assertFalse(result["success"])
        self.assertIn("绝育", result["message"])

    def test_add_animal_invalid_vaccinated(self):
        """非法疫苗状态应失败"""
        result = self.lib.add_animal("测试", "测试", is_vaccinated=99)
        self.assertFalse(result["success"])
        self.assertIn("疫苗", result["message"])

    # ==================== 2. get_animal_by_id ====================

    def test_get_animal_by_id_success(self):
        """查询存在的动物"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.get_animal_by_id(pet_id)
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["pet_id"], pet_id)

    def test_get_animal_by_id_not_found(self):
        """查询不存在的动物"""
        result = self.lib.get_animal_by_id(999999)
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    # ==================== 3. get_animal_by_name ====================

    def test_get_animal_by_name_success(self):
        """模糊查询名字"""
        name = f"test_animal_{uuid.uuid4().hex[:8]}"
        self._add_test_animal(name=name)
        result = self.lib.get_animal_by_name(name[:8])
        self.assertTrue(result["success"])
        self.assertGreaterEqual(len(result["data"]["animals"]), 1)

    def test_get_animal_by_name_not_found(self):
        """查询不存在的名字"""
        result = self.lib.get_animal_by_name("不存在的名字xyz123")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["animals"]), 0)

    # ==================== 4. get_animals_by_status ====================

    def test_get_animals_by_status_success(self):
        """按状态分页查询"""
        self._add_test_animal(status=1)
        result = self.lib.get_animals_by_status(1, page=1, page_size=10)
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["data"]["total"], 1)
        self.assertIsInstance(result["data"]["animals"], list)

    def test_get_animals_by_status_invalid(self):
        """非法状态返回错误"""
        result = self.lib.get_animals_by_status(99)
        self.assertFalse(result["success"])
        self.assertIn("状态", result["message"])

    # ==================== 5. get_all_animals ====================

    def test_get_all_animals_pagination(self):
        """分页获取所有动物"""
        self._add_test_animal()
        self._add_test_animal()
        result = self.lib.get_all_animals(page=1, page_size=1)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["animals"]), 1)
        self.assertGreaterEqual(result["data"]["total"], 2)

    # ==================== 6. update_animal ====================

    def test_update_animal_success(self):
        """通用更新成功"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        new_name = f"updated_{uuid.uuid4().hex[:6]}"
        result = self.lib.update_animal(pet_id, {
            "name": new_name,
            "description": "新描述",
            "personality": "新性格"
        })
        self.assertTrue(result["success"])
        query = self.lib.get_animal_by_id(pet_id)
        self.assertEqual(query["data"]["name"], new_name)

    def test_update_animal_forbidden_fields(self):
        """禁止字段应被过滤，导致无有效字段可更新"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.update_animal(pet_id, {
            "pet_id": 99999,
            "created_at": "2020-01-01"
        })
        self.assertFalse(result["success"])
        self.assertIn("没有需要更新", result["message"])

    def test_update_animal_not_found(self):
        """更新不存在的动物"""
        result = self.lib.update_animal(999999, {"name": "test"})
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    def test_update_animal_invalid_status(self):
        """更新非法状态"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.update_animal(pet_id, {"status": 99})
        self.assertFalse(result["success"])
        self.assertIn("状态", result["message"])

    # ==================== 7. update_animal_status ====================

    def test_update_animal_status_success(self):
        """更新状态成功"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.update_animal_status(pet_id, 2)
        self.assertTrue(result["success"])
        query = self.lib.get_animal_by_id(pet_id)
        self.assertEqual(query["data"]["status"], 2)

    def test_update_animal_status_invalid(self):
        """更新非法状态"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.update_animal_status(pet_id, 99)
        self.assertFalse(result["success"])

    # ==================== 8. update_animal_vector ====================

    def test_update_animal_vector_success(self):
        """更新向量成功"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        vector = json.dumps([0.1, 0.2, 0.3])
        result = self.lib.update_animal_vector(pet_id, vector)
        self.assertTrue(result["success"])
        query = self.lib.get_animal_by_id(pet_id)
        self.assertEqual(query["data"]["vector"], vector)

    # ==================== 9. delete_animal ====================

    def test_delete_animal_success(self):
        """删除成功"""
        add_result = self._add_test_animal()
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.delete_animal(pet_id)
        self.assertTrue(result["success"])
        query = self.lib.get_animal_by_id(pet_id)
        self.assertFalse(query["success"])
        if pet_id in self.created_pet_ids:
            self.created_pet_ids.remove(pet_id)

    def test_delete_animal_not_found(self):
        """删除不存在的动物"""
        result = self.lib.delete_animal(999999)
        self.assertFalse(result["success"])

    # ==================== 10. add_photo ====================

    def test_add_photo_success(self):
        """添加照片成功"""
        add_result = self._add_test_animal(photo_urls=json.dumps(["http://old.jpg"]))
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.add_photo(pet_id, "http://new1.jpg")
        self.assertTrue(result["success"])
        query = self.lib.get_animal_by_id(pet_id)
        photos = json.loads(query["data"]["photo_urls"])
        self.assertIn("http://new1.jpg", photos)
        self.assertIn("http://old.jpg", photos)

    def test_add_photo_duplicate(self):
        """重复添加应去重"""
        add_result = self._add_test_animal(photo_urls=json.dumps(["http://dup.jpg"]))
        pet_id = add_result["data"]["pet_id"]
        self.lib.add_photo(pet_id, "http://dup.jpg")
        result = self.lib.add_photo(pet_id, "http://dup.jpg")
        self.assertTrue(result["success"])
        query = self.lib.get_animal_by_id(pet_id)
        photos = json.loads(query["data"]["photo_urls"])
        self.assertEqual(photos.count("http://dup.jpg"), 1)

    # ==================== 11. remove_photo ====================

    def test_remove_photo_success(self):
        """移除照片成功"""
        add_result = self._add_test_animal(photo_urls=json.dumps(["http://a.jpg", "http://b.jpg"]))
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.remove_photo(pet_id, "http://a.jpg")
        self.assertTrue(result["success"])
        query = self.lib.get_animal_by_id(pet_id)
        photos = json.loads(query["data"]["photo_urls"])
        self.assertNotIn("http://a.jpg", photos)
        self.assertIn("http://b.jpg", photos)

    def test_remove_photo_not_found(self):
        """移除不存在的照片"""
        add_result = self._add_test_animal(photo_urls=json.dumps(["http://a.jpg"]))
        pet_id = add_result["data"]["pet_id"]
        result = self.lib.remove_photo(pet_id, "http://not_exist.jpg")
        self.assertFalse(result["success"])

    # ==================== 12. search_animals_by_location ====================

    def test_search_animals_by_location_success(self):
        """按地点搜索"""
        self._add_test_animal(found_location="图书馆北门草丛")
        result = self.lib.search_animals_by_location("图书馆", page=1, page_size=10)
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["data"]["total"], 1)

    def test_search_animals_by_location_not_found(self):
        """搜索不存在的地点"""
        result = self.lib.search_animals_by_location("火星xyz", page=1, page_size=10)
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["total"], 0)

    # ==================== 13. get_animal_statistics ====================

    def test_get_animal_statistics(self):
        """统计汇总"""
        result = self.lib.get_animal_statistics()
        self.assertTrue(result["success"])
        data = result["data"]
        self.assertIn("total", data)
        self.assertIn("on_campus", data)
        self.assertIn("adopted", data)
        self.assertIn("medical_needed", data)
        self.assertGreaterEqual(data["total"], data["on_campus"] + data["adopted"] + data["medical_needed"])

    # ==================== 14. search_similar_animals ====================

    def test_search_similar_animals_success(self):
        """向量相似度搜索"""
        name1 = f"similar_1_{uuid.uuid4().hex[:6]}"
        name2 = f"similar_2_{uuid.uuid4().hex[:6]}"
        self._add_test_animal(name=name1, vector=json.dumps([0.1, 0.2, 0.3]))
        self._add_test_animal(name=name2, vector=json.dumps([0.9, 0.8, 0.7]))
        result = self.lib.search_similar_animals([0.1, 0.2, 0.3], limit=2)
        self.assertTrue(result["success"])
        sims = result["data"]["similar_animals"]
        self.assertGreaterEqual(len(sims), 1)
        self.assertEqual(sims[0]["animal"]["name"], name1)

    def test_search_similar_animals_invalid_vector(self):
        """无效向量返回错误 — 先确保库里有 vector 记录，才能触发参数校验"""
        # 先插入一条带 vector 的数据，确保 search_similar_animals 不会提前返回空结果
        self._add_test_animal(
            name=f"vector_holder_{uuid.uuid4().hex[:6]}",
            vector=json.dumps([0.1, 0.2, 0.3])
        )
        result = self.lib.search_similar_animals("invalid")
        self.assertFalse(result["success"])
        self.assertIn("格式", result["message"])

    # ==================== 15. add_animal_with_ai (Mock) ====================

    @patch('backend.libs.animal_library.detect_species')
    @patch('backend.libs.animal_library.extract_features')
    @patch('backend.libs.animal_library.add_animal_to_ai_db')
    def test_add_animal_with_ai_mock_success(self, mock_add_ai, mock_extract, mock_detect):
        """AI识别成功场景（Mock）"""
        mock_detect.return_value = {
            "success": True,
            "category": "cat",
            "breed": "tabby",
            "breed_name": "虎斑猫",
            "confidence": 0.95
        }
        mock_extract.return_value = {
            "success": True,
            "features": [0.1, 0.2, 0.3, 0.4],
            "dimension": 4
        }
        mock_add_ai.return_value = {"success": True}

        name = f"test_ai_{uuid.uuid4().hex[:6]}"
        result = self.lib.add_animal_with_ai(
            photo_bytes=b"fake_image_bytes",
            name=name,
            status=0,
            color="黑白",
            age=12,
            gender=1,
            description="AI识别测试猫"
        )
        self._track(result)
        self.created_names.append(name)
        self.assertTrue(result["success"])
        pet_id = result["data"]["pet_id"]
        query = self.lib.get_animal_by_id(pet_id)
        self.assertEqual(query["data"]["breed"], "虎斑猫")
        self.assertIsNotNone(query["data"]["vector"])

    @patch('backend.libs.animal_library.detect_species')
    @patch('backend.libs.animal_library.extract_features')
    @patch('backend.libs.animal_library.add_animal_to_ai_db')
    def test_add_animal_with_ai_mock_fallback(self, mock_add_ai, mock_extract, mock_detect):
        """AI识别失败降级（Mock）：breed='未知', vector=None，但整体仍成功"""
        mock_detect.return_value = {"success": False}
        mock_extract.return_value = {"success": False}
        mock_add_ai.return_value = {"success": True}

        name = f"test_fallback_{uuid.uuid4().hex[:6]}"
        result = self.lib.add_animal_with_ai(
            photo_bytes=b"fake_image_bytes",
            name=name,
            status=0
        )
        self._track(result)
        self.created_names.append(name)
        self.assertTrue(result["success"])
        pet_id = result["data"]["pet_id"]
        query = self.lib.get_animal_by_id(pet_id)
        self.assertEqual(query["data"]["breed"], "未知")
        self.assertIsNone(query["data"]["vector"])

    # ==================== 16. search_by_image (Mock) ====================

    @patch('backend.libs.animal_library.identify_animal')
    @patch('backend.libs.animal_library.extract_features')
    def test_search_by_image_mock_new(self, mock_extract, mock_identify):
        """以图搜图：AI判断为新动物，返回空列表"""
        mock_identify.return_value = {
            "success": True,
            "is_new": True,
            "message": "首次识别"
        }
        mock_extract.return_value = {
            "success": True,
            "features": [0.1, 0.2, 0.3]
        }
        result = self.lib.search_by_image(b"fake")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["animals"]), 0)

    @patch('backend.libs.animal_library.identify_animal')
    @patch('backend.libs.animal_library.extract_features')
    def test_search_by_image_mock_existing(self, mock_extract, mock_identify):
        """以图搜图：找到相似动物"""
        name = f"mock_search_{uuid.uuid4().hex[:6]}"
        self._add_test_animal(name=name, vector=json.dumps([0.1, 0.2, 0.3]))
        mock_identify.return_value = {
            "success": True,
            "is_new": False,
            "confidence": 0.85
        }
        mock_extract.return_value = {
            "success": True,
            "features": [0.1, 0.2, 0.3]
        }
        result = self.lib.search_by_image(b"fake")
        self.assertTrue(result["success"])
        self.assertGreaterEqual(len(result["data"]["animals"]), 1)
        self.assertIn("confidence", result["data"])

    # ==================== 17. find_lost_animal (Mock) ====================

    @patch('backend.libs.animal_library.identify_animal')
    @patch('backend.libs.animal_library.extract_features')
    def test_find_lost_animal_mock(self, mock_extract, mock_identify):
        """失踪动物找回（Mock，复用 search_by_image）"""
        mock_identify.return_value = {
            "success": True,
            "is_new": True,
            "message": "未匹配"
        }
        mock_extract.return_value = {
            "success": True,
            "features": [0.1, 0.2, 0.3]
        }
        result = self.lib.find_lost_animal(b"fake")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["animals"]), 0)


# ==================== 真实 AI 集成测试（AI 服务未启动则自动跳过） ====================

@unittest.skipUnless(_ai_service_available(), "AI 服务未启动（localhost:8001），跳过真实 AI 测试")
class TestAnimalLibraryAIReal(unittest.TestCase):
    """真实 AI 服务集成测试（需提前启动 flask_api）"""

    @classmethod
    def setUpClass(cls):
        cls.lib = AnimalLibrary()
        cls._cleanup_all_test_data()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all_test_data()

    def setUp(self):
        self.created_pet_ids = []
        self.created_names = []

    def tearDown(self):
        if self.lib.db.open_database():
            for pet_id in self.created_pet_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_animal WHERE pet_id = %s", (pet_id,))
            for name in self.created_names:
                self.lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name = %s", (name,))
            self.lib.db.close_database()

    @classmethod
    def _cleanup_all_test_data(cls):
        if cls.lib.db.open_database():
            prefixes = ['real_ai_%', 'real_search_%', 'real_find_%']
            for prefix in prefixes:
                cls.lib.db.execute_raw_sql(
                    "DELETE FROM t_animal WHERE name LIKE %s", (prefix,)
                )
            cls.lib.db.close_database()

    def _track(self, result: dict) -> dict:
        if result.get("success") and result.get("data", {}).get("pet_id"):
            self.created_pet_ids.append(result["data"]["pet_id"])
        return result

    # ---------- 真实 AI：添加动物 ----------

    def test_add_animal_with_ai_real_cat(self):
        """真实 AI：识别虎斑猫"""
        with open(CAT_IMG, "rb") as f:
            photo = f.read()
        name = f"real_ai_cat_{uuid.uuid4().hex[:6]}"
        result = self.lib.add_animal_with_ai(
            photo_bytes=photo,
            name=name,
            status=0,
            color="橘色",
            age=2,
            gender=1
        )
        self._track(result)
        self.created_names.append(name)
        self.assertTrue(result["success"], f"AI添加失败：{result}")
        pet_id = result["data"]["pet_id"]
        query = self.lib.get_animal_by_id(pet_id)
        self.assertTrue(query["success"])
        self.assertNotEqual(query["data"]["breed"], "未知")
        self.assertIsNotNone(query["data"]["vector"])
        print(f"  [AI识别结果] breed={query['data']['breed']}, vector长度={len(json.loads(query['data']['vector']))}")

    def test_add_animal_with_ai_real_dog(self):
        """真实 AI：识别金毛寻回犬"""
        with open(DOG_IMG, "rb") as f:
            photo = f.read()
        name = f"real_ai_dog_{uuid.uuid4().hex[:6]}"
        result = self.lib.add_animal_with_ai(
            photo_bytes=photo,
            name=name,
            status=0
        )
        self._track(result)
        self.created_names.append(name)
        self.assertTrue(result["success"])
        pet_id = result["data"]["pet_id"]
        query = self.lib.get_animal_by_id(pet_id)
        self.assertNotEqual(query["data"]["breed"], "未知")
        print(f"  [AI识别结果] breed={query['data']['breed']}, vector长度={len(json.loads(query['data']['vector']))}")

    def test_add_animal_with_ai_real_cheetah(self):
        """真实 AI：识别猎豹（非猫狗，验证 other 分支）"""
        with open(CHEETAH_IMG, "rb") as f:
            photo = f.read()
        name = f"real_ai_cheetah_{uuid.uuid4().hex[:6]}"
        result = self.lib.add_animal_with_ai(
            photo_bytes=photo,
            name=name,
            status=0
        )
        self._track(result)
        self.created_names.append(name)
        self.assertTrue(result["success"])
        pet_id = result["data"]["pet_id"]
        query = self.lib.get_animal_by_id(pet_id)
        print(f"  [猎豹识别结果] breed={query['data']['breed']}")

    # ---------- 真实 AI：以图搜图 ----------

    def test_search_by_image_real(self):
        """真实 AI：以图搜图"""
        with open(CAT_IMG, "rb") as f:
            photo = f.read()
        name = f"real_search_{uuid.uuid4().hex[:6]}"
        add_result = self.lib.add_animal_with_ai(photo_bytes=photo, name=name, status=0)
        self._track(add_result)
        self.created_names.append(name)
        self.assertTrue(add_result["success"])

        result = self.lib.search_by_image(photo)
        self.assertTrue(result["success"])
        self.assertIn("animals", result["data"])
        print(f"  [以图搜图] 返回相似动物数：{len(result['data']['animals'])}")

    # ---------- 真实 AI：失踪动物找回 ----------

    def test_find_lost_animal_real(self):
        """真实 AI：失踪动物找回"""
        with open(DOG2_IMG, "rb") as f:
            photo = f.read()
        result = self.lib.find_lost_animal(photo)
        self.assertTrue(result["success"])
        self.assertIn("animals", result["data"])
        print(f"  [失踪找回] 返回相似动物数：{len(result['data']['animals'])}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
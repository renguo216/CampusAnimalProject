# ===== backend/tests/test_post_library.py =====
"""
PostLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_post_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_post, t_comment, t_like, t_user 表已存在
    - AI 服务（可选）：python -m backend.ai_module.flask_api
    - 测试图片：backend/tests/test_data/ 目录下存在：
        虎斑猫.jpg, 金毛寻回犬.jpg, 猎豹.jpg
"""

import json
import os
import sys
import unittest
import uuid
import threading
import socketserver
import http.server
import requests
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.post_library import PostLibrary
from backend.libs.user_library import UserLibrary


# ==================== 测试配置 ====================

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
AI_BASE_URL = "http://localhost:8001"
BIRD_IMG = os.path.join(TEST_DATA_DIR, "小鸟.jpg")
TEST_SERVER_PORT = 18001  # 临时文件服务器端口


def _ai_service_available() -> bool:
    """检查 AI 服务是否可访问"""
    try:
        r = requests.get(f"{AI_BASE_URL}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


class TestImageServer:
    """在测试期间提供本地图片的临时 HTTP 服务"""
    def __init__(self, port=TEST_SERVER_PORT):
        self.port = port
        self.server = None
        self.thread = None
        self._started = False

    def start(self):
        if self._started:
            return
        # 切换到 test_data 目录作为根目录
        os.chdir(TEST_DATA_DIR)
        handler = http.server.SimpleHTTPRequestHandler
        self.server = socketserver.TCPServer(("", self.port), handler)
        self.server.allow_reuse_address = True
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self._started = True

    def stop(self):
        if self.server and self._started:
            self.server.shutdown()
            self.server.server_close()
            self._started = False

    def get_url(self, filename):
        return f"http://localhost:{self.port}/{filename}"


# ==================== 基础功能 + Mock AI 测试 ====================

class TestPostLibrary(unittest.TestCase):
    """PostLibrary 基础功能 + Mock AI 测试"""

    @classmethod
    def setUpClass(cls):
        cls.post_lib = PostLibrary()
        cls.user_lib = UserLibrary()
        cls._cleanup_all_test_data()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all_test_data()

    def setUp(self):
        self.created_post_ids = []
        self.created_comment_ids = []
        self.created_user_ids = []

    def tearDown(self):
        self._cleanup_created_data()

    # ---------- 内部辅助 ----------

    @classmethod
    def _cleanup_all_test_data(cls):
        """清理所有测试数据"""
        if cls.post_lib.db.open_database():
            # 清理帖子（关联的 comment/like 通过外键 CASCADE）
            cls.post_lib.db.execute_raw_sql(
                "DELETE FROM t_post WHERE user_id LIKE %s", ("test_post_user_%",)
            )
            # 清理评论（防止孤立）
            cls.post_lib.db.execute_raw_sql(
                "DELETE FROM t_comment WHERE user_id LIKE %s", ("test_post_user_%",)
            )
            # 清理点赞
            cls.post_lib.db.execute_raw_sql(
                "DELETE FROM t_like WHERE user_id LIKE %s", ("test_post_user_%",)
            )
            cls.post_lib.db.close_database()

        if cls.user_lib.db.open_database():
            cls.user_lib.db.execute_raw_sql(
                "DELETE FROM t_user WHERE user_id LIKE %s", ("test_post_user_%",)
            )
            cls.user_lib.db.close_database()

    def _cleanup_created_data(self):
        """清理本测试方法创建的数据"""
        if self.post_lib.db.open_database():
            for post_id in self.created_post_ids:
                self.post_lib.db.execute_raw_sql(
                    "DELETE FROM t_post WHERE post_id = %s", (post_id,)
                )
            for comment_id in self.created_comment_ids:
                self.post_lib.db.execute_raw_sql(
                    "DELETE FROM t_comment WHERE comment_id = %s", (comment_id,)
                )
            # 清理该用户产生的点赞
            for user_id in self.created_user_ids:
                self.post_lib.db.execute_raw_sql(
                    "DELETE FROM t_like WHERE user_id = %s", (user_id,)
                )
            self.post_lib.db.close_database()

        if self.user_lib.db.open_database():
            for user_id in self.created_user_ids:
                self.user_lib.db.execute_raw_sql(
                    "DELETE FROM t_user WHERE user_id = %s", (user_id,)
                )
            self.user_lib.db.close_database()

    def _create_test_user(self, suffix="") -> str:
        """创建测试用户并追踪"""
        user_id = f"test_post_user_{uuid.uuid4().hex[:6]}{suffix}"
        result = self.user_lib.register_user(user_id, f"测试用户{suffix}", role=1)
        self.assertTrue(result["success"], f"创建用户失败：{result}")
        self.created_user_ids.append(user_id)
        return user_id

    def _create_post(self, user_id, content="测试帖子", image_urls=None, status=None) -> dict:
        """创建测试帖子并追踪"""
        result = self.post_lib.create_post(user_id, content, image_urls)
        self.assertTrue(result["success"], f"创建帖子失败：{result}")
        self.created_post_ids.append(result["data"]["post_id"])
        return result

    def _create_post_with_status(self, status: int) -> tuple:
        """创建指定状态的帖子（通过数据库直接修改）"""
        user_id = self._create_test_user()
        result = self._create_post(user_id, "状态测试帖子")
        post_id = result["data"]["post_id"]
        if status != 1:
            if self.post_lib.db.open_database():
                self.post_lib.db.execute_raw_sql(
                    "UPDATE t_post SET status = %s WHERE post_id = %s", (status, post_id)
                )
                self.post_lib.db.close_database()
        return user_id, post_id

    # ==================== 1. create_post ====================

    def test_create_post_success(self):
        """正常发布帖子"""
        user_id = self._create_test_user()
        result = self.post_lib.create_post(user_id, "正常帖子", None)
        self.assertTrue(result["success"])
        self.assertIn("post_id", result["data"])
        self.created_post_ids.append(result["data"]["post_id"])

    def test_create_post_with_images(self):
        """发布带图片的帖子"""
        user_id = self._create_test_user()
        image_urls = json.dumps(["http://example.com/img1.jpg", "http://example.com/img2.jpg"])
        result = self.post_lib.create_post(user_id, "带图片的帖子", image_urls)
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        # 验证图片URL被正确存储
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["image_urls"], image_urls)

    def test_create_post_invalid_image_urls(self):
        """image_urls 不是合法 JSON"""
        user_id = self._create_test_user()
        result = self.post_lib.create_post(user_id, "测试", "not_json")
        self.assertFalse(result["success"])
        self.assertIn("格式", result["message"])

    # ==================== 2. delete_post ====================

    def test_delete_post_success(self):
        """作者删除自己的帖子"""
        user_id = self._create_test_user()
        post_result = self._create_post(user_id)
        post_id = post_result["data"]["post_id"]
        result = self.post_lib.delete_post(post_id, user_id)
        self.assertTrue(result["success"])
        self.created_post_ids.remove(post_id)

    def test_delete_post_not_author(self):
        """非作者删除帖子应失败"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        result = self.post_lib.delete_post(post_id, user2)
        self.assertFalse(result["success"])
        self.assertIn("无权", result["message"])

    def test_delete_post_not_found(self):
        """删除不存在的帖子"""
        user_id = self._create_test_user()
        result = self.post_lib.delete_post("non_exist_post", user_id)
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    # ==================== 3. get_post_by_id ====================

    def test_get_post_by_id_success(self):
        """查询存在的帖子"""
        user_id = self._create_test_user()
        post_result = self._create_post(user_id, "查询测试")
        post_id = post_result["data"]["post_id"]
        result = self.post_lib.get_post_by_id(post_id)
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["post_id"], post_id)
        self.assertEqual(result["data"]["content"], "查询测试")

    def test_get_post_by_id_not_found(self):
        """查询不存在的帖子"""
        result = self.post_lib.get_post_by_id("non_exist")
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    def test_get_post_by_id_with_like_status(self):
        """查询帖子并检测当前用户点赞状态"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        # 未点赞
        result = self.post_lib.get_post_by_id(post_id, user2)
        self.assertFalse(result["data"]["is_liked_by_current_user"])
        # 点赞后
        self.post_lib.toggle_like_post(post_id, user2)
        result = self.post_lib.get_post_by_id(post_id, user2)
        self.assertTrue(result["data"]["is_liked_by_current_user"])

    # ==================== 4. get_posts_by_user ====================

    def test_get_posts_by_user_success(self):
        """按用户查询帖子"""
        user_id = self._create_test_user()
        self._create_post(user_id, "帖子1")
        self._create_post(user_id, "帖子2")
        result = self.post_lib.get_posts_by_user(user_id, page=1, page_size=10)
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["data"]["total"], 2)

    def test_get_posts_by_user_empty(self):
        """查询无帖子的用户"""
        user_id = self._create_test_user()
        result = self.post_lib.get_posts_by_user(user_id)
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["total"], 0)

    # ==================== 5. get_all_posts ====================

    def test_get_all_posts_pagination(self):
        """分页获取所有帖子"""
        user_id = self._create_test_user()
        self._create_post(user_id, "分页测试1")
        self._create_post(user_id, "分页测试2")
        result = self.post_lib.get_all_posts(page=1, page_size=1)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["posts"]), 1)
        self.assertGreaterEqual(result["data"]["total"], 2)

    def test_get_all_posts_order(self):
        """验证帖子按时间倒序"""
        user_id = self._create_test_user()
        self._create_post(user_id, "较早的帖子")
        self._create_post(user_id, "较新的帖子")
        result = self.post_lib.get_all_posts(page=1, page_size=10)
        self.assertTrue(result["success"])
        if len(result["data"]["posts"]) >= 2:
            t1 = result["data"]["posts"][0]["created_at"]
            t2 = result["data"]["posts"][1]["created_at"]
            self.assertGreaterEqual(t1, t2)

    # ==================== 6. get_post_detail_with_comments ====================

    def test_get_post_detail_with_comments(self):
        """获取帖子详情含评论"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        # 添加评论
        comment_result = self.post_lib.add_comment(post_id, user2, "测试评论")
        self.assertTrue(comment_result["success"])
        self.created_comment_ids.append(comment_result["data"]["comment_id"])
        # 获取详情
        result = self.post_lib.get_post_detail_with_comments(post_id)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["comments"]), 1)
        self.assertEqual(result["data"]["comment_count"], 1)

    def test_get_post_detail_not_found(self):
        """获取不存在的帖子详情"""
        result = self.post_lib.get_post_detail_with_comments("non_exist")
        self.assertFalse(result["success"])

    # ==================== 7. add_comment ====================

    def test_add_comment_success(self):
        """正常添加评论"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        result = self.post_lib.add_comment(post_id, user2, "评论内容")
        self.assertTrue(result["success"])
        self.assertIn("comment_id", result["data"])
        self.created_comment_ids.append(result["data"]["comment_id"])
        # 验证评论数增加
        detail = self.post_lib.get_post_by_id(post_id)
        self.assertEqual(detail["data"]["comment_count"], 1)

    def test_add_comment_post_not_found(self):
        """评论不存在的帖子"""
        user_id = self._create_test_user()
        result = self.post_lib.add_comment("non_exist", user_id, "评论")
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    def test_add_comment_unapproved_post(self):
        """评论未审核通过的帖子"""
        user_id = self._create_test_user()
        # 创建 status=0 的帖子
        post_result = self._create_post(user_id)
        post_id = post_result["data"]["post_id"]
        if self.post_lib.db.open_database():
            self.post_lib.db.execute_raw_sql(
                "UPDATE t_post SET status = 0 WHERE post_id = %s", (post_id,)
            )
            self.post_lib.db.close_database()
        result = self.post_lib.add_comment(post_id, user_id, "评论")
        self.assertFalse(result["success"])
        self.assertIn("未通过", result["message"])

    # ==================== 8. delete_comment ====================

    def test_delete_comment_success(self):
        """删除自己的评论"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        comment_result = self.post_lib.add_comment(post_id, user2, "要删除的评论")
        comment_id = comment_result["data"]["comment_id"]
        self.created_comment_ids.append(comment_id)
        result = self.post_lib.delete_comment(comment_id, user2)
        self.assertTrue(result["success"])
        self.created_comment_ids.remove(comment_id)

    def test_delete_comment_not_author(self):
        """删除别人的评论"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        user3 = self._create_test_user("_c")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        comment_result = self.post_lib.add_comment(post_id, user2, "别人的评论")
        comment_id = comment_result["data"]["comment_id"]
        self.created_comment_ids.append(comment_id)
        result = self.post_lib.delete_comment(comment_id, user3)
        self.assertFalse(result["success"])
        self.assertIn("无权", result["message"])

    def test_delete_comment_not_found(self):
        """删除不存在的评论"""
        user_id = self._create_test_user()
        result = self.post_lib.delete_comment(999999, user_id)
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    # ==================== 9. toggle_like_post ====================

    def test_toggle_like_post_like(self):
        """点赞帖子"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        result = self.post_lib.toggle_like_post(post_id, user2)
        self.assertTrue(result["success"])
        self.assertTrue(result["data"]["is_liked"])
        # 验证点赞数增加
        detail = self.post_lib.get_post_by_id(post_id)
        self.assertEqual(detail["data"]["like_count"], 1)

    def test_toggle_like_post_unlike(self):
        """取消点赞"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        self.post_lib.toggle_like_post(post_id, user2)  # 先点赞
        result = self.post_lib.toggle_like_post(post_id, user2)  # 再取消
        self.assertTrue(result["success"])
        self.assertFalse(result["data"]["is_liked"])
        detail = self.post_lib.get_post_by_id(post_id)
        self.assertEqual(detail["data"]["like_count"], 0)

    def test_toggle_like_post_not_found(self):
        """点赞不存在的帖子"""
        user_id = self._create_test_user()
        result = self.post_lib.toggle_like_post("non_exist", user_id)
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    # ==================== 10. toggle_like_comment ====================

    def test_toggle_like_comment_like(self):
        """点赞评论"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        comment_result = self.post_lib.add_comment(post_id, user1, "评论")
        comment_id = comment_result["data"]["comment_id"]
        self.created_comment_ids.append(comment_id)
        result = self.post_lib.toggle_like_comment(comment_id, user2)
        self.assertTrue(result["success"])
        self.assertTrue(result["data"]["is_liked"])

    def test_toggle_like_comment_unlike(self):
        """取消点赞评论"""
        user1 = self._create_test_user("_a")
        user2 = self._create_test_user("_b")
        post_result = self._create_post(user1)
        post_id = post_result["data"]["post_id"]
        comment_result = self.post_lib.add_comment(post_id, user1, "评论")
        comment_id = comment_result["data"]["comment_id"]
        self.created_comment_ids.append(comment_id)
        self.post_lib.toggle_like_comment(comment_id, user2)  # 点赞
        result = self.post_lib.toggle_like_comment(comment_id, user2)  # 取消
        self.assertTrue(result["success"])
        self.assertFalse(result["data"]["is_liked"])

    def test_toggle_like_comment_not_found(self):
        """点赞不存在的评论"""
        user_id = self._create_test_user()
        result = self.post_lib.toggle_like_comment(999999, user_id)
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    # ==================== 11. AI 审核 Mock 测试 ====================

    @patch("backend.libs.post_library.requests.get")
    @patch("backend.libs.post_library.detect_species")
    def test_ai_audit_cat_pass(self, mock_detect, mock_get):
        """AI审核：猫图片 -> status=1（通过）"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"fake_cat"
        mock_get.return_value = mock_resp
        mock_detect.return_value = {"success": True, "category": "cat", "breed": "tabby", "confidence": 0.95}

        user_id = self._create_test_user()
        result = self.post_lib.create_post(
            user_id, "AI测试-猫", json.dumps(["http://example.com/cat.jpg"])
        )
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 1)

    @patch("backend.libs.post_library.requests.get")
    @patch("backend.libs.post_library.detect_species")
    def test_ai_audit_dog_pass(self, mock_detect, mock_get):
        """AI审核：狗图片 -> status=1（通过）"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"fake_dog"
        mock_get.return_value = mock_resp
        mock_detect.return_value = {"success": True, "category": "dog", "breed": "labrador", "confidence": 0.90}

        user_id = self._create_test_user()
        result = self.post_lib.create_post(
            user_id, "AI测试-狗", json.dumps(["http://example.com/dog.jpg"])
        )
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 1)

    @patch("backend.libs.post_library.requests.get")
    @patch("backend.libs.post_library.detect_species")
    def test_ai_audit_other_pending(self, mock_detect, mock_get):
        """AI审核：非猫狗图片 -> status=0（待审核）"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"fake_landscape"
        mock_get.return_value = mock_resp
        mock_detect.return_value = {"success": True, "category": "other", "breed": "unknown", "confidence": 0.0}

        user_id = self._create_test_user()
        result = self.post_lib.create_post(
            user_id, "AI测试-风景", json.dumps(["http://example.com/landscape.jpg"])
        )
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 0)

    @patch("backend.libs.post_library.requests.get")
    @patch("backend.libs.post_library.detect_species")
    def test_ai_audit_exception_fallback(self, mock_detect, mock_get):
        """AI审核异常 -> 降级为 status=1（通过）"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"fake"
        mock_get.return_value = mock_resp
        mock_detect.side_effect = Exception("AI超时")

        user_id = self._create_test_user()
        result = self.post_lib.create_post(
            user_id, "AI测试-异常", json.dumps(["http://example.com/img.jpg"])
        )
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 1)

    def test_ai_audit_no_image(self):
        """无图片 -> status=1（不触发AI）"""
        user_id = self._create_test_user()
        result = self.post_lib.create_post(user_id, "无图片帖子")
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 1)


# ==================== 真实 AI 集成测试 ====================

@unittest.skipUnless(_ai_service_available(), "AI 服务未启动（localhost:8001），跳过真实 AI 测试")
class TestPostLibraryAIReal(unittest.TestCase):
    """真实 AI 服务集成测试（需提前启动 flask_api）"""

    @classmethod
    def setUpClass(cls):
        cls.post_lib = PostLibrary()
        cls.user_lib = UserLibrary()
        cls.img_server = TestImageServer()
        cls.img_server.start()
        cls._cleanup_all_test_data()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all_test_data()
        cls.img_server.stop()

    def setUp(self):
        self.created_post_ids = []
        self.created_user_ids = []

    def tearDown(self):
        self._cleanup_created_data()

    @classmethod
    def _cleanup_all_test_data(cls):
        if cls.post_lib.db.open_database():
            cls.post_lib.db.execute_raw_sql(
                "DELETE FROM t_post WHERE user_id LIKE %s", ("test_post_user_%",)
            )
            cls.post_lib.db.execute_raw_sql(
                "DELETE FROM t_like WHERE user_id LIKE %s", ("test_post_user_%",)
            )
            cls.post_lib.db.close_database()
        if cls.user_lib.db.open_database():
            cls.user_lib.db.execute_raw_sql(
                "DELETE FROM t_user WHERE user_id LIKE %s", ("test_post_user_%",)
            )
            cls.user_lib.db.close_database()

    def _cleanup_created_data(self):
        if self.post_lib.db.open_database():
            for post_id in self.created_post_ids:
                self.post_lib.db.execute_raw_sql(
                    "DELETE FROM t_post WHERE post_id = %s", (post_id,)
                )
            self.post_lib.db.close_database()
        if self.user_lib.db.open_database():
            for user_id in self.created_user_ids:
                self.user_lib.db.execute_raw_sql(
                    "DELETE FROM t_user WHERE user_id = %s", (user_id,)
                )
            self.user_lib.db.close_database()

    def _create_test_user(self, suffix="") -> str:
        user_id = f"test_post_user_{uuid.uuid4().hex[:6]}{suffix}"
        result = self.user_lib.register_user(user_id, f"真实AI测试用户{suffix}", role=1)
        self.assertTrue(result["success"])
        self.created_user_ids.append(user_id)
        return user_id

    def test_ai_real_cat_pass(self):
        """真实 AI：猫图片 -> status=1"""
        user_id = self._create_test_user()
        cat_url = self.img_server.get_url("虎斑猫.jpg")
        result = self.post_lib.create_post(
            user_id, "真实AI测试-猫", json.dumps([cat_url])
        )
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 1)
        print(f"  [真实AI-猫] status={detail['data']['status']}")

    def test_ai_real_dog_pass(self):
        """真实 AI：狗图片 -> status=1"""
        user_id = self._create_test_user()
        dog_url = self.img_server.get_url("金毛寻回犬.jpg")
        result = self.post_lib.create_post(
            user_id, "真实AI测试-狗", json.dumps([dog_url])
        )
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 1)
        print(f"  [真实AI-狗] status={detail['data']['status']}")

    def test_ai_real_other_pending(self):
        """真实 AI：小鸟（非猫狗）-> status=0"""
        user_id = self._create_test_user()
        bird_url = self.img_server.get_url("小鸟.jpg")
        result = self.post_lib.create_post(
            user_id, "真实AI测试-小鸟", json.dumps([bird_url])
        )
        self.assertTrue(result["success"])
        self.created_post_ids.append(result["data"]["post_id"])
        detail = self.post_lib.get_post_by_id(result["data"]["post_id"])
        self.assertEqual(detail["data"]["status"], 0)
        print(f"  [真实AI-小鸟] status={detail['data']['status']}（非猫狗，待审核）")

if __name__ == "__main__":
    unittest.main(verbosity=2)
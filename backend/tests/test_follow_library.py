# backend/tests/test_follow_library.py
"""
FollowLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_follow_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_follow 表已存在
"""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.follow_library import FollowLibrary
from backend.libs.user_library import UserLibrary

PREFIX = "test_follow_user_"


class TestFollowLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lib = FollowLibrary()
        cls.user_lib = UserLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.user_ids = []

    def tearDown(self):
        if not self.user_ids:
            return
        if self.lib.db.open_database():
            for uid in self.user_ids:
                self.lib.db.execute_raw_sql(
                    "DELETE FROM t_follow WHERE from_user_id=%s OR to_user_id=%s", (uid, uid)
                )
                self.lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id=%s", (uid,))
            self.lib.db.close_database()

    @classmethod
    def _cleanup_all(cls):
        if cls.lib.db.open_database():
            cls.lib.db.execute_raw_sql(
                "DELETE FROM t_follow WHERE from_user_id LIKE %s OR to_user_id LIKE %s",
                (f"{PREFIX}%", f"{PREFIX}%")
            )
            cls.lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", (f"{PREFIX}%",))
            cls.lib.db.close_database()

    def _add_user(self) -> str:
        uid = f"{PREFIX}{uuid.uuid4().hex[:8]}"
        self.user_lib.register_user(uid, f"nick_{uuid.uuid4().hex[:6]}")
        self.user_ids.append(uid)
        return uid

    # ==================== follow_user ====================

    def test_follow_success(self):
        a, b = self._add_user(), self._add_user()
        r = self.lib.follow_user(a, b)
        self.assertTrue(r["success"])
        self.assertIsNotNone(r["data"]["follow_id"])

    def test_follow_duplicate(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        r = self.lib.follow_user(a, b)
        self.assertTrue(r["success"])
        self.assertIn("已关注", r["message"])

    def test_follow_self(self):
        a = self._add_user()
        r = self.lib.follow_user(a, a)
        self.assertFalse(r["success"])
        self.assertIn("不能关注自己", r["message"])

    def test_follow_empty_params(self):
        b = self._add_user()
        self.assertFalse(self.lib.follow_user("", b)["success"])
        self.assertFalse(self.lib.follow_user(b, "")["success"])

    def test_follow_invalid_users(self):
        a, b = self._add_user(), self._add_user()
        self.assertIn("关注者不存在", self.lib.follow_user("no_user_xxx", b)["message"])
        self.assertIn("被关注者不存在", self.lib.follow_user(a, "no_user_xxx")["message"])

    def test_follow_updates_counts(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        self.assertEqual(self.lib.get_following_count(a)["data"]["following_count"], 1)
        self.assertEqual(self.lib.get_follower_count(b)["data"]["follower_count"], 1)

    # ==================== check_follow_status ====================

    def test_check_following(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        self.assertTrue(self.lib.check_follow_status(a, b)["data"]["is_following"])

    def test_check_not_following(self):
        a, b = self._add_user(), self._add_user()
        self.assertFalse(self.lib.check_follow_status(a, b)["data"]["is_following"])

    # ==================== get_following_list ====================

    def test_following_list_success(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        r = self.lib.get_following_list(a)
        self.assertGreaterEqual(r["data"]["total"], 1)
        self.assertIn("total_pages", r["data"])

    def test_following_list_mutual_flag(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        self.lib.follow_user(b, a)
        records = self.lib.get_following_list(a)["data"]["records"]
        b_rec = next((r for r in records if r["user_id"] == b), None)
        self.assertIsNotNone(b_rec)
        self.assertTrue(b_rec["is_mutual"])

    def test_following_list_not_mutual(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        records = self.lib.get_following_list(a)["data"]["records"]
        b_rec = next((r for r in records if r["user_id"] == b), None)
        self.assertFalse(b_rec["is_mutual"])

    def test_following_list_pagination(self):
        a = self._add_user()
        for _ in range(3):
            self.lib.follow_user(a, self._add_user())
        self.assertEqual(len(self.lib.get_following_list(a, 1, 2)["data"]["records"]), 2)
        self.assertGreaterEqual(len(self.lib.get_following_list(a, 2, 2)["data"]["records"]), 1)

    def test_following_list_empty(self):
        a = self._add_user()
        self.assertEqual(self.lib.get_following_list(a)["data"]["total"], 0)

    def test_following_list_fields(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        rec = self.lib.get_following_list(a)["data"]["records"][0]
        for f in ["follow_id", "follow_time", "user_id", "nickname", "avatar_url",
                   "follower_count", "following_count", "like_count", "is_active", "is_mutual"]:
            self.assertIn(f, rec)

    # ==================== get_follower_list ====================

    def test_follower_list_success(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        r = self.lib.get_follower_list(b)
        self.assertGreaterEqual(r["data"]["total"], 1)

    def test_follower_list_following_back_flag(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        self.lib.follow_user(b, a)
        records = self.lib.get_follower_list(b)["data"]["records"]
        a_rec = next((r for r in records if r["user_id"] == a), None)
        self.assertTrue(a_rec["is_following_back"])

    def test_follower_list_pagination(self):
        b = self._add_user()
        for _ in range(3):
            self.lib.follow_user(self._add_user(), b)
        self.assertEqual(len(self.lib.get_follower_list(b, 1, 2)["data"]["records"]), 2)

    def test_follower_list_empty(self):
        b = self._add_user()
        self.assertEqual(self.lib.get_follower_list(b)["data"]["total"], 0)

    # ==================== get_following_count / get_follower_count ====================

    def test_following_count_success(self):
        a = self._add_user()
        self.lib.follow_user(a, self._add_user())
        self.assertEqual(self.lib.get_following_count(a)["data"]["following_count"], 1)

    def test_follower_count_success(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        self.assertEqual(self.lib.get_follower_count(b)["data"]["follower_count"], 1)

    def test_count_invalid_user(self):
        self.assertFalse(self.lib.get_following_count("no_user")["success"])
        self.assertFalse(self.lib.get_follower_count("no_user")["success"])

    # ==================== unfollow_user ====================

    def test_unfollow_success(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        r = self.lib.unfollow_user(a, b)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["unfollowed"])
        self.assertFalse(self.lib.check_follow_status(a, b)["data"]["is_following"])

    def test_unfollow_not_following(self):
        a, b = self._add_user(), self._add_user()
        r = self.lib.unfollow_user(a, b)
        self.assertFalse(r["success"])
        self.assertIn("尚未关注", r["message"])

    def test_unfollow_self(self):
        a = self._add_user()
        r = self.lib.unfollow_user(a, a)
        self.assertFalse(r["success"])
        self.assertIn("不能对自己操作", r["message"])

    def test_unfollow_empty_params(self):
        b = self._add_user()
        self.assertFalse(self.lib.unfollow_user("", b)["success"])
        self.assertFalse(self.lib.unfollow_user(b, "")["success"])

    def test_unfollow_invalid_user(self):
        a, b = self._add_user(), self._add_user()
        self.assertIn("关注者不存在", self.lib.unfollow_user("no_user", b)["message"])

    def test_unfollow_updates_counts(self):
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        self.lib.unfollow_user(a, b)
        self.assertEqual(self.lib.get_following_count(a)["data"]["following_count"], 0)
        self.assertEqual(self.lib.get_follower_count(b)["data"]["follower_count"], 0)

    # ==================== DB 连接失败批量覆盖 ====================

    def test_db_connection_fail(self):
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.follow_user("a", "b")["success"])
            self.assertFalse(self.lib.unfollow_user("a", "b")["success"])
            self.assertFalse(self.lib.check_follow_status("a", "b")["success"])
            self.assertFalse(self.lib.get_following_list("a")["success"])
            self.assertFalse(self.lib.get_follower_list("a")["success"])

    # ==================== 综合场景 ====================

    def test_full_lifecycle(self):
        """关注 -> 检查状态 -> 查列表 -> 取消关注 -> 状态与数量验证"""
        a, b, c = self._add_user(), self._add_user(), self._add_user()
        # A关注B和C
        self.lib.follow_user(a, b)
        self.lib.follow_user(a, c)
        self.assertEqual(self.lib.get_following_count(a)["data"]["following_count"], 2)
        self.assertTrue(self.lib.check_follow_status(a, b)["data"]["is_following"])
        # B关注A（互关）
        self.lib.follow_user(b, a)
        recs = self.lib.get_following_list(a)["data"]["records"]
        b_rec = next(r for r in recs if r["user_id"] == b)
        self.assertTrue(b_rec["is_mutual"])
        # A取消关注B
        self.lib.unfollow_user(a, b)
        self.assertFalse(self.lib.check_follow_status(a, b)["data"]["is_following"])
        self.assertEqual(self.lib.get_following_count(a)["data"]["following_count"], 1)
        # B粉丝数应减回0
        self.assertEqual(self.lib.get_follower_count(b)["data"]["follower_count"], 0)

    def test_mutual_follow_marks(self):
        """互关：A的关注列表中B标记is_mutual，B的粉丝列表中A标记is_following_back"""
        a, b = self._add_user(), self._add_user()
        self.lib.follow_user(a, b)
        self.lib.follow_user(b, a)
        following = self.lib.get_following_list(a)["data"]["records"]
        self.assertTrue(next(r for r in following if r["user_id"] == b)["is_mutual"])
        followers = self.lib.get_follower_list(b)["data"]["records"]
        self.assertTrue(next(r for r in followers if r["user_id"] == a)["is_following_back"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

# backend/tests/test_like_library.py
"""
LikeLibrary 完整测试套件（unittest 框架）
运行方式：
    cd 项目根目录
    python -m backend.tests.test_like_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_post、t_comment、t_like 表已存在
"""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.like_library import LikeLibrary
from backend.libs.user_library import UserLibrary


class TestLikeLibrary(unittest.TestCase):
    """LikeLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = LikeLibrary()
        cls.user_lib = UserLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.user_ids = []
        self.post_ids = []
        self.comment_ids = []

    def tearDown(self):
        if not (self.user_ids or self.post_ids or self.comment_ids):
            return
        db = self.lib.db
        try:
            if db.connection is None:
                if not db.open_database():
                    return
                need_close = True
            else:
                need_close = False
            for uid in self.user_ids:
                db.execute_raw_sql("DELETE FROM t_like WHERE user_id = %s", (uid,))
                db.execute_raw_sql("DELETE FROM t_comment WHERE user_id = %s", (uid,))
                db.execute_raw_sql("DELETE FROM t_post WHERE user_id = %s", (uid,))
                db.execute_raw_sql("DELETE FROM t_user WHERE user_id = %s", (uid,))
            for post_id in self.post_ids:
                db.execute_raw_sql("DELETE FROM t_like WHERE target_id = %s AND target_type = 'post'", (post_id,))
                db.execute_raw_sql("DELETE FROM t_comment WHERE post_id = %s", (post_id,))
                db.execute_raw_sql("DELETE FROM t_post WHERE post_id = %s", (post_id,))
            for cid in self.comment_ids:
                db.execute_raw_sql("DELETE FROM t_like WHERE target_id = %s AND target_type = 'comment'", (str(cid),))
                db.execute_raw_sql("DELETE FROM t_comment WHERE comment_id = %s", (cid,))
            if need_close:
                db.close_database()
        except Exception as e:
            print(f"[tearDown 警告] 清理失败: {e}")
            try:
                db.close_database()
            except:
                pass

    @classmethod
    def _cleanup_all(cls):
        db = cls.lib.db
        try:
            if db.connection is None:
                if not db.open_database():
                    return
                need_close = True
            else:
                need_close = False
            db.execute_raw_sql("DELETE FROM t_like WHERE user_id LIKE %s", ("test_like_%",))
            db.execute_raw_sql("DELETE FROM t_comment WHERE user_id LIKE %s", ("test_like_%",))
            db.execute_raw_sql("DELETE FROM t_post WHERE user_id LIKE %s", ("test_like_%",))
            db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", ("test_like_%",))
            if need_close:
                db.close_database()
        except Exception as e:
            print(f"[_cleanup_all 警告] 清理失败: {e}")

    # ---- 辅助方法 ----

    def _add_user(self, points=500):
        """注册测试用户并返回 user_id"""
        uid = f"test_like_{uuid.uuid4().hex[:8]}"
        r = self.user_lib.register_user(uid, f"nick_{uid[:8]}",
                                          avatar_url="http://x.com/a.jpg", role=1)
        if not r.get("success"):
            self.user_lib.delete_user(uid)
            r = self.user_lib.register_user(uid, f"nick_{uid[:8]}",
                                              avatar_url="http://x.com/a.jpg", role=1)
        self.user_ids.append(uid)
        return uid

    def _add_post(self, user_id, status=1):
        """插入测试帖子并返回 post_id"""
        post_id = f"test_like_{uuid.uuid4().hex[:8]}"
        db = self.lib.db
        if db.connection is None:
            db.open_database()
            need_close = True
        else:
            need_close = False
        db.execute_raw_sql(
            "INSERT INTO t_post (post_id, user_id, content, status, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (post_id, user_id, "测试帖子内容", status)
        )
        if need_close:
            db.close_database()
        self.post_ids.append(post_id)
        return post_id

    def _add_comment(self, post_id, user_id):
        """插入测试评论并返回 comment_id"""
        db = self.lib.db
        if db.connection is None:
            db.open_database()
            need_close = True
        else:
            need_close = False
        db.execute_raw_sql(
            "INSERT INTO t_comment (post_id, user_id, content, created_at) VALUES (%s, %s, %s, NOW())",
            (post_id, user_id, "测试评论内容")
        )
        cid = db.get_last_insert_id()
        if need_close:
            db.close_database()
        self.comment_ids.append(cid)
        return cid

    # ==================== toggle_like_post ====================

    def test_like_post_success(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        r = self.lib.toggle_like_post(post_id, user_a)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["is_liked"])
        self.assertIn("点赞成功", r["message"])

    def test_like_post_cancel(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        self.lib.toggle_like_post(post_id, user_a)  # 点赞
        r = self.lib.toggle_like_post(post_id, user_a)  # 取消
        self.assertTrue(r["success"])
        self.assertFalse(r["data"]["is_liked"])
        self.assertIn("取消点赞", r["message"])

    def test_like_post_not_found(self):
        user_a = self._add_user()
        r = self.lib.toggle_like_post("fake_post", user_a)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_like_post_invisible(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b, status=0)
        r = self.lib.toggle_like_post(post_id, user_a)
        self.assertFalse(r["success"])
        self.assertIn("不可见", r["message"])

    # ==================== toggle_like_comment ====================

    def test_like_comment_success(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        r = self.lib.toggle_like_comment(comment_id, user_a)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["is_liked"])
        self.assertIn("点赞成功", r["message"])

    def test_like_comment_cancel(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        self.lib.toggle_like_comment(comment_id, user_a)
        r = self.lib.toggle_like_comment(comment_id, user_a)
        self.assertTrue(r["success"])
        self.assertFalse(r["data"]["is_liked"])
        self.assertIn("取消点赞", r["message"])

    def test_like_comment_not_found(self):
        user_a = self._add_user()
        r = self.lib.toggle_like_comment(999999, user_a)
        self.assertFalse(r["success"])
        self.assertIn("评论不存在", r["message"])

    def test_like_comment_post_invisible(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b, status=0)
        comment_id = self._add_comment(post_id, user_c)
        r = self.lib.toggle_like_comment(comment_id, user_a)
        self.assertFalse(r["success"])
        self.assertIn("不可见", r["message"])

    # ==================== get_post_like_count ====================

    def test_get_post_like_count(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        self.lib.toggle_like_post(post_id, user_a)
        r = self.lib.get_post_like_count(post_id)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["count"], 1)

    def test_get_post_like_count_zero(self):
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        r = self.lib.get_post_like_count(post_id)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["count"], 0)

    # ==================== get_comment_like_count ====================

    def test_get_comment_like_count(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        self.lib.toggle_like_comment(comment_id, user_a)
        r = self.lib.get_comment_like_count(comment_id)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["count"], 1)

    def test_get_comment_like_count_zero(self):
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        r = self.lib.get_comment_like_count(comment_id)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["count"], 0)

    # ==================== check_user_liked_post ====================

    def test_check_liked_post_true(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        self.lib.toggle_like_post(post_id, user_a)
        r = self.lib.check_user_liked_post(user_a, post_id)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["is_liked"])

    def test_check_liked_post_false(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        r = self.lib.check_user_liked_post(user_a, post_id)
        self.assertTrue(r["success"])
        self.assertFalse(r["data"]["is_liked"])

    # ==================== check_user_liked_comment ====================

    def test_check_liked_comment_true(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        self.lib.toggle_like_comment(comment_id, user_a)
        r = self.lib.check_user_liked_comment(user_a, comment_id)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["is_liked"])

    def test_check_liked_comment_false(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        r = self.lib.check_user_liked_comment(user_a, comment_id)
        self.assertTrue(r["success"])
        self.assertFalse(r["data"]["is_liked"])

    # ==================== get_user_liked_list ====================

    def test_get_user_liked_list(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        self.lib.toggle_like_post(post_id, user_a)
        self.lib.toggle_like_comment(comment_id, user_a)
        r = self.lib.get_user_liked_list(user_a, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 2)
        self.assertGreaterEqual(len(r["data"]["items"]), 2)
        types = [i["target_type"] for i in r["data"]["items"]]
        self.assertIn("post", types)
        self.assertIn("comment", types)

    def test_get_user_liked_list_pagination(self):
        user_a = self._add_user()
        user_b = self._add_user()
        for _ in range(3):
            post_id = self._add_post(user_b)
            self.lib.toggle_like_post(post_id, user_a)
        r = self.lib.get_user_liked_list(user_a, page=1, page_size=2)
        self.assertEqual(len(r["data"]["items"]), 2)
        r2 = self.lib.get_user_liked_list(user_a, page=2, page_size=2)
        self.assertGreaterEqual(len(r2["data"]["items"]), 1)

    # ==================== get_post_liked_users ====================

    def test_get_post_liked_users(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        self.lib.toggle_like_post(post_id, user_a)
        r = self.lib.get_post_liked_users(post_id, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 1)
        user_ids = [u["user_id"] for u in r["data"]["users"]]
        self.assertIn(user_a, user_ids)

    def test_get_post_liked_users_pagination(self):
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)
        self.lib.toggle_like_post(post_id, user_a)
        r = self.lib.get_post_liked_users(post_id, page=1, page_size=1)
        self.assertEqual(len(r["data"]["users"]), 1)

    # ==================== get_comment_liked_users ====================

    def test_get_comment_liked_users(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        self.lib.toggle_like_comment(comment_id, user_a)
        r = self.lib.get_comment_liked_users(comment_id, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 1)
        user_ids = [u["user_id"] for u in r["data"]["users"]]
        self.assertIn(user_a, user_ids)

    def test_get_comment_liked_users_pagination(self):
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)
        self.lib.toggle_like_comment(comment_id, user_a)
        r = self.lib.get_comment_liked_users(comment_id, page=1, page_size=1)
        self.assertEqual(len(r["data"]["users"]), 1)

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.toggle_like_post("p", "u")["success"])
            self.assertFalse(self.lib.toggle_like_comment(1, "u")["success"])
            self.assertFalse(self.lib.get_post_like_count("p")["success"])
            self.assertFalse(self.lib.get_comment_like_count(1)["success"])
            self.assertFalse(self.lib.check_user_liked_post("u", "p")["success"])
            self.assertFalse(self.lib.check_user_liked_comment("u", 1)["success"])
            self.assertFalse(self.lib.get_user_liked_list("u")["success"])
            self.assertFalse(self.lib.get_post_liked_users("p")["success"])
            self.assertFalse(self.lib.get_comment_liked_users(1)["success"])

    # ==================== 综合业务场景 ====================

    def test_full_like_lifecycle(self):
        """完整生命周期：点赞帖子 → 取消 → 再点赞 → 查状态 → 查数量 → 查用户列表"""
        user_a = self._add_user()
        user_b = self._add_user()
        post_id = self._add_post(user_b)

        # 点赞
        r = self.lib.toggle_like_post(post_id, user_a)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["is_liked"])

        # 取消
        r = self.lib.toggle_like_post(post_id, user_a)
        self.assertFalse(r["data"]["is_liked"])

        # 再点赞
        r = self.lib.toggle_like_post(post_id, user_a)
        self.assertTrue(r["data"]["is_liked"])

        # 查状态
        r = self.lib.check_user_liked_post(user_a, post_id)
        self.assertTrue(r["data"]["is_liked"])

        # 查数量
        r = self.lib.get_post_like_count(post_id)
        self.assertEqual(r["data"]["count"], 1)

        # 查用户列表
        r = self.lib.get_post_liked_users(post_id)
        self.assertIn(user_a, [u["user_id"] for u in r["data"]["users"]])

    def test_post_and_comment_like_together(self):
        """同时点赞帖子和评论"""
        user_a = self._add_user()
        user_b = self._add_user()
        user_c = self._add_user()
        post_id = self._add_post(user_b)
        comment_id = self._add_comment(post_id, user_c)

        self.lib.toggle_like_post(post_id, user_a)
        self.lib.toggle_like_comment(comment_id, user_a)

        r = self.lib.get_user_liked_list(user_a)
        self.assertEqual(r["data"]["total"], 2)

        r_post = self.lib.get_post_liked_users(post_id)
        self.assertIn(user_a, [u["user_id"] for u in r_post["data"]["users"]])

        r_comment = self.lib.get_comment_liked_users(comment_id)
        self.assertIn(user_a, [u["user_id"] for u in r_comment["data"]["users"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
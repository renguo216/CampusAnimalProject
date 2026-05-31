# backend/tests/test_comment_library.py
"""
CommentLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_comment_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_post、t_comment、t_like 表已存在
"""

import os
import sys
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.comment_library import CommentLibrary
from backend.libs.post_library import PostLibrary
from backend.libs.user_library import UserLibrary

PREFIX = "test_cmt_"


class TestCommentLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lib = CommentLibrary()
        cls.post_lib = PostLibrary()
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
        if not (self.user_ids or self.post_ids):
            return
        if self.lib.db.open_database():
            for cid in self.comment_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_like WHERE target_id=%s", (str(cid),))
            for pid in self.post_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_comment WHERE post_id=%s", (pid,))
                self.lib.db.execute_raw_sql("DELETE FROM t_post WHERE post_id=%s", (pid,))
            for uid in self.user_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id=%s", (uid,))
            self.lib.db.close_database()

    @classmethod
    def _cleanup_all(cls):
        if cls.lib.db.open_database():
            cls.lib.db.execute_raw_sql("DELETE FROM t_like WHERE user_id LIKE %s", (f"{PREFIX}%",))
            cls.lib.db.execute_raw_sql("DELETE FROM t_comment WHERE user_id LIKE %s", (f"{PREFIX}%",))
            cls.lib.db.execute_raw_sql("DELETE FROM t_post WHERE user_id LIKE %s", (f"{PREFIX}%",))
            cls.lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", (f"{PREFIX}%",))
            cls.lib.db.close_database()

    # ---- 辅助 ----

    def _add_user(self, role=1) -> str:
        uid = f"{PREFIX}user_{uuid.uuid4().hex[:8]}"
        self.user_lib.register_user(uid, f"测试_{uuid.uuid4().hex[:6]}", role=role)
        self.user_ids.append(uid)
        return uid

    def _add_post(self, user_id=None) -> str:
        uid = user_id or self._add_user()
        r = self.post_lib.create_post(uid, "测试帖子内容")
        if not r.get("success"):
            raise RuntimeError(f"创建帖子失败: {r}")
        pid = r["data"]["post_id"]
        self.post_ids.append(pid)
        return pid

    def _add_comment(self, post_id, user_id=None, content="测试评论", parent_id=None) -> int:
        uid = user_id or self._add_user()
        r = self.lib.create_comment(post_id, uid, content, parent_id)
        if r.get("success"):
            self.comment_ids.append(r["data"]["comment_id"])
        return r

    # ==================== create_comment ====================

    def test_create_success(self):
        pid = self._add_post()
        r = self._add_comment(pid)
        self.assertTrue(r["success"])
        self.assertIsNotNone(r["data"]["comment_id"])
        self.assertEqual(r["data"]["post_id"], pid)
        self.assertEqual(r["data"]["like_count"], 0)

    def test_create_reply(self):
        pid = self._add_post()
        parent = self._add_comment(pid)
        r = self._add_comment(pid, content="回复内容", parent_id=parent["data"]["comment_id"])
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["parent_comment_id"], parent["data"]["comment_id"])

    def test_create_empty_params(self):
        pid = self._add_post()
        self.assertFalse(self.lib.create_comment("", "u", "c")["success"])
        self.assertFalse(self.lib.create_comment(pid, "", "c")["success"])
        self.assertFalse(self.lib.create_comment(pid, "u", "")["success"])

    def test_create_post_not_exists(self):
        self.assertFalse(self.lib.create_comment("no_post", self._add_user(), "c")["success"])

    def test_create_parent_not_exists(self):
        pid = self._add_post()
        r = self.lib.create_comment(pid, self._add_user(), "c", parent_comment_id=999999)
        self.assertFalse(r["success"])
        self.assertIn("父评论", r["message"])

    # ==================== reply_comment ====================

    def test_reply_delegates_to_create(self):
        pid = self._add_post()
        parent = self._add_comment(pid)
        r = self.lib.reply_comment(pid, self._add_user(), "回复", parent["data"]["comment_id"])
        self.assertTrue(r["success"])

    # ==================== get_comment_by_id ====================

    def test_get_by_id_success(self):
        pid = self._add_post()
        r = self._add_comment(pid, content="查我")
        d = self.lib.get_comment_by_id(r["data"]["comment_id"])["data"]
        self.assertEqual(d["content"], "查我")
        self.assertEqual(d["post_id"], pid)
        for f in ["comment_id", "post_id", "user_id", "content", "parent_comment_id", "like_count", "created_at"]:
            self.assertIn(f, d)

    def test_get_by_id_not_exists(self):
        self.assertFalse(self.lib.get_comment_by_id(999999)["success"])

    def test_get_by_id_empty(self):
        self.assertFalse(self.lib.get_comment_by_id(None)["success"])

    # ==================== get_post_comments ====================

    def test_get_post_comments_success(self):
        pid = self._add_post()
        for _ in range(3):
            self._add_comment(pid)
        r = self.lib.get_post_comments(pid)
        self.assertEqual(r["data"]["total"], 3)
        self.assertEqual(len(r["data"]["comments"]), 3)

    def test_get_post_comments_empty(self):
        self.assertEqual(self.lib.get_post_comments("no_post")["data"]["total"], 0)

    def test_get_post_comments_pagination(self):
        pid = self._add_post()
        for _ in range(3):
            self._add_comment(pid)
        self.assertEqual(len(self.lib.get_post_comments(pid, 1, 2)["data"]["comments"]), 2)
        self.assertGreaterEqual(len(self.lib.get_post_comments(pid, 2, 2)["data"]["comments"]), 1)

    def test_get_post_comments_order_asc(self):
        pid = self._add_post()
        self._add_comment(pid, content="先")
        self._add_comment(pid, content="后")
        apps = self.lib.get_post_comments(pid)["data"]["comments"]
        self.assertLessEqual(
            datetime.strptime(apps[0]["created_at"], "%Y-%m-%d %H:%M:%S"),
            datetime.strptime(apps[1]["created_at"], "%Y-%m-%d %H:%M:%S")
        )

    def test_get_post_comments_empty_param(self):
        self.assertFalse(self.lib.get_post_comments("")["success"])

    # ==================== get_user_comments ====================

    def test_get_user_comments_success(self):
        uid = self._add_user()
        for _ in range(2):
            self._add_comment(self._add_post(uid), uid)
        r = self.lib.get_user_comments(uid)
        self.assertEqual(r["data"]["total"], 2)

    def test_get_user_comments_empty(self):
        self.assertEqual(self.lib.get_user_comments("no_user")["data"]["total"], 0)

    def test_get_user_comments_pagination(self):
        uid = self._add_user()
        for _ in range(3):
            self._add_comment(self._add_post(uid), uid)
        self.assertEqual(len(self.lib.get_user_comments(uid, 1, 2)["data"]["comments"]), 2)

    def test_get_user_comments_order_desc(self):
        uid = self._add_user()
        self._add_comment(self._add_post(uid), uid, content="先")
        self._add_comment(self._add_post(uid), uid, content="后")
        apps = self.lib.get_user_comments(uid)["data"]["comments"]
        self.assertGreaterEqual(
            datetime.strptime(apps[0]["created_at"], "%Y-%m-%d %H:%M:%S"),
            datetime.strptime(apps[1]["created_at"], "%Y-%m-%d %H:%M:%S")
        )

    def test_get_user_comments_empty_param(self):
        self.assertFalse(self.lib.get_user_comments("")["success"])
    # ==================== get_comment_replies ====================

    def test_get_replies_success(self):
        pid = self._add_post()
        parent = self._add_comment(pid)
        for _ in range(2):
            self._add_comment(pid, content="回复", parent_id=parent["data"]["comment_id"])
        r = self.lib.get_comment_replies(parent["data"]["comment_id"])
        self.assertEqual(len(r["data"]["replies"]), 2)

    def test_get_replies_empty(self):
        self.assertEqual(len(self.lib.get_comment_replies(999999)["data"]["replies"]), 0)

    def test_get_replies_empty_param(self):
        self.assertFalse(self.lib.get_comment_replies(None)["success"])

    # ==================== toggle_comment_like ====================

    def test_like_then_unlike(self):
        pid = self._add_post()
        r = self._add_comment(pid)
        cid = r["data"]["comment_id"]
        uid = r["data"]["user_id"]

        liker = self._add_user()
        r1 = self.lib.toggle_comment_like(cid, liker)
        self.assertTrue(r1["success"])
        self.assertTrue(r1["data"]["is_liked"])

        r2 = self.lib.toggle_comment_like(cid, liker)
        self.assertTrue(r2["success"])
        self.assertFalse(r2["data"]["is_liked"])

    def test_like_comment_not_exists(self):
        self.assertFalse(self.lib.toggle_comment_like(999999, self._add_user())["success"])

    def test_like_empty_params(self):
        self.assertFalse(self.lib.toggle_comment_like(None, "u")["success"])
        self.assertFalse(self.lib.toggle_comment_like(1, "")["success"])

    # ==================== check_user_liked_post / comment ====================

    def test_check_liked_post(self):
        pid = self._add_post()
        uid = self._add_user()
        r = self.lib.check_user_liked_post(uid, pid)
        self.assertTrue(r["success"])
        self.assertFalse(r["data"]["is_liked"])

    def test_check_liked_comment(self):
        pid = self._add_post()
        r = self._add_comment(pid)
        uid = self._add_user()
        r2 = self.lib.check_user_liked_comment(uid, r["data"]["comment_id"])
        self.assertTrue(r2["success"])
        self.assertFalse(r2["data"]["is_liked"])

    # ==================== delete_comment ====================

    def test_delete_own_success(self):
        pid = self._add_post()
        uid = self._add_user()
        r = self._add_comment(pid, uid)
        cid = r["data"]["comment_id"]
        dr = self.lib.delete_comment(cid, uid)
        self.assertTrue(dr["success"])
        self.assertFalse(self.lib.get_comment_by_id(cid)["success"])

    def test_delete_other_fail(self):
        pid = self._add_post()
        r = self._add_comment(pid)
        self.assertFalse(self.lib.delete_comment(r["data"]["comment_id"], self._add_user())["success"])
        self.assertIn("无权", self.lib.delete_comment(r["data"]["comment_id"], self._add_user())["message"])

    def test_delete_not_exists(self):
        self.assertFalse(self.lib.delete_comment(999999, self._add_user())["success"])

    def test_delete_empty_params(self):
        self.assertFalse(self.lib.delete_comment(None, "u")["success"])
        self.assertFalse(self.lib.delete_comment(1, "")["success"])

    # ==================== admin_delete_comment ====================

    def test_admin_delete_success(self):
        pid = self._add_post()
        r = self._add_comment(pid)
        admin = self._add_user(role=3)
        dr = self.lib.admin_delete_comment(r["data"]["comment_id"], admin)
        self.assertTrue(dr["success"])
        self.assertFalse(self.lib.get_comment_by_id(r["data"]["comment_id"])["success"])

    def test_admin_delete_not_exists(self):
        admin = self._add_user(role=3)
        self.assertFalse(self.lib.admin_delete_comment(999999, admin)["success"])

    def test_admin_delete_not_admin(self):
        pid = self._add_post()
        r = self._add_comment(pid)
        self.assertFalse(self.lib.admin_delete_comment(r["data"]["comment_id"], self._add_user())["success"])
        self.assertIn("仅管理员", self.lib.admin_delete_comment(r["data"]["comment_id"], self._add_user())["message"])

    def test_admin_delete_empty_params(self):
        self.assertFalse(self.lib.admin_delete_comment(None, "u")["success"])
        self.assertFalse(self.lib.admin_delete_comment(1, "")["success"])

    # ==================== DB 连接失败批量覆盖 ====================

    def test_db_connection_fail(self):
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.create_comment("p", "u", "c")["success"])
            self.assertFalse(self.lib.delete_comment(1, "u")["success"])
            self.assertFalse(self.lib.admin_delete_comment(1, "u")["success"])
            self.assertFalse(self.lib.get_post_comments("p")["success"])
            self.assertFalse(self.lib.get_user_comments("u")["success"])
            self.assertFalse(self.lib.get_comment_replies(1)["success"])
            self.assertFalse(self.lib.toggle_comment_like(1, "u")["success"])
            self.assertFalse(self.lib.check_user_liked_post("u", "p")["success"])
            self.assertFalse(self.lib.check_user_liked_comment("u", 1)["success"])

    # ==================== 综合场景 ====================

    def test_full_lifecycle(self):
        """发帖 -> 评论 -> 回复 -> 点赞 -> 取消赞 -> 删回复 -> 删评论"""
        uid = self._add_user()
        other = self._add_user()
        pid = self._add_post(uid)

        # 评论
        c1 = self._add_comment(pid, uid, "顶级评论")
        self.assertTrue(c1["success"])

        # 回复
        c2 = self._add_comment(pid, other, "回复", c1["data"]["comment_id"])
        self.assertTrue(c2["success"])

        # 点赞
        lr = self.lib.toggle_comment_like(c1["data"]["comment_id"], other)
        self.assertTrue(lr["data"]["is_liked"])

        # 取消赞
        ur = self.lib.toggle_comment_like(c1["data"]["comment_id"], other)
        self.assertFalse(ur["data"]["is_liked"])

        # 删回复
        self.assertTrue(self.lib.delete_comment(c2["data"]["comment_id"], other)["success"])
        self.assertEqual(len(self.lib.get_comment_replies(c1["data"]["comment_id"])["data"]["replies"]), 0)

        # 删评论
        self.assertTrue(self.lib.delete_comment(c1["data"]["comment_id"], uid)["success"])
        self.assertEqual(self.lib.get_post_comments(pid)["data"]["total"], 0)

    def test_admin_delete_others_comment(self):
        """管理员可删除任意评论"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_post(uid)
        c = self._add_comment(pid, uid)
        self.assertTrue(self.lib.admin_delete_comment(c["data"]["comment_id"], admin)["success"])

    def test_delete_reduces_post_comment_count(self):
        """删除评论后帖子 comment_count 减少"""
        uid = self._add_user()
        pid = self._add_post(uid)
        self._add_comment(pid, uid)
        self._add_comment(pid, uid)
        post = self.post_lib.get_post_by_id(pid)
        count_before = post["data"]["comment_count"]
        self.lib.delete_comment(
            self.lib.get_post_comments(pid)["data"]["comments"][0]["comment_id"], uid
        )
        post_after = self.post_lib.get_post_by_id(pid)
        self.assertEqual(post_after["data"]["comment_count"], count_before - 1)

    def test_like_increases_counts(self):
        """点赞后评论 like_count 和用户 like_count 都增加"""
        pid = self._add_post()
        author = self._add_user()
        c = self._add_comment(pid, author)
        liker = self._add_user()
        self.lib.toggle_comment_like(c["data"]["comment_id"], liker)
        comment = self.lib.get_comment_by_id(c["data"]["comment_id"])["data"]
        self.assertEqual(comment["like_count"], 1)
        # 作者的 like_count 也应 +1
        from backend.libs.user_library import UserLibrary
        author_info = UserLibrary().get_user_by_account(author)["data"]
        self.assertGreaterEqual(author_info["like_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
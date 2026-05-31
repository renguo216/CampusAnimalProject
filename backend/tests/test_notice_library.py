# backend/tests/test_notice_library.py
"""
NoticeLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_notice_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_notice 表已存在
"""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.notice_library import NoticeLibrary

PREFIX = "test_notice_"


class TestNoticeLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lib = NoticeLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.notice_ids = []

    def tearDown(self):
        if not self.notice_ids:
            return
        if self.lib.db.open_database():
            for nid in self.notice_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_notice WHERE notice_id=%s", (nid,))
            self.lib.db.close_database()

    @classmethod
    def _cleanup_all(cls):
        if cls.lib.db.open_database():
            cls.lib.db.execute_raw_sql("DELETE FROM t_notice WHERE title LIKE %s", (f"{PREFIX}%",))
            cls.lib.db.close_database()

    def _add_notice(self, **kw) -> str:
        kw.setdefault("title", f"{PREFIX}{uuid.uuid4().hex[:8]}")
        kw.setdefault("content", "测试内容")
        kw.setdefault("is_top", 0)
        r = self.lib.create_notice(**kw)
        if not r.get("success"):
            raise RuntimeError(f"创建公告失败: {r}")
        nid = r["data"]["notice_id"]
        self.notice_ids.append(nid)
        return nid

    # ==================== create_notice ====================

    def test_create_normal(self):
        r = self.lib.create_notice(f"{PREFIX}普通", "内容", is_top=0)
        self.assertTrue(r["success"])
        self.assertIn("notice_id", r["data"])

    def test_create_top(self):
        r = self.lib.create_notice(f"{PREFIX}置顶", "内容", is_top=1)
        self.assertTrue(r["success"])
        self.notice_ids.append(r["data"]["notice_id"])

    def test_create_empty_title(self):
        self.assertFalse(self.lib.create_notice("", "内容")["success"])
        self.assertFalse(self.lib.create_notice("   ", "内容")["success"])

    # ==================== get_notice_by_id ====================

    def test_get_by_id_success(self):
        nid = self._add_notice(title="详情测试")
        d = self.lib.get_notice_by_id(nid)["data"]
        self.assertEqual(d["notice_id"], nid)
        self.assertEqual(d["title"], "详情测试")
        for f in ["notice_id", "title", "content", "is_top", "created_at"]:
            self.assertIn(f, d)

    def test_get_by_id_not_exists(self):
        self.assertFalse(self.lib.get_notice_by_id("no_xxx")["success"])

    # ==================== get_all_notices ====================

    def test_get_all_success(self):
        self._add_notice()
        r = self.lib.get_all_notices()
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 1)
        self.assertIn("notices", r["data"])

    def test_get_all_top_first(self):
        self._add_notice(title="普通A", is_top=0)
        self._add_notice(title="置顶B", is_top=1)
        notices = self.lib.get_all_notices()["data"]["notices"]
        self.assertEqual(notices[0]["is_top"], 1)

    def test_get_all_pagination(self):
        for _ in range(3):
            self._add_notice()
        self.assertEqual(len(self.lib.get_all_notices(1, 2)["data"]["notices"]), 2)
        self.assertGreaterEqual(len(self.lib.get_all_notices(2, 2)["data"]["notices"]), 1)

    def test_get_all_order_by(self):
        if self.lib.db.open_database():
            self.lib.db.execute_raw_sql("DELETE FROM t_notice")
            self.lib.db.close_database()
        self._add_notice(title="AAA", is_top=0)
        self._add_notice(title="ZZZ", is_top=0)
        asc = self.lib.get_all_notices(order_by="title ASC")["data"]["notices"]
        self.assertLessEqual(asc[0]["title"], asc[1]["title"])
    # ==================== get_latest_notice ====================

    def test_latest_returns_top(self):
        self._add_notice(title="普通", is_top=0)
        top_id = self._add_notice(title="置顶最新", is_top=1)
        d = self.lib.get_latest_notice()["data"]
        self.assertEqual(d["notice_id"], top_id)
        self.assertEqual(d["is_top"], 1)

    def test_latest_fallback_to_normal(self):
        if self.lib.db.open_database():
            self.lib.db.execute_raw_sql("DELETE FROM t_notice")
            self.lib.db.close_database()
        nid = self._add_notice(title="没有置顶时取我", is_top=0)
        d = self.lib.get_latest_notice()["data"]
        self.assertEqual(d["notice_id"], nid)

    def test_latest_no_notices(self):
        if self.lib.db.open_database():
            self.lib.db.execute_raw_sql("DELETE FROM t_notice")
            self.lib.db.close_database()
        self.assertFalse(self.lib.get_latest_notice()["success"])

    # ==================== update_notice ====================

    def test_update_title_and_content(self):
        nid = self._add_notice()
        self.lib.update_notice(nid, title="新标题", content="新内容")
        d = self.lib.get_notice_by_id(nid)["data"]
        self.assertEqual(d["title"], "新标题")
        self.assertEqual(d["content"], "新内容")

    def test_update_is_top(self):
        nid = self._add_notice(is_top=0)
        self.lib.update_notice(nid, is_top=1)
        self.assertEqual(self.lib.get_notice_by_id(nid)["data"]["is_top"], 1)

    def test_update_empty_title(self):
        nid = self._add_notice()
        self.assertFalse(self.lib.update_notice(nid, title="")["success"])
        self.assertFalse(self.lib.update_notice(nid, title="  ")["success"])

    def test_update_not_exists(self):
        self.assertFalse(self.lib.update_notice("no_xxx", title="x")["success"])

    def test_update_no_fields(self):
        nid = self._add_notice()
        self.assertFalse(self.lib.update_notice(nid)["success"])
        self.assertIn("没有需要更新", self.lib.update_notice(nid)["message"])

    # ==================== search_notices_by_title ====================

    def test_search_success(self):
        self._add_notice(title="可搜索的目标")
        self.assertGreaterEqual(self.lib.search_notices_by_title("可搜索")["data"]["total"], 1)

    def test_search_not_found(self):
        self.assertEqual(self.lib.search_notices_by_title("不存在xyz123")["data"]["total"], 0)

    def test_search_pagination(self):
        for _ in range(3):
            self._add_notice(title="分页搜索")
        self.assertEqual(len(self.lib.search_notices_by_title("分页搜索", 1, 2)["data"]["notices"]), 2)

    # ==================== delete_notice ====================

    def test_delete_success(self):
        nid = self._add_notice()
        self.assertTrue(self.lib.delete_notice(nid)["success"])
        self.assertFalse(self.lib.get_notice_by_id(nid)["success"])
        self.notice_ids.remove(nid)

    def test_delete_not_exists(self):
        self.assertFalse(self.lib.delete_notice("no_xxx")["success"])

    # ==================== DB 连接失败批量覆盖 ====================

    def test_db_connection_fail(self):
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.create_notice("t", "c")["success"])
            self.assertFalse(self.lib.get_notice_by_id("x")["success"])
            self.assertFalse(self.lib.get_all_notices()["success"])
            self.assertFalse(self.lib.get_latest_notice()["success"])
            self.assertFalse(self.lib.update_notice("x", title="t")["success"])
            self.assertFalse(self.lib.search_notices_by_title("x")["success"])
            self.assertFalse(self.lib.delete_notice("x")["success"])

    # ==================== 综合场景 ====================

    def test_full_lifecycle(self):
        """创建 -> 查询 -> 更新 -> 搜索 -> 删除"""
        nid = self._add_notice(title="生命周期", content="原始内容", is_top=0)
        d = self.lib.get_notice_by_id(nid)["data"]
        self.assertEqual(d["title"], "生命周期")

        self.lib.update_notice(nid, title="已更新", is_top=1)
        self.assertEqual(self.lib.get_notice_by_id(nid)["data"]["is_top"], 1)
        self.assertGreaterEqual(self.lib.search_notices_by_title("已更新")["data"]["total"], 1)

        self.lib.delete_notice(nid)
        self.assertFalse(self.lib.get_notice_by_id(nid)["success"])
        self.notice_ids.remove(nid)

    def test_top_always_first(self):
        """多条公告混合置顶/普通，置顶始终在前"""
        self._add_notice(title="普通1", is_top=0)
        self._add_notice(title="置顶1", is_top=1)
        self._add_notice(title="普通2", is_top=0)
        self._add_notice(title="置顶2", is_top=1)
        notices = self.lib.get_all_notices()["data"]["notices"]
        # 前两条都应是置顶
        self.assertEqual(notices[0]["is_top"], 1)
        self.assertEqual(notices[1]["is_top"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
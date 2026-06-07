# backend/tests/test_donation_project_library.py
"""
DonationProjectLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_donation_project_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_donation_project 表已存在
"""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.donation_project_library import DonationProjectLibrary

PREFIX = "测试项目_"


class TestDonationProjectLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lib = DonationProjectLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.project_ids = []

    def tearDown(self):
        if not self.project_ids:
            return
        if self.lib.db.open_database():
            for pid in self.project_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_donation_project WHERE project_id=%s", (pid,))
            self.lib.db.close_database()

    @classmethod
    def _cleanup_all(cls):
        if cls.lib.db.open_database():
            cls.lib.db.execute_raw_sql("DELETE FROM t_donation_project WHERE title LIKE %s", (f"{PREFIX}%",))
            cls.lib.db.close_database()

    # ---- 辅助 ----

    def _add_project(self, **kw) -> int:
        kw.setdefault("title", f"{PREFIX}{uuid.uuid4().hex[:8]}")
        kw.setdefault("description", "测试描述")
        kw.setdefault("target_amount", 1000.0)
        r = self.lib.create_project(**kw)
        if not r.get("success"):
            raise RuntimeError(f"创建项目失败: {r}")
        pid = r["data"]["project_id"]
        self.project_ids.append(pid)
        return pid

    # ==================== create_project ====================

    def test_create_success(self):
        title = f"{PREFIX}{uuid.uuid4().hex[:8]}"
        r = self.lib.create_project(title, "描述", 1000.0)
        self.assertTrue(r["success"])
        self.assertIsNotNone(r["data"]["project_id"])
        self.assertIn("created_at", r["data"])

    def test_create_empty_title(self):
        r = self.lib.create_project("", "描述", 100.0)
        self.assertFalse(r["success"])
        self.assertIn("标题不能为空", r["message"])

    def test_create_whitespace_title(self):
        r = self.lib.create_project("   ", "描述", 100.0)
        self.assertFalse(r["success"])
        self.assertIn("标题不能为空", r["message"])

    # ==================== get_project_by_id ====================

    def test_get_by_id_success(self):
        pid = self._add_project(title="详情测试")
        d = self.lib.get_project_by_id(pid)["data"]
        self.assertEqual(d["project_id"], pid)
        self.assertEqual(d["title"], "详情测试")
        self.assertEqual(d["target_amount"], 1000.0)
        self.assertEqual(d["current_amount"], 0.0)
        self.assertEqual(d["participant_count"], 0)
        self.assertEqual(d["status"], 1)
        for f in ["project_id", "title", "description", "target_amount", "current_amount",
                   "participant_count", "status", "created_at"]:
            self.assertIn(f, d)

    def test_get_by_id_not_exists(self):
        self.assertFalse(self.lib.get_project_by_id(999999)["success"])

    # ==================== update_project ====================

    def test_update_success(self):
        pid = self._add_project()
        r = self.lib.update_project(pid, {"title": "新标题", "target_amount": 2000.0})
        self.assertTrue(r["success"])
        d = self.lib.get_project_by_id(pid)["data"]
        self.assertEqual(d["title"], "新标题")
        self.assertEqual(d["target_amount"], 2000.0)

    def test_update_not_exists(self):
        self.assertFalse(self.lib.update_project(999999, {"title": "x"})["success"])

    def test_update_forbidden_fields(self):
        pid = self._add_project()
        r = self.lib.update_project(pid, {"current_amount": 9999.0, "participant_count": 999})
        self.assertFalse(r["success"])
        self.assertIn("没有需要更新", r["message"])
        # 确认确实没改
        d = self.lib.get_project_by_id(pid)["data"]
        self.assertEqual(d["current_amount"], 0.0)

    def test_update_empty_data(self):
        pid = self._add_project()
        r = self.lib.update_project(pid, {})
        self.assertFalse(r["success"])
        self.assertIn("没有需要更新", r["message"])

    def test_update_status(self):
        pid = self._add_project()
        self.lib.update_project(pid, {"status": 0})
        self.assertEqual(self.lib.get_project_by_id(pid)["data"]["status"], 0)

    # ==================== delete_project ====================

    def test_delete_success(self):
        pid = self._add_project()
        r = self.lib.delete_project(pid)
        self.assertTrue(r["success"])
        self.assertFalse(self.lib.get_project_by_id(pid)["success"])
        self.project_ids.remove(pid)

    def test_delete_not_exists(self):
        self.assertFalse(self.lib.delete_project(999999)["success"])

    # ==================== get_all_projects ====================

    def test_get_all_success(self):
        self._add_project()
        r = self.lib.get_all_projects()
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 1)
        self.assertIn("projects", r["data"])
        self.assertIn("total", r["data"])

    def test_get_all_pagination(self):
        for _ in range(3):
            self._add_project()
        p1 = self.lib.get_all_projects(page=1, page_size=2)
        self.assertEqual(len(p1["data"]["projects"]), 2)
        p2 = self.lib.get_all_projects(page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["projects"]), 1)

    def test_get_all_empty(self):
        # 清空后查
        if self.lib.db.open_database():
            self.lib.db.execute_raw_sql("DELETE FROM t_donation_project")
            self.lib.db.close_database()
        r = self.lib.get_all_projects()
        self.assertEqual(r["data"]["total"], 0)

    # ==================== get_projects_by_status ====================

    def test_get_by_status_success(self):
        pid = self._add_project()
        r1 = self.lib.get_projects_by_status(1)
        self.assertGreaterEqual(r1["data"]["total"], 1)

        self.lib.update_project(pid, {"status": 0})
        r0 = self.lib.get_projects_by_status(0)
        self.assertGreaterEqual(r0["data"]["total"], 1)

    def test_get_by_status_empty(self):
        r = self.lib.get_projects_by_status(99)
        self.assertEqual(r["data"]["total"], 0)

    def test_get_by_status_pagination(self):
        for _ in range(3):
            self._add_project()
        self.assertEqual(len(self.lib.get_projects_by_status(1, 1, 2)["data"]["projects"]), 2)

    # ==================== search_projects_by_title ====================

    def test_search_success(self):
        title = f"{PREFIX}搜索目标{uuid.uuid4().hex[:6]}"
        self._add_project(title=title)
        r = self.lib.search_projects_by_title("搜索目标")
        self.assertGreaterEqual(r["data"]["total"], 1)

    def test_search_not_found(self):
        r = self.lib.search_projects_by_title("不存在关键字xyz123")
        self.assertEqual(r["data"]["total"], 0)

    def test_search_pagination(self):
        title = f"{PREFIX}分页搜索{uuid.uuid4().hex[:4]}"
        for _ in range(3):
            self._add_project(title=f"{title}_{uuid.uuid4().hex[:4]}")
        self.assertEqual(len(self.lib.search_projects_by_title("分页搜索", 1, 2)["data"]["projects"]), 2)

    # ==================== _update_project_stats ====================

    def test_stats_increase(self):
        pid = self._add_project(target_amount=10000.0)
        self.assertTrue(self.lib._update_project_stats(pid, 500.0, 1))
        d = self.lib.get_project_by_id(pid)["data"]
        self.assertEqual(d["current_amount"], 500.0)
        self.assertEqual(d["participant_count"], 1)

    def test_stats_decrease(self):
        pid = self._add_project(target_amount=10000.0)
        self.lib._update_project_stats(pid, 500.0, 1)
        self.lib._update_project_stats(pid, -200.0, -1)
        d = self.lib.get_project_by_id(pid)["data"]
        self.assertEqual(d["current_amount"], 300.0)
        self.assertEqual(d["participant_count"], 0)

    def test_stats_negative_boundary(self):
        pid = self._add_project(target_amount=10000.0)
        self.lib._update_project_stats(pid, 100.0, 1)
        self.lib._update_project_stats(pid, -500.0, -1)
        d = self.lib.get_project_by_id(pid)["data"]
        self.assertEqual(d["current_amount"], 0.0)
        self.assertEqual(d["participant_count"], 0)

    def test_stats_not_exists(self):
        self.assertFalse(self.lib._update_project_stats(999999, 100.0, 1))

    # ==================== get_project_summary ====================

    def test_summary_success(self):
        pid = self._add_project(title="摘要测试", target_amount=1000.0)
        self.lib._update_project_stats(pid, 300.0, 2)
        d = self.lib.get_project_summary(pid)["data"]
        self.assertEqual(d["project_id"], pid)
        self.assertEqual(d["target_amount"], 1000.0)
        self.assertEqual(d["current_amount"], 300.0)
        self.assertEqual(d["completion_percentage"], 30.0)
        self.assertEqual(d["participant_count"], 2)
        self.assertEqual(d["total_donation_count"], 0)
        for f in ["project_id", "title", "target_amount", "current_amount",
                   "completion_percentage", "participant_count", "total_donation_count",
                   "status", "created_at"]:
            self.assertIn(f, d)

    def test_summary_zero_target(self):
        """目标金额为0时完成百分比应为0，不除零"""
        pid = self._add_project(target_amount=0.0)
        d = self.lib.get_project_summary(pid)["data"]
        self.assertEqual(d["completion_percentage"], 0.0)

    def test_summary_not_exists(self):
        self.assertFalse(self.lib.get_project_summary(999999)["success"])

    # ==================== DB 连接失败批量覆盖 ====================

    def test_db_connection_fail(self):
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.create_project("t", "d", 1.0)["success"])
            self.assertFalse(self.lib.get_project_by_id(1)["success"])
            self.assertFalse(self.lib.update_project(1, {"title": "x"})["success"])
            self.assertFalse(self.lib.delete_project(1)["success"])
            self.assertFalse(self.lib.get_all_projects()["success"])
            self.assertFalse(self.lib.get_projects_by_status(1)["success"])
            self.assertFalse(self.lib.search_projects_by_title("x")["success"])
            self.assertFalse(self.lib.get_project_summary(1)["success"])
            self.assertFalse(self.lib._update_project_stats(1, 1.0, 1))

    # ==================== 综合场景 ====================

    def test_full_lifecycle(self):
        """创建 -> 查询 -> 更新 -> 统计 -> 摘要 -> 删除"""
        pid = self._add_project(title="生命周期", target_amount=5000.0)

        d = self.lib.get_project_by_id(pid)["data"]
        self.assertEqual(d["status"], 1)

        self.lib.update_project(pid, {"title": "已更新", "status": 0})
        self.assertEqual(self.lib.get_project_by_id(pid)["data"]["title"], "已更新")

        self.lib._update_project_stats(pid, 2500.0, 3)
        s = self.lib.get_project_summary(pid)["data"]
        self.assertEqual(s["completion_percentage"], 50.0)
        self.assertEqual(s["participant_count"], 3)

        self.lib.delete_project(pid)
        self.assertFalse(self.lib.get_project_by_id(pid)["success"])
        self.project_ids.remove(pid)

    def test_create_then_list_and_search(self):
        """创建后能在列表和搜索中找到"""
        title = f"{PREFIX}能找到吗{uuid.uuid4().hex[:6]}"
        pid = self._add_project(title=title)
        self.assertGreaterEqual(self.lib.get_all_projects()["data"]["total"], 1)
        self.assertGreaterEqual(self.lib.search_projects_by_title("能找到吗")["data"]["total"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
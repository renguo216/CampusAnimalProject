# backend/tests/test_donation_library.py
"""
DonationLibrary 完整测试套件（unittest 框架）
运行方式：
    cd 项目根目录
    python -m backend.tests.test_donation_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_donation_project、t_donation 表已存在
"""

import os
import sys
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.donation_library import DonationLibrary
from backend.libs.user_library import UserLibrary


# 期望的捐赠详情字段
EXPECTED_DETAIL_FIELDS = [
    "donation_id", "user_id", "nickname", "avatar_url",
    "project_id", "project_title", "amount", "status",
    "reviewed_by", "reviewed_at", "review_comment", "created_at"
]


class TestDonationLibrary(unittest.TestCase):
    """DonationLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = DonationLibrary()
        cls.user_lib = UserLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.donation_ids = []
        self.project_ids = []
        self.user_ids = []

    def tearDown(self):
        if not (self.donation_ids or self.project_ids or self.user_ids):
            return
        db = self.lib.db
        try:
            if db.connection is None:
                if not db.open_database():
                    return
                need_close = True
            else:
                need_close = False
            for did in self.donation_ids:
                db.execute_raw_sql("DELETE FROM t_donation WHERE donation_id=%s", (did,))
            for pid in self.project_ids:
                db.execute_raw_sql("DELETE FROM t_donation_project WHERE project_id=%s", (pid,))
            for uid in self.user_ids:
                db.execute_raw_sql("DELETE FROM t_user WHERE user_id=%s", (uid,))
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
            db.execute_raw_sql("DELETE FROM t_donation WHERE user_id LIKE %s", ("test_donation_%",))
            db.execute_raw_sql("DELETE FROM t_donation_project WHERE title LIKE %s", ("test_donation_%",))
            db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", ("test_donation_%",))
            if need_close:
                db.close_database()
        except Exception as e:
            print(f"[_cleanup_all 警告] 清理失败: {e}")

    # ---- 辅助方法 ----

    def _add_user(self, role=1, is_active=1):
        """注册测试用户并返回 user_id"""
        uid = f"test_donation_{uuid.uuid4().hex[:8]}"
        r = self.user_lib.register_user(uid, f"nick_{uid[:8]}",
                                        avatar_url="http://x.com/a.jpg", role=role)
        if not r.get("success"):
            self.user_lib.delete_user(uid)
            r = self.user_lib.register_user(uid, f"nick_{uid[:8]}",
                                              avatar_url="http://x.com/a.jpg", role=role)
        if is_active == 0:
            self.user_lib.toggle_active_status(uid, 0)
        self.user_ids.append(uid)
        return uid

    def _add_project(self, title=None, target_amount=1000.00, status=1):
        """创建测试募捐项目并返回 project_id"""
        db = self.lib.db
        if db.connection is None:
            db.open_database()
            need_close = True
        else:
            need_close = False

        title = title or f"test_donation_{uuid.uuid4().hex[:8]}"
        sql = """INSERT INTO t_donation_project
                 (title, description, target_amount, current_amount, participant_count, status, created_at)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        db.execute_raw_sql(sql, (title, "测试描述", target_amount, 0.00, 0, status,
                                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        pid = db.get_last_insert_id()
        if need_close:
            db.close_database()
        self.project_ids.append(pid)
        return pid

    def _submit(self, user_id, project_id, amount=50.00):
        """提交捐赠并返回结果"""
        r = self.lib.submit_donation(user_id, project_id, amount)
        if r.get("success"):
            self.donation_ids.append(r["data"]["donation_id"])
        return r

    # ==================== submit_donation ====================

    def test_submit_success(self):
        """正常提交捐赠"""
        uid = self._add_user()
        pid = self._add_project()
        r = self._submit(uid, pid, 50.00)
        self.assertTrue(r["success"])
        self.assertEqual(len(r["data"]["donation_id"]), 32)
        self.assertEqual(r["data"]["status"], 0)
        self.assertEqual(r["data"]["amount"], 50.00)

    def test_submit_user_not_exists(self):
        pid = self._add_project()
        r = self.lib.submit_donation("no_user", pid, 10.00)
        self.assertFalse(r["success"])
        self.assertIn("用户不存在", r["message"])

    def test_submit_user_banned(self):
        banned = self._add_user(is_active=0)
        pid = self._add_project()
        r = self.lib.submit_donation(banned, pid, 10.00)
        self.assertFalse(r["success"])
        self.assertIn("封禁", r["message"])

    def test_submit_project_not_exists(self):
        uid = self._add_user()
        r = self.lib.submit_donation(uid, 999999, 10.00)
        self.assertFalse(r["success"])
        self.assertIn("募捐项目不存在", r["message"])

    def test_submit_project_closed(self):
        uid = self._add_user()
        pid = self._add_project(status=0)
        r = self.lib.submit_donation(uid, pid, 10.00)
        self.assertFalse(r["success"])
        self.assertIn("已结束", r["message"])

    def test_submit_duplicate(self):
        uid = self._add_user()
        pid = self._add_project()
        r1 = self._submit(uid, pid, 50.00)
        r2 = self.lib.submit_donation(uid, pid, 20.00)
        self.assertFalse(r2["success"])
        self.assertIn("重复提交", r2["message"])
        self.assertEqual(r2["data"]["donation_id"], r1["data"]["donation_id"])

    def test_submit_updates_project_stats(self):
        """提交后项目统计更新"""
        uid = self._add_user()
        pid = self._add_project(target_amount=1000.00)
        self._submit(uid, pid, 100.00)
        db = self.lib.db
        if db.connection is None:
            db.open_database()
            need_close = True
        else:
            need_close = False
        result = db.execute_raw_sql("SELECT current_amount, participant_count FROM t_donation_project WHERE project_id=%s", (pid,))
        if need_close:
            db.close_database()
        self.assertEqual(float(result[0]["current_amount"]), 100.00)
        self.assertEqual(result[0]["participant_count"], 1)

    # ==================== check_duplicate_donation ====================

    def test_check_duplicate_no_duplicate(self):
        uid = self._add_user()
        pid = self._add_project()
        r = self.lib.check_duplicate_donation(uid, pid)
        self.assertTrue(r["success"])
        self.assertFalse(r["data"]["is_duplicate"])
        self.assertIsNone(r["data"]["donation_id"])

    def test_check_duplicate_has_duplicate(self):
        uid = self._add_user()
        pid = self._add_project()
        r1 = self._submit(uid, pid)
        r2 = self.lib.check_duplicate_donation(uid, pid)
        self.assertTrue(r2["data"]["is_duplicate"])
        self.assertEqual(r2["data"]["donation_id"], r1["data"]["donation_id"])

    def test_check_duplicate_after_approve(self):
        """审核通过后不再视为重复"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.approve_donation(did, admin)
        r = self.lib.check_duplicate_donation(uid, pid)
        self.assertFalse(r["data"]["is_duplicate"])

    def test_check_duplicate_after_reject(self):
        """驳回后不再视为重复"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.reject_donation(did, admin, "驳回")
        r = self.lib.check_duplicate_donation(uid, pid)
        self.assertFalse(r["data"]["is_duplicate"])

    def test_check_duplicate_after_cancel(self):
        """取消后不再视为重复"""
        uid = self._add_user()
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.cancel_donation(did, uid)
        r = self.lib.check_duplicate_donation(uid, pid)
        self.assertFalse(r["data"]["is_duplicate"])

    # ==================== cancel_donation ====================

    def test_cancel_success(self):
        uid = self._add_user()
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        r = self.lib.cancel_donation(did, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 3)
        self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], 3)

    def test_cancel_rollback_project_stats(self):
        """取消后回滚项目统计"""
        uid = self._add_user()
        pid = self._add_project()
        did = self._submit(uid, pid, 100.00)["data"]["donation_id"]
        self.lib.cancel_donation(did, uid)
        db = self.lib.db
        if db.connection is None:
            db.open_database()
            need_close = True
        else:
            need_close = False
        result = db.execute_raw_sql("SELECT current_amount, participant_count FROM t_donation_project WHERE project_id=%s", (pid,))
        if need_close:
            db.close_database()
        self.assertEqual(float(result[0]["current_amount"]), 0.00)
        self.assertEqual(result[0]["participant_count"], 0)

    def test_cancel_not_exists(self):
        uid = self._add_user()
        r = self.lib.cancel_donation("no_xxx", uid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_cancel_not_pending(self):
        """非待确认状态不能取消"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.approve_donation(did, admin)
        r = self.lib.cancel_donation(did, uid)
        self.assertFalse(r["success"])
        self.assertIn("仅待确认", r["message"])

    def test_cancel_not_owner(self):
        """不能取消他人的捐赠"""
        uid = self._add_user()
        other = self._add_user()
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        r = self.lib.cancel_donation(did, other)
        self.assertFalse(r["success"])
        self.assertIn("无权取消", r["message"])

    # ==================== get_donation_by_id ====================

    def test_get_by_id_success(self):
        uid = self._add_user()
        pid = self._add_project()
        did = self._submit(uid, pid, 50.00)["data"]["donation_id"]
        d = self.lib.get_donation_by_id(did)["data"]
        self.assertEqual(d["donation_id"], did)
        self.assertEqual(d["user_id"], uid)
        self.assertEqual(d["amount"], 50.00)
        self.assertEqual(d["status"], 0)
        for f in EXPECTED_DETAIL_FIELDS:
            self.assertIn(f, d)

    def test_get_by_id_not_exists(self):
        r = self.lib.get_donation_by_id("no_xxx")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_get_by_id_all_statuses(self):
        """各状态下的详情均可正常查询"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        for fn, expected in [
            (lambda d: None, 0),
            (lambda d: self.lib.approve_donation(d, admin), 1),
        ]:
            did = self._submit(uid, pid)["data"]["donation_id"]
            fn(did)
            self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], expected)

    def test_get_by_id_created_at_format(self):
        uid = self._add_user()
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        t = self.lib.get_donation_by_id(did)["data"]["created_at"]
        if hasattr(t, 'strftime'):
            t = t.strftime("%Y-%m-%d %H:%M:%S")
        datetime.strptime(t, "%Y-%m-%d %H:%M:%S")

    # ==================== get_user_donations ====================

    def test_get_user_donations_success(self):
        uid = self._add_user()
        for _ in range(3):
            pid = self._add_project()
            self._submit(uid, pid)
        r = self.lib.get_user_donations(uid, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 3)
        self.assertEqual(len(r["data"]["donations"]), 3)
        for f in ["donations", "total", "page", "page_size"]:
            self.assertIn(f, r["data"])

    def test_get_user_donations_empty(self):
        r = self.lib.get_user_donations("no_user")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)

    def test_get_user_donations_pagination(self):
        uid = self._add_user()
        for _ in range(3):
            pid = self._add_project()
            self._submit(uid, pid)
        p1 = self.lib.get_user_donations(uid, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["donations"]), 2)
        p2 = self.lib.get_user_donations(uid, page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["donations"]), 1)
        p99 = self.lib.get_user_donations(uid, page=99, page_size=20)
        self.assertEqual(len(p99["data"]["donations"]), 0)

    def test_get_user_donations_order_desc(self):
        uid = self._add_user()
        self._submit(uid, self._add_project())
        self._submit(uid, self._add_project())
        donations = self.lib.get_user_donations(uid)["data"]["donations"]
        self.assertGreaterEqual(len(donations), 2, "需要至少2条记录来验证排序")
        t1 = datetime.strptime(donations[0]["created_at"], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(donations[1]["created_at"], "%Y-%m-%d %H:%M:%S")
        self.assertGreaterEqual(t1, t2)

    def test_get_user_donations_field_completeness(self):
        uid = self._add_user()
        self._submit(uid, self._add_project())
        d = self.lib.get_user_donations(uid)["data"]["donations"][0]
        for f in EXPECTED_DETAIL_FIELDS:
            self.assertIn(f, d)

    # ==================== get_project_donations ====================

    def test_get_project_donations_success(self):
        pid = self._add_project()
        for _ in range(2):
            self._submit(self._add_user(), pid)
        r = self.lib.get_project_donations(pid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 2)

    def test_get_project_donations_empty(self):
        r = self.lib.get_project_donations(999999)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)

    def test_get_project_donations_pagination(self):
        pid = self._add_project()
        for _ in range(3):
            self._submit(self._add_user(), pid)
        p1 = self.lib.get_project_donations(pid, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["donations"]), 2)
        p2 = self.lib.get_project_donations(pid, page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["donations"]), 1)

    def test_get_project_donations_field(self):
        pid = self._add_project()
        self._submit(self._add_user(), pid)
        d = self.lib.get_project_donations(pid)["data"]["donations"][0]
        for f in EXPECTED_DETAIL_FIELDS:
            self.assertIn(f, d)

    # ==================== approve_donation ====================

    def test_approve_success(self):
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        r = self.lib.approve_donation(did, admin)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 1)
        self.assertEqual(r["data"]["reviewed_by"], admin)
        self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], 1)

    def test_approve_not_exists(self):
        admin = self._add_user(role=3)
        r = self.lib.approve_donation("no_xxx", admin)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_approve_not_pending(self):
        """非待确认不能审核"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.approve_donation(did, admin)
        r = self.lib.approve_donation(did, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待确认", r["message"])

    def test_approve_after_reject(self):
        """驳回后不能再次审核"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.reject_donation(did, admin, "驳回")
        r = self.lib.approve_donation(did, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待确认", r["message"])

    def test_approve_after_cancel(self):
        """取消后不能审核"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.cancel_donation(did, uid)
        r = self.lib.approve_donation(did, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待确认", r["message"])

    # ==================== reject_donation ====================

    def test_reject_success(self):
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid, 100.00)["data"]["donation_id"]
        r = self.lib.reject_donation(did, admin, "金额不符合规定")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)
        self.assertEqual(r["data"]["review_comment"], "金额不符合规定")
        self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], 2)

    def test_reject_rollback_project_stats(self):
        """驳回后回滚项目统计"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid, 100.00)["data"]["donation_id"]
        self.lib.reject_donation(did, admin, "驳回")
        db = self.lib.db
        if db.connection is None:
            db.open_database()
            need_close = True
        else:
            need_close = False
        result = db.execute_raw_sql("SELECT current_amount, participant_count FROM t_donation_project WHERE project_id=%s", (pid,))
        if need_close:
            db.close_database()
        self.assertEqual(float(result[0]["current_amount"]), 0.00)
        self.assertEqual(result[0]["participant_count"], 0)

    def test_reject_not_exists(self):
        admin = self._add_user(role=3)
        r = self.lib.reject_donation("no_xxx", admin)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_reject_not_pending(self):
        """非待确认不能驳回"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.approve_donation(did, admin)
        r = self.lib.reject_donation(did, admin, "再次驳回")
        self.assertFalse(r["success"])
        self.assertIn("仅待确认", r["message"])

    # ==================== get_donation_summary_by_project ====================

    def test_summary_success(self):
        uid = self._add_user()
        uid2 = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        self._submit(uid, pid, 50.00)
        self._submit(uid2, pid, 30.00)
        r = self.lib.get_donation_summary_by_project(pid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total_amount"], 80.00)
        self.assertEqual(r["data"]["participant_count"], 2)
        self.assertEqual(r["data"]["avg_amount"], 40.00)
        self.assertEqual(r["data"]["pending_count"], 2)

    def test_summary_after_status_change(self):
        """状态变化后统计正确"""
        uid = self._add_user()
        uid2 = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did1 = self._submit(uid, pid, 50.00)["data"]["donation_id"]
        did2 = self._submit(uid2, pid, 30.00)["data"]["donation_id"]
        self.lib.approve_donation(did1, admin)
        self.lib.reject_donation(did2, admin, "驳回")
        r = self.lib.get_donation_summary_by_project(pid)
        self.assertEqual(r["data"]["confirmed_count"], 1)
        self.assertEqual(r["data"]["rejected_count"], 1)
        self.assertEqual(r["data"]["pending_count"], 0)

    def test_summary_empty(self):
        pid = self._add_project()
        r = self.lib.get_donation_summary_by_project(pid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total_amount"], 0.0)
        self.assertEqual(r["data"]["participant_count"], 0)

    def test_summary_structure(self):
        pid = self._add_project()
        r = self.lib.get_donation_summary_by_project(pid)
        self.assertTrue(r["success"])
        for f in ["total_amount", "participant_count", "avg_amount",
                  "pending_count", "confirmed_count", "rejected_count", "cancelled_count"]:
            self.assertIn(f, r["data"])

    # ==================== get_all_donations ====================

    def test_get_all_donations_success(self):
        for _ in range(3):
            u = self._add_user()
            pid = self._add_project()
            self._submit(u, pid)
        r = self.lib.get_all_donations(page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 3)

    def test_get_all_donations_filter(self):
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid)["data"]["donation_id"]
        self.lib.approve_donation(did, admin)
        r = self.lib.get_all_donations(page=1, page_size=20, status_filter=1)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 1)
        self.assertEqual(r["data"]["donations"][0]["status"], 1)

    def test_get_all_donations_pagination(self):
        for _ in range(3):
            u = self._add_user()
            pid = self._add_project()
            self._submit(u, pid)
        p1 = self.lib.get_all_donations(page=1, page_size=2)
        self.assertEqual(len(p1["data"]["donations"]), 2)
        p2 = self.lib.get_all_donations(page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["donations"]), 1)

    def test_get_all_donations_field(self):
        u = self._add_user()
        pid = self._add_project()
        self._submit(u, pid)
        d = self.lib.get_all_donations()["data"]["donations"][0]
        for f in EXPECTED_DETAIL_FIELDS:
            self.assertIn(f, d)

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.get_donation_by_id("x")["success"])
            self.assertFalse(self.lib.get_user_donations("x")["success"])
            self.assertFalse(self.lib.get_project_donations(1)["success"])
            self.assertFalse(self.lib.get_all_donations()["success"])
            self.assertFalse(self.lib.get_donation_summary_by_project(1)["success"])
            self.assertFalse(self.lib.submit_donation("x", 1, 10.00)["success"])
            self.assertFalse(self.lib.cancel_donation("x", "u")["success"])
            self.assertFalse(self.lib.approve_donation("x", "a")["success"])
            self.assertFalse(self.lib.reject_donation("x", "a")["success"])
            self.assertFalse(self.lib.check_duplicate_donation("u", 1)["success"])

    # ==================== 综合业务场景 ====================

    def test_full_lifecycle_approved(self):
        """提交 → 待确认 → 审核通过"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid, 100.00)["data"]["donation_id"]
        self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], 0)
        self.lib.approve_donation(did, admin)
        self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], 1)

    def test_full_lifecycle_rejected(self):
        """提交 → 驳回"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did = self._submit(uid, pid, 100.00)["data"]["donation_id"]
        self.lib.reject_donation(did, admin, "不符合条件")
        self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], 2)

    def test_full_lifecycle_cancelled(self):
        """提交 → 取消"""
        uid = self._add_user()
        pid = self._add_project()
        did = self._submit(uid, pid, 100.00)["data"]["donation_id"]
        self.lib.cancel_donation(did, uid)
        self.assertEqual(self.lib.get_donation_by_id(did)["data"]["status"], 3)

    def test_cancel_then_resubmit(self):
        """取消后可以重新捐赠同一项目"""
        uid = self._add_user()
        pid = self._add_project()
        did1 = self._submit(uid, pid, 50.00)["data"]["donation_id"]
        self.lib.cancel_donation(did1, uid)
        r = self._submit(uid, pid, 30.00)
        self.assertTrue(r["success"])
        self.assertNotEqual(r["data"]["donation_id"], did1)

    def test_reject_then_resubmit(self):
        """驳回后可以重新捐赠同一项目"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_project()
        did1 = self._submit(uid, pid, 50.00)["data"]["donation_id"]
        self.lib.reject_donation(did1, admin, "驳回")
        r = self._submit(uid, pid, 30.00)
        self.assertTrue(r["success"])
        self.assertNotEqual(r["data"]["donation_id"], did1)

    def test_multiple_users_same_project(self):
        """多用户捐赠同一项目"""
        pid = self._add_project()
        for _ in range(3):
            self._submit(self._add_user(), pid)
        self.assertEqual(self.lib.get_project_donations(pid)["data"]["total"], 3)

    def test_same_user_multiple_projects(self):
        """同一用户捐赠多个项目"""
        uid = self._add_user()
        for _ in range(3):
            pid = self._add_project()
            self._submit(uid, pid)
        self.assertGreaterEqual(self.lib.get_user_donations(uid)["data"]["total"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
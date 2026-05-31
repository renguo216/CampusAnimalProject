# backend/tests/test_reimbursement_library.py
"""
ReimbursementLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_reimbursement_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_reimbursement 表已存在
"""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.reimbursement_library import ReimbursementLibrary
from backend.libs.user_library import UserLibrary

PREFIX_USER = "test_reimb_user_"
PREFIX_ADMIN = "test_reimb_admin_"


class TestReimbursementLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lib = ReimbursementLibrary()
        cls.user_lib = UserLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.reimb_ids = []
        self.user_ids = []

    def tearDown(self):
        if not (self.reimb_ids or self.user_ids):
            return
        if self.lib.db.open_database():
            for rid in self.reimb_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_reimbursement WHERE reimb_id=%s", (rid,))
            for uid in self.user_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id=%s", (uid,))
            self.lib.db.close_database()

    @classmethod
    def _cleanup_all(cls):
        if cls.lib.db.open_database():
            cls.lib.db.execute_raw_sql(
                "DELETE FROM t_reimbursement WHERE user_id LIKE %s OR user_id LIKE %s",
                (f"{PREFIX_USER}%", f"{PREFIX_ADMIN}%")
            )
            cls.lib.db.execute_raw_sql(
                "DELETE FROM t_user WHERE user_id LIKE %s OR user_id LIKE %s",
                (f"{PREFIX_USER}%", f"{PREFIX_ADMIN}%")
            )
            cls.lib.db.close_database()

    def _add_user(self, role=1, is_active=1) -> str:
        uid = f"{PREFIX_USER}{uuid.uuid4().hex[:8]}"
        self.user_lib.register_user(uid, f"nick_{uuid.uuid4().hex[:6]}", role=role)
        if not is_active:
            self.user_lib.toggle_active_status(uid, 0)
        self.user_ids.append(uid)
        return uid

    def _add_admin(self) -> str:
        return self._add_user(role=3)

    def _submit(self, user_id, amount=100.0, **kw) -> str:
        r = self.lib.submit_reimbursement(user_id, amount, **kw)
        if not r.get("success"):
            raise RuntimeError(f"提交报销失败: {r}")
        rid = r["data"]["reimb_id"]
        self.reimb_ids.append(rid)
        return rid

    # ==================== submit_reimbursement ====================

    def test_submit_success(self):
        uid = self._add_user()
        r = self.lib.submit_reimbursement(uid, 100.5, type_="医疗费", description="看病")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["amount"], 100.5)
        self.assertEqual(r["data"]["status"], 0)

    def test_submit_user_not_exists(self):
        r = self.lib.submit_reimbursement("no_user", 50.0)
        self.assertFalse(r["success"])
        self.assertIn("用户不存在", r["message"])

    def test_submit_user_banned(self):
        uid = self._add_user(is_active=0)
        r = self.lib.submit_reimbursement(uid, 50.0)
        self.assertFalse(r["success"])
        self.assertIn("封禁", r["message"])

    # ==================== update_reimbursement ====================

    def test_update_success(self):
        uid = self._add_user()
        rid = self._submit(uid, 100.0)
        r = self.lib.update_reimbursement(rid, uid, amount=200.0, description="改了")
        self.assertTrue(r["success"])
        d = self.lib.get_reimbursement_by_id(rid)["data"]
        self.assertEqual(d["amount"], 200.0)
        self.assertEqual(d["description"], "改了")

    def test_update_not_owner(self):
        uid, other = self._add_user(), self._add_user()
        rid = self._submit(uid)
        r = self.lib.update_reimbursement(rid, other, amount=999.0)
        self.assertFalse(r["success"])
        self.assertIn("无权修改", r["message"])

    def test_update_not_exists(self):
        uid = self._add_user()
        r = self.lib.update_reimbursement("no_xxx", uid, amount=1.0)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_update_not_pending(self):
        uid = self._add_user()
        admin = self._add_admin()
        rid = self._submit(uid)
        self.lib.approve_reimbursement(rid, admin)
        r = self.lib.update_reimbursement(rid, uid, amount=1.0)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    # ==================== cancel_reimbursement ====================

    def test_cancel_success(self):
        uid = self._add_user()
        rid = self._submit(uid)
        r = self.lib.cancel_reimbursement(rid, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 3)

    def test_cancel_not_owner(self):
        uid, other = self._add_user(), self._add_user()
        rid = self._submit(uid)
        r = self.lib.cancel_reimbursement(rid, other)
        self.assertFalse(r["success"])
        self.assertIn("无权撤销", r["message"])

    def test_cancel_not_exists(self):
        uid = self._add_user()
        r = self.lib.cancel_reimbursement("no_xxx", uid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_cancel_not_pending(self):
        uid = self._add_user()
        admin = self._add_admin()
        rid = self._submit(uid)
        self.lib.approve_reimbursement(rid, admin)
        r = self.lib.cancel_reimbursement(rid, uid)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    # ==================== get_reimbursement_by_id ====================

    def test_get_by_id_success(self):
        uid = self._add_user()
        rid = self._submit(uid, amount=100.0, type_="测试类型")
        d = self.lib.get_reimbursement_by_id(rid)["data"]
        self.assertEqual(d["reimb_id"], rid)
        self.assertEqual(d["amount"], 100.0)
        self.assertEqual(d["type"], "测试类型")
        for f in ["reimb_id", "user_id", "nickname", "amount", "status", "type",
                   "description", "review_comment", "created_at", "updated_at"]:
            self.assertIn(f, d)

    def test_get_by_id_not_exists(self):
        self.assertFalse(self.lib.get_reimbursement_by_id("no_xxx")["success"])

    # ==================== get_user_reimbursements ====================

    def test_user_list_success(self):
        uid = self._add_user()
        for _ in range(3):
            self._submit(uid)
        r = self.lib.get_user_reimbursements(uid)
        self.assertGreaterEqual(r["data"]["total"], 3)
        self.assertIn("reimbursements", r["data"])

    def test_user_list_empty(self):
        self.assertEqual(self.lib.get_user_reimbursements("no_user")["data"]["total"], 0)

    def test_user_list_pagination(self):
        uid = self._add_user()
        for _ in range(3):
            self._submit(uid)
        self.assertEqual(len(self.lib.get_user_reimbursements(uid, 1, 2)["data"]["reimbursements"]), 2)
        self.assertGreaterEqual(len(self.lib.get_user_reimbursements(uid, 2, 2)["data"]["reimbursements"]), 1)

    # ==================== get_all_reimbursements ====================

    def test_all_list_success(self):
        uid = self._add_user()
        self._submit(uid)
        r = self.lib.get_all_reimbursements()
        self.assertGreaterEqual(r["data"]["total"], 1)

    def test_all_list_filter_by_status(self):
        uid = self._add_user()
        admin = self._add_admin()
        r1 = self._submit(uid)
        self._submit(uid)
        self.lib.approve_reimbursement(r1, admin)
        r0 = self.lib.get_all_reimbursements(status_filter=0)
        r1f = self.lib.get_all_reimbursements(status_filter=1)
        self.assertGreaterEqual(r0["data"]["total"], 1)
        self.assertGreaterEqual(r1f["data"]["total"], 1)

    def test_all_list_pagination(self):
        uid = self._add_user()
        for _ in range(3):
            self._submit(uid)
        self.assertEqual(len(self.lib.get_all_reimbursements(1, 2)["data"]["reimbursements"]), 2)

    # ==================== approve_reimbursement ====================

    def test_approve_success(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        r = self.lib.approve_reimbursement(rid, admin, "同意")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 1)
        d = self.lib.get_reimbursement_by_id(rid)["data"]
        self.assertEqual(d["status"], 1)
        self.assertEqual(d["review_comment"], "同意")

    def test_approve_not_exists(self):
        admin = self._add_admin()
        r = self.lib.approve_reimbursement("no_xxx", admin)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_approve_not_pending(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        self.lib.approve_reimbursement(rid, admin)
        r = self.lib.approve_reimbursement(rid, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    def test_approve_already_rejected(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        self.lib.reject_reimbursement(rid, admin, "驳回")
        r = self.lib.approve_reimbursement(rid, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    def test_approve_already_cancelled(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        self.lib.cancel_reimbursement(rid, uid)
        r = self.lib.approve_reimbursement(rid, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    # ==================== reject_reimbursement ====================

    def test_reject_success(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        r = self.lib.reject_reimbursement(rid, admin, "票据不全")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)
        d = self.lib.get_reimbursement_by_id(rid)["data"]
        self.assertEqual(d["review_comment"], "票据不全")

    def test_reject_not_exists(self):
        admin = self._add_admin()
        r = self.lib.reject_reimbursement("no_xxx", admin)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_reject_not_pending(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        self.lib.approve_reimbursement(rid, admin)
        r = self.lib.reject_reimbursement(rid, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    def test_reject_without_reason(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        r = self.lib.reject_reimbursement(rid, admin)
        self.assertTrue(r["success"])

    # ==================== get_reimbursement_status ====================

    def test_status_success(self):
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid)
        self.lib.approve_reimbursement(rid, admin)
        d = self.lib.get_reimbursement_status(rid)["data"]
        self.assertEqual(d["status"], 1)
        self.assertEqual(d["status_text"], "已通过")

    def test_status_cancelled(self):
        uid = self._add_user()
        rid = self._submit(uid)
        self.lib.cancel_reimbursement(rid, uid)
        d = self.lib.get_reimbursement_status(rid)["data"]
        self.assertEqual(d["status"], 3)
        self.assertEqual(d["status_text"], "已撤销")

    def test_status_not_exists(self):
        self.assertFalse(self.lib.get_reimbursement_status("no_xxx")["success"])

    # ==================== get_reimbursement_count_by_status ====================

    def test_count_all(self):
        uid, admin = self._add_user(), self._add_admin()
        self._submit(uid)
        self._submit(uid)
        self.lib.approve_reimbursement(self._submit(uid), admin)
        r = self.lib.get_reimbursement_count_by_status()
        self.assertGreaterEqual(r["data"]["total"], 3)
        self.assertIn("pending", r["data"])
        self.assertIn("approved", r["data"])

    def test_count_by_single_status(self):
        uid, admin = self._add_user(), self._add_admin()
        self._submit(uid)
        self.lib.approve_reimbursement(self._submit(uid), admin)
        r = self.lib.get_reimbursement_count_by_status(status=1)
        self.assertGreaterEqual(r["data"]["count"], 1)

    # ==================== DB 连接失败批量覆盖 ====================

    def test_db_connection_fail(self):
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.submit_reimbursement("u", 1.0)["success"])
            self.assertFalse(self.lib.update_reimbursement("r", "u")["success"])
            self.assertFalse(self.lib.cancel_reimbursement("r", "u")["success"])
            self.assertFalse(self.lib.get_reimbursement_by_id("r")["success"])
            self.assertFalse(self.lib.get_user_reimbursements("u")["success"])
            self.assertFalse(self.lib.get_all_reimbursements()["success"])
            self.assertFalse(self.lib.approve_reimbursement("r", "a")["success"])
            self.assertFalse(self.lib.reject_reimbursement("r", "a")["success"])
            self.assertFalse(self.lib.get_reimbursement_status("r")["success"])
            self.assertFalse(self.lib.get_reimbursement_count_by_status()["success"])

    # ==================== 综合场景 ====================

    def test_full_lifecycle_approved(self):
        """提交 -> 查询 -> 修改 -> 通过 -> 状态查询"""
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid, 100.0, description="原始")
        d = self.lib.get_reimbursement_by_id(rid)["data"]
        self.assertEqual(d["description"], "原始")
        self.lib.update_reimbursement(rid, uid, amount=200.0, description="已修改")
        self.lib.approve_reimbursement(rid, admin, "同意")
        s = self.lib.get_reimbursement_status(rid)["data"]
        self.assertEqual(s["status"], 1)
        self.assertEqual(s["status_text"], "已通过")

    def test_full_lifecycle_rejected(self):
        """提交 -> 驳回 -> 状态查询"""
        uid, admin = self._add_user(), self._add_admin()
        rid = self._submit(uid, 100.0)
        self.lib.reject_reimbursement(rid, admin, "票据不全")
        s = self.lib.get_reimbursement_status(rid)["data"]
        self.assertEqual(s["status"], 2)
        self.assertEqual(s["status_text"], "已驳回")

    def test_full_lifecycle_cancelled(self):
        """提交 -> 撤销 -> 状态查询"""
        uid = self._add_user()
        rid = self._submit(uid, 100.0)
        self.lib.cancel_reimbursement(rid, uid)
        s = self.lib.get_reimbursement_status(rid)["data"]
        self.assertEqual(s["status"], 3)
        self.assertEqual(s["status_text"], "已撤销")

    def test_approve_then_reject_fails(self):
        """通过后不能驳回，驳回后不能通过"""
        uid, admin = self._add_user(), self._add_admin()
        rid1 = self._submit(uid)
        rid2 = self._submit(uid)
        self.lib.approve_reimbursement(rid1, admin)
        self.assertFalse(self.lib.reject_reimbursement(rid1, admin)["success"])
        self.lib.reject_reimbursement(rid2, admin, "驳回")
        self.assertFalse(self.lib.approve_reimbursement(rid2, admin)["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
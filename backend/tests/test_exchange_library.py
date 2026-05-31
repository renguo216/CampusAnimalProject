# backend/tests/test_exchange_library.py
"""
ExchangeLibrary 完整测试套件（unittest 框架）
运行方式：
    cd 项目根目录
    python -m backend.tests.test_exchange_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_exchange_product、t_exchange 表已存在
"""

import os
import sys
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.exchange_library import ExchangeLibrary
from backend.libs.exchange_product_library import ExchangeProductLibrary
from backend.libs.user_library import UserLibrary


# 期望的兑换记录详情字段
EXPECTED_DETAIL_FIELDS = [
    "exchange_id", "user_id", "product_id", "points_used",
    "status", "created_at", "updated_at",
    "reviewed_by", "reviewed_at", "review_comment", "contact_info"
]


class TestExchangeLibrary(unittest.TestCase):
    """ExchangeLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = ExchangeLibrary()
        cls.product_lib = ExchangeProductLibrary()
        cls.user_lib = UserLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.exchange_ids = []
        self.product_ids = []
        self.user_ids = []

    def tearDown(self):
        if not (self.exchange_ids or self.product_ids or self.user_ids):
            return
        db = self.lib.db
        try:
            if db.connection is None:
                if not db.open_database():
                    return
                need_close = True
            else:
                need_close = False
            for eid in self.exchange_ids:
                db.execute_raw_sql("DELETE FROM t_exchange WHERE exchange_id=%s", (eid,))
            for pid in self.product_ids:
                db.execute_raw_sql("DELETE FROM t_exchange_product WHERE product_id=%s", (pid,))
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
            db.execute_raw_sql("DELETE FROM t_exchange WHERE user_id LIKE %s", ("test_exchange_%",))
            db.execute_raw_sql("DELETE FROM t_exchange_product WHERE name LIKE %s", ("test_exchange_%",))
            db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", ("test_exchange_%",))
            if need_close:
                db.close_database()
        except Exception as e:
            print(f"[_cleanup_all 警告] 清理失败: {e}")

    # ---- 辅助方法 ----

    def _add_user(self, role=1, is_active=1, points=500):
        """注册测试用户并返回 user_id"""
        uid = f"test_exchange_{uuid.uuid4().hex[:8]}"
        r = self.user_lib.register_user(uid, f"nick_{uid[:8]}",
                                          avatar_url="http://x.com/a.jpg", role=role)
        if not r.get("success"):
            self.user_lib.delete_user(uid)
            r = self.user_lib.register_user(uid, f"nick_{uid[:8]}",
                                              avatar_url="http://x.com/a.jpg", role=role)
        if is_active == 0:
            self.user_lib.toggle_active_status(uid, 0)
        # 设置积分
        db = self.lib.db
        if db.connection is None:
            db.open_database()
            need_close = True
        else:
            need_close = False
        db.execute_raw_sql("UPDATE t_user SET points = %s WHERE user_id = %s", (points, uid))
        if need_close:
            db.close_database()
        self.user_ids.append(uid)
        return uid

    def _add_product(self, points_required=100, stock=5, status=1):
        """创建测试商品并返回 product_id"""
        r = self.product_lib.create_exchange_product({
            "name": f"test_exchange_{uuid.uuid4().hex[:8]}",
            "points_required": points_required,
            "stock": stock,
            "status": status
        })
        if not r.get("success"):
            raise RuntimeError(f"创建商品失败: {r}")
        pid = r["data"]["product_id"]
        self.product_ids.append(pid)
        return pid

    def _submit(self, user_id, product_id):
        """提交兑换并返回结果"""
        r = self.lib.submit_exchange(user_id, product_id)
        if r.get("success"):
            self.exchange_ids.append(r["data"]["exchange_id"])
        return r

    # ==================== check_user_points ====================

    def test_check_points_success(self):
        uid = self._add_user(points=500)
        r = self.lib.check_user_points(uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["points"], 500)

    def test_check_points_not_exists(self):
        r = self.lib.check_user_points("no_user")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== submit_exchange ====================

    def test_submit_success(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        r = self._submit(uid, pid)
        self.assertTrue(r["success"])
        self.assertIn("exchange_id", r["data"])
        self.assertEqual(r["data"]["points_used"], 100)

    def test_submit_deducts_points(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        self._submit(uid, pid)
        pts = self.lib.check_user_points(uid)
        self.assertEqual(pts["data"]["points"], 400)

    def test_submit_deducts_stock(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        self._submit(uid, pid)
        stock = self.product_lib.get_product_stock(pid)
        self.assertEqual(stock["data"]["stock"], 4)

    def test_submit_insufficient_points(self):
        uid = self._add_user(points=50)
        pid = self._add_product(points_required=100, stock=5)
        r = self.lib.submit_exchange(uid, pid)
        self.assertFalse(r["success"])
        self.assertIn("积分不足", r["message"])

    def test_submit_insufficient_stock(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=0)
        r = self.lib.submit_exchange(uid, pid)
        self.assertFalse(r["success"])
        self.assertIn("库存不足", r["message"])

    def test_submit_product_not_exists(self):
        uid = self._add_user(points=500)
        r = self.lib.submit_exchange(uid, 999999)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_submit_user_not_exists(self):
        pid = self._add_product(points_required=100, stock=5)
        r = self.lib.submit_exchange("no_user", pid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== cancel_exchange ====================

    def test_cancel_success(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        r = self.lib.cancel_exchange(eid, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)

    def test_cancel_refunds_points(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.cancel_exchange(eid, uid)
        pts = self.lib.check_user_points(uid)
        self.assertEqual(pts["data"]["points"], 500)

    def test_cancel_restores_stock(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.cancel_exchange(eid, uid)
        stock = self.product_lib.get_product_stock(pid)
        self.assertEqual(stock["data"]["stock"], 5)

    def test_cancel_not_owner(self):
        uid = self._add_user(points=500)
        other = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        r = self.lib.cancel_exchange(eid, other)
        self.assertFalse(r["success"])
        self.assertIn("无权", r["message"])

    def test_cancel_not_exists(self):
        uid = self._add_user()
        r = self.lib.cancel_exchange(999999, uid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_cancel_after_complete(self):
        """已完成的不能取消"""
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.complete_exchange(eid)
        r = self.lib.cancel_exchange(eid, uid)
        self.assertFalse(r["success"])
        self.assertIn("状态", r["message"])

    # ==================== complete_exchange ====================

    def test_complete_success(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        r = self.lib.complete_exchange(eid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 1)

    def test_complete_not_exists(self):
        r = self.lib.complete_exchange(999999)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_complete_after_cancel(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.cancel_exchange(eid, uid)
        r = self.lib.complete_exchange(eid)
        self.assertFalse(r["success"])
        self.assertIn("状态", r["message"])

    # ==================== reject_exchange ====================

    def test_reject_success(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        r = self.lib.reject_exchange(eid, "库存不足，拒绝兑换")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)

    def test_reject_refunds_points(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.reject_exchange(eid, "驳回")
        pts = self.lib.check_user_points(uid)
        self.assertEqual(pts["data"]["points"], 500)

    def test_reject_restores_stock(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.reject_exchange(eid, "驳回")
        stock = self.product_lib.get_product_stock(pid)
        self.assertEqual(stock["data"]["stock"], 5)

    def test_reject_not_exists(self):
        r = self.lib.reject_exchange(999999, "测试")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_reject_after_complete(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.complete_exchange(eid)
        r = self.lib.reject_exchange(eid, "驳回")
        self.assertFalse(r["success"])
        self.assertIn("状态", r["message"])

    # ==================== get_user_exchanges ====================

    def test_get_user_exchanges_success(self):
        uid = self._add_user(points=500)
        for _ in range(3):
            pid = self._add_product(points_required=10, stock=5)
            self._submit(uid, pid)
        r = self.lib.get_user_exchanges(uid, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 3)
        self.assertEqual(len(r["data"]["records"]), 3)
        for f in ["records", "total", "page", "page_size"]:
            self.assertIn(f, r["data"])

    def test_get_user_exchanges_empty(self):
        r = self.lib.get_user_exchanges("no_user")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)

    def test_get_user_exchanges_pagination(self):
        uid = self._add_user(points=500)
        for _ in range(3):
            pid = self._add_product(points_required=10, stock=5)
            self._submit(uid, pid)
        p1 = self.lib.get_user_exchanges(uid, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["records"]), 2)
        p2 = self.lib.get_user_exchanges(uid, page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["records"]), 1)

    def test_get_user_excludes_other_users(self):
        uid1 = self._add_user(points=500)
        uid2 = self._add_user(points=500)
        pid = self._add_product(points_required=10, stock=5)
        self._submit(uid1, pid)
        r = self.lib.get_user_exchanges(uid2)
        self.assertEqual(r["data"]["total"], 0)

    # ==================== get_all_exchanges ====================

    def test_get_all_exchanges_success(self):
        for _ in range(3):
            uid = self._add_user(points=500)
            pid = self._add_product(points_required=10, stock=5)
            self._submit(uid, pid)
        r = self.lib.get_all_exchanges(page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 3)

    def test_get_all_exchanges_pagination(self):
        for _ in range(3):
            uid = self._add_user(points=500)
            pid = self._add_product(points_required=10, stock=5)
            self._submit(uid, pid)
        p1 = self.lib.get_all_exchanges(page=1, page_size=2)
        self.assertEqual(len(p1["data"]["records"]), 2)
        p2 = self.lib.get_all_exchanges(page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["records"]), 1)

    def test_get_all_exchanges_field(self):
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=10, stock=5)
        self._submit(uid, pid)
        r = self.lib.get_all_exchanges()
        record = r["data"]["records"][0]
        for f in ["exchange_id", "user_id", "product_id", "product_name", "status"]:
            self.assertIn(f, record)

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.check_user_points("x")["success"])
            self.assertFalse(self.lib.submit_exchange("x", 1)["success"])
            self.assertFalse(self.lib.cancel_exchange(1, "u")["success"])
            self.assertFalse(self.lib.complete_exchange(1)["success"])
            self.assertFalse(self.lib.reject_exchange(1)["success"])
            self.assertFalse(self.lib.get_user_exchanges("x")["success"])
            self.assertFalse(self.lib.get_all_exchanges()["success"])

    # ==================== 综合业务场景 ====================

    def test_full_lifecycle_complete(self):
        """提交 → 完成"""
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.assertEqual(self.lib.get_user_exchanges(uid)["data"]["records"][0]["status"], 0)
        self.lib.complete_exchange(eid)
        self.assertEqual(self.lib.get_user_exchanges(uid)["data"]["records"][0]["status"], 1)

    def test_full_lifecycle_cancel(self):
        """提交 → 取消"""
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.cancel_exchange(eid, uid)
        self.assertEqual(self.lib.get_user_exchanges(uid)["data"]["records"][0]["status"], 2)

    def test_full_lifecycle_reject(self):
        """提交 → 拒绝"""
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.reject_exchange(eid, "不符合条件")
        self.assertEqual(self.lib.get_user_exchanges(uid)["data"]["records"][0]["status"], 2)

    def test_cancel_then_resubmit(self):
        """取消后可以重新兑换同一商品"""
        uid = self._add_user(points=500)
        pid = self._add_product(points_required=100, stock=5)
        eid1 = self._submit(uid, pid)["data"]["exchange_id"]
        self.lib.cancel_exchange(eid1, uid)
        r = self._submit(uid, pid)
        self.assertTrue(r["success"])
        self.assertNotEqual(r["data"]["exchange_id"], eid1)

    def test_multiple_users_same_product(self):
        """多用户兑换同一商品"""
        pid = self._add_product(points_required=10, stock=5)
        for _ in range(3):
            uid = self._add_user(points=500)
            self._submit(uid, pid)
        r = self.lib.get_all_exchanges()
        self.assertGreaterEqual(r["data"]["total"], 3)

    def test_same_user_multiple_products(self):
        """同一用户兑换多个商品"""
        uid = self._add_user(points=500)
        for _ in range(3):
            pid = self._add_product(points_required=10, stock=5)
            self._submit(uid, pid)
        r = self.lib.get_user_exchanges(uid)
        self.assertEqual(r["data"]["total"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
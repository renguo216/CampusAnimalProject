# backend/tests/test_exchange_product_library.py
"""
ExchangeProductLibrary 完整测试套件（unittest 框架）
运行方式：
    cd 项目根目录
    python -m backend.tests.test_exchange_product_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_exchange_product 表已存在
"""

import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.exchange_product_library import ExchangeProductLibrary


class TestExchangeProductLibrary(unittest.TestCase):
    """ExchangeProductLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = ExchangeProductLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.product_ids = []

    def tearDown(self):
        if not self.product_ids:
            return
        db = self.lib.db
        try:
            if db.connection is None:
                if not db.open_database():
                    return
                need_close = True
            else:
                need_close = False
            for pid in self.product_ids:
                db.execute_raw_sql("DELETE FROM t_exchange_product WHERE product_id=%s", (pid,))
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
            db.execute_raw_sql("DELETE FROM t_exchange_product WHERE name LIKE %s", ("test_product_%",))
            if need_close:
                db.close_database()
        except Exception as e:
            print(f"[_cleanup_all 警告] 清理失败: {e}")

    # ---- 辅助方法 ----

    def _add_product(self, name=None, points_required=100, stock=10, status=1, **kwargs):
        """创建测试商品并返回 product_id"""
        if name is None:
            name = f"test_product_{uuid.uuid4().hex[:8]}"
        data = {
            "name": name,
            "points_required": points_required,
            "stock": stock,
            "status": status,
            **kwargs
        }
        r = self.lib.create_exchange_product(data)
        if not r.get("success"):
            raise RuntimeError(f"创建商品失败: {r}")
        pid = r["data"]["product_id"]
        self.product_ids.append(pid)
        return pid

    # ==================== create_exchange_product ====================

    def test_create_product_success(self):
        r = self.lib.create_exchange_product({
            "name": f"test_product_{uuid.uuid4().hex[:8]}",
            "description": "测试描述",
            "points_required": 100,
            "image_url": "http://example.com/1.jpg",
            "stock": 10,
            "status": 1
        })
        self.assertTrue(r["success"])
        self.assertIn("product_id", r["data"])
        self.product_ids.append(r["data"]["product_id"])

    def test_create_product_missing_name(self):
        r = self.lib.create_exchange_product({"points_required": 50, "stock": 5})
        self.assertFalse(r["success"])
        self.assertIn("name", r["message"])

    def test_create_product_missing_points_required(self):
        r = self.lib.create_exchange_product({"name": "测试商品", "stock": 5})
        self.assertFalse(r["success"])
        self.assertIn("points_required", r["message"])

    def test_create_product_default_stock(self):
        """stock 不是必填，默认值为 0"""
        r = self.lib.create_exchange_product({
            "name": f"test_product_{uuid.uuid4().hex[:8]}",
            "points_required": 50
        })
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["stock"], 0)
        self.product_ids.append(r["data"]["product_id"])

    # ==================== get_exchange_item_by_id ====================

    def test_get_item_by_id_success(self):
        pid = self._add_product(name="查询测试商品", points_required=50)
        r = self.lib.get_exchange_item_by_id(pid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["name"], "查询测试商品")
        self.assertEqual(r["data"]["points_required"], 50)

    def test_get_item_by_id_not_found(self):
        r = self.lib.get_exchange_item_by_id(999999)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== product_exists ====================

    def test_product_exists_true(self):
        pid = self._add_product()
        r = self.lib.product_exists(pid)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["exists"])

    def test_product_exists_false(self):
        r = self.lib.product_exists(999999)
        self.assertTrue(r["success"])  # product_exists 始终返回 success=True
        self.assertFalse(r["data"]["exists"])

    # ==================== get_exchange_items ====================
    # 注意：get_exchange_items 使用 get_paginated，返回 data.data 为列表

    def test_get_items_success(self):
        for _ in range(3):
            self._add_product(status=1)
        r = self.lib.get_exchange_items(page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 3)
        self.assertGreaterEqual(len(r["data"]["data"]), 3)
        for f in ["data", "total", "page", "page_size", "total_pages"]:
            self.assertIn(f, r["data"])

    def test_get_items_pagination(self):
        for _ in range(3):
            self._add_product(status=1)
        p1 = self.lib.get_exchange_items(page=1, page_size=2)
        self.assertEqual(len(p1["data"]["data"]), 2)
        p2 = self.lib.get_exchange_items(page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["data"]), 1)

    # ==================== update_exchange_product ====================

    def test_update_product_success(self):
        pid = self._add_product(name="更新前名称")
        r = self.lib.update_exchange_product(pid, {"name": "更新后名称", "stock": 20})
        self.assertTrue(r["success"])
        detail = self.lib.get_exchange_item_by_id(pid)
        self.assertEqual(detail["data"]["name"], "更新后名称")
        self.assertEqual(detail["data"]["stock"], 20)

    def test_update_product_illegal_fields(self):
        pid = self._add_product()
        r = self.lib.update_exchange_product(pid, {"illegal": "test"})
        self.assertFalse(r["success"])
        self.assertIn("没有有效更新字段", r["message"])

    def test_update_product_not_found(self):
        r = self.lib.update_exchange_product(999999, {"name": "test"})
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== update_product_stock ====================

    def test_update_stock_success(self):
        pid = self._add_product(stock=10)
        r = self.lib.update_product_stock(pid, 5)
        self.assertTrue(r["success"])
        stock = self.lib.get_product_stock(pid)
        self.assertEqual(stock["data"]["stock"], 5)

    def test_update_stock_not_found(self):
        r = self.lib.update_product_stock(999999, 5)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== get_product_stock ====================

    def test_get_stock_success(self):
        pid = self._add_product(stock=15)
        r = self.lib.get_product_stock(pid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["stock"], 15)

    def test_get_stock_not_found(self):
        r = self.lib.get_product_stock(999999)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== toggle_product_status ====================

    def test_toggle_status_off(self):
        pid = self._add_product(status=1)
        r = self.lib.toggle_product_status(pid, 0)
        self.assertTrue(r["success"])
        detail = self.lib.get_exchange_item_by_id(pid)
        self.assertEqual(detail["data"]["status"], 0)

    def test_toggle_status_on(self):
        pid = self._add_product(status=0)
        r = self.lib.toggle_product_status(pid, 1)
        self.assertTrue(r["success"])
        detail = self.lib.get_exchange_item_by_id(pid)
        self.assertEqual(detail["data"]["status"], 1)

    def test_toggle_status_not_found(self):
        r = self.lib.toggle_product_status(999999, 0)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== delete_exchange_product ====================

    def test_delete_product_success(self):
        pid = self._add_product()
        r = self.lib.delete_exchange_product(pid)
        self.assertTrue(r["success"])
        check = self.lib.get_exchange_item_by_id(pid)
        self.assertFalse(check["success"])
        self.assertIn("不存在", check["message"])

    def test_delete_product_not_found(self):
        r = self.lib.delete_exchange_product(999999)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        from unittest.mock import patch
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.create_exchange_product({"name": "x", "points_required": 1})["success"])
            self.assertFalse(self.lib.get_exchange_item_by_id(1)["success"])
            # product_exists 内部调用 get_exchange_item_by_id，即使 DB 失败也包装为 success=True
            exists_result = self.lib.product_exists(1)
            self.assertTrue(exists_result["success"])
            self.assertFalse(exists_result["data"]["exists"])
            self.assertFalse(self.lib.get_exchange_items()["success"])
            self.assertFalse(self.lib.update_exchange_product(1, {"name": "x"})["success"])
            self.assertFalse(self.lib.update_product_stock(1, 5)["success"])
            self.assertFalse(self.lib.get_product_stock(1)["success"])
            self.assertFalse(self.lib.toggle_product_status(1, 0)["success"])
            self.assertFalse(self.lib.delete_exchange_product(1)["success"])

    # ==================== 综合业务场景 ====================

    def test_full_lifecycle(self):
        """完整生命周期：创建 → 查询 → 更新 → 库存 → 上下架 → 删除"""
        # 创建
        r = self.lib.create_exchange_product({
            "name": f"test_product_{uuid.uuid4().hex[:8]}",
            "points_required": 50,
            "stock": 100,
            "status": 1
        })
        self.assertTrue(r["success"])
        pid = r["data"]["product_id"]
        self.product_ids.append(pid)

        # 查询
        detail = self.lib.get_exchange_item_by_id(pid)
        self.assertTrue(detail["success"])
        self.assertEqual(detail["data"]["stock"], 100)

        # 更新
        r = self.lib.update_exchange_product(pid, {"name": "已更新", "stock": 50})
        self.assertTrue(r["success"])
        detail = self.lib.get_exchange_item_by_id(pid)
        self.assertEqual(detail["data"]["name"], "已更新")
        self.assertEqual(detail["data"]["stock"], 50)

        # 库存修改
        r = self.lib.update_product_stock(pid, 30)
        self.assertTrue(r["success"])
        stock = self.lib.get_product_stock(pid)
        self.assertEqual(stock["data"]["stock"], 30)

        # 下架
        r = self.lib.toggle_product_status(pid, 0)
        self.assertTrue(r["success"])
        detail = self.lib.get_exchange_item_by_id(pid)
        self.assertEqual(detail["data"]["status"], 0)

        # 上架
        r = self.lib.toggle_product_status(pid, 1)
        self.assertTrue(r["success"])
        detail = self.lib.get_exchange_item_by_id(pid)
        self.assertEqual(detail["data"]["status"], 1)

        # 删除
        r = self.lib.delete_exchange_product(pid)
        self.assertTrue(r["success"])
        self.product_ids.remove(pid)
        check = self.lib.get_exchange_item_by_id(pid)
        self.assertFalse(check["success"])

    def test_create_multiple_and_list(self):
        """创建多个商品并验证列表"""
        for i in range(3):
            self._add_product(name=f"批量商品{i}", status=1)
        r = self.lib.get_exchange_items(page=1, page_size=20)
        self.assertTrue(r["success"])
        names = [item["name"] for item in r["data"]["data"]]
        for i in range(3):
            self.assertIn(f"批量商品{i}", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
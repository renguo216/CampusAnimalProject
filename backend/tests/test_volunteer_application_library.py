# backend/tests/test_volunteer_application_library.py
"""
VolunteerApplicationLibrary 完整测试套件（unittest 框架）
运行方式：
    cd 项目根目录
    python -m backend.tests.test_volunteer_application_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_volunteer_application 表已存在
"""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.volunteer_application_library import VolunteerApplicationLibrary
from backend.libs.user_library import UserLibrary


class TestVolunteerApplicationLibrary(unittest.TestCase):
    """VolunteerApplicationLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = VolunteerApplicationLibrary()
        cls.user_lib = UserLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.user_ids = []
        self.application_ids = []

    def tearDown(self):
        if not (self.user_ids or self.application_ids):
            return
        db = self.lib.db
        try:
            if db.connection is None:
                if not db.open_database():
                    return
                need_close = True
            else:
                need_close = False
            for app_id in self.application_ids:
                db.execute_raw_sql("DELETE FROM t_volunteer_application WHERE application_id=%s", (app_id,))
            for uid in self.user_ids:
                db.execute_raw_sql("DELETE FROM t_volunteer_application WHERE user_id=%s", (uid,))
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
            db.execute_raw_sql("DELETE FROM t_volunteer_application WHERE user_id LIKE %s", ("test_vol_%",))
            db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", ("test_vol_%",))
            if need_close:
                db.close_database()
        except Exception as e:
            print(f"[_cleanup_all 警告] 清理失败: {e}")

    # ---- 辅助方法 ----

    def _add_user(self, nickname=None, role=1, is_active=1):
        """注册测试用户并返回 user_id"""
        uid = f"test_vol_{uuid.uuid4().hex[:8]}"
        if nickname is None:
            nickname = f"nick_{uid[:8]}"
        r = self.user_lib.register_user(uid, nickname, avatar_url="http://x.com/a.jpg", role=role)
        if not r.get("success"):
            self.user_lib.delete_user(uid)
            r = self.user_lib.register_user(uid, nickname, avatar_url="http://x.com/a.jpg", role=role)
        if not r.get("success"):
            raise RuntimeError(f"注册用户失败: {r}")
        self.user_ids.append(uid)
        if is_active == 0:
            self.user_lib.toggle_active_status(uid, 0)
        return uid

    def _submit_app(self, user_id, content="我想成为志愿者"):
        """提交志愿者申请并返回 application_id"""
        r = self.lib.submit_volunteer_application(user_id, apply_content=content)
        if r.get("success"):
            self.application_ids.append(r["data"]["application_id"])
            return r["data"]["application_id"]
        return None

    # ==================== submit_volunteer_application ====================

    def test_submit_success(self):
        uid = self._add_user(role=1)
        r = self.lib.submit_volunteer_application(uid, "我想成为志愿者")
        self.assertTrue(r["success"])
        self.assertIn("application_id", r["data"])
        self.application_ids.append(r["data"]["application_id"])

    def test_submit_duplicate(self):
        uid = self._add_user(role=1)
        self._submit_app(uid)
        r = self.lib.submit_volunteer_application(uid, "再次提交")
        self.assertFalse(r["success"])
        self.assertIn("已提交过", r["message"])

    def test_submit_already_volunteer(self):
        uid = self._add_user(role=2)
        r = self.lib.submit_volunteer_application(uid, "test")
        self.assertFalse(r["success"])
        self.assertIn("已经是志愿者", r["message"])

    def test_submit_admin(self):
        uid = self._add_user(role=3)
        r = self.lib.submit_volunteer_application(uid, "test")
        self.assertFalse(r["success"])
        self.assertIn("管理员无需申请", r["message"])

    def test_submit_banned(self):
        uid = self._add_user(role=1, is_active=0)
        r = self.lib.submit_volunteer_application(uid, "test")
        self.assertFalse(r["success"])
        self.assertIn("封禁", r["message"])

    def test_submit_not_exists(self):
        r = self.lib.submit_volunteer_application("not_exist", "test")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== get_application_by_id ====================

    def test_get_application_success(self):
        uid = self._add_user(role=1)
        app_id = self._submit_app(uid)
        r = self.lib.get_application_by_id(app_id)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["application_id"], app_id)
        self.assertEqual(r["data"]["user_id"], uid)

    def test_get_application_not_found(self):
        r = self.lib.get_application_by_id(999999)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== update_volunteer_application ====================

    def test_update_application_success(self):
        uid = self._add_user(role=1)
        app_id = self._submit_app(uid, "原始理由")
        r = self.lib.update_volunteer_application(app_id, uid, "修改后的理由")
        self.assertTrue(r["success"])
        detail = self.lib.get_application_by_id(app_id)
        self.assertEqual(detail["data"]["apply_content"], "修改后的理由")

    def test_update_application_not_owner(self):
        uid = self._add_user(role=1)
        other = self._add_user(role=1)
        app_id = self._submit_app(uid)
        r = self.lib.update_volunteer_application(app_id, other, "越权修改")
        self.assertFalse(r["success"])
        self.assertIn("无权修改", r["message"])

    def test_update_application_not_pending(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.update_volunteer_application(app_id, uid, "test")
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    def test_update_application_not_found(self):
        uid = self._add_user(role=1)
        r = self.lib.update_volunteer_application(999999, uid, "test")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== cancel_volunteer_application ====================

    def test_cancel_application_success(self):
        uid = self._add_user(role=1)
        app_id = self._submit_app(uid)
        r = self.lib.cancel_volunteer_application(app_id, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 3)

    def test_cancel_application_not_owner(self):
        uid = self._add_user(role=1)
        other = self._add_user(role=1)
        app_id = self._submit_app(uid)
        r = self.lib.cancel_volunteer_application(app_id, other)
        self.assertFalse(r["success"])
        self.assertIn("无权撤销", r["message"])

    def test_cancel_application_not_pending(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.cancel_volunteer_application(app_id, uid)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    def test_cancel_application_not_found(self):
        uid = self._add_user(role=1)
        r = self.lib.cancel_volunteer_application(999999, uid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== get_application_status ====================

    def test_get_status_pending(self):
        uid = self._add_user(role=1)
        app_id = self._submit_app(uid)
        r = self.lib.get_application_status(app_id)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 0)
        self.assertEqual(r["data"]["status_text"], "待审核")

    def test_get_status_not_found(self):
        r = self.lib.get_application_status(999999)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== approve_application ====================

    def test_approve_success(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        r = self.lib.approve_application(app_id, admin, "审核通过")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 1)
        # 验证用户已升级为志愿者
        info = self.lib.get_volunteer_info(uid)
        self.assertTrue(info["success"])
        self.assertIsNotNone(info["data"]["volunteer_id"])

    def test_approve_not_pending(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.approve_application(app_id, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    def test_approve_not_admin(self):
        uid = self._add_user(role=1)
        other = self._add_user(role=1)
        app_id = self._submit_app(uid)
        r = self.lib.approve_application(app_id, other)
        self.assertFalse(r["success"])
        self.assertIn("仅管理员", r["message"])

    def test_approve_not_found(self):
        admin = self._add_user(role=3)
        r = self.lib.approve_application(999999, admin)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== reject_application ====================

    def test_reject_success(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        r = self.lib.reject_application(app_id, admin, "不符合条件")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)
        self.assertEqual(r["data"]["review_comment"], "不符合条件")

    def test_reject_not_pending(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.reject_application(app_id, admin)
        r = self.lib.reject_application(app_id, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅待审核", r["message"])

    def test_reject_not_admin(self):
        uid = self._add_user(role=1)
        other = self._add_user(role=1)
        app_id = self._submit_app(uid)
        r = self.lib.reject_application(app_id, other)
        self.assertFalse(r["success"])
        self.assertIn("仅管理员", r["message"])

    # ==================== get_user_applications ====================

    def test_get_user_applications(self):
        uid = self._add_user(role=1)
        # 提交一个待审核的申请
        app1 = self._submit_app(uid, "申请1")
        # 再降级为普通用户后重新申请（模拟驳回后重申请）
        admin = self._add_user(role=3)
        self.lib.approve_application(app1, admin)
        # 降级回普通用户
        self.user_lib.update_role(uid, 1)
        app2 = self._submit_app(uid, "申请2")
        r = self.lib.get_user_applications(uid, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 2)
        self.assertGreaterEqual(len(r["data"]["applications"]), 2)

    def test_get_user_applications_pagination(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app1 = self._submit_app(uid, "申请1")
        self.lib.approve_application(app1, admin)
        self.user_lib.update_role(uid, 1)
        app2 = self._submit_app(uid, "申请2")
        self.lib.approve_application(app2, admin)
        self.user_lib.update_role(uid, 1)
        app3 = self._submit_app(uid, "申请3")
        r = self.lib.get_user_applications(uid, page=1, page_size=1)
        self.assertEqual(len(r["data"]["applications"]), 1)

    # ==================== get_all_applications ====================

    def test_get_all_applications(self):
        for _ in range(3):
            uid = self._add_user(role=1)
            self._submit_app(uid)
        r = self.lib.get_all_applications(page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 3)

    def test_get_all_applications_filter(self):
        uid1 = self._add_user(role=1)
        uid2 = self._add_user(role=1)
        admin = self._add_user(role=3)
        app1 = self._submit_app(uid1)
        app2 = self._submit_app(uid2)
        self.lib.approve_application(app1, admin)
        self.lib.reject_application(app2, admin)
        r = self.lib.get_all_applications(page=1, page_size=20, status_filter=1)
        self.assertTrue(r["success"])
        approved_ids = [a["application_id"] for a in r["data"]["applications"]]
        self.assertIn(app1, approved_ids)
        r2 = self.lib.get_all_applications(page=1, page_size=20, status_filter=2)
        rejected_ids = [a["application_id"] for a in r2["data"]["applications"]]
        self.assertIn(app2, rejected_ids)

    # ==================== get_pending_applications ====================

    def test_get_pending_applications(self):
        for _ in range(3):
            uid = self._add_user(role=1)
            self._submit_app(uid)
        r = self.lib.get_pending_applications(page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 3)
        for app in r["data"]["applications"]:
            self.assertEqual(app["status"], 0)

    # ==================== get_volunteer_info ====================

    def test_get_volunteer_info_success(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.get_volunteer_info(uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["user_id"], uid)
        self.assertIsNotNone(r["data"]["volunteer_id"])

    def test_get_volunteer_info_not_volunteer(self):
        uid = self._add_user(role=1)
        r = self.lib.get_volunteer_info(uid)
        self.assertFalse(r["success"])
        self.assertIn("不是志愿者", r["message"])

    # ==================== get_volunteer_number ====================

    def test_get_volunteer_number(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.get_volunteer_number(uid)
        self.assertTrue(r["success"])
        self.assertIsNotNone(r["data"]["volunteer_id"])

    def test_get_volunteer_number_not_volunteer(self):
        uid = self._add_user(role=1)
        r = self.lib.get_volunteer_number(uid)
        self.assertTrue(r["success"])
        self.assertIsNone(r["data"]["volunteer_id"])

    # ==================== get_volunteer_level ====================

    def test_get_volunteer_level(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.get_volunteer_level(uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["level"], 1)

    def test_get_volunteer_level_not_volunteer(self):
        uid = self._add_user(role=1)
        r = self.lib.get_volunteer_level(uid)
        self.assertTrue(r["success"])
        self.assertIsNone(r["data"]["level"])

    # ==================== update_volunteer_level ====================

    def test_update_volunteer_level_success(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.update_volunteer_level(uid, 5, admin)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["level"], 5)
        level = self.lib.get_volunteer_level(uid)
        self.assertEqual(level["data"]["level"], 5)

    def test_update_volunteer_level_not_admin(self):
        uid = self._add_user(role=1)
        other = self._add_user(role=1)
        r = self.lib.update_volunteer_level(uid, 5, other)
        self.assertFalse(r["success"])
        self.assertIn("仅管理员", r["message"])

    def test_update_volunteer_level_not_volunteer(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        r = self.lib.update_volunteer_level(uid, 5, admin)
        self.assertFalse(r["success"])
        self.assertIn("不是志愿者", r["message"])

    def test_update_volunteer_level_invalid(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.update_volunteer_level(uid, 0, admin)
        self.assertFalse(r["success"])
        self.assertIn("正整数", r["message"])

    # ==================== count_applications_by_status ====================

    def test_count_applications(self):
        for _ in range(3):
            uid = self._add_user(role=1)
            self._submit_app(uid)
        r = self.lib.count_applications_by_status()
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 3)
        self.assertGreaterEqual(r["data"]["pending"], 3)

    # ==================== count_approved_volunteers ====================

    def test_count_approved_volunteers(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        app_id = self._submit_app(uid)
        self.lib.approve_application(app_id, admin)
        r = self.lib.count_approved_volunteers()
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["count"], 1)

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.submit_volunteer_application("u", "c")["success"])
            self.assertFalse(self.lib.get_application_by_id(1)["success"])
            self.assertFalse(self.lib.update_volunteer_application(1, "u", "c")["success"])
            self.assertFalse(self.lib.cancel_volunteer_application(1, "u")["success"])
            self.assertFalse(self.lib.get_application_status(1)["success"])
            self.assertFalse(self.lib.approve_application(1, "a")["success"])
            self.assertFalse(self.lib.reject_application(1, "a")["success"])
            self.assertFalse(self.lib.get_user_applications("u")["success"])
            self.assertFalse(self.lib.get_all_applications()["success"])
            self.assertFalse(self.lib.get_pending_applications()["success"])
            self.assertFalse(self.lib.get_volunteer_info("u")["success"])
            self.assertFalse(self.lib.get_volunteer_number("u")["success"])
            self.assertFalse(self.lib.get_volunteer_level("u")["success"])
            self.assertFalse(self.lib.update_volunteer_level("u", 1, "a")["success"])
            self.assertFalse(self.lib.count_applications_by_status()["success"])
            self.assertFalse(self.lib.count_approved_volunteers()["success"])

    # ==================== 综合业务场景 ====================

    def test_full_lifecycle(self):
        """完整生命周期：提交 → 修改 → 查询 → 通过 → 查志愿者信息 → 升级等级"""
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)

        # 提交
        r = self.lib.submit_volunteer_application(uid, "原始理由")
        self.assertTrue(r["success"])
        app_id = r["data"]["application_id"]
        self.application_ids.append(app_id)

        # 修改
        r = self.lib.update_volunteer_application(app_id, uid, "修改后的理由")
        self.assertTrue(r["success"])

        # 查询详情
        detail = self.lib.get_application_by_id(app_id)
        self.assertEqual(detail["data"]["apply_content"], "修改后的理由")

        # 查询状态
        status = self.lib.get_application_status(app_id)
        self.assertEqual(status["data"]["status"], 0)

        # 通过
        r = self.lib.approve_application(app_id, admin, "审核通过")
        self.assertTrue(r["success"])

        # 查志愿者信息
        info = self.lib.get_volunteer_info(uid)
        self.assertTrue(info["success"])
        self.assertIsNotNone(info["data"]["volunteer_id"])

        # 升级等级
        r = self.lib.update_volunteer_level(uid, 3, admin)
        self.assertTrue(r["success"])
        level = self.lib.get_volunteer_level(uid)
        self.assertEqual(level["data"]["level"], 3)

    def test_reject_then_reapply(self):
        """驳回后可以重新申请"""
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)

        app1 = self._submit_app(uid, "第一次申请")
        self.lib.reject_application(app1, admin, "不符合条件")

        # 重新申请
        app2 = self._submit_app(uid, "第二次申请")
        self.assertIsNotNone(app2)
        self.assertNotEqual(app1, app2)

        # 这次通过
        r = self.lib.approve_application(app2, admin)
        self.assertTrue(r["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
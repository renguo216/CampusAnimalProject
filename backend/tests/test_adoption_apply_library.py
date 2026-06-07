# backend/tests/test_adoption_apply_library.py
"""
AdoptionApplyLibrary 完整测试套件
运行方式：
    cd 项目根目录
    python -m backend.tests.test_adoption_apply_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_animal、t_adoptionapply 表已存在
"""

import os
import sys
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.adoption_apply_library import AdoptionApplyLibrary
from backend.libs.user_library import UserLibrary
from backend.libs.animal_library import AnimalLibrary
from backend.utils.response import error_response



# 期望的申请详情字段（详情和列表共用）
EXPECTED_FIELDS = [
    "apply_id", "pet_id", "user_id", "applicant_nickname",
    "applicant_avatar", "pet_name", "pet_breed", "pet_photo_urls",
    "pet_status", "status", "content", "review_comment", "created_at"
]


class TestAdoptionApplyLibrary(unittest.TestCase):
    """AdoptionApplyLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = AdoptionApplyLibrary()
        cls.user_lib = UserLibrary()
        cls.animal_lib = AnimalLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.apply_ids = []
        self.pet_ids = []
        self.user_ids = []
        self.pet_names = []

    def tearDown(self):
        if not (self.apply_ids or self.pet_ids or self.user_ids):
            return
        if self.lib.db.open_database():
            for aid in self.apply_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_adoptionapply WHERE apply_id=%s", (aid,))
            for pid in self.pet_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_animal WHERE pet_id=%s", (pid,))
            for name in self.pet_names:
                self.lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name=%s", (name,))
            for uid in self.user_ids:
                self.lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id=%s", (uid,))
            self.lib.db.close_database()

    @classmethod
    def _cleanup_all(cls):
        if cls.lib.db.open_database():
            cls.lib.db.execute_raw_sql("DELETE FROM t_adoptionapply WHERE apply_id LIKE %s", ("test_apply_%",))
            cls.lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE %s", ("test_adopt_%",))
            cls.lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", ("test_adopt_user_%",))
            cls.lib.db.close_database()

    # ---- 辅助方法 ----

    def _add_user(self, **kw) -> str:
        uid = kw.pop("user_id", f"test_adopt_user_{uuid.uuid4().hex[:8]}")
        kw.pop("avatarURL", None)
        self.user_lib.register_user(uid, nickname=f"测试_{uuid.uuid4().hex[:6]}",
                                    avatar_url="http://x.com/a.jpg", role=1)
        self.user_ids.append(uid)
        return uid

    def _add_animal(self, **kw) -> int:
        kw.setdefault("name", f"test_adopt_{uuid.uuid4().hex[:8]}")
        kw.setdefault("breed", "田园猫")
        kw.setdefault("status", 0)
        r = self.animal_lib.add_animal(**kw)
        if not r.get("success"):
            raise RuntimeError(f"添加动物失败: {r}")
        pid = r["data"]["pet_id"]
        self.pet_ids.append(pid)
        self.pet_names.append(kw["name"])
        return pid

    def _submit(self, user_id, pet_id, content="") -> dict:
        r = self.lib.submit_adoption_application(user_id, pet_id, content)
        if r.get("success"):
            self.apply_ids.append(r["data"]["apply_id"])
        return r

    def _make_pending(self, user_id=None, pet_id=None) -> tuple:
        """创建一个待审核申请，返回 (apply_id, user_id, pet_id)"""
        uid = user_id or self._add_user()
        pid = pet_id or self._add_animal()
        r = self._submit(uid, pid, "测试")
        return r["data"]["apply_id"], uid, pid

    def _set_status(self, apply_id, status, **kw):
        """将申请设为指定状态：0=待审核, 1=通过, 2=驳回/取消"""
        if status == 1:
            return self.lib.approve_application(apply_id, self._add_user(), **kw)
        if status == 2 and "review_comment" in kw:
            return self.lib.reject_application(apply_id, **kw)
        if status == 2:
            # 取消需要 user_id
            return self.lib.cancel_adoption_application(apply_id, kw.get("user_id", self._add_user()))
        return {"success": True}

    # ==================== submit_adoption_application ====================

    def test_submit_success(self):
        """正常提交（带/不带理由均成功）"""
        uid, pid = self._add_user(), self._add_animal()
        r = self._submit(uid, pid, "喜欢这只猫")
        self.assertTrue(r["success"])
        self.assertEqual(len(r["data"]["apply_id"]), 32)

        uid2 = self._add_user()
        pid2 = self._add_animal()
        r2 = self._submit(uid2, pid2, "")
        self.assertTrue(r2["success"])

    def test_submit_user_not_exists(self):
        pid = self._add_animal()
        r = self.lib.submit_adoption_application("no_user_xxx", pid)
        self.assertFalse(r["success"])
        self.assertIn("用户不存在", r["message"])

    def test_submit_animal_not_exists(self):
        uid = self._add_user()
        r = self.lib.submit_adoption_application(uid, 999999)
        self.assertFalse(r["success"])
        self.assertIn("动物不存在", r["message"])

    def test_submit_animal_adopted(self):
        uid = self._add_user()
        pid = self._add_animal(status=1)
        r = self.lib.submit_adoption_application(uid, pid)
        self.assertFalse(r["success"])
        self.assertIn("已被领养", r["message"])

    def test_submit_duplicate(self):
        uid, pid = self._add_user(), self._add_animal()
        r1 = self._submit(uid, pid)
        r2 = self.lib.submit_adoption_application(uid, pid, "重复")
        self.assertFalse(r2["success"])
        self.assertIn("重复提交", r2["message"])
        self.assertEqual(r2["data"]["apply_id"], r1["data"]["apply_id"])

    def test_submit_db_errors(self):
        uid, pid = self._add_user(), self._add_animal()
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.submit_adoption_application(uid, pid)["success"])
        with patch.object(self.lib.db, 'execute_raw_sql', return_value=None):
            r = self.lib.submit_adoption_application(uid, pid)
            self.assertFalse(r["success"])
            self.assertIn("数据库插入失败", r["message"])

    # ==================== _check_duplicate_application ====================

    def test_check_duplicate(self):
        uid, pid = self._add_user(), self._add_animal()
        # 无重复
        r = self.lib._check_duplicate_application(uid, pid)
        self.assertTrue(r["success"])
        self.assertFalse(r["data"]["is_duplicate"])

        # 有重复
        self._submit(uid, pid)
        r2 = self.lib._check_duplicate_application(uid, pid)
        self.assertTrue(r2["data"]["is_duplicate"])

    def test_check_duplicate_after_status_change(self):
        """取消或驳回后不再视为重复"""
        uid, pid = self._add_user(), self._add_animal()
        aid = self._submit(uid, pid)["data"]["apply_id"]
        self.lib.cancel_adoption_application(aid, uid)
        self.assertFalse(self.lib._check_duplicate_application(uid, pid)["data"]["is_duplicate"])

        aid2 = self._submit(uid, pid)["data"]["apply_id"]
        self.lib.reject_application(aid2, "驳回")
        self.assertFalse(self.lib._check_duplicate_application(uid, pid)["data"]["is_duplicate"])

    def test_check_duplicate_different_user(self):
        uid1, uid2, pid = self._add_user(), self._add_user(), self._add_animal()
        self._submit(uid1, pid)
        self.assertFalse(self.lib._check_duplicate_application(uid2, pid)["data"]["is_duplicate"])

    # ==================== cancel_adoption_application ====================

    def test_cancel_success(self):
        aid, uid, _ = self._make_pending()
        r = self.lib.cancel_adoption_application(aid, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["status"], 2)

    def test_cancel_fail_conditions(self):
        """申请不存在 / 非本人 / 非待审核状态"""
        uid, other = self._add_user(), self._add_user()
        aid, _, _ = self._make_pending(uid)

        # 不存在
        self.assertFalse(self.lib.cancel_adoption_application("no_xxx", uid)["success"])

        # 非本人
        r = self.lib.cancel_adoption_application(aid, other)
        self.assertFalse(r["success"])
        self.assertIn("无权取消", r["message"])

        # 已通过后取消
        self._set_status(aid, 1)
        r = self.lib.cancel_adoption_application(aid, uid)
        self.assertFalse(r["success"])
        self.assertIn("只能取消待审核", r["message"])

    def test_cancel_after_reject_or_cancel(self):
        """已驳回/已取消的不能再取消"""
        for status_fn in [
            lambda a, u: self.lib.reject_application(a, "驳回"),
            lambda a, u: self.lib.cancel_adoption_application(a, u),
        ]:
            aid, uid, _ = self._make_pending()
            status_fn(aid, uid)
            r = self.lib.cancel_adoption_application(aid, uid)
            self.assertFalse(r["success"])
            self.assertIn("只能取消待审核", r["message"])

    # ==================== get_application_by_id ====================

    def test_get_by_id_success(self):
        aid, uid, pid = self._make_pending()
        r = self.lib.get_application_by_id(aid)
        self.assertTrue(r["success"])
        d = r["data"]
        self.assertEqual(d["apply_id"], aid)
        self.assertEqual(d["user_id"], uid)
        self.assertEqual(d["pet_id"], pid)
        self.assertEqual(d["status"], 0)
        for f in EXPECTED_FIELDS:
            self.assertIn(f, d)

    def test_get_by_id_not_exists(self):
        self.assertFalse(self.lib.get_application_by_id("no_xxx")["success"])

    def test_get_by_id_all_statuses(self):
        """各状态下的详情均可正常查询"""
        reviewer = self._add_user()
        for fn, expected_status in [
            (lambda a: None, 0),  # 待审核
            (lambda a: self.lib.approve_application(a, reviewer, "通过"), 1),
            (lambda a: self.lib.reject_application(a, "驳回"), 2),
        ]:
            aid, uid, _ = self._make_pending()
            if fn(aid):
                pass  # 执行状态变更
            d = self.lib.get_application_by_id(aid)["data"]
            self.assertEqual(d["status"], expected_status)

    def test_get_by_id_created_at_format(self):
        aid, _, _ = self._make_pending()
        t = self.lib.get_application_by_id(aid)["data"]["created_at"]
        datetime.strptime(t, "%Y-%m-%d %H:%M:%S")  # 不抛异常即通过

    # ==================== get_user_applications ====================

    def test_get_user_apps_success(self):
        uid = self._add_user()
        for _ in range(3):
            self._submit(uid, self._add_animal())
        r = self.lib.get_user_applications(uid, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 3)
        self.assertEqual(len(r["data"]["applications"]), 3)
        for f in ["applications", "total", "page", "page_size"]:
            self.assertIn(f, r["data"])

    def test_get_user_apps_empty(self):
        r = self.lib.get_user_applications("no_user_xxx")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)

    def test_get_user_apps_pagination(self):
        uid = self._add_user()
        for _ in range(3):
            self._submit(uid, self._add_animal())
        p1 = self.lib.get_user_applications(uid, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["applications"]), 2)
        p2 = self.lib.get_user_applications(uid, page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["applications"]), 1)
        p99 = self.lib.get_user_applications(uid, page=99, page_size=20)
        self.assertEqual(len(p99["data"]["applications"]), 0)

    def test_get_user_apps_order_desc(self):
        uid = self._add_user()
        self._submit(uid, self._add_animal())
        self._submit(uid, self._add_animal())
        apps = self.lib.get_user_applications(uid)["data"]["applications"]
        t1 = datetime.strptime(apps[0]["created_at"], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(apps[1]["created_at"], "%Y-%m-%d %H:%M:%S")
        self.assertGreaterEqual(t1, t2)

    def test_get_user_apps_field_completeness(self):
        uid = self._add_user()
        self._submit(uid, self._add_animal())
        app = self.lib.get_user_applications(uid)["data"]["applications"][0]
        for f in EXPECTED_FIELDS:
            self.assertIn(f, app)

    def test_get_user_apps_multiple_statuses(self):
        """列表中可同时包含不同状态的申请"""
        uid, reviewer = self._add_user(), self._add_user()
        self._submit(uid, self._add_animal())  # 待审核
        r2 = self._submit(uid, self._add_animal())
        self.lib.approve_application(r2["data"]["apply_id"], reviewer)  # 通过
        r3 = self._submit(uid, self._add_animal())
        self.lib.reject_application(r3["data"]["apply_id"], "驳回")  # 驳回
        statuses = {a["status"] for a in self.lib.get_user_applications(uid)["data"]["applications"]}
        self.assertEqual(statuses, {0, 1, 2})

    # ==================== get_animal_applications ====================

    def test_get_animal_apps_success(self):
        pid = self._add_animal()
        for _ in range(2):
            self._submit(self._add_user(), pid)
        r = self.lib.get_animal_applications(pid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 2)

    def test_get_animal_apps_empty(self):
        self.assertEqual(self.lib.get_animal_applications(999999)["data"]["total"], 0)

    def test_get_animal_apps_pagination(self):
        pid = self._add_animal()
        for _ in range(3):
            self._submit(self._add_user(), pid)
        p1 = self.lib.get_animal_applications(pid, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["applications"]), 2)
        p2 = self.lib.get_animal_applications(pid, page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["applications"]), 1)

    def test_get_animal_apps_field_and_order(self):
        pid = self._add_animal()
        self._submit(self._add_user(), pid)
        self._submit(self._add_user(), pid)
        apps = self.lib.get_animal_applications(pid)["data"]["applications"]
        for f in EXPECTED_FIELDS:
            self.assertIn(f, apps[0])
        t1 = datetime.strptime(apps[0]["created_at"], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(apps[1]["created_at"], "%Y-%m-%d %H:%M:%S")
        self.assertGreaterEqual(t1, t2)

    # ==================== approve_application ====================

    def test_approve_success(self):
        aid, uid, pid = self._make_pending()
        reviewer = self._add_user()
        r = self.lib.approve_application(aid, reviewer, "同意领养")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 1)
        # 验证申请和动物状态
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["status"], 1)
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["review_comment"], "同意领养")
        self.assertEqual(self.animal_lib.get_animal_by_id(pid)["data"]["status"], 1)

    def test_approve_without_comment(self):
        aid, _, _ = self._make_pending()
        self.assertTrue(self.lib.approve_application(aid, self._add_user())["success"])
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["review_comment"], "")

    def test_approve_fail_conditions(self):
        """不存在 / 非待审核状态"""
        reviewer = self._add_user()
        self.assertFalse(self.lib.approve_application("no_xxx", reviewer)["success"])

        for status_fn in [
            lambda a, u: self.lib.approve_application(a, reviewer),
            lambda a, u: self.lib.reject_application(a, "驳回"),
            lambda a, u: self.lib.cancel_adoption_application(a, u),
        ]:
            aid, uid, _ = self._make_pending()
            status_fn(aid, uid)
            r = self.lib.approve_application(aid, reviewer, "再次操作")
            self.assertFalse(r["success"])
            self.assertIn("只能审核待审核", r["message"])

    def test_approve_animal_update_fail_graceful(self):
        """动物状态更新失败时申请仍成功"""
        aid, _, _ = self._make_pending()
        with patch.object(self.lib.animal_lib, 'update_animal_status',
                          return_value=error_response("失败")):
            r = self.lib.approve_application(aid, self._add_user(), "同意")
        self.assertTrue(r["success"])

    # ==================== reject_application ====================

    def test_reject_success(self):
        aid, _, pid = self._make_pending()
        r = self.lib.reject_application(aid, "不符合条件")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["review_comment"], "不符合条件")
        # 动物状态不变
        self.assertEqual(self.animal_lib.get_animal_by_id(pid)["data"]["status"], 0)

    def test_reject_without_comment(self):
        aid, _, _ = self._make_pending()
        self.assertTrue(self.lib.reject_application(aid)["success"])
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["review_comment"], "")

    def test_reject_fail_conditions(self):
        """不存在 / 非待审核状态"""
        self.assertFalse(self.lib.reject_application("no_xxx")["success"])

        reviewer = self._add_user()
        for status_fn in [
            lambda a, u: self.lib.approve_application(a, reviewer),
            lambda a, u: self.lib.reject_application(a, "驳回"),
            lambda a, u: self.lib.cancel_adoption_application(a, u),
        ]:
            aid, uid, _ = self._make_pending()
            status_fn(aid, uid)
            r = self.lib.reject_application(aid, "再次操作")
            self.assertFalse(r["success"])
            self.assertIn("只能驳回待审核", r["message"])

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.get_application_by_id("x")["success"])
            self.assertFalse(self.lib.get_user_applications("x")["success"])
            self.assertFalse(self.lib.get_animal_applications(1)["success"])
            self.assertFalse(self.lib.cancel_adoption_application("x", "u")["success"])
            self.assertFalse(self.lib.approve_application("x", "r")["success"])
            self.assertFalse(self.lib.reject_application("x")["success"])
            self.assertFalse(self.lib._check_duplicate_application("u", 1)["success"])

    # ==================== 综合业务场景 ====================

    def test_full_lifecycle_approved(self):
        """提交 -> 待审核 -> 通过 -> 动物变为已领养"""
        aid, uid, pid = self._make_pending()
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["status"], 0)
        self.lib.approve_application(aid, self._add_user(), "通过")
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["status"], 1)
        self.assertEqual(self.animal_lib.get_animal_by_id(pid)["data"]["status"], 1)

    def test_full_lifecycle_rejected(self):
        """提交 -> 驳回 -> 动物状态不变"""
        aid, _, pid = self._make_pending()
        self.lib.reject_application(aid, "驳回")
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["status"], 2)
        self.assertEqual(self.animal_lib.get_animal_by_id(pid)["data"]["status"], 0)

    def test_full_lifecycle_cancelled(self):
        """提交 -> 取消 -> 动物状态不变"""
        aid, uid, pid = self._make_pending()
        self.lib.cancel_adoption_application(aid, uid)
        self.assertEqual(self.lib.get_application_by_id(aid)["data"]["status"], 2)
        self.assertEqual(self.animal_lib.get_animal_by_id(pid)["data"]["status"], 0)

    def test_cancel_or_reject_then_reapply(self):
        """取消/驳回后可重新申请同一动物"""
        for fn in [
            lambda a, u: self.lib.cancel_adoption_application(a, u),
            lambda a, u: self.lib.reject_application(a, "驳回"),
        ]:
            uid, pid = self._add_user(), self._add_animal()
            old_aid = self._submit(uid, pid)["data"]["apply_id"]
            fn(old_aid, uid)
            new_aid = self._submit(uid, pid)["data"]["apply_id"]
            self.assertNotEqual(old_aid, new_aid)

    def test_approved_animal_blocks_new_application(self):
        """动物被领养后新用户无法申请"""
        uid1, uid2 = self._add_user(), self._add_user()
        pid = self._add_animal()
        aid = self._submit(uid1, pid)["data"]["apply_id"]
        self.lib.approve_application(aid, self._add_user(), "同意")
        r = self.lib.submit_adoption_application(uid2, pid)
        self.assertFalse(r["success"])
        self.assertIn("已被领养", r["message"])

    def test_approve_one_does_not_affect_other_pending(self):
        """通过一个申请不影响同一动物的其他待审核申请"""
        pid = self._add_animal()
        aid1 = self._submit(self._add_user(), pid)["data"]["apply_id"]
        aid2 = self._submit(self._add_user(), pid)["data"]["apply_id"]
        self.lib.approve_application(aid1, self._add_user(), "同意")
        self.assertEqual(self.lib.get_application_by_id(aid1)["data"]["status"], 1)
        self.assertEqual(self.lib.get_application_by_id(aid2)["data"]["status"], 0)
        self.assertEqual(self.animal_lib.get_animal_by_id(pid)["data"]["status"], 1)

    def test_multiple_users_same_animal_and_vice_versa(self):
        """多用户申请同一动物 / 同一用户申请多只动物"""
        # 多用户 -> 同一动物
        pid = self._add_animal()
        for _ in range(3):
            self._submit(self._add_user(), pid)
        self.assertEqual(self.lib.get_animal_applications(pid)["data"]["total"], 3)

        # 同一用户 -> 多只动物
        uid = self._add_user()
        for _ in range(3):
            self._submit(uid, self._add_animal())
        self.assertGreaterEqual(self.lib.get_user_applications(uid)["data"]["total"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
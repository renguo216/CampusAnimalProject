# backend/tests/test_rescue_record_library.py
"""
RescueRecordLibrary 完整测试套件（unittest 框架）
运行方式：
    cd 项目根目录
    python -m backend.tests.test_rescue_record_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_animal、t_rescuerecord 表已存在
"""

import os
import sys
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.rescue_record_library import RescueRecordLibrary
from backend.libs.user_library import UserLibrary
from backend.libs.animal_library import AnimalLibrary


# 期望的详情字段（详情查询返回）
EXPECTED_DETAIL_FIELDS = [
    "record_id", "user_id", "user_nickname", "user_avatar",
    "helper_id", "helper_nickname", "helper_avatar",
    "pet_id", "pet_name", "title", "location", "found_location_text",
    "description", "need_type", "photo_urls", "priority", "animal_name",
    "location_lat", "location_lng",
    "status", "resolved_by", "resolver_nickname",
    "created_at", "updated_at", "completed_at"
]


class TestRescueRecordLibrary(unittest.TestCase):
    """RescueRecordLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = RescueRecordLibrary()
        cls.user_lib = UserLibrary()
        cls.animal_lib = AnimalLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.record_ids = []
        self.pet_ids = []
        self.user_ids = []

    def tearDown(self):
        if not (self.record_ids or self.pet_ids or self.user_ids):
            return
        db = self.lib.db
        # 如果 open_database 被 Mock 了，先恢复
        if hasattr(db.open_database, '_mock_name'):
            # patch 未正确恢复，跳过清理（依赖 tearDownClass 统一清理）
            return
        if db.open_database():
            try:
                for rid in self.record_ids:
                    db.execute_raw_sql("DELETE FROM t_rescuerecord WHERE record_id=%s", (rid,))
                for pid in self.pet_ids:
                    db.execute_raw_sql("DELETE FROM t_animal WHERE pet_id=%s", (pid,))
                for uid in self.user_ids:
                    db.execute_raw_sql("DELETE FROM t_user WHERE user_id=%s", (uid,))
            finally:
                db.close_database()

    @classmethod
    def _cleanup_all(cls):
        db = cls.lib.db
        try:
            if db.open_database():
                db.execute_raw_sql(
                    "DELETE FROM t_rescuerecord WHERE user_id LIKE %s OR helper_id LIKE %s",
                    ("test_rescue_%", "test_rescue_%")
                )
                db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE %s", ("test_rescue_%",))
                db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", ("test_rescue_%",))
                db.close_database()
        except Exception as e:
            print(f"[_cleanup_all 警告] 清理失败: {e}")

    # ---- 辅助方法 ----

    def _add_user(self, role=1, is_active=1):
        """注册测试用户并返回 user_id"""
        uid = f"test_rescue_{uuid.uuid4().hex[:8]}"
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

    def _add_animal(self, **kw):
        """添加测试动物并返回 pet_id"""
        kw.setdefault("name", f"test_rescue_{uuid.uuid4().hex[:8]}")
        kw.setdefault("breed", "田园猫")
        kw.setdefault("status", 0)
        r = self.animal_lib.add_animal(**kw)
        if not r.get("success"):
            raise RuntimeError(f"添加动物失败: {r}")
        pid = r["data"]["pet_id"]
        self.pet_ids.append(pid)
        return pid

    def _create_record(self, user_id, **kw):
        """创建救助记录并返回 record_id"""
        kw.setdefault("title", f"救助_{uuid.uuid4().hex[:6]}")
        kw.setdefault("description", "测试描述")
        kw.setdefault("location", "测试地点")
        r = self.lib.create_rescue_record(user_id, **kw)
        if not r.get("success"):
            raise RuntimeError(f"创建救助记录失败: {r}")
        rid = r["data"]["record_id"]
        self.record_ids.append(rid)
        return rid

    def _claim(self, record_id, helper_id):
        r = self.lib.claim_rescue(record_id, helper_id)
        if not r.get("success"):
            raise RuntimeError(f"接单失败: {r}")
        return r

    def _complete(self, record_id, user_id):
        r = self.lib.complete_rescue(record_id, user_id)
        if not r.get("success"):
            raise RuntimeError(f"标记完成失败: {r}")
        return r

    def _confirm(self, record_id, admin_id):
        r = self.lib.confirm_rescue(record_id, admin_id)
        if not r.get("success"):
            raise RuntimeError(f"确认完成失败: {r}")
        return r

    def _close(self, record_id, operator_id):
        r = self.lib.close_rescue(record_id, operator_id)
        if not r.get("success"):
            raise RuntimeError(f"关闭失败: {r}")
        return r

    # ==================== create_rescue_record ====================

    def test_create_success(self):
        """正常创建，返回 record_id 和 status=0"""
        uid = self._add_user()
        r = self.lib.create_rescue_record(uid, title="正常创建")
        self.assertTrue(r["success"])
        self.assertEqual(len(r["data"]["record_id"]), 32)
        self.assertEqual(r["data"]["status"], 0)
        self.record_ids.append(r["data"]["record_id"])

    def test_create_with_full_fields(self):
        """带全字段创建，验证各字段保存正确"""
        uid = self._add_user()
        rid = self._create_record(
            uid, title="完整字段", description="详细说明", location="图书馆",
            found_location_text="图书馆门口", need_type="救助", priority=2,
            location_lat=31.1234567, location_lng=121.12345678,
            photo_urls='["http://p.jpg"]', animal_name="小白"
        )
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["title"], "完整字段")
        self.assertEqual(d["description"], "详细说明")
        self.assertEqual(d["location"], "图书馆")
        self.assertEqual(d["found_location_text"], "图书馆门口")
        self.assertEqual(d["need_type"], "救助")
        self.assertEqual(d["priority"], 2)
        self.assertEqual(d["location_lat"], 31.1234567)
        self.assertEqual(d["location_lng"], 121.12345678)
        self.assertEqual(d["animal_name"], "小白")
        self.assertEqual(d["photo_urls"], '["http://p.jpg"]')

    def test_create_with_pet_id(self):
        """创建时携带 pet_id"""
        uid = self._add_user()
        pid = self._add_animal()
        r = self.lib.create_rescue_record(uid, title="带动物", pet_id=pid)
        self.assertTrue(r["success"])
        self.record_ids.append(r["data"]["record_id"])
        d = self.lib.get_rescue_record_by_id(r["data"]["record_id"])["data"]
        self.assertEqual(d["pet_id"], pid)

    def test_create_without_title(self):
        """不传 title 也能创建（title 默认 None）"""
        uid = self._add_user()
        r = self.lib.create_rescue_record(uid)
        self.assertTrue(r["success"])
        self.record_ids.append(r["data"]["record_id"])

    def test_create_user_not_exists(self):
        """无效用户创建失败"""
        r = self.lib.create_rescue_record("no_user", title="test")
        self.assertFalse(r["success"])
        self.assertIn("用户不存在", r["message"])

    def test_create_user_banned(self):
        """封禁用户创建失败"""
        banned = self._add_user(is_active=0)
        r = self.lib.create_rescue_record(banned, title="test")
        self.assertFalse(r["success"])
        self.assertIn("封禁", r["message"])

    def test_create_ai_success(self):
        """AI 成功识别并自动填充 animal_name"""
        uid = self._add_user()
        with patch('backend.libs.rescue_record_library.requests.get') as mock_get,              patch('backend.libs.rescue_record_library.detect_species') as mock_detect:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"fake_img"
            mock_get.return_value = mock_resp
            mock_detect.return_value = {
                "success": True, "category": "cat", "breed": "tabby",
                "breed_name": "虎斑猫", "confidence": 0.92
            }
            r = self.lib.create_rescue_record(
                uid, title="AI识别测试",
                photo_urls='["http://example.com/photo.jpg"]'
            )
            self.assertTrue(r["success"])
            self.record_ids.append(r["data"]["record_id"])
            d = self.lib.get_rescue_record_by_id(r["data"]["record_id"])["data"]
            self.assertEqual(d["animal_name"], "虎斑猫")

    def test_create_ai_fail(self):
        """AI 识别失败不阻塞创建，animal_name 保持 None"""
        uid = self._add_user()
        with patch('backend.libs.rescue_record_library.requests.get') as mock_get,              patch('backend.libs.rescue_record_library.detect_species') as mock_detect:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"fake_img"
            mock_get.return_value = mock_resp
            mock_detect.return_value = {"success": False}
            r = self.lib.create_rescue_record(
                uid, title="AI失败测试",
                photo_urls='["http://example.com/bad.jpg"]'
            )
            self.assertTrue(r["success"])
            self.record_ids.append(r["data"]["record_id"])
            d = self.lib.get_rescue_record_by_id(r["data"]["record_id"])["data"]
            self.assertIsNone(d["animal_name"])

    def test_create_no_photo_no_ai(self):
        """无图片且已有 animal_name，不触发 AI"""
        uid = self._add_user()
        r = self.lib.create_rescue_record(uid, title="无AI", animal_name="已手动命名")
        self.assertTrue(r["success"])
        self.record_ids.append(r["data"]["record_id"])
        d = self.lib.get_rescue_record_by_id(r["data"]["record_id"])["data"]
        self.assertEqual(d["animal_name"], "已手动命名")

    # ==================== get_rescue_record_by_id ====================

    def test_get_by_id_success(self):
        """正常查询详情，字段完整"""
        uid = self._add_user()
        rid = self._create_record(uid, title="详情测试", description="说明", location="地点",
                                  found_location_text="门口", need_type="救助", priority=1,
                                  photo_urls='["http://p.jpg"]', animal_name="小白")
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["record_id"], rid)
        self.assertEqual(d["user_id"], uid)
        self.assertEqual(d["title"], "详情测试")
        self.assertEqual(d["status"], 0)
        for f in EXPECTED_DETAIL_FIELDS:
            self.assertIn(f, d)

    def test_get_by_id_not_exists(self):
        r = self.lib.get_rescue_record_by_id("no_xxx")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_get_by_id_deleted(self):
        """软删除后查询不到"""
        uid = self._add_user()
        rid = self._create_record(uid)
        self.lib.delete_rescue_record(rid, uid)
        r = self.lib.get_rescue_record_by_id(rid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_get_by_id_all_statuses(self):
        """各状态下的详情均可正常查询"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        for setup_fn, expected in [
            (lambda r: None, 0),                                    # 待接单
            (lambda r: self.lib.claim_rescue(r, volunteer), 1),     # 救助中
            (lambda r: (self.lib.claim_rescue(r, volunteer),        # 待确认
                        self.lib.complete_rescue(r, uid)), 2),
            (lambda r: (self.lib.claim_rescue(r, volunteer),        # 已完成
                        self.lib.complete_rescue(r, uid),
                        self.lib.confirm_rescue(r, admin)), 3),
        ]:
            rid = self._create_record(uid, title="状态测试")
            setup_fn(rid)
            self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], expected)

    def test_get_by_id_with_helper(self):
        """查询包含 helper 信息"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["helper_id"], volunteer)
        self.assertEqual(d["helper_nickname"], f"nick_{volunteer[:8]}")

    def test_get_by_id_with_resolver(self):
        """查询包含 resolver 信息"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        self._confirm(rid, admin)
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["resolved_by"], admin)
        self.assertEqual(d["resolver_nickname"], f"nick_{admin[:8]}")

    def test_get_by_id_with_pet(self):
        """查询包含 pet 信息"""
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        pid = self._add_animal(name="关联动物")
        rid = self._create_record(uid)
        self.lib.link_animal(rid, pid, admin)
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["pet_id"], pid)
        self.assertEqual(d["pet_name"], "关联动物")

    def test_get_by_id_created_at_format(self):
        """created_at 格式为 %Y-%m-%d %H:%M:%S"""
        uid = self._add_user()
        rid = self._create_record(uid)
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        t = d.get("created_at")
        self.assertIsNotNone(t, f"created_at 为 None，data={d}")
        # 支持 datetime 对象或字符串
        if hasattr(t, 'strftime'):
            t = t.strftime("%Y-%m-%d %H:%M:%S")
        datetime.strptime(t, "%Y-%m-%d %H:%M:%S")

    # ==================== update_rescue_record ====================

    def test_update_success(self):
        """上报人修改成功"""
        uid = self._add_user()
        rid = self._create_record(uid, title="原标题")
        r = self.lib.update_rescue_record(rid, uid, title="新标题", description="新描述", priority=2)
        self.assertTrue(r["success"])
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["title"], "新标题")
        self.assertEqual(d["description"], "新描述")
        self.assertEqual(d["priority"], 2)

    def test_update_by_helper(self):
        """接单志愿者可以修改"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.update_rescue_record(rid, volunteer, title="志愿者修改")
        self.assertTrue(r["success"])
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["title"], "志愿者修改")

    def test_update_by_admin(self):
        """管理员可以修改"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        r = self.lib.update_rescue_record(rid, admin, title="管理员修改")
        self.assertTrue(r["success"])

    def test_update_by_other(self):
        """其他用户无权修改"""
        uid = self._add_user()
        other = self._add_user()
        rid = self._create_record(uid)
        r = self.lib.update_rescue_record(rid, other, title="越权")
        self.assertFalse(r["success"])
        self.assertIn("无权修改", r["message"])

    def test_update_not_exists(self):
        uid = self._add_user()
        r = self.lib.update_rescue_record("no_xxx", uid, title="test")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_update_terminal_status(self):
        """终态（已完成/已关闭）不能修改"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._close(rid, uid)
        r = self.lib.update_rescue_record(rid, uid, title="修改")
        self.assertFalse(r["success"])
        self.assertIn("已完成或已关闭", r["message"])

        rid2 = self._create_record(uid)
        self._claim(rid2, volunteer)
        self._complete(rid2, uid)
        self._confirm(rid2, admin)
        r = self.lib.update_rescue_record(rid2, uid, title="修改")
        self.assertFalse(r["success"])
        self.assertIn("已完成或已关闭", r["message"])

    def test_update_partial(self):
        """只更新部分字段，其余保持不变"""
        uid = self._add_user()
        rid = self._create_record(uid, title="原", description="原描述")
        r = self.lib.update_rescue_record(rid, uid, title="新")
        self.assertTrue(r["success"])
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["title"], "新")
        self.assertEqual(d["description"], "原描述")

    # ==================== delete_rescue_record ====================

    def test_delete_success_by_reporter(self):
        """上报人软删除成功"""
        uid = self._add_user()
        rid = self._create_record(uid)
        r = self.lib.delete_rescue_record(rid, uid)
        self.assertTrue(r["success"])
        self.assertFalse(self.lib.get_rescue_record_by_id(rid)["success"])

    def test_delete_success_by_admin(self):
        """管理员软删除成功"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        r = self.lib.delete_rescue_record(rid, admin)
        self.assertTrue(r["success"])

    def test_delete_by_helper_fail(self):
        """接单志愿者无权删除"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.delete_rescue_record(rid, volunteer)
        self.assertFalse(r["success"])
        self.assertIn("无权删除", r["message"])

    def test_delete_by_other_fail(self):
        """其他用户无权删除"""
        uid = self._add_user()
        other = self._add_user()
        rid = self._create_record(uid)
        r = self.lib.delete_rescue_record(rid, other)
        self.assertFalse(r["success"])
        self.assertIn("无权删除", r["message"])

    def test_delete_not_exists(self):
        uid = self._add_user()
        r = self.lib.delete_rescue_record("no_xxx", uid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== 状态流转：claim / complete / confirm / close ====================

    def test_claim_success(self):
        """志愿者接单 0→1"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        r = self.lib.claim_rescue(rid, volunteer)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 1)
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["helper_id"], volunteer)

    def test_claim_by_admin(self):
        """管理员可以接单"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        r = self.lib.claim_rescue(rid, admin)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 1)

    def test_claim_by_reporter_fail(self):
        """上报人（非志愿者/管理员）不能接单"""
        uid = self._add_user()
        rid = self._create_record(uid)
        r = self.lib.claim_rescue(rid, uid)
        self.assertFalse(r["success"])
        self.assertIn("仅志愿者或管理员可以接单", r["message"])

    def test_claim_duplicate(self):
        """重复接单失败"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.claim_rescue(rid, volunteer)
        self.assertFalse(r["success"])
        self.assertIn("不允许", r["message"])

    def test_claim_not_exists(self):
        volunteer = self._add_user(role=2)
        r = self.lib.claim_rescue("no_xxx", volunteer)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_complete_success(self):
        """上报人标记完成 1→2"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.complete_rescue(rid, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)

    def test_complete_by_helper(self):
        """志愿者可以标记完成"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.complete_rescue(rid, volunteer)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 2)

    def test_complete_by_admin_fail(self):
        """管理员不能标记完成（除非他也是上报人或志愿者）"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.complete_rescue(rid, admin)
        self.assertFalse(r["success"])
        self.assertIn("仅上报人或接单志愿者可以标记完成", r["message"])

    def test_complete_not_claimed(self):
        """未接单（status=0）不能直接标记完成"""
        uid = self._add_user()
        rid = self._create_record(uid)
        r = self.lib.complete_rescue(rid, uid)
        self.assertFalse(r["success"])
        self.assertIn("不允许", r["message"])

    def test_complete_not_exists(self):
        uid = self._add_user()
        r = self.lib.complete_rescue("no_xxx", uid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_confirm_success(self):
        """管理员确认完成 2→3"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        r = self.lib.confirm_rescue(rid, admin)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 3)
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["resolved_by"], admin)

    def test_confirm_by_volunteer_fail(self):
        """志愿者不能确认完成"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        r = self.lib.confirm_rescue(rid, volunteer)
        self.assertFalse(r["success"])
        self.assertIn("仅管理员可以确认完成", r["message"])

    def test_confirm_by_reporter_fail(self):
        """上报人不能确认完成"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        r = self.lib.confirm_rescue(rid, uid)
        self.assertFalse(r["success"])
        self.assertIn("仅管理员可以确认完成", r["message"])

    def test_confirm_not_exists(self):
        admin = self._add_user(role=3)
        r = self.lib.confirm_rescue("no_xxx", admin)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_close_success_by_reporter(self):
        """上报人关闭 0→4"""
        uid = self._add_user()
        rid = self._create_record(uid)
        r = self.lib.close_rescue(rid, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 4)

    def test_close_success_by_admin(self):
        """管理员关闭"""
        uid = self._add_user()
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        r = self.lib.close_rescue(rid, admin)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 4)

    def test_close_by_helper_fail(self):
        """志愿者不能关闭"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.close_rescue(rid, volunteer)
        self.assertFalse(r["success"])
        self.assertIn("仅上报人或管理员可以关闭", r["message"])

    def test_close_from_completed_fail(self):
        """已完成（3）不能关闭"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        self._confirm(rid, admin)
        r = self.lib.close_rescue(rid, admin)
        self.assertFalse(r["success"])
        self.assertIn("不允许", r["message"])

    def test_close_from_in_progress(self):
        """救助中（1）可以关闭"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        r = self.lib.close_rescue(rid, uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 4)

    def test_close_from_to_confirm(self):
        """待确认（2）可以关闭"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        r = self.lib.close_rescue(rid, admin)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["status"], 4)

    def test_close_not_exists(self):
        uid = self._add_user()
        r = self.lib.close_rescue("no_xxx", uid)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_return_to_rescue(self):
        """管理员退回：2→1"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        r = self.lib.update_rescue_status(rid, admin, 1)
        self.assertTrue(r["success"])
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], 1)

    def test_reopen_completed_fail(self):
        """已完成不能退回"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        self._confirm(rid, admin)
        r = self.lib.update_rescue_status(rid, admin, 1)
        self.assertFalse(r["success"])
        self.assertIn("不允许", r["message"])

    def test_status_transition_invalid(self):
        """非法状态转移"""
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)

        rid = self._create_record(uid)
        r = self.lib.update_rescue_status(rid, uid, 2)
        self.assertFalse(r["success"])
        self.assertIn("不允许", r["message"])

        rid2 = self._create_record(uid)
        r = self.lib.update_rescue_status(rid2, admin, 3)
        self.assertFalse(r["success"])
        self.assertIn("不允许", r["message"])

        rid3 = self._create_record(uid)
        self._claim(rid3, volunteer)
        r = self.lib.update_rescue_status(rid3, admin, 3)
        self.assertFalse(r["success"])
        self.assertIn("不允许", r["message"])

    # ==================== link_animal ====================

    def test_link_success(self):
        """正常关联动物档案"""
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        pid = self._add_animal()
        rid = self._create_record(uid)
        r = self.lib.link_animal(rid, pid, admin)
        self.assertTrue(r["success"])
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["pet_id"], pid)

    def test_link_animal_not_exists(self):
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        rid = self._create_record(uid)
        r = self.lib.link_animal(rid, 999999, admin)
        self.assertFalse(r["success"])
        self.assertIn("动物档案不存在", r["message"])

    def test_link_record_not_exists(self):
        admin = self._add_user(role=3)
        pid = self._add_animal()
        r = self.lib.link_animal("no_xxx", pid, admin)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    def test_link_ai_success(self):
        """关联时 AI 特征提取成功，更新动物向量"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        pid = self._add_animal()
        rid = self._create_record(uid, title="linkAI", photo_urls='["http://example.com/p.jpg"]')
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        self._confirm(rid, admin)
        with patch('backend.libs.rescue_record_library.requests.get') as mock_get,              patch('backend.libs.rescue_record_library.extract_features') as mock_extract:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"fake_img"
            mock_get.return_value = mock_resp
            mock_extract.return_value = {"success": True, "features": [0.1, 0.2, 0.3]}
            r = self.lib.link_animal(rid, pid, admin)
            self.assertTrue(r["success"])
            animal = self.animal_lib.get_animal_by_id(pid)
            self.assertTrue(animal["success"])
            self.assertEqual(animal["data"]["vector"], "[0.1, 0.2, 0.3]")

    def test_link_ai_fail(self):
        """AI 特征提取失败不阻塞关联"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        pid = self._add_animal()
        rid = self._create_record(uid, title="linkAI失败", photo_urls='["http://example.com/p.jpg"]')
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        self._confirm(rid, admin)
        with patch('backend.libs.rescue_record_library.requests.get') as mock_get,              patch('backend.libs.rescue_record_library.extract_features') as mock_extract:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"fake"
            mock_get.return_value = mock_resp
            mock_extract.return_value = {"success": False}
            r = self.lib.link_animal(rid, pid, admin)
            self.assertTrue(r["success"])

    def test_link_no_photo(self):
        """记录无图片时不触发 AI"""
        uid = self._add_user(role=1)
        admin = self._add_user(role=3)
        pid = self._add_animal()
        rid = self._create_record(uid, title="无图link")
        r = self.lib.link_animal(rid, pid, admin)
        self.assertTrue(r["success"])

    # ==================== 查询列表 ====================

    def test_get_user_rescues(self):
        uid = self._add_user()
        for _ in range(3):
            self._create_record(uid)
        r = self.lib.get_user_rescues(uid, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 3)
        self.assertEqual(len(r["data"]["records"]), 3)
        for f in ["records", "total", "page", "page_size"]:
            self.assertIn(f, r["data"])

    def test_get_user_rescues_empty(self):
        r = self.lib.get_user_rescues("no_user")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)

    def test_get_user_rescues_pagination(self):
        uid = self._add_user()
        for _ in range(3):
            self._create_record(uid)
        p1 = self.lib.get_user_rescues(uid, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["records"]), 2)
        p2 = self.lib.get_user_rescues(uid, page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["records"]), 1)
        p99 = self.lib.get_user_rescues(uid, page=99, page_size=20)
        self.assertEqual(len(p99["data"]["records"]), 0)

    def test_get_user_rescues_order_desc(self):
        uid = self._add_user()
        self._create_record(uid, title="第一条")
        self._create_record(uid, title="第二条")
        apps = self.lib.get_user_rescues(uid)["data"]["records"]
        t1 = datetime.strptime(apps[0]["created_at"], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(apps[1]["created_at"], "%Y-%m-%d %H:%M:%S")
        self.assertGreaterEqual(t1, t2)

    def test_get_user_rescues_field_completeness(self):
        uid = self._add_user()
        self._create_record(uid)
        record = self.lib.get_user_rescues(uid)["data"]["records"][0]
        for f in ["record_id", "user_id", "user_nickname", "title", "status", "created_at"]:
            self.assertIn(f, record)

    def test_get_helper_rescues(self):
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        for _ in range(2):
            rid = self._create_record(uid)
            self._claim(rid, volunteer)
        r = self.lib.get_helper_rescues(volunteer, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 2)

    def test_get_helper_rescues_empty(self):
        r = self.lib.get_helper_rescues("no_user")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)

    def test_get_helper_rescues_pagination(self):
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        for _ in range(3):
            rid = self._create_record(uid)
            self._claim(rid, volunteer)
        p1 = self.lib.get_helper_rescues(volunteer, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["records"]), 2)
        p2 = self.lib.get_helper_rescues(volunteer, page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["records"]), 1)

    def test_get_helper_rescues_field(self):
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        rid = self._create_record(uid)
        self._claim(rid, volunteer)
        record = self.lib.get_helper_rescues(volunteer)["data"]["records"][0]
        for f in ["record_id", "helper_id", "helper_nickname", "title", "status"]:
            self.assertIn(f, record)

    def test_get_animal_rescue_history(self):
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_animal()
        for _ in range(2):
            rid = self._create_record(uid)
            self.lib.link_animal(rid, pid, admin)
        r = self.lib.get_animal_rescue_history(pid, page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 2)

    def test_get_animal_rescue_history_empty(self):
        r = self.lib.get_animal_rescue_history(999999)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)

    def test_get_animal_rescue_history_pagination(self):
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_animal()
        for _ in range(3):
            rid = self._create_record(uid)
            self.lib.link_animal(rid, pid, admin)
        p1 = self.lib.get_animal_rescue_history(pid, page=1, page_size=2)
        self.assertEqual(len(p1["data"]["records"]), 2)

    def test_get_animal_rescue_history_field(self):
        uid = self._add_user()
        admin = self._add_user(role=3)
        pid = self._add_animal(name="历史动物")
        rid = self._create_record(uid)
        self.lib.link_animal(rid, pid, admin)
        record = self.lib.get_animal_rescue_history(pid)["data"]["records"][0]
        for f in ["record_id", "pet_id", "pet_name", "title"]:
            self.assertIn(f, record)
        self.assertEqual(record["pet_name"], "历史动物")

    def test_get_all_rescues(self):
        for _ in range(3):
            u = self._add_user()
            self._create_record(u)
        r = self.lib.get_all_rescues(page=1, page_size=20)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 3)

    def test_get_all_rescues_filter(self):
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid1 = self._create_record(uid, title="待接单")
        rid2 = self._create_record(uid, title="已完成")
        self._claim(rid2, volunteer)
        self._complete(rid2, uid)
        self._confirm(rid2, admin)
        r = self.lib.get_all_rescues(page=1, page_size=20, status_filter=3)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 1)
        self.assertEqual(r["data"]["records"][0]["status"], 3)

    def test_get_all_rescues_pagination(self):
        for _ in range(3):
            u = self._add_user()
            self._create_record(u)
        p1 = self.lib.get_all_rescues(page=1, page_size=2)
        self.assertEqual(len(p1["data"]["records"]), 2)
        p2 = self.lib.get_all_rescues(page=2, page_size=2)
        self.assertGreaterEqual(len(p2["data"]["records"]), 1)

    def test_get_all_rescues_field(self):
        uid = self._add_user()
        self._create_record(uid)
        record = self.lib.get_all_rescues()["data"]["records"][0]
        for f in ["record_id", "user_id", "title", "status", "created_at"]:
            self.assertIn(f, record)

    def test_get_rescue_status_count(self):
        uid = self._add_user()
        volunteer = self._add_user(role=2)
        self._create_record(uid)
        self._create_record(uid)
        rid3 = self._create_record(uid)
        self._claim(rid3, volunteer)
        r = self.lib.get_rescue_status_count()
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["pending"], 2)
        self.assertGreaterEqual(r["data"]["in_progress"], 1)
        self.assertIn("total", r["data"])

    def test_get_rescue_status_count_structure(self):
        r = self.lib.get_rescue_status_count()
        self.assertTrue(r["success"])
        for f in ["total", "pending", "in_progress", "to_confirm", "completed", "closed"]:
            self.assertIn(f, r["data"])

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        patcher = patch.object(self.lib.db, 'open_database', return_value=False)
        mock_open = patcher.start()
        try:
            self.assertFalse(self.lib.get_rescue_record_by_id("x")["success"])
            self.assertFalse(self.lib.get_user_rescues("x")["success"])
            self.assertFalse(self.lib.get_helper_rescues("x")["success"])
            self.assertFalse(self.lib.get_animal_rescue_history(1)["success"])
            self.assertFalse(self.lib.get_all_rescues()["success"])
            self.assertFalse(self.lib.get_rescue_status_count()["success"])
            self.assertFalse(self.lib.create_rescue_record("x", title="t")["success"])
            self.assertFalse(self.lib.update_rescue_record("x", "u", title="t")["success"])
            self.assertFalse(self.lib.delete_rescue_record("x", "u")["success"])
            self.assertFalse(self.lib.claim_rescue("x", "u")["success"])
            self.assertFalse(self.lib.complete_rescue("x", "u")["success"])
            self.assertFalse(self.lib.confirm_rescue("x", "u")["success"])
            self.assertFalse(self.lib.close_rescue("x", "u")["success"])
            self.assertFalse(self.lib.update_rescue_status("x", "u", 1)["success"])
            self.assertFalse(self.lib.link_animal("x", 1, "u")["success"])
        finally:
            patcher.stop()

    # ==================== 综合业务场景 ====================

    def test_full_lifecycle_approved(self):
        """完整生命周期：创建→接单→完成→确认→关联动物"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        pid = self._add_animal()
        rid = self._create_record(uid, title="生命周期")

        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], 0)

        self._claim(rid, volunteer)
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["status"], 1)
        self.assertEqual(d["helper_id"], volunteer)

        self._complete(rid, uid)
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], 2)

        self._confirm(rid, admin)
        d = self.lib.get_rescue_record_by_id(rid)["data"]
        self.assertEqual(d["status"], 3)
        self.assertEqual(d["resolved_by"], admin)

        r = self.lib.link_animal(rid, pid, admin)
        self.assertTrue(r["success"])
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["pet_id"], pid)

    def test_full_lifecycle_closed(self):
        """创建后直接关闭"""
        uid = self._add_user(role=1)
        rid = self._create_record(uid, title="直接关闭")
        self._close(rid, uid)
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], 4)

    def test_full_lifecycle_return(self):
        """创建→接单→完成→退回→再次完成→确认"""
        uid = self._add_user(role=1)
        volunteer = self._add_user(role=2)
        admin = self._add_user(role=3)
        rid = self._create_record(uid, title="退回测试")
        self._claim(rid, volunteer)
        self._complete(rid, uid)
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], 2)

        r = self.lib.update_rescue_status(rid, admin, 1)
        self.assertTrue(r["success"])
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], 1)

        self._complete(rid, uid)
        self._confirm(rid, admin)
        self.assertEqual(self.lib.get_rescue_record_by_id(rid)["data"]["status"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
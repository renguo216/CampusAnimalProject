# backend/tests/test_user_library.py
"""
UserLibrary 完整测试套件（unittest 框架）
运行方式：
    cd 项目根目录
    python -m backend.tests.test_user_library

依赖：
    - MySQL 数据库已启动且可连接
    - t_user、t_points_log 表已存在
"""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.libs.user_library import UserLibrary


class TestUserLibrary(unittest.TestCase):
    """UserLibrary 完整功能测试"""

    @classmethod
    def setUpClass(cls):
        cls.lib = UserLibrary()
        cls._cleanup_all()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all()

    def setUp(self):
        self.user_ids = []

    def tearDown(self):
        if not self.user_ids:
            return
        db = self.lib.db
        try:
            if db.connection is None:
                if not db.open_database():
                    return
                need_close = True
            else:
                need_close = False
            for uid in self.user_ids:
                db.execute_raw_sql("DELETE FROM t_points_log WHERE user_id = %s", (uid,))
                db.execute_raw_sql("DELETE FROM t_user WHERE user_id = %s", (uid,))
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
            db.execute_raw_sql("DELETE FROM t_points_log WHERE user_id LIKE %s", ("test_user_%",))
            db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE %s", ("test_user_%",))
            if need_close:
                db.close_database()
        except Exception as e:
            print(f"[_cleanup_all 警告] 清理失败: {e}")

    # ---- 辅助方法 ----

    def _add_user(self, nickname=None, role=1, points=0, is_active=1, **kwargs):
        """注册测试用户并返回 user_id"""
        uid = f"test_user_{uuid.uuid4().hex[:8]}"
        if nickname is None:
            nickname = f"nick_{uid[:8]}"
        r = self.lib.register_user(uid, nickname, avatar_url="http://x.com/a.jpg", role=role)
        if not r.get("success"):
            self.lib.delete_user(uid)
            r = self.lib.register_user(uid, nickname, avatar_url="http://x.com/a.jpg", role=role)
        if not r.get("success"):
            raise RuntimeError(f"注册用户失败: {r}")
        self.user_ids.append(uid)
        # 设置积分和状态
        if points != 0 or is_active != 1:
            db = self.lib.db
            if db.connection is None:
                db.open_database()
                need_close = True
            else:
                need_close = False
            if points != 0:
                db.execute_raw_sql("UPDATE t_user SET points = %s WHERE user_id = %s", (points, uid))
            if is_active != 1:
                db.execute_raw_sql("UPDATE t_user SET is_active = %s WHERE user_id = %s", (is_active, uid))
            if need_close:
                db.close_database()
        return uid

    # ==================== register_user ====================

    def test_register_user_success(self):
        uid = f"test_user_{uuid.uuid4().hex[:8]}"
        r = self.lib.register_user(uid, "测试用户", avatar_url="http://x.com/a.jpg", role=1)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["user_id"], uid)
        self.user_ids.append(uid)

    def test_register_user_duplicate(self):
        uid = self._add_user()
        r = self.lib.register_user(uid, "重复注册", role=1)
        self.assertFalse(r["success"])
        self.assertIn("已存在", r["message"])

    def test_register_user_invalid_role(self):
        uid = f"test_user_{uuid.uuid4().hex[:8]}"
        r = self.lib.register_user(uid, "非法角色", role=99)
        self.assertFalse(r["success"])
        self.assertIn("角色", r["message"])

    def test_register_volunteer(self):
        uid = f"test_user_{uuid.uuid4().hex[:8]}"
        r = self.lib.register_user(uid, "测试志愿者", role=2)
        self.assertTrue(r["success"])
        profile = self.lib.get_user_profile(uid)
        self.assertEqual(profile["data"]["role"], 2)
        self.assertTrue(profile["data"]["volunteer_id"].startswith("VOL_"))
        self.assertEqual(profile["data"]["level"], 1)
        self.user_ids.append(uid)

    # ==================== get_user_by_account ====================

    def test_get_user_success(self):
        uid = self._add_user(nickname="查询测试")
        r = self.lib.get_user_by_account(uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["nickname"], "查询测试")
        self.assertEqual(r["data"]["role"], 1)

    def test_get_user_not_found(self):
        r = self.lib.get_user_by_account("not_exist_123")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== verify_user_validity ====================

    def test_verify_valid_user(self):
        uid = self._add_user()
        r = self.lib.verify_user_validity(uid)
        self.assertTrue(r["success"])
        self.assertTrue(r["data"]["is_valid"])

    def test_verify_not_exists(self):
        r = self.lib.verify_user_validity("not_exist_123")
        self.assertFalse(r["success"])
        self.assertFalse(r["data"]["is_valid"])

    def test_verify_banned_user(self):
        uid = self._add_user(is_active=0)
        r = self.lib.verify_user_validity(uid)
        self.assertFalse(r["success"])
        self.assertFalse(r["data"]["is_valid"])

    # ==================== update_user_info ====================

    def test_update_user_info_success(self):
        uid = self._add_user()
        r = self.lib.update_user_info(uid, {"nickname": "新昵称", "avatarURL": "http://new.jpg"})
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["nickname"], "新昵称")
        self.assertEqual(user["data"]["avatarURL"], "http://new.jpg")

    def test_update_user_info_illegal_fields(self):
        uid = self._add_user(points=100)
        r = self.lib.update_user_info(uid, {"points": 99999, "role": 3})
        self.assertFalse(r["success"])
        self.assertIn("没有需要更新的有效字段", r["message"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["points"], 100)
        self.assertEqual(user["data"]["role"], 1)

    def test_update_user_info_not_exists(self):
        r = self.lib.update_user_info("not_exist", {"nickname": "test"})
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== update_role ====================

    def test_update_role_to_volunteer(self):
        uid = self._add_user(role=1)
        r = self.lib.update_role(uid, 2)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["role"], 2)
        self.assertIsNotNone(user["data"]["volunteer_id"])
        self.assertEqual(user["data"]["level"], 1)
        self.assertIsNone(user["data"]["admin_id"])

    def test_update_role_to_admin(self):
        uid = self._add_user(role=2)
        r = self.lib.update_role(uid, 3)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["role"], 3)
        self.assertIsNone(user["data"]["volunteer_id"])
        self.assertIsNone(user["data"]["level"])

    def test_update_role_to_normal(self):
        uid = self._add_user(role=3)
        self.lib.set_admin_id(uid, "ADMIN_001")
        r = self.lib.update_role(uid, 1)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["role"], 1)
        self.assertIsNone(user["data"]["volunteer_id"])
        self.assertIsNone(user["data"]["admin_id"])
        self.assertIsNone(user["data"]["level"])

    def test_update_role_invalid(self):
        uid = self._add_user()
        r = self.lib.update_role(uid, 99)
        self.assertFalse(r["success"])
        self.assertIn("角色", r["message"])

    # ==================== set_admin_id ====================

    def test_set_admin_id_success(self):
        uid = self._add_user(role=3)
        r = self.lib.set_admin_id(uid, "ADMIN_001")
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["admin_id"], "ADMIN_001")

    def test_set_admin_id_normal_user(self):
        uid = self._add_user(role=1)
        r = self.lib.set_admin_id(uid, "ADMIN_002")
        self.assertFalse(r["success"])
        self.assertIn("仅管理员", r["message"])

    def test_set_admin_id_empty(self):
        uid = self._add_user(role=3)
        r = self.lib.set_admin_id(uid, "")
        self.assertFalse(r["success"])
        self.assertIn("不能为空", r["message"])

    # ==================== toggle_active_status ====================

    def test_toggle_active_ban(self):
        uid = self._add_user()
        r = self.lib.toggle_active_status(uid, 0)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["is_active"], 0)

    def test_toggle_active_unban(self):
        uid = self._add_user(is_active=0)
        r = self.lib.toggle_active_status(uid, 1)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["is_active"], 1)

    def test_toggle_active_invalid(self):
        uid = self._add_user()
        r = self.lib.toggle_active_status(uid, 2)
        self.assertFalse(r["success"])
        self.assertIn("状态", r["message"])

    # ==================== deactivate_user ====================

    def test_deactivate_user(self):
        uid = self._add_user()
        r = self.lib.deactivate_user(uid)
        self.assertTrue(r["success"])
        verify = self.lib.verify_user_validity(uid)
        self.assertFalse(verify["data"]["is_valid"])

    # ==================== delete_user ====================

    def test_delete_user_success(self):
        uid = f"test_user_{uuid.uuid4().hex[:8]}"
        self.lib.register_user(uid, "待删除", role=1)
        r = self.lib.delete_user(uid)
        self.assertTrue(r["success"])
        get_r = self.lib.get_user_by_account(uid)
        self.assertFalse(get_r["success"])

    def test_delete_user_not_found(self):
        r = self.lib.delete_user("not_exist")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== add_points ====================

    def test_add_points_increase(self):
        uid = self._add_user(points=0)
        r = self.lib.add_points(uid, 100, reason="签到奖励")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["points"], 100)
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["points"], 100)

    def test_add_points_decrease(self):
        uid = self._add_user(points=100)
        r = self.lib.add_points(uid, -30, reason="兑换商品")
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["points"], 70)
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["points"], 70)

    def test_add_points_negative(self):
        uid = self._add_user(points=10)
        r = self.lib.add_points(uid, -999, reason="恶意扣减")
        self.assertFalse(r["success"])
        self.assertIn("积分不足", r["message"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["points"], 10)

    def test_add_points_not_found(self):
        r = self.lib.add_points("not_exist", 100)
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== get_points_history ====================

    def test_get_points_history(self):
        uid = self._add_user(points=0)
        self.lib.add_points(uid, 100, reason="签到")
        self.lib.add_points(uid, -30, reason="兑换")
        r = self.lib.get_points_history(uid)
        self.assertTrue(r["success"])
        self.assertGreaterEqual(r["data"]["total"], 2)
        self.assertGreaterEqual(len(r["data"]["logs"]), 2)

    def test_get_points_history_empty(self):
        uid = self._add_user()
        r = self.lib.get_points_history(uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["total"], 0)
        self.assertEqual(len(r["data"]["logs"]), 0)

    # ==================== update_user_stats ====================

    def test_update_stats_all(self):
        uid = self._add_user()
        r = self.lib.update_user_stats(uid, like_count=10, follower_count=5, following_count=3)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["like_count"], 10)
        self.assertEqual(user["data"]["follower_count"], 5)
        self.assertEqual(user["data"]["following_count"], 3)

    def test_update_stats_partial(self):
        uid = self._add_user()
        self.lib.update_user_stats(uid, like_count=10, follower_count=5)
        r = self.lib.update_user_stats(uid, like_count=20)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["like_count"], 20)
        self.assertEqual(user["data"]["follower_count"], 5)

    def test_update_stats_negative_clamp(self):
        uid = self._add_user()
        r = self.lib.update_user_stats(uid, like_count=-5)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["like_count"], 0)

    def test_update_stats_no_fields(self):
        uid = self._add_user()
        r = self.lib.update_user_stats(uid)
        self.assertFalse(r["success"])
        self.assertIn("没有需要更新的统计字段", r["message"])

    # ==================== increment_user_stats ====================

    def test_increment_stats(self):
        uid = self._add_user()
        self.lib.update_user_stats(uid, like_count=10, follower_count=5)
        r = self.lib.increment_user_stats(uid, like_delta=5, follower_delta=-2)
        self.assertTrue(r["success"])
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["like_count"], 15)
        self.assertEqual(user["data"]["follower_count"], 3)

    def test_increment_stats_no_fields(self):
        uid = self._add_user()
        r = self.lib.increment_user_stats(uid)
        self.assertFalse(r["success"])
        self.assertIn("没有需要更新的统计字段", r["message"])

    # ==================== get_user_profile ====================

    def test_get_profile_success(self):
        uid = self._add_user(nickname="个人主页测试")
        r = self.lib.get_user_profile(uid)
        self.assertTrue(r["success"])
        self.assertEqual(r["data"]["user_id"], uid)
        self.assertEqual(r["data"]["nickname"], "个人主页测试")

    def test_get_profile_not_found(self):
        r = self.lib.get_user_profile("not_exist")
        self.assertFalse(r["success"])
        self.assertIn("不存在", r["message"])

    # ==================== get_volunteers_ranking ====================

    def test_get_volunteers_ranking(self):
        top_id = self._add_user(nickname="高分志愿者", role=2, points=1000)
        low_id = self._add_user(nickname="低分志愿者", role=2, points=10)
        r = self.lib.get_volunteers_ranking(limit=10)
        self.assertTrue(r["success"])
        volunteers = r["data"]["volunteers"]
        self.assertGreaterEqual(len(volunteers), 2)
        # 验证排序：高分在前
        points_list = [v["points"] for v in volunteers]
        self.assertEqual(points_list, sorted(points_list, reverse=True))
        # 验证高分志愿者在榜
        self.assertIn(top_id, [v["user_id"] for v in volunteers])

    def test_get_volunteers_ranking_banned_excluded(self):
        top_id = self._add_user(nickname="高分志愿者", role=2, points=1000)
        self.lib.toggle_active_status(top_id, 0)
        r = self.lib.get_volunteers_ranking(limit=10)
        self.assertTrue(r["success"])
        volunteers = r["data"]["volunteers"]
        self.assertNotIn(top_id, [v["user_id"] for v in volunteers])

    # ==================== DB 连接失败（批量覆盖） ====================

    def test_db_connection_fail(self):
        """所有需要数据库的方法在连接失败时均返回错误"""
        with patch.object(self.lib.db, 'open_database', return_value=False):
            self.assertFalse(self.lib.get_user_by_account("x")["success"])
            self.assertFalse(self.lib.register_user("x", "n")["success"])
            self.assertFalse(self.lib.update_user_info("x", {"nickname": "n"})["success"])
            self.assertFalse(self.lib.update_role("x", 2)["success"])
            self.assertFalse(self.lib.set_admin_id("x", "A")["success"])
            self.assertFalse(self.lib.toggle_active_status("x", 0)["success"])
            self.assertFalse(self.lib.deactivate_user("x")["success"])
            self.assertFalse(self.lib.delete_user("x")["success"])
            self.assertFalse(self.lib.add_points("x", 100)["success"])
            self.assertFalse(self.lib.get_points_history("x")["success"])
            self.assertFalse(self.lib.update_user_stats("x", like_count=1)["success"])
            self.assertFalse(self.lib.increment_user_stats("x", like_delta=1)["success"])
            self.assertFalse(self.lib.get_user_profile("x")["success"])
            self.assertFalse(self.lib.get_volunteers_ranking()["success"])

    # ==================== 综合业务场景 ====================

    def test_full_lifecycle(self):
        """完整生命周期：注册 → 查询 → 更新信息 → 加积分 → 切换角色 → 设置工号 → 封禁 → 解封 → 删除"""
        uid = f"test_user_{uuid.uuid4().hex[:8]}"
        # 注册
        r = self.lib.register_user(uid, "生命周期用户", role=1)
        self.assertTrue(r["success"])
        self.user_ids.append(uid)

        # 查询
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["nickname"], "生命周期用户")

        # 更新信息
        self.lib.update_user_info(uid, {"nickname": "已更新"})
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["nickname"], "已更新")

        # 加积分
        self.lib.add_points(uid, 500)
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["points"], 500)

        # 切换为志愿者
        self.lib.update_role(uid, 2)
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["role"], 2)

        # 切换为管理员 + 设置工号
        self.lib.update_role(uid, 3)
        self.lib.set_admin_id(uid, "ADMIN_999")
        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["admin_id"], "ADMIN_999")

        # 封禁
        self.lib.toggle_active_status(uid, 0)
        verify = self.lib.verify_user_validity(uid)
        self.assertFalse(verify["data"]["is_valid"])

        # 解封
        self.lib.toggle_active_status(uid, 1)
        verify = self.lib.verify_user_validity(uid)
        self.assertTrue(verify["data"]["is_valid"])

        # 删除
        self.lib.delete_user(uid)
        self.user_ids.remove(uid)
        get_r = self.lib.get_user_by_account(uid)
        self.assertFalse(get_r["success"])

    def test_points_flow_integrity(self):
        """积分流水完整性验证"""
        uid = self._add_user(points=0)
        self.lib.add_points(uid, 100, reason="奖励")
        self.lib.add_points(uid, -20, reason="消费")
        self.lib.add_points(uid, 50, reason="奖励2")

        history = self.lib.get_points_history(uid)
        self.assertEqual(history["data"]["total"], 3)

        user = self.lib.get_user_by_account(uid)
        self.assertEqual(user["data"]["points"], 130)


if __name__ == "__main__":
    unittest.main(verbosity=2)
# ===== backend/libs/user_library.py =====
"""
用户业务逻辑层
提供用户注册、查询、信息更新、积分管理、角色变更等核心功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from backend.utils.db_manager import DatabaseManager
from backend.model.user import User
from backend.utils.response import success_response, error_response
import uuid
import random
import string
from datetime import datetime
from typing import Optional


class UserLibrary:
    """
    用户业务逻辑库
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        self.db = DatabaseManager()

    # ========== 内部方法（返回原始类型，供本类内部使用） ==========

    def _get_user_by_account(self, user_id) -> Optional[User]:
        """内部方法：根据账号精确查询用户信息，返回 User 对象"""
        if not self.db.open_database():
            return None
        user_data = self.db.get_by_id('t_user', 'user_id', user_id)
        self.db.close_database()
        if user_data:
            return User(**user_data)
        return None

    def _verify_user_validity(self, user_id) -> bool:
        """内部方法：验证用户是否存在且未注销，返回 bool"""
        user = self._get_user_by_account(user_id)
        return user is not None and user.is_active == 1

    def _raw_update(self, user_id, data_dict) -> bool:
        """内部通用更新（跳过白名单校验）"""
        if not self.db.open_database():
            return False
        success = self.db.update('t_user', 'user_id', user_id, data_dict)
        self.db.close_database()
        return success

    # ========== 公共方法（统一返回格式，供外部调用） ==========

    def get_user_by_account(self, user_id) -> dict:
        """
        根据账号精确查询用户信息
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        user = self._get_user_by_account(user_id)
        if not user:
            return error_response("用户不存在")
        return success_response(
            message="成功",
            data={
                'user_id': user.user_id,
                'nickname': user.nickname,
                'avatarURL': user.avatarURL,
                'role': user.role,
                'points': user.points,
                'volunteer_id': user.volunteer_id,
                'admin_id': user.admin_id,
                'level': user.level,
                'like_count': user.like_count,
                'follower_count': user.follower_count,
                'following_count': user.following_count,
                'is_active': user.is_active,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
            }
        )

    def verify_user_validity(self, user_id) -> dict:
        """
        验证用户是否存在且未注销
        :return: dict {"success": bool, "message": str, "data": {"is_valid": bool}}
        """
        is_valid = self._verify_user_validity(user_id)
        if is_valid:
            return success_response(message="用户有效", data={"is_valid": True})
        return error_response("用户不存在或已注销", data={"is_valid": False})

    def register_user(self, user_id, nickname, avatar_url=None, role=1) -> dict:
        """
        注册新用户
        - user_id: 微信OpenID（外部传入）
        - 默认角色为1（普通用户）
        - 管理员admin_id不由系统生成，需后台手动设置
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if self._get_user_by_account(user_id):
            return error_response("用户已存在")

        if role not in (1, 2, 3):
            return error_response("角色值无效，必须是 1, 2 或 3")

        level = 1 if role == 2 else None
        volunteer_id = self._generate_volunteer_id() if role == 2 else None

        data = {
            'user_id': user_id,
            'nickname': nickname,
            'avatarURL': avatar_url,
            'role': role,
            'points': 0,
            'volunteer_id': volunteer_id,
            'admin_id': None,
            'level': level,
            'phone_number': None,
            'like_count': 0,
            'follower_count': 0,
            'following_count': 0,
            'is_active': 1,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if not self.db.open_database():
            return error_response("数据库连接失败")
        success = self.db.insert('t_user', data)
        self.db.close_database()

        if success:
            return success_response("注册成功", data={"user_id": user_id})
        return error_response("注册失败")

    def update_user_info(self, user_id, update_data) -> dict:
        """
        通用更新用户信息
        白名单限制：只允许修改昵称、头像、手机号等基础资料
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self._verify_user_validity(user_id):
            return error_response("用户不存在或已注销")

        allowed_fields = {'nickname', 'avatarURL', 'phone_number', 'gender', 'bio', 'birthday'}
        clean_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        if not clean_data:
            return error_response("没有需要更新的有效字段")

        success = self._raw_update(user_id, clean_data)
        if success:
            return success_response("更新成功", data={"user_id": user_id})
        return error_response("更新失败")

    def update_role(self, user_id, new_role) -> dict:
        """
        修改用户角色，自动调整关联字段
        1->普通用户, 2->志愿者, 3->管理员
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if new_role not in (1, 2, 3):
            return error_response("角色值必须是 1, 2 或 3")

        user = self._get_user_by_account(user_id)
        if not user:
            return error_response("用户不存在")

        update_data = {'role': new_role}

        if new_role == 2:
            update_data['level'] = 1
            update_data['admin_id'] = None
            if not user.volunteer_id:
                update_data['volunteer_id'] = self._generate_volunteer_id()
        elif new_role == 3:
            update_data['level'] = None
            update_data['volunteer_id'] = None
        else:
            update_data['level'] = None
            update_data['volunteer_id'] = None
            update_data['admin_id'] = None

        success = self._raw_update(user_id, update_data)
        if success:
            return success_response(
                "角色更新成功",
                data={"user_id": user_id, "role": new_role}
            )
        return error_response("角色更新失败")

    def set_admin_id(self, user_id, admin_id) -> dict:
        """
        为管理员设置工号（开发者后台手动调用）
        仅允许role=3的用户
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        user = self._get_user_by_account(user_id)
        if not user or user.role != 3:
            return error_response("仅管理员可设置工号")
        if not admin_id or not admin_id.strip():
            return error_response("工号不能为空")

        success = self._raw_update(user_id, {'admin_id': admin_id.strip()})
        if success:
            return success_response(
                "工号设置成功",
                data={"admin_id": admin_id.strip()}
            )
        return error_response("设置失败")

    def toggle_active_status(self, user_id, is_active) -> dict:
        """
        设置用户激活状态：0-封禁/注销，1-正常
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if is_active not in (0, 1):
            return error_response("状态值必须是 0 或 1")

        success = self._raw_update(user_id, {'is_active': is_active})
        if success:
            status_text = "激活" if is_active == 1 else "封禁"
            return success_response(
                f"用户已{status_text}",
                data={"is_active": is_active}
            )
        return error_response("状态更新失败")

    def deactivate_user(self, user_id) -> dict:
        """
        用户注销（逻辑删除）
        将is_active设为0，数据保留
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        return self.toggle_active_status(user_id, 0)

    def delete_user(self, user_id) -> dict:
        """
        物理删除用户（开发者后台慎用）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        user = self._get_user_by_account(user_id)
        if not user:
            return error_response("用户不存在")
        if not self.db.open_database():
            return error_response("数据库连接失败")
        success = self.db.delete('t_user', 'user_id', user_id)
        self.db.close_database()

        if success:
            return success_response("用户已删除")
        return error_response("删除失败")

    def add_points(self, user_id, delta, reason=None) -> dict:
        """
        增减用户积分
        - delta: 正数为增加，负数为扣减
        - reason: 积分变动原因（用于流水记录）
        - 不允许积分扣到负数
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        user = self._get_user_by_account(user_id)
        if not user:
            return error_response("用户不存在")

        new_points = user.points + delta
        if new_points < 0:
            return error_response("积分不足")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 更新用户积分
            self.db.update_tx('t_user', 'user_id', user_id, {'points': new_points})

            # 记录积分流水
            log_data = {
                'user_id': user_id,
                'delta': delta,
                'before_points': user.points,
                'after_points': new_points,
                'reason': reason or '',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.db.insert_tx('t_points_log', log_data)

            self.db.commit()
            return success_response(
                "积分更新成功",
                data={"user_id": user_id, "points": new_points, "delta": delta}
            )
        except Exception as e:
            self.db.rollback()
            return error_response(f"积分操作失败: {str(e)}")
        finally:
            self.db.close_database()

    def get_points_history(self, user_id, page=1, page_size=20) -> dict:
        """
        查询用户积分变动流水
        :return: dict {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        result = self.db.get_paginated(
            't_points_log',
            page=page,
            page_size=page_size,
            where_clause="user_id = %s",
            params=(user_id,),
            order_by="created_at DESC"
        )
        self.db.close_database()

        if not result:
            return success_response(
                message="成功",
                data={"logs": [], "total": 0, "page": page, "page_size": page_size}
            )

        return success_response(
            message="成功",
            data={
                "logs": result.get("data", []),
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
        )

    def update_user_stats(self, user_id, like_count=None, follower_count=None, following_count=None) -> dict:
        """
        直接赋值更新统计数据
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        update_data = {}
        if like_count is not None:
            update_data['like_count'] = max(int(like_count), 0)
        if follower_count is not None:
            update_data['follower_count'] = max(int(follower_count), 0)
        if following_count is not None:
            update_data['following_count'] = max(int(following_count), 0)
        if not update_data:
            return error_response("没有需要更新的统计字段")

        success = self._raw_update(user_id, update_data)
        if success:
            return success_response("统计更新成功", data={"user_id": user_id})
        return error_response("统计更新失败")

    def increment_user_stats(self, user_id, like_delta=0, follower_delta=0, following_delta=0) -> dict:
        """
        原子增量更新统计数据（解决并发丢更新）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        user = self._get_user_by_account(user_id)
        if not user:
            return error_response("用户不存在")

        update_data = {}
        if like_delta != 0:
            update_data['like_count'] = max(user.like_count + like_delta, 0)
        if follower_delta != 0:
            update_data['follower_count'] = max(user.follower_count + follower_delta, 0)
        if following_delta != 0:
            update_data['following_count'] = max(user.following_count + following_delta, 0)
        if not update_data:
            return error_response("没有需要更新的统计字段")

        success = self._raw_update(user_id, update_data)
        if success:
            return success_response("统计更新成功", data={"user_id": user_id})
        return error_response("统计更新失败")

    def get_user_profile(self, user_id) -> dict:
        """
        获取用户个人中心完整信息
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        user = self._get_user_by_account(user_id)
        if not user:
            return error_response("用户不存在")

        return success_response(
            message="成功",
            data={
                'user_id': user.user_id,
                'nickname': user.nickname,
                'avatarURL': user.avatarURL,
                'role': user.role,
                'points': user.points,
                'volunteer_id': user.volunteer_id,
                'admin_id': user.admin_id,
                'level': user.level,
                'like_count': user.like_count,
                'follower_count': user.follower_count,
                'following_count': user.following_count,
                'is_active': user.is_active,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
            }
        )

    def get_volunteers_ranking(self, limit=10) -> dict:
        """
        获取积分最高的前N名志愿者
        :return: dict {"success": bool, "message": str, "data": {"volunteers": list}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = """
            SELECT * FROM t_user 
            WHERE role = 2 AND is_active = 1
            ORDER BY points DESC 
            LIMIT %s
        """
        results = self.db.execute_raw_sql(sql, (limit,))
        self.db.close_database()

        if not results:
            return success_response("成功", data={"volunteers": []})

        volunteers = []
        for row in results:
            user = User(**row)
            volunteers.append({
                'user_id': user.user_id,
                'nickname': user.nickname,
                'avatarURL': user.avatarURL,
                'points': user.points,
                'volunteer_id': user.volunteer_id,
                'level': user.level
            })

        return success_response("成功", data={"volunteers": volunteers})

    # ========== 内部辅助方法 ==========

    def _generate_volunteer_id(self):
        """生成全局唯一的志愿者编号"""
        while True:
            vid = 'VOL_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            if not self._volunteer_id_exists(vid):
                return vid

    def _volunteer_id_exists(self, volunteer_id):
        """检查志愿者编号是否已存在"""
        if not self.db.open_database():
            return True
        sql = "SELECT 1 FROM t_user WHERE volunteer_id = %s LIMIT 1"
        results = self.db.execute_raw_sql(sql, (volunteer_id,))
        self.db.close_database()
        return bool(results)
# ===== backend/libs/volunteer_application_library.py =====
"""
志愿者申请（资格申请）业务逻辑层
提供志愿者申请提交、修改、撤销、审核、信息查询等核心功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
import random
import string


class VolunteerApplicationLibrary:
    """
    志愿者申请业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        """初始化：创建数据库管理器实例"""
        self.db = DatabaseManager()

    # ==================== 用户操作：志愿者申请 ====================

    def submit_volunteer_application(self, user_id: str, apply_content: str = None) -> dict:
        """
        提交志愿者资格申请
        - 验证用户存在且激活
        - 验证用户当前角色：管理员（role=3）不能申请，已是志愿者（role=2）不能重复申请
        - 插入 t_volunteer_application（status=0）

        Args:
            user_id: 申请人ID
            apply_content: 申请理由

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        # 先检查是否有待审核申请（内部自己管理连接）
        if self._has_pending_application(user_id):
            return error_response("您已提交过申请，请等待审核")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 1. 验证用户存在且激活
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("用户不存在")
            if user.get("is_active") == 0:
                return error_response("用户已被封禁，无法申请")

            # 2. 检查角色：管理员不能申请，已是志愿者不能重复申请
            role = user.get("role")
            if role == 3:
                return error_response("管理员无需申请志愿者")
            if role == 2:
                return error_response("您已经是志愿者，无需重复申请")

            # 3. 插入申请记录（自增主键，不手动设置）
            now = datetime.now()
            data = {
                "user_id": user_id,
                "apply_content": apply_content,
                "status": 0,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.insert("t_volunteer_application", data):
                return error_response("提交申请失败")

            # 获取自增ID
            application_id = self.db.get_last_insert_id()

            return {
                "success": True,
                "message": "志愿者申请提交成功，等待管理员审核",
                "data": {
                    "application_id": application_id,
                    "status": 0,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        except Exception as e:
            return error_response(f"提交申请失败：{str(e)}")
        finally:
            self.db.close_database()

    def update_volunteer_application(self, application_id: int, user_id: str,
                                     apply_content: str) -> dict:
        """
        修改志愿者申请内容（仅允许自己的待审核申请）

        Args:
            application_id: 申请ID
            user_id: 申请人ID
            apply_content: 新的申请理由

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            application = self.db.get_by_id("t_volunteer_application", "application_id", application_id)
            if not application:
                return error_response("申请记录不存在")

            # 验证所有权和状态
            if application.get("user_id") != user_id:
                return error_response("无权修改他人的申请")
            if application.get("status") != 0:
                return error_response("仅待审核的申请可以修改")

            now = datetime.now()
            update_data = {
                "apply_content": apply_content,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_volunteer_application", "application_id", application_id, update_data):
                return error_response("修改申请失败")

            return {
                "success": True,
                "message": "申请内容已修改",
                "data": {"application_id": application_id, "updated_at": update_data["updated_at"]}
            }
        except Exception as e:
            return error_response(f"修改申请失败：{str(e)}")
        finally:
            self.db.close_database()

    def cancel_volunteer_application(self, application_id: int, user_id: str) -> dict:
        """
        撤销志愿者申请（仅允许自己的待审核申请）

        Args:
            application_id: 申请ID
            user_id: 申请人ID

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            application = self.db.get_by_id("t_volunteer_application", "application_id", application_id)
            if not application:
                return error_response("申请记录不存在")

            if application.get("user_id") != user_id:
                return error_response("无权撤销他人的申请")
            if application.get("status") != 0:
                return error_response("仅待审核的申请可以撤销")

            now = datetime.now()
            update_data = {
                "status": 3,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_volunteer_application", "application_id", application_id, update_data):
                return error_response("撤销申请失败")

            return {
                "success": True,
                "message": "志愿者申请已撤销",
                "data": {"application_id": application_id, "status": 3, "cancelled_at": now.strftime("%Y-%m-%d %H:%M:%S")}
            }
        except Exception as e:
            return error_response(f"撤销申请失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 查询操作 ====================

    def get_application_by_id(self, application_id: int) -> dict:
        """
        查询申请详情（含申请人信息）

        Args:
            application_id: 申请ID

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            application = self.db.get_by_id("t_volunteer_application", "application_id", application_id)
            if not application:
                return error_response("申请记录不存在")

            user = self.db.get_by_id("t_user", "user_id", application.get("user_id"))

            data = {
                "application_id": application.get("application_id"),
                "user_id": application.get("user_id"),
                "nickname": user.get("nickname") if user else None,
                "avatar_url": user.get("avatarURL") if user else None,
                "role": user.get("role") if user else None,
                "apply_content": application.get("apply_content"),
                "status": application.get("status"),
                "review_comment": application.get("review_comment"),
                "reviewed_by": application.get("reviewed_by"),
                "reviewed_at": application.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if application.get("reviewed_at") else None,
                "created_at": application.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if application.get("created_at") else None,
                "updated_at": application.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if application.get("updated_at") else None
            }
            return success_response("成功", data)
        except Exception as e:
            return error_response(f"查询申请详情失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_user_applications(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        分页查询指定用户的所有志愿者申请记录（按时间倒序）

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页条数

        Returns:
            dict: {"success": bool, "message": str, "data": {"applications": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_volunteer_application",
                page=page,
                page_size=page_size,
                where_clause="user_id = %s",
                params=(user_id,),
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"applications": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data)

            items = self._format_application_list(result["data"])
            data = {
                "applications": items,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data)
        except Exception as e:
            return error_response(f"查询用户申请记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_application_status(self, application_id: int) -> dict:
        """
        获取申请状态及文字说明

        Args:
            application_id: 申请ID

        Returns:
            dict: {"success": bool, "message": str, "data": {"application_id": int, "status": int, "status_text": str}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            application = self.db.get_by_id("t_volunteer_application", "application_id", application_id)
            if not application:
                return error_response("申请记录不存在")

            status_map = {0: "待审核", 1: "已通过", 2: "已驳回", 3: "已撤销"}
            return {
                "success": True,
                "message": "成功",
                "data": {
                    "application_id": application.get("application_id"),
                    "status": application.get("status"),
                    "status_text": status_map.get(application.get("status"), "未知状态")
                }
            }
        except Exception as e:
            return error_response(f"查询申请状态失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_pending_applications(self, page: int = 1, page_size: int = 20) -> dict:
        """
        管理员：分页查询所有待审核的申请（status=0）

        Args:
            page: 页码
            page_size: 每页条数

        Returns:
            dict: {"success": bool, "message": str, "data": {"applications": list, ...}}
        """
        return self.get_all_applications(page, page_size, status_filter=0)

    def get_all_applications(self, page: int = 1, page_size: int = 20,
                             status_filter: int = None) -> dict:
        """
        管理员：分页查询所有志愿者申请记录（按时间倒序）
        可指定状态筛选

        Args:
            page: 页码
            page_size: 每页条数
            status_filter: 状态筛选（0/1/2/3，可选）

        Returns:
            dict: {"success": bool, "message": str, "data": {"applications": list, ...}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            where_clause = None
            params = None
            if status_filter is not None:
                where_clause = "status = %s"
                params = (status_filter,)

            result = self.db.get_paginated(
                table_name="t_volunteer_application",
                page=page,
                page_size=page_size,
                where_clause=where_clause,
                params=params,
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"applications": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data)

            items = self._format_application_list(result["data"])
            data = {
                "applications": items,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data)
        except Exception as e:
            return error_response(f"查询申请记录失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 管理员审核操作 ====================

    def approve_application(self, application_id: int, admin_id: str,
                            review_comment: str = None) -> dict:
        """
        管理员审核通过志愿者申请
        - 更新申请状态为 1，记录审核人和审核时间
        - 更新 t_user: role=2, volunteer_id（若空则生成）, level=1

        Args:
            application_id: 申请ID
            admin_id: 管理员ID
            review_comment: 审核意见（可选）

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            application = self.db.get_by_id("t_volunteer_application", "application_id", application_id)
            if not application:
                return error_response("申请记录不存在")

            if application.get("status") != 0:
                return error_response("仅待审核的申请可以通过")

            # 验证操作者是否为管理员
            admin = self.db.get_by_id("t_user", "user_id", admin_id)
            if not admin or admin.get("role") != 3:
                return error_response("仅管理员可以审核")

            now = datetime.now()

            # 1. 更新申请状态
            update_app = {
                "status": 1,
                "reviewed_by": admin_id,
                "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if review_comment is not None:
                update_app["review_comment"] = review_comment

            if not self.db.update("t_volunteer_application", "application_id", application_id, update_app):
                return error_response("更新申请状态失败")

            # 2. 更新用户表：设置角色、志愿者编号、等级
            user_id = application.get("user_id")
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("申请人不存在")

            update_user = {"role": 2, "level": 1}
            # 如果用户还没有志愿者编号，则生成一个
            if not user.get("volunteer_id"):
                volunteer_id = self._generate_volunteer_id()
                update_user["volunteer_id"] = volunteer_id

            if not self.db.update("t_user", "user_id", user_id, update_user):
                return error_response("更新用户角色失败")

            return {
                "success": True,
                "message": "审核通过，用户已升级为志愿者",
                "data": {
                    "application_id": application_id,
                    "status": 1,
                    "reviewed_by": admin_id,
                    "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "volunteer_id": update_user.get("volunteer_id", user.get("volunteer_id")),
                    "level": 1
                }
            }
        except Exception as e:
            return error_response(f"审核通过失败：{str(e)}")
        finally:
            self.db.close_database()

    def reject_application(self, application_id: int, admin_id: str,
                           reason: str = "") -> dict:
        """
        管理员驳回报销申请

        Args:
            application_id: 申请ID
            admin_id: 管理员ID
            reason: 驳回原因

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            application = self.db.get_by_id("t_volunteer_application", "application_id", application_id)
            if not application:
                return error_response("申请记录不存在")

            if application.get("status") != 0:
                return error_response("仅待审核的申请可以驳回")

            # 验证管理员身份
            admin = self.db.get_by_id("t_user", "user_id", admin_id)
            if not admin or admin.get("role") != 3:
                return error_response("仅管理员可以审核")

            now = datetime.now()
            update_data = {
                "status": 2,
                "reviewed_by": admin_id,
                "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "review_comment": reason,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_volunteer_application", "application_id", application_id, update_data):
                return error_response("驳回申请失败")

            return {
                "success": True,
                "message": "志愿者申请已驳回",
                "data": {
                    "application_id": application_id,
                    "status": 2,
                    "reviewed_by": admin_id,
                    "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "review_comment": reason
                }
            }
        except Exception as e:
            return error_response(f"驳回申请失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 志愿者信息查询（直接操作 t_user） ====================

    def get_volunteer_info(self, user_id: str) -> dict:
        """
        查询用户的志愿者信息（必须是志愿者角色）

        Args:
            user_id: 用户ID

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("用户不存在")

            if user.get("role") != 2:
                return error_response("该用户不是志愿者")

            data = {
                "user_id": user.get("user_id"),
                "nickname": user.get("nickname"),
                "avatar_url": user.get("avatarURL"),
                "volunteer_id": user.get("volunteer_id"),
                "level": user.get("level"),
                "points": user.get("points"),
                "created_at": user.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if user.get("created_at") else None
            }
            return success_response("成功", data)
        except Exception as e:
            return error_response(f"查询志愿者信息失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_volunteer_number(self, user_id: str) -> dict:
        """
        查询用户志愿者编号

        Args:
            user_id: 用户ID

        Returns:
            dict: {"success": bool, "message": str, "data": {"volunteer_id": str or None}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("用户不存在")
            if user.get("role") != 2:
                return success_response("该用户不是志愿者", {"volunteer_id": None})
            return success_response("成功", {"volunteer_id": user.get("volunteer_id")})
        except Exception as e:
            return error_response(f"查询志愿者编号失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_volunteer_level(self, user_id: str) -> dict:
        """
        查询用户志愿者等级

        Args:
            user_id: 用户ID

        Returns:
            dict: {"success": bool, "message": str, "data": {"level": int or None}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("用户不存在")
            if user.get("role") != 2:
                return success_response("该用户不是志愿者", {"level": None})
            return success_response("成功", {"level": user.get("level")})
        except Exception as e:
            return error_response(f"查询志愿者等级失败：{str(e)}")
        finally:
            self.db.close_database()

    def update_volunteer_level(self, user_id: str, new_level: int, admin_id: str) -> dict:
        """
        管理员更新志愿者等级

        Args:
            user_id: 目标用户ID
            new_level: 新等级（正整数）
            admin_id: 操作管理员ID

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 验证操作者身份
            admin = self.db.get_by_id("t_user", "user_id", admin_id)
            if not admin or admin.get("role") != 3:
                return error_response("仅管理员可以修改志愿者等级")

            # 验证目标用户
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("目标用户不存在")
            if user.get("role") != 2:
                return error_response("该用户不是志愿者")

            if new_level < 1:
                return error_response("等级必须为正整数")

            if not self.db.update("t_user", "user_id", user_id, {"level": new_level}):
                return error_response("更新等级失败")

            return {
                "success": True,
                "message": "志愿者等级已更新",
                "data": {"user_id": user_id, "level": new_level}
            }
        except Exception as e:
            return error_response(f"更新志愿者等级失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 统计功能 ====================

    def count_applications_by_status(self) -> dict:
        """
        统计各状态申请数量

        Returns:
            dict: {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            sql = """SELECT status, COUNT(*) AS count
                     FROM t_volunteer_application
                     GROUP BY status"""
            results = self.db.execute_raw_sql(sql)
            count_map = {}
            if results:
                for row in results:
                    count_map[str(row["status"])] = row["count"]

            for s in [0, 1, 2, 3]:
                if str(s) not in count_map:
                    count_map[str(s)] = 0

            total = sum(count_map.values())
            data = {
                "total": total,
                "pending": count_map["0"],
                "approved": count_map["1"],
                "rejected": count_map["2"],
                "cancelled": count_map["3"]
            }
            return success_response("成功", data)
        except Exception as e:
            return error_response(f"统计失败：{str(e)}")
        finally:
            self.db.close_database()

    def count_approved_volunteers(self) -> dict:
        """
        统计当前已成为志愿者的人数（t_user 中 role=2 的数量）

        Returns:
            dict: {"success": bool, "message": str, "data": {"count": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            sql = "SELECT COUNT(*) AS count FROM t_user WHERE role = 2 AND is_active = 1"
            result = self.db.execute_raw_sql(sql)
            count = result[0]["count"] if result else 0
            return success_response("成功", {"count": count})
        except Exception as e:
            return error_response(f"统计失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 内部辅助方法 ====================

    def _has_pending_application(self, user_id: str) -> bool:
        """
        检查用户是否已有待审核的申请

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否存在
        """
        if not self.db.open_database():
            return False
        try:
            sql = "SELECT 1 FROM t_volunteer_application WHERE user_id = %s AND status = 0 LIMIT 1"
            result = self.db.execute_raw_sql(sql, (user_id,))
            return len(result) > 0 if result else False
        except Exception:
            return False
        finally:
            self.db.close_database()

    def _generate_volunteer_id(self) -> str:
        """
        生成全局唯一的志愿者编号（格式：VOL_ + 6位随机小写字母+数字）

        Returns:
            str: 生成的志愿者编号
        """
        while True:
            vid = 'VOL_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            if not self._volunteer_id_exists(vid):
                return vid

    def _volunteer_id_exists(self, volunteer_id: str) -> bool:
        """
        检查志愿者编号是否已存在
        调用前需确保数据库连接已打开
        """
        try:
            sql = "SELECT 1 FROM t_user WHERE volunteer_id = %s LIMIT 1"
            results = self.db.execute_raw_sql(sql, (volunteer_id,))
            return len(results) > 0 if results else False
        except Exception:
            return True

    def _format_application_list(self, rows: list) -> list:
        """
        格式化申请列表（关联用户信息）

        Args:
            rows: 原始数据库行列表

        Returns:
            list: 格式化后的列表
        """
        if not rows:
            return []
        formatted = []
        for row in rows:
            user = self.db.get_by_id("t_user", "user_id", row.get("user_id"))
            formatted.append({
                "application_id": row.get("application_id"),
                "user_id": row.get("user_id"),
                "nickname": user.get("nickname") if user else None,
                "avatar_url": user.get("avatarURL") if user else None,
                "role": user.get("role") if user else None,
                "apply_content": row.get("apply_content"),
                "status": row.get("status"),
                "review_comment": row.get("review_comment"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("reviewed_at") else None,
                "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None,
                "updated_at": row.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("updated_at") else None
            })
        return formatted
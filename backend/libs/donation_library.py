"""
捐赠（募捐）业务逻辑层
提供捐赠提交、取消、查询、审核、汇总等核心功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
import uuid


class DonationLibrary:
    """
    捐赠业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        """初始化：创建数据库管理器实例"""
        self.db = DatabaseManager()

    # ==================== 第一批次：核心捐赠操作 ====================

    def submit_donation(self, user_id: str, project_id: int, amount: float) -> dict:
        """
        提交捐赠申请
        - 验证用户是否存在且激活
        - 验证募捐项目是否存在且进行中
        - 检查重复捐赠（调用 check_duplicate_donation）
        - 生成 donation_id，插入 t_donation 记录（status=0 待确认）
        - 更新 t_donation_project 的 current_amount 和 participant_count

        Args:
            user_id: 捐款人ID
            project_id: 募捐项目ID
            amount: 捐赠金额

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 1. 验证用户是否存在且激活
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("用户不存在")
            if user.get("is_active") == 0:
                return error_response("用户已被封禁，无法捐赠")

            # 2. 验证募捐项目是否存在且进行中
            project = self.db.get_by_id("t_donation_project", "project_id", project_id)
            if not project:
                return error_response("募捐项目不存在")
            if project.get("status") == 0:
                return error_response("募捐项目已结束，无法捐赠")

            # 3. 检查重复捐赠
            dup_result = self.check_duplicate_donation(user_id, project_id)
            if dup_result.get("data", {}).get("is_duplicate"):
                return error_response("您已对该项目提交过捐赠，请勿重复提交", data={"donation_id": dup_result["data"]["donation_id"]})

            # 4. 生成捐赠单号，插入捐赠记录
            donation_id = str(uuid.uuid4()).replace("-", "")[:32]
            now = datetime.now()
            donation_data = {
                "donation_id": donation_id,
                "user_id": user_id,
                "project_id": project_id,
                "amount": amount,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "status": 0
            }
            if not self.db.insert("t_donation", donation_data):
                return error_response("插入捐赠记录失败")

            # 5. 更新项目统计（已筹金额 + 参与人数）
            update_data = {
                "current_amount": float(project.get("current_amount", 0)) + amount,
                "participant_count": project.get("participant_count", 0) + 1
            }
            if not self.db.update("t_donation_project", "project_id", project_id, update_data):
                return error_response("更新项目统计失败，请联系管理员")

            return success_response(
                "捐赠提交成功，等待管理员确认",
                data={
                    "donation_id": donation_id,
                    "amount": float(amount),
                    "status": 0,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            return error_response(f"提交捐赠失败：{str(e)}")
        finally:
            self.db.close_database()

    def cancel_donation(self, donation_id: str, user_id: str) -> dict:
        """
        取消捐赠（仅允许捐赠者本人取消自己的待确认捐赠）
        - 验证捐赠记录存在且 status=0
        - 验证捐赠者与当前用户一致
        - 更新 status=3（已取消）
        - 回滚 t_donation_project 的 current_amount 和 participant_count

        Args:
            donation_id: 捐赠单号
            user_id: 请求取消的用户ID（必须与捐赠者一致）

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 1. 查询捐赠记录
            donation = self.db.get_by_id("t_donation", "donation_id", donation_id)
            if not donation:
                return error_response("捐赠记录不存在")

            # 2. 验证状态是否为待确认
            if donation.get("status") != 0:
                return error_response("仅待确认的捐赠可以取消")

            # 3. 验证所有权
            if donation.get("user_id") != user_id:
                return error_response("无权取消他人的捐赠")

            # 4. 更新捐赠状态为已取消
            now = datetime.now()
            update_donation_data = {
                "status": 3,
                "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_donation", "donation_id", donation_id, update_donation_data):
                return error_response("更新捐赠状态失败")

            # 5. 回滚项目统计
            project = self.db.get_by_id("t_donation_project", "project_id", donation.get("project_id"))
            if project:
                new_amount = max(float(project.get("current_amount", 0)) - float(donation.get("amount", 0)), 0)
                new_participant = max(project.get("participant_count", 0) - 1, 0)
                update_project_data = {
                    "current_amount": new_amount,
                    "participant_count": new_participant
                }
                self.db.update("t_donation_project", "project_id", donation.get("project_id"), update_project_data)

            return success_response(
                "捐赠已取消",
                data={
                    "donation_id": donation_id,
                    "status": 3,
                    "cancelled_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            return error_response(f"取消捐赠失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_donation_by_id(self, donation_id: str) -> dict:
        """
        根据捐赠单号查询捐赠详情
        - 返回包含用户昵称、头像、项目标题、审核信息等

        Args:
            donation_id: 捐赠单号

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
                   data 结构：donation_id, user_id, nickname, avatar_url,
                              project_id, project_title, amount, status,
                              reviewed_by, reviewed_at, review_comment, created_at
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            donation = self.db.get_by_id("t_donation", "donation_id", donation_id)
            if not donation:
                return error_response("捐赠记录不存在")

            user = self.db.get_by_id("t_user", "user_id", donation.get("user_id"))
            project = self.db.get_by_id("t_donation_project", "project_id", donation.get("project_id"))

            data = {
                "donation_id": donation.get("donation_id"),
                "user_id": donation.get("user_id"),
                "nickname": user.get("nickname") if user else None,
                "avatar_url": user.get("avatarURL") if user else None,
                "project_id": donation.get("project_id"),
                "project_title": project.get("title") if project else None,
                "amount": float(donation.get("amount", 0)),
                "status": donation.get("status"),
                "reviewed_by": donation.get("reviewed_by"),
                "reviewed_at": donation.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if donation.get("reviewed_at") else None,
                "review_comment": donation.get("review_comment"),
                "created_at": donation.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if donation.get("created_at") else None
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询捐赠详情失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_user_donations(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        分页查询指定用户的所有捐赠记录（按时间倒序）
        - 关联 t_donation_project 获取项目标题

        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页条数

        Returns:
            dict: {"success": bool, "message": str, "data": {"donations": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_donation",
                page=page,
                page_size=page_size,
                where_clause="user_id = %s",
                params=(user_id,),
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"donations": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            donations = result["data"]
            donation_list = []
            for row in donations:
                user = self.db.get_by_id("t_user", "user_id", row.get("user_id"))
                project = self.db.get_by_id("t_donation_project", "project_id", row.get("project_id"))
                donation_list.append({
                    "donation_id": row.get("donation_id"),
                    "user_id": row.get("user_id"),
                    "nickname": user.get("nickname") if user else None,
                    "avatar_url": user.get("avatarURL") if user else None,
                    "project_id": row.get("project_id"),
                    "project_title": project.get("title") if project else None,
                    "amount": float(row.get("amount", 0)),
                    "status": row.get("status"),
                    "reviewed_by": row.get("reviewed_by"),
                    "reviewed_at": row.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("reviewed_at") else None,
                    "review_comment": row.get("review_comment"),
                    "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
                })

            data = {
                "donations": donation_list,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询用户捐赠记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_project_donations(self, project_id: int, page: int = 1, page_size: int = 20) -> dict:
        """
        分页查询指定募捐项目的所有捐赠记录（按时间倒序）
        - 关联 t_user 获取捐赠人昵称

        Args:
            project_id: 募捐项目ID
            page: 页码（从1开始）
            page_size: 每页条数

        Returns:
            dict: {"success": bool, "message": str, "data": {"donations": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_donation",
                page=page,
                page_size=page_size,
                where_clause="project_id = %s",
                params=(project_id,),
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"donations": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            donations = result["data"]
            donation_list = []
            for row in donations:
                user = self.db.get_by_id("t_user", "user_id", row.get("user_id"))
                project = self.db.get_by_id("t_donation_project", "project_id", row.get("project_id"))
                donation_list.append({
                    "donation_id": row.get("donation_id"),
                    "user_id": row.get("user_id"),
                    "nickname": user.get("nickname") if user else None,
                    "avatar_url": user.get("avatarURL") if user else None,
                    "project_id": row.get("project_id"),
                    "project_title": project.get("title") if project else None,
                    "amount": float(row.get("amount", 0)),
                    "status": row.get("status"),
                    "reviewed_by": row.get("reviewed_by"),
                    "reviewed_at": row.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("reviewed_at") else None,
                    "review_comment": row.get("review_comment"),
                    "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
                })

            data = {
                "donations": donation_list,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询项目捐赠记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def check_duplicate_donation(self, user_id: str, project_id: int) -> dict:
        """
        检查同一用户是否已对同一项目提交过未完成的捐赠（status=0 或 1）
        用于防止重复提交

        Args:
            user_id: 捐赠人ID
            project_id: 募捐项目ID

        Returns:
            dict: {"success": bool, "message": str, "data": {"is_duplicate": bool, "donation_id": str or None}}
        """
        should_close = False
        if not self.db.connection:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            should_close = True

        try:
            result = self.db.get_paginated(
                table_name="t_donation",
                page=1,
                page_size=1,
                where_clause="user_id = %s AND project_id = %s AND status = 0",
                params=(user_id, project_id),
                order_by=None
            )

            if result and result.get("data") and len(result["data"]) > 0:
                donation_row = result["data"][0]
                return success_response(
                    "已存在未完成的捐赠记录",
                    data={"is_duplicate": True, "donation_id": donation_row["donation_id"]}
                )
            else:
                return success_response("未发现重复捐赠", data={"is_duplicate": False, "donation_id": None})
        except Exception as e:
            return error_response(f"查重失败：{str(e)}")
        finally:
            if should_close:
                self.db.close_database()
    
    # ==================== 第二批次：管理与统计功能 ====================

    def approve_donation(self, donation_id: str, admin_id: str) -> dict:
        """
        管理员确认捐赠到账
        - 验证捐赠记录存在且 status=0
        - 更新 status=1（已到账），设置 reviewed_by, reviewed_at

        Args:
            donation_id: 捐赠单号
            admin_id: 审核管理员ID

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            donation = self.db.get_by_id("t_donation", "donation_id", donation_id)
            if not donation:
                return error_response("捐赠记录不存在")

            if donation.get("status") != 0:
                return error_response("仅待确认的捐赠可以进行到账确认")

            now = datetime.now()
            update_data = {
                "status": 1,
                "reviewed_by": admin_id,
                "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_donation", "donation_id", donation_id, update_data):
                return error_response("确认到账失败")

            return success_response(
                "捐赠已确认到账",
                data={
                    "donation_id": donation_id,
                    "status": 1,
                    "reviewed_by": admin_id,
                    "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            return error_response(f"确认捐赠失败：{str(e)}")
        finally:
            self.db.close_database()

    def reject_donation(self, donation_id: str, admin_id: str, reason: str = "") -> dict:
        """
        管理员驳回捐赠
        - 验证捐赠记录存在且 status=0
        - 更新 status=2（已驳回），设置 reviewed_by, reviewed_at, review_comment
        - 回滚 t_donation_project 的 current_amount 和 participant_count

        Args:
            donation_id: 捐赠单号
            admin_id: 审核管理员ID
            reason: 驳回原因

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            donation = self.db.get_by_id("t_donation", "donation_id", donation_id)
            if not donation:
                return error_response("捐赠记录不存在")

            if donation.get("status") != 0:
                return error_response("仅待确认的捐赠可以驳回")

            now = datetime.now()
            update_donation_data = {
                "status": 2,
                "reviewed_by": admin_id,
                "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "review_comment": reason
            }
            if not self.db.update("t_donation", "donation_id", donation_id, update_donation_data):
                return error_response("驳回捐赠失败")

            project = self.db.get_by_id("t_donation_project", "project_id", donation.get("project_id"))
            if project:
                new_amount = max(float(project.get("current_amount", 0)) - float(donation.get("amount", 0)), 0)
                new_participant = max(project.get("participant_count", 0) - 1, 0)
                update_project_data = {
                    "current_amount": new_amount,
                    "participant_count": new_participant
                }
                self.db.update("t_donation_project", "project_id", donation.get("project_id"), update_project_data)

            return success_response(
                "捐赠已驳回",
                data={
                    "donation_id": donation_id,
                    "status": 2,
                    "reviewed_by": admin_id,
                    "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "review_comment": reason
                }
            )
        except Exception as e:
            return error_response(f"驳回捐赠失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_donation_summary_by_project(self, project_id: int) -> dict:
        """
        获取指定项目的捐赠统计信息
        - 统计：总捐赠金额、总参与人数、平均金额、各状态数量

        Args:
            project_id: 募捐项目ID

        Returns:
            dict: {"success": bool, "message": str, "data": {
                "total_amount": float, "participant_count": int,
                "avg_amount": float, "pending_count": int,
                "confirmed_count": int, "rejected_count": int,
                "cancelled_count": int
            }}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_donation",
                page=1,
                page_size=999999,
                where_clause="project_id = %s",
                params=(project_id,),
                order_by=None
            )

            if not result or not result.get("data"):
                data = {
                    "total_amount": 0.0,
                    "participant_count": 0,
                    "avg_amount": 0.0,
                    "pending_count": 0,
                    "confirmed_count": 0,
                    "rejected_count": 0,
                    "cancelled_count": 0
                }
                return success_response("成功", data=data)

            rows = result["data"]
            total_amount = sum(float(r.get("amount", 0)) for r in rows)
            participant_ids = set(r.get("user_id") for r in rows if r.get("user_id"))
            participant_count = len(participant_ids)
            avg_amount = round(total_amount / len(rows), 2) if rows else 0
            pending_count = sum(1 for r in rows if r.get("status") == 0)
            confirmed_count = sum(1 for r in rows if r.get("status") == 1)
            rejected_count = sum(1 for r in rows if r.get("status") == 2)
            cancelled_count = sum(1 for r in rows if r.get("status") == 3)

            data = {
                "total_amount": total_amount,
                "participant_count": participant_count,
                "avg_amount": avg_amount,
                "pending_count": pending_count,
                "confirmed_count": confirmed_count,
                "rejected_count": rejected_count,
                "cancelled_count": cancelled_count
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"获取统计信息失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_all_donations(self, page: int = 1, page_size: int = 20,
                          status_filter: int = None) -> dict:
        """
        管理员查看所有捐赠记录（分页，按时间倒序）
        - 关联用户昵称、项目标题
        - 支持按状态筛选

        Args:
            page: 页码（从1开始）
            page_size: 每页条数
            status_filter: 状态筛选（0/1/2/3，可选）

        Returns:
            dict: {"success": bool, "message": str, "data": {
                "donations": list, "total": int, "page": int, "page_size": int
            }}
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
                table_name="t_donation",
                page=page,
                page_size=page_size,
                where_clause=where_clause,
                params=params,
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"donations": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            donations = result["data"]
            donation_list = []
            for row in donations:
                user = self.db.get_by_id("t_user", "user_id", row.get("user_id"))
                project = self.db.get_by_id("t_donation_project", "project_id", row.get("project_id"))
                donation_list.append({
                    "donation_id": row.get("donation_id"),
                    "user_id": row.get("user_id"),
                    "nickname": user.get("nickname") if user else None,
                    "avatar_url": user.get("avatarURL") if user else None,
                    "project_id": row.get("project_id"),
                    "project_title": project.get("title") if project else None,
                    "amount": float(row.get("amount", 0)),
                    "status": row.get("status"),
                    "reviewed_by": row.get("reviewed_by"),
                    "reviewed_at": row.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("reviewed_at") else None,
                    "review_comment": row.get("review_comment"),
                    "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
                })

            data = {
                "donations": donation_list,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"获取所有捐赠记录失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 内部辅助方法 ====================

    def _update_project_stats(self, project_id: int, amount_delta: float, participant_delta: int) -> bool:
        """
        内部方法：更新募捐项目的统计数据（已筹金额、参与人数）
        由 submit_donation / cancel_donation / reject_donation 调用

        Args:
            project_id: 募捐项目ID
            amount_delta: 金额变化（正数增加，负数减少）
            participant_delta: 参与人数变化（+1 或 -1）

        Returns:
            bool: 是否成功
        """
        if not self.db.open_database():
            return False

        try:
            project = self.db.get_by_id("t_donation_project", "project_id", project_id)
            if not project:
                return False

            new_amount = max(float(project.get("current_amount", 0)) + amount_delta, 0)
            new_participant = max(project.get("participant_count", 0) + participant_delta, 0)
            update_data = {
                "current_amount": new_amount,
                "participant_count": new_participant
            }
            return self.db.update("t_donation_project", "project_id", project_id, update_data)
        except Exception as e:
            return False
        finally:
            self.db.close_database()
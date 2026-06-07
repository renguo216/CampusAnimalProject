# ===== backend/libs/reimbursement_library.py =====
"""
报销（报销申请）业务逻辑层
提供报销提交、修改、撤销、查询、审核等核心功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
import uuid


class ReimbursementLibrary:
    """
    报销业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        """初始化：创建数据库管理器实例"""
        self.db = DatabaseManager()

    # ==================== 用户操作 ====================

    def submit_reimbursement(self, user_id: str, amount: float, type_: str = None,
                             description: str = None, receipt_urls: str = None) -> dict:
        """
        提交报销申请
        - 验证用户是否存在且激活
        - 生成 reimb_id，插入 t_reimbursement 记录（status=0）

        Args:
            user_id: 申请人ID
            amount: 申请金额
            type_: 报销类型（如 医疗费、运输费等）
            description: 报销说明
            receipt_urls: 收据图片链接（JSON数组字符串）

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 1. 验证用户存在且激活
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("用户不存在")
            if user.get("is_active") == 0:
                return error_response("用户已被封禁，无法提交报销")

            # 2. 生成报销单号
            reimb_id = str(uuid.uuid4()).replace("-", "")[:32]
            now = datetime.now()

            # 3. 插入报销记录
            data = {
                "reimb_id": reimb_id,
                "user_id": user_id,
                "amount": amount,
                "status": 0,
                "type": type_,
                "description": description,
                "receipt_urls": receipt_urls,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.insert("t_reimbursement", data):
                return error_response("提交报销申请失败")

            return success_response(
                "报销申请提交成功，等待管理员审核",
                data={
                    "reimb_id": reimb_id,
                    "amount": float(amount),
                    "status": 0,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            return error_response(f"提交报销申请失败：{str(e)}")
        finally:
            self.db.close_database()

    def update_reimbursement(self, reimb_id: str, user_id: str,
                             amount: float = None, type_: str = None,
                             description: str = None, receipt_urls: str = None) -> dict:
        """
        修改报销申请（仅允许自己的待审核申请）

        Args:
            reimb_id: 报销单号
            user_id: 申请用户ID（用于验证所有权）
            amount: 新金额（可选）
            type_: 新类型（可选）
            description: 新说明（可选）
            receipt_urls: 新凭证（可选）

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 1. 查询报销记录
            reimbursement = self.db.get_by_id("t_reimbursement", "reimb_id", reimb_id)
            if not reimbursement:
                return error_response("报销记录不存在")

            # 2. 验证所有权和状态
            if reimbursement.get("user_id") != user_id:
                return error_response("无权修改他人的报销申请")
            if reimbursement.get("status") != 0:
                return error_response("仅待审核的报销可以修改")

            # 3. 构造需要更新的字段（只允许修改的字段）
            update_data = {"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            if amount is not None:
                update_data["amount"] = amount
            if type_ is not None:
                update_data["type"] = type_
            if description is not None:
                update_data["description"] = description
            if receipt_urls is not None:
                update_data["receipt_urls"] = receipt_urls

            if not self.db.update("t_reimbursement", "reimb_id", reimb_id, update_data):
                return error_response("修改报销申请失败")

            return success_response(
                "报销申请已修改",
                data={"reimb_id": reimb_id, "updated_at": update_data["updated_at"]}
            )
        except Exception as e:
            return error_response(f"修改报销申请失败：{str(e)}")
        finally:
            self.db.close_database()

    def cancel_reimbursement(self, reimb_id: str, user_id: str) -> dict:
        """
        撤销报销申请（仅允许自己的待审核申请）

        Args:
            reimb_id: 报销单号
            user_id: 申请用户ID

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            reimbursement = self.db.get_by_id("t_reimbursement", "reimb_id", reimb_id)
            if not reimbursement:
                return error_response("报销记录不存在")

            if reimbursement.get("user_id") != user_id:
                return error_response("无权撤销他人的报销申请")
            if reimbursement.get("status") != 0:
                return error_response("仅待审核的报销可以撤销")

            now = datetime.now()
            update_data = {
                "status": 3,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_reimbursement", "reimb_id", reimb_id, update_data):
                return error_response("撤销报销申请失败")

            return success_response(
                "报销申请已撤销",
                data={"reimb_id": reimb_id, "status": 3, "cancelled_at": now.strftime("%Y-%m-%d %H:%M:%S")}
            )
        except Exception as e:
            return error_response(f"撤销报销申请失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 查询操作 ====================

    def get_reimbursement_by_id(self, reimb_id: str) -> dict:
        """
        根据报销单号查询报销详情（含申请人信息）

        Args:
            reimb_id: 报销单号

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            reimbursement = self.db.get_by_id("t_reimbursement", "reimb_id", reimb_id)
            if not reimbursement:
                return error_response("报销记录不存在")

            # 关联查询申请人信息
            user = self.db.get_by_id("t_user", "user_id", reimbursement.get("user_id"))

            data = {
                "reimb_id": reimbursement.get("reimb_id"),
                "user_id": reimbursement.get("user_id"),
                "nickname": user.get("nickname") if user else None,
                "avatar_url": user.get("avatarURL") if user else None,
                "amount": float(reimbursement.get("amount", 0)),
                "status": reimbursement.get("status"),
                "type": reimbursement.get("type"),
                "description": reimbursement.get("description"),
                "receipt_urls": reimbursement.get("receipt_urls"),
                "review_comment": reimbursement.get("review_comment"),
                "reviewed_by": reimbursement.get("reviewed_by"),
                "reviewed_at": reimbursement.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if reimbursement.get("reviewed_at") else None,
                "created_at": reimbursement.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if reimbursement.get("created_at") else None,
                "updated_at": reimbursement.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if reimbursement.get("updated_at") else None
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询报销详情失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_user_reimbursements(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        分页查询指定用户的所有报销记录（按时间倒序）

        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页条数

        Returns:
            dict: {"success": bool, "message": str, "data": {"reimbursements": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_reimbursement",
                page=page,
                page_size=page_size,
                where_clause="user_id = %s",
                params=(user_id,),
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"reimbursements": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            return success_response(
                "成功",
                data={
                    "reimbursements": self._format_reimbursements_list(result["data"]),
                    "total": result.get("total", 0),
                    "page": page,
                    "page_size": page_size
                }
            )
        except Exception as e:
            return error_response(f"查询用户报销记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_all_reimbursements(self, page: int = 1, page_size: int = 20,
                               status_filter: int = None) -> dict:
        """
        管理员查看所有报销记录（分页，按时间倒序）
        可指定状态筛选

        Args:
            page: 页码
            page_size: 每页条数
            status_filter: 状态筛选（0/1/2/3，可选）

        Returns:
            dict: {"success": bool, "message": str, "data": {...}}
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
                table_name="t_reimbursement",
                page=page,
                page_size=page_size,
                where_clause=where_clause,
                params=params,
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"reimbursements": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            return success_response(
                "成功",
                data={
                    "reimbursements": self._format_reimbursements_list(result["data"]),
                    "total": result.get("total", 0),
                    "page": page,
                    "page_size": page_size
                }
            )
        except Exception as e:
            return error_response(f"查询所有报销记录失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 管理员审核操作 ====================

    def approve_reimbursement(self, reimb_id: str, admin_id: str, review_comment: str = None) -> dict:
        """
        管理员审核通过报销

        Args:
            reimb_id: 报销单号
            admin_id: 审核管理员ID
            review_comment: 审核意见（可选）

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            reimbursement = self.db.get_by_id("t_reimbursement", "reimb_id", reimb_id)
            if not reimbursement:
                return error_response("报销记录不存在")
            if reimbursement.get("status") != 0:
                return error_response("仅待审核的报销可以通过")

            now = datetime.now()
            update_data = {
                "status": 1,
                "reviewed_by": admin_id,
                "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if review_comment is not None:
                update_data["review_comment"] = review_comment

            if not self.db.update("t_reimbursement", "reimb_id", reimb_id, update_data):
                return error_response("审核通过失败")

            return success_response(
                "报销审核通过",
                data={
                    "reimb_id": reimb_id,
                    "status": 1,
                    "reviewed_by": admin_id,
                    "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "review_comment": review_comment
                }
            )
        except Exception as e:
            return error_response(f"审核通过失败：{str(e)}")
        finally:
            self.db.close_database()

    def reject_reimbursement(self, reimb_id: str, admin_id: str, reason: str = "") -> dict:
        """
        管理员驳回报销申请

        Args:
            reimb_id: 报销单号
            admin_id: 审核管理员ID
            reason: 驳回原因

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            reimbursement = self.db.get_by_id("t_reimbursement", "reimb_id", reimb_id)
            if not reimbursement:
                return error_response("报销记录不存在")
            if reimbursement.get("status") != 0:
                return error_response("仅待审核的报销可以驳回")

            now = datetime.now()
            update_data = {
                "status": 2,
                "reviewed_by": admin_id,
                "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "review_comment": reason,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_reimbursement", "reimb_id", reimb_id, update_data):
                return error_response("驳回失败")

            return success_response(
                "报销申请已驳回",
                data={
                    "reimb_id": reimb_id,
                    "status": 2,
                    "reviewed_by": admin_id,
                    "reviewed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "review_comment": reason
                }
            )
        except Exception as e:
            return error_response(f"驳回报销失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 状态查询 ====================

    def get_reimbursement_status(self, reimb_id: str) -> dict:
        """
        获取报销状态及对应文本说明

        Args:
            reimb_id: 报销单号

        Returns:
            dict: {"success": bool, "message": str, "data": {"reimb_id": str, "status": int, "status_text": str}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            reimbursement = self.db.get_by_id("t_reimbursement", "reimb_id", reimb_id)
            if not reimbursement:
                return error_response("报销记录不存在")

            status_map = {0: "待审核", 1: "已通过", 2: "已驳回", 3: "已撤销"}
            return success_response(
                "成功",
                data={
                    "reimb_id": reimbursement.get("reimb_id"),
                    "status": reimbursement.get("status"),
                    "status_text": status_map.get(reimbursement.get("status"), "未知状态")
                }
            )
        except Exception as e:
            return error_response(f"查询报销状态失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_reimbursement_count_by_status(self, status: int = None) -> dict:
        """
        获取报销各状态的数量统计（用于管理看板）

        Args:
            status: 可选，指定状态统计（不传则统计全部）

        Returns:
            dict: {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            if status is not None:
                sql = "SELECT COUNT(*) AS count FROM t_reimbursement WHERE status = %s"
                result = self.db.execute_raw_sql(sql, (status,))
                total = result[0]["count"] if result else 0
                data = {"status": status, "count": total}
            else:
                sql = """SELECT status, COUNT(*) AS count
                         FROM t_reimbursement
                         GROUP BY status"""
                results = self.db.execute_raw_sql(sql)
                count_by_status = {}
                if results:
                    for row in results:
                        count_by_status[str(row["status"])] = row["count"]
                # 补全所有状态（若某状态无记录则为0）
                for s in [0, 1, 2, 3]:
                    if str(s) not in count_by_status:
                        count_by_status[str(s)] = 0
                total = sum(count_by_status.values())
                data = {
                    "total": total,
                    "pending": count_by_status["0"],
                    "approved": count_by_status["1"],
                    "rejected": count_by_status["2"],
                    "cancelled": count_by_status["3"]
                }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"统计查询失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 内部辅助方法 ====================

    def _format_reimbursements_list(self, rows: list) -> list:
        """
        格式化报销列表（统一时间字段、关联用户信息）

        Args:
            rows: 原始数据库行列表

        Returns:
            list: 格式化后的报销列表
        """
        if not rows:
            return []
        formatted = []
        for row in rows:
            # 关联查询用户信息（每个记录单独查，简洁但性能可控，与 donation_library 保持一致）
            user = self.db.get_by_id("t_user", "user_id", row.get("user_id"))
            formatted.append({
                "reimb_id": row.get("reimb_id"),
                "user_id": row.get("user_id"),
                "nickname": user.get("nickname") if user else None,
                "avatar_url": user.get("avatarURL") if user else None,
                "amount": float(row.get("amount", 0)),
                "status": row.get("status"),
                "type": row.get("type"),
                "description": row.get("description"),
                "receipt_urls": row.get("receipt_urls"),
                "review_comment": row.get("review_comment"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("reviewed_at") else None,
                "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None,
                "updated_at": row.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("updated_at") else None
            })
        return formatted
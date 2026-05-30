"""
募捐项目业务逻辑层
提供募捐项目的增删改查、搜索、统计等功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager


class DonationProjectLibrary:
    """
    募捐项目业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        """初始化：创建数据库管理器实例"""
        self.db = DatabaseManager()

    # ==================== 基础 CRUD ====================

    def create_project(self, title: str, description: str = None, target_amount: float = 0.0) -> dict:
        """
        创建募捐项目
        - 生成 created_at，设置 status=1（进行中）
        - current_amount=0，participant_count=0

        Args:
            title: 项目标题
            description: 项目描述（可选）
            target_amount: 目标金额

        Returns:
            dict: {"success": bool, "message": str, "data": {"project_id": int, "created_at": str}}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            # 校验项目标题不能为空
            if not title or not title.strip():
                return {"success": False, "message": "项目标题不能为空", "data": None}
            now = datetime.now()
            data = {
                'title': title,
                'description': description,
                'target_amount': target_amount,
                'current_amount': 0.0,
                'participant_count': 0,
                'status': 1,
                'created_at': now.strftime('%Y-%m-%d %H:%M:%S')
            }
            if not self.db.insert('t_donation_project', data):
                return {"success": False, "message": "创建募捐项目失败", "data": None}
            # 获取自动生成的 project_id
            result = self.db.execute_raw_sql("SELECT LAST_INSERT_ID() AS id")
            project_id = result[0]["id"] if result else None
            if not project_id:
                return {"success": False, "message": "获取项目ID失败", "data": None}
            return {
                "success": True,
                "message": "创建募捐项目成功",
                "data": {
                    "project_id": project_id,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        except Exception as e:
            return {"success": False, "message": f"创建募捐项目失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def update_project(self, project_id: int, update_data: dict) -> dict:
        """
        更新募捐项目信息（管理员调用）
        - 可更新的字段：title, description, target_amount, status 等
        - 不对 current_amount, participant_count 进行修改（由 donation_library 或 _update_project_stats 处理）

        Args:
            project_id: 募捐项目ID
            update_data: 要更新的字段字典

        Returns:
            dict: {"success": bool, "message": str, "data": dict or None}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            # 检查项目是否存在
            project = self.db.get_by_id('t_donation_project', 'project_id', project_id)
            if not project:
                return {"success": False, "message": "募捐项目不存在", "data": None}
            # 过滤只允许更新的字段（禁止直接修改统计字段）
            allowed_fields = ['title', 'description', 'target_amount', 'status']
            clean_data = {k: v for k, v in update_data.items() if k in allowed_fields}
            if not clean_data:
                return {"success": False, "message": "没有需要更新的有效字段", "data": None}
            if not self.db.update('t_donation_project', 'project_id', project_id, clean_data):
                return {"success": False, "message": "更新募捐项目失败", "data": None}
            return {
                "success": True,
                "message": "更新募捐项目成功",
                "data": {"project_id": project_id}
            }
        except Exception as e:
            return {"success": False, "message": f"更新募捐项目失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def delete_project(self, project_id: int) -> dict:
        """
        删除募捐项目（管理员调用）
        - 级联删除关联的捐赠记录（由数据库外键 ON DELETE CASCADE 处理）

        Args:
            project_id: 募捐项目ID

        Returns:
            dict: {"success": bool, "message": str, "data": {"project_id": int}}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            # 检查项目是否存在
            project = self.db.get_by_id('t_donation_project', 'project_id', project_id)
            if not project:
                return {"success": False, "message": "募捐项目不存在", "data": None}
            if not self.db.delete('t_donation_project', 'project_id', project_id):
                return {"success": False, "message": "删除募捐项目失败", "data": None}
            return {
                "success": True,
                "message": "删除募捐项目成功",
                "data": {"project_id": project_id}
            }
        except Exception as e:
            return {"success": False, "message": f"删除募捐项目失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    # ==================== 查询 ====================

    def get_project_by_id(self, project_id: int) -> dict:
        """
        根据项目ID查询募捐项目详情

        Args:
            project_id: 募捐项目ID

        Returns:
            dict: {"success": bool, "message": str, "data": {
                "project_id": int,
                "title": str,
                "description": str or None,
                "target_amount": float,
                "current_amount": float,
                "participant_count": int,
                "status": int,
                "created_at": str or None
            }}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            project = self.db.get_by_id('t_donation_project', 'project_id', project_id)
            if not project:
                return {"success": False, "message": "募捐项目不存在", "data": None}
            data = {
                "project_id": project["project_id"],
                "title": project["title"],
                "description": project.get("description"),
                "target_amount": float(project.get("target_amount", 0)),
                "current_amount": float(project.get("current_amount", 0)),
                "participant_count": project.get("participant_count", 0),
                "status": project.get("status"),
                "created_at": project["created_at"].strftime("%Y-%m-%d %H:%M:%S") if project.get("created_at") else None
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"查询募捐项目详情失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def get_all_projects(self, page: int = 1, page_size: int = 20,
                         order_by: str = "created_at DESC") -> dict:
        """
        获取所有募捐项目（分页，按指定排序）

        Args:
            page: 页码（从1开始）
            page_size: 每页条数
            order_by: 排序字段（如 "created_at DESC", "current_amount DESC"）

        Returns:
            dict: {"success": bool, "message": str, "data": {
                "projects": list,
                "total": int,
                "page": int,
                "page_size": int
            }}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            result = self.db.get_paginated(
                table_name='t_donation_project',
                page=page,
                page_size=page_size,
                order_by=order_by
            )
            if not result:
                data = {"projects": [], "total": 0, "page": page, "page_size": page_size}
                return {"success": True, "message": "成功", "data": data}
            projects = []
            for row in result.get("data", []):
                projects.append({
                    "project_id": row["project_id"],
                    "title": row["title"],
                    "description": row.get("description"),
                    "target_amount": float(row.get("target_amount", 0)),
                    "current_amount": float(row.get("current_amount", 0)),
                    "participant_count": row.get("participant_count", 0),
                    "status": row.get("status"),
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
                })
            data = {
                "projects": projects,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"查询募捐项目列表失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def get_projects_by_status(self, status: int, page: int = 1,
                               page_size: int = 20) -> dict:
        """
        按状态筛选募捐项目（分页，按创建时间倒序）

        Args:
            status: 项目状态（0-已结束，1-进行中）
            page: 页码（从1开始）
            page_size: 每页条数

        Returns:
            dict: {"success": bool, "message": str, "data": {
                "projects": list,
                "total": int,
                "page": int,
                "page_size": int
            }}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            result = self.db.get_paginated(
                table_name='t_donation_project',
                page=page,
                page_size=page_size,
                where_clause="status = %s",
                params=(status,),
                order_by="created_at DESC"
            )
            if not result:
                data = {"projects": [], "total": 0, "page": page, "page_size": page_size}
                return {"success": True, "message": "成功", "data": data}
            projects = []
            for row in result.get("data", []):
                projects.append({
                    "project_id": row["project_id"],
                    "title": row["title"],
                    "description": row.get("description"),
                    "target_amount": float(row.get("target_amount", 0)),
                    "current_amount": float(row.get("current_amount", 0)),
                    "participant_count": row.get("participant_count", 0),
                    "status": row.get("status"),
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
                })
            data = {
                "projects": projects,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"按状态查询募捐项目失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def search_projects_by_title(self, keyword: str, page: int = 1,
                                 page_size: int = 20) -> dict:
        """
        根据项目标题模糊搜索（分页）

        Args:
            keyword: 搜索关键字
            page: 页码（从1开始）
            page_size: 每页条数

        Returns:
            dict: {"success": bool, "message": str, "data": {
                "projects": list,
                "total": int,
                "page": int,
                "page_size": int
            }}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            like_pattern = f"%{keyword}%"
            result = self.db.get_paginated(
                table_name='t_donation_project',
                page=page,
                page_size=page_size,
                where_clause="title LIKE %s",
                params=(like_pattern,),
                order_by="created_at DESC"
            )
            if not result:
                data = {"projects": [], "total": 0, "page": page, "page_size": page_size}
                return {"success": True, "message": "成功", "data": data}
            projects = []
            for row in result.get("data", []):
                projects.append({
                    "project_id": row["project_id"],
                    "title": row["title"],
                    "description": row.get("description"),
                    "target_amount": float(row.get("target_amount", 0)),
                    "current_amount": float(row.get("current_amount", 0)),
                    "participant_count": row.get("participant_count", 0),
                    "status": row.get("status"),
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
                })
            data = {
                "projects": projects,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"搜索募捐项目失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    # ==================== 统计与辅助 ====================

    def _update_project_stats(self, project_id: int, amount_delta: float,
                              participant_delta: int) -> bool:
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
        try:
            if not self.db.open_database():
                return False
            project = self.db.get_by_id('t_donation_project', 'project_id', project_id)
            if not project:
                return False
            new_amount = max(float(project.get("current_amount", 0)) + amount_delta, 0)
            new_participant = max(int(project.get("participant_count", 0)) + participant_delta, 0)
            update_data = {
                "current_amount": new_amount,
                "participant_count": new_participant
            }
            return self.db.update('t_donation_project', 'project_id', project_id, update_data)
        except Exception as e:
            return False
        finally:
            self.db.close_database()

    def get_project_summary(self, project_id: int) -> dict:
        """
        获取指定募捐项目的统计摘要
        - 包含：目标金额、已筹金额、完成百分比、参与人数、捐赠次数等

        Args:
            project_id: 募捐项目ID

        Returns:
            dict: {"success": bool, "message": str, "data": {
                "project_id": int,
                "title": str,
                "target_amount": float,
                "current_amount": float,
                "completion_percentage": float,
                "participant_count": int,
                "total_donation_count": int,
                "status": int,
                "created_at": str or None
            }}
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            project = self.db.get_by_id('t_donation_project', 'project_id', project_id)
            if not project:
                return {"success": False, "message": "募捐项目不存在", "data": None}
            count_result = self.db.execute_raw_sql(
                "SELECT COUNT(*) AS cnt FROM t_donation WHERE project_id = %s",
                (project_id,)
            )
            total_donation_count = count_result[0]["cnt"] if count_result else 0
            target_amount = float(project.get("target_amount", 0))
            current_amount = float(project.get("current_amount", 0))
            completion_percentage = round((current_amount / target_amount * 100), 2) if target_amount > 0 else 0.0
            data = {
                "project_id": project["project_id"],
                "title": project["title"],
                "target_amount": target_amount,
                "current_amount": current_amount,
                "completion_percentage": completion_percentage,
                "participant_count": project.get("participant_count", 0),
                "total_donation_count": total_donation_count,
                "status": project.get("status"),
                "created_at": project["created_at"].strftime("%Y-%m-%d %H:%M:%S") if project.get("created_at") else None
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"获取募捐项目统计摘要失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()
# ===== backend/libs/notice_library.py =====
"""
系统公告业务逻辑层
提供公告的增删改查、置顶、分页搜索等核心功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
import uuid
from datetime import datetime


class NoticeLibrary:
    """
    系统公告业务逻辑库
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        self.db = DatabaseManager()

    def _notice_to_dict(self, row: dict) -> dict:
        """将数据库行转为字典"""
        return {
            "notice_id": row["notice_id"],
            "title": row["title"],
            "content": row.get("content"),
            "is_top": row.get("is_top", 0),
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None
        }

    def _paginated_result(self, result, page, page_size) -> dict:
        """统一组装分页结果"""
        if not result:
            return success_response("成功", data={"notices": [], "total": 0, "page": page, "page_size": page_size})
        notices = [self._notice_to_dict(row) for row in result.get("data", [])]
        return success_response("成功", data={
            "notices": notices,
            "total": result.get("total", 0),
            "page": page,
            "page_size": page_size
        })

    # ========== 公告管理 ==========

    def create_notice(self, title, content, is_top=0):
        """创建公告"""
        if not title or not title.strip():
            return error_response("标题不能为空")

        notice_id = uuid.uuid4().hex[:12]
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not self.db.open_database():
            return error_response("数据库连接失败")

        data = {
            'notice_id': notice_id,
            'title': title,
            'content': content,
            'is_top': 1 if is_top else 0,
            'created_at': created_at
        }
        success = self.db.insert('t_notice', data)
        self.db.close_database()

        if not success:
            return error_response("创建公告失败")

        return success_response("公告创建成功", data={"notice_id": notice_id, "created_at": created_at})

    def get_all_notices(self, page=1, page_size=20, order_by='created_at DESC'):
        """
        获取公告列表（分页）
        默认按创建时间倒序排列，置顶公告优先显示
        """
        allowed_orders = {
            'created_at DESC': 'created_at DESC',
            'created_at ASC': 'created_at ASC',
            'title ASC': 'title ASC',
            'title DESC': 'title DESC'
        }
        safe_order = allowed_orders.get(order_by, 'created_at DESC')

        if not self.db.open_database():
            return error_response("数据库连接失败")

        result = self.db.get_paginated(
            't_notice',
            page=page,
            page_size=page_size,
            order_by=f"is_top DESC, {safe_order}"
        )
        self.db.close_database()

        return self._paginated_result(result, page, page_size)

    def get_latest_notice(self):
        """获取最新公告（置顶公告优先）"""
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = "SELECT * FROM t_notice WHERE is_top = 1 ORDER BY created_at DESC LIMIT 1"
        results = self.db.execute_raw_sql(sql)
        if not results:
            sql = "SELECT * FROM t_notice WHERE is_top = 0 ORDER BY created_at DESC LIMIT 1"
            results = self.db.execute_raw_sql(sql)

        self.db.close_database()

        if not results:
            return error_response("暂无公告")

        return success_response("成功", data=self._notice_to_dict(results[0]))

    def get_notice_by_id(self, notice_id):
        """根据ID查询公告详情"""
        if not self.db.open_database():
            return error_response("数据库连接失败")

        data = self.db.get_by_id('t_notice', 'notice_id', notice_id)
        self.db.close_database()

        if data:
            return success_response("成功", data=self._notice_to_dict(data))
        return error_response("公告不存在")

    def update_notice(self, notice_id, title=None, content=None, is_top=None):
        """更新公告"""
        update_data = {}
        if title is not None:
            if not title.strip():
                return error_response("标题不能为空")
            update_data['title'] = title
        if content is not None:
            update_data['content'] = content
        if is_top is not None:
            update_data['is_top'] = 1 if is_top else 0

        if not update_data:
            return error_response("没有需要更新的字段")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        success = self.db.update('t_notice', 'notice_id', notice_id, update_data)
        self.db.close_database()

        if not success:
            return error_response("更新失败，公告不存在")

        return success_response("公告更新成功", data={"notice_id": notice_id})

    def search_notices_by_title(self, keyword, page=1, page_size=20):
        """按标题搜索公告（支持分页）"""
        if not self.db.open_database():
            return error_response("数据库连接失败")

        result = self.db.get_paginated(
            't_notice',
            page=page,
            page_size=page_size,
            where_clause="title LIKE %s",
            params=(f'%{keyword}%',),
            order_by="is_top DESC, created_at DESC"
        )
        self.db.close_database()

        return self._paginated_result(result, page, page_size)

    def delete_notice(self, notice_id):
        """删除公告"""
        check_result = self.get_notice_by_id(notice_id)
        if not check_result["success"]:
            return error_response("公告不存在")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        success = self.db.delete('t_notice', 'notice_id', notice_id)
        self.db.close_database()

        if not success:
            return error_response("删除失败")

        return success_response("公告已删除", data={"notice_id": notice_id})
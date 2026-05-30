from backend.utils.db_manager import DatabaseManager
from backend.model.notice import Notice
import uuid
from datetime import datetime


class NoticeLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    # ========== 公告管理 ==========

    def create_notice(self, title, content, is_top=0):
        """
        创建新公告
        :param title: 公告标题
        :param content: 公告内容
        :param is_top: 是否置顶（0=普通，1=置顶）
        :return: 成功返回 True，失败返回 False
        """
        if not title or not title.strip():
            return False
        
        notice_id = uuid.uuid4().hex[:12]
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not self.db.open_database():
            return False
        data = {
            'notice_id': notice_id,
            'title': title,
            'content': content,
            'is_top': 1 if is_top else 0,
            'created_at': created_at
        }
        success = self.db.insert('t_notice', data)
        self.db.close_database()
        return success

    def get_all_notices(self, page=1, page_size=20, order_by='created_at DESC'):
        """
        获取所有公告列表（分页，置顶优先）
        :param page: 页码
        :param page_size: 每页数量
        :param order_by: 排序字段（白名单限制）
        :return: {"notices": [...], "total": N, "page": page, "page_size": page_size}
        """
        # 白名单防止 SQL 注入
        allowed_orders = {
            'created_at DESC': 'created_at DESC',
            'created_at ASC': 'created_at ASC',
            'title ASC': 'title ASC',
            'title DESC': 'title DESC'
        }
        safe_order = allowed_orders.get(order_by, 'created_at DESC')

        if not self.db.open_database():
            return {"notices": [], "total": 0, "page": page, "page_size": page_size}

        # 置顶优先，再按指定排序
        result = self.db.get_paginated(
            't_notice',
            page=page,
            page_size=page_size,
            order_by=f"is_top DESC, {safe_order}"
        )
        self.db.close_database()

        if not result:
            return {"notices": [], "total": 0, "page": page, "page_size": page_size}

        notices = [Notice(**row) for row in result.get("data", [])]
        return {
            "notices": notices,
            "total": result.get("total", 0),
            "page": page,
            "page_size": page_size
        }

    def get_latest_notice(self):
        """
        获取最新置顶公告，如果没有置顶则取最新普通公告
        :return: Notice 对象 或 None
        """
        if not self.db.open_database():
            return None
        
        # 先查置顶的
        sql = "SELECT * FROM t_notice WHERE is_top = 1 ORDER BY created_at DESC LIMIT 1"
        results = self.db.execute_raw_sql(sql)
        if not results:
            # 没有置顶，取最新的普通公告
            sql = "SELECT * FROM t_notice WHERE is_top = 0 ORDER BY created_at DESC LIMIT 1"
            results = self.db.execute_raw_sql(sql)
        
        self.db.close_database()
        return Notice(**results[0]) if results else None

    def get_notice_by_id(self, notice_id):
        """
        根据公告 ID 精确查询
        """
        if not self.db.open_database():
            return None
        data = self.db.get_by_id('t_notice', 'notice_id', notice_id)
        self.db.close_database()
        if data:
            return Notice(**data)
        return None

    def update_notice(self, notice_id, title=None, content=None, is_top=None):
        """
        更新公告信息
        :param notice_id: 公告ID
        :param title: 新标题（可选）
        :param content: 新内容（可选）
        :param is_top: 置顶状态（可选，0/1）
        :return: 成功返回 True，失败返回 False
        """
        update_data = {}
        if title is not None:
            if not title.strip():
                return False
            update_data['title'] = title
        if content is not None:
            update_data['content'] = content
        if is_top is not None:
            update_data['is_top'] = 1 if is_top else 0
        
        if not update_data:
            return False

        if not self.db.open_database():
            return False
        success = self.db.update('t_notice', 'notice_id', notice_id, update_data)
        self.db.close_database()
        return success

    def search_notices_by_title(self, keyword, page=1, page_size=20):
        """
        按标题模糊搜索公告
        """
        if not self.db.open_database():
            return {"notices": [], "total": 0, "page": page, "page_size": page_size}

        result = self.db.get_paginated(
            't_notice',
            page=page,
            page_size=page_size,
            where_clause="title LIKE %s",
            params=(f'%{keyword}%',),
            order_by="is_top DESC, created_at DESC"
        )
        self.db.close_database()

        if not result:
            return {"notices": [], "total": 0, "page": page, "page_size": page_size}

        notices = [Notice(**row) for row in result.get("data", [])]
        return {
            "notices": notices,
            "total": result.get("total", 0),
            "page": page,
            "page_size": page_size
        }

    def delete_notice(self, notice_id):
        """
        删除公告
        """
        if not self.get_notice_by_id(notice_id):
            return False
        if not self.db.open_database():
            return False
        success = self.db.delete('t_notice', 'notice_id', notice_id)
        self.db.close_database()
        return success
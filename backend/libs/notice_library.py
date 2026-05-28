from backend.utils.db_manager import DatabaseManager
from backend.model.notice import Notice
import uuid
from datetime import datetime

class NoticeLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    # ========== 公告管理 ==========

    def create_notice(self, title, content):
        """
        创建新公告
        :param title: 公告标题
        :param content: 公告内容
        :return: 成功返回 True，失败返回 False
        """
        notice_id = uuid.uuid4().hex[:12]
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not self.db.open_database():
            return False
        data = {
            'notice_id': notice_id,
            'title': title,
            'content': content,
            'created_at': created_at
        }
        success = self.db.insert('t_notice', data)
        self.db.close_database()
        return success

    def get_all_notices(self, order_by='created_at DESC'):
        """
        获取所有公告列表（按时间倒序排列）
        :param order_by: 排序字段，默认按创建时间降序
        :return: Notice 对象列表
        """
        if not self.db.open_database():
            return []
        sql = f"SELECT * FROM t_notice ORDER BY {order_by}"
        results = self.db.execute_raw_sql(sql)
        self.db.close_database()
        return [Notice(**row) for row in results] if results else []

    def get_latest_notice(self):
        """
        获取最新发布的公告（置顶公告）
        :return: Notice 对象 或 None
        """
        if not self.db.open_database():
            return None
        sql = "SELECT * FROM t_notice ORDER BY created_at DESC LIMIT 1"
        results = self.db.execute_raw_sql(sql)
        self.db.close_database()
        return Notice(**results[0]) if results else None

    def get_notice_by_id(self, notice_id):
        """
        根据公告 ID 精确查询
        :param notice_id: 公告 ID
        :return: Notice 对象 或 None
        """
        if not self.db.open_database():
            return None
        data = self.db.get_by_id('t_notice', 'notice_id', notice_id)
        self.db.close_database()
        if data:
            return Notice(**data)
        return None

    def delete_notice(self, notice_id):
        """
        删除公告（管理员后台使用）
        :param notice_id: 公告 ID
        :return: 成功返回 True，失败返回 False
        """
        if not self.db.open_database():
            return False
        success = self.db.delete('t_notice', 'notice_id', notice_id)
        self.db.close_database()
        return success
from backend.utils.db_manager import DatabaseManager

class NoticeLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def create_notice(self, notice_id, title, content):
        if not self.db.open_database():
            return False
        data = {'notice_id': notice_id, 'title': title, 'content': content}
        success = self.db.insert('t_notice', data)
        self.db.close_database()
        return success

    def get_all_notices(self):
        if not self.db.open_database():
            return None
        data = self.db.get_all('t_notice')
        self.db.close_database()
        return data
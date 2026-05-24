from backend.utils.db_manager import DatabaseManager

class PostLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def create_post(self, post_id, content):
        if not self.db.open_database():
            return False
        data = {'post_id': post_id, 'content': content}
        success = self.db.insert('t_post', data)
        self.db.close_database()
        return success

    def get_post(self, post_id):
        if not self.db.open_database():
            return None
        data = self.db.get_by_id('t_post', 'post_id', post_id)
        self.db.close_database()
        return data

    def update_like_count(self, post_id, change=1):
        if not self.db.open_database():
            return False
        post = self.db.get_by_id('t_post', 'post_id', post_id)
        if post:
            new_count = post['like_count'] + change
            self.db.update('t_post', 'post_id', post_id, {'like_count': new_count})
        self.db.close_database()
        return True
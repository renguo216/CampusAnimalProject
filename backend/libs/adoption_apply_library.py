from backend.utils.db_manager import DatabaseManager

class AdoptionApplyLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def create_application(self, apply_id, pet_id, user_id, content=""):
        if not self.db.open_database():
            return False
        data = {'apply_id': apply_id, 'pet_id': pet_id, 'user_id': user_id, 'content': content}
        success = self.db.insert('t_adoptionapply', data)
        self.db.close_database()
        return success

    def update_status(self, apply_id, status):
        if not self.db.open_database():
            return False
        success = self.db.update('t_adoptionapply', 'apply_id', apply_id, {'status': status})
        self.db.close_database()
        return success
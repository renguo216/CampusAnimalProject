from backend.utils.db_manager import DatabaseManager

class ReimbursementLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def create_reimbursement(self, reimb_id, amount):
        if not self.db.open_database():
            return False
        data = {'reimb_id': reimb_id, 'amount': amount}
        success = self.db.insert('t_reimbursement', data)
        self.db.close_database()
        return success

    def update_status(self, reimb_id, status):
        if not self.db.open_database():
            return False
        success = self.db.update('t_reimbursement', 'reimb_id', reimb_id, {'status': status})
        self.db.close_database()
        return success
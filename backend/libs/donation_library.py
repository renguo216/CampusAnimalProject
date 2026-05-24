from backend.utils.db_manager import DatabaseManager

class DonationLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def create_donation(self, donation_id, amount, target_pet_id=None):
        if not self.db.open_database():
            return False
        data = {'donation_id': donation_id, 'amount': amount, 'target_pet_id': target_pet_id}
        success = self.db.insert('t_donation', data)
        self.db.close_database()
        return success
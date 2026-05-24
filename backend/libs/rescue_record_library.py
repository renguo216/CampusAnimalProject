from backend.utils.db_manager import DatabaseManager

class RescueRecordLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def create_record(self, record_id, location, description):
        if not self.db.open_database():
            return False
        data = {'record_id': record_id, 'location': location, 'description': description}
        success = self.db.insert('t_rescuerecord', data)
        self.db.close_database()
        return success
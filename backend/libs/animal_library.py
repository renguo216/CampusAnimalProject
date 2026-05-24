from backend.utils.db_manager import DatabaseManager

class AnimalLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def add_animal(self, pet_id, name, breed, status=0):
        if not self.db.open_database():
            return False
        data = {'pet_id': pet_id, 'name': name, 'breed': breed, 'status': status}
        success = self.db.insert('t_animal', data)
        self.db.close_database()
        return success

    def get_animal(self, pet_id):
        if not self.db.open_database():
            return None
        data = self.db.get_by_id('t_animal', 'pet_id', pet_id)
        self.db.close_database()
        return data

    def update_animal_status(self, pet_id, new_status):
        if not self.db.open_database():
            return False
        data = {'status': new_status}
        success = self.db.update('t_animal', 'pet_id', pet_id, data)
        self.db.close_database()
        return success
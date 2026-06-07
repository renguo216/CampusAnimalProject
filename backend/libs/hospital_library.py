
# ===== backend/libs/hospital_library.py =====
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
from datetime import datetime


class HospitalLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all_hospitals(self, page=1, page_size=100):
        if not self.db.open_database():
            return error_response("数据库连接失败")
        try:
            result = self.db.get_paginated(
                table_name="t_hospital",
                page=page,
                page_size=page_size,
                order_by="distance ASC"
            )
            return success_response("成功", data={
                "hospitals": result["data"],
                "total": result["total"]
            })
        except Exception as e:
            return error_response(f"查询医院失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_hospital_by_id(self, hospital_id):
        if not self.db.open_database():
            return error_response("数据库连接失败")
        try:
            hospital = self.db.get_by_id("t_hospital", "hospital_id", hospital_id)
            if not hospital:
                return error_response("医院不存在")
            return success_response("成功", data=hospital)
        except Exception as e:
            return error_response(f"查询医院失败：{str(e)}")
        finally:
            self.db.close_database()

    def create_hospital(self, name, address, phone, services, distance):
        if not self.db.open_database():
            return error_response("数据库连接失败")
        try:
            now = datetime.now()
            data = {
                "name": name,
                "address": address,
                "phone": phone,
                "services": services,
                "distance": distance,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            hospital_id = self.db.insert_with_id("t_hospital", data)
            if not hospital_id:
                return error_response("创建医院失败")
            return success_response("创建成功", data={"hospital_id": hospital_id})
        except Exception as e:
            return error_response(f"创建医院失败：{str(e)}")
        finally:
            self.db.close_database()


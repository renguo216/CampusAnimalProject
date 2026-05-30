from datetime import datetime
from backend.utils.db_manager import DatabaseManager


class ExchangeProductLibrary:
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()

    def get_exchange_items(self, page=1, page_size=20):
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            result = self.db.get_paginated(
                't_exchange_product',
                page=page,
                page_size=page_size,
                where_clause="status = 1",
                params=None,
                order_by="created_at DESC"
            )
            self.db.close_database()
            if result is None:
                return {"success": False, "message": "查询失败", "data": None}
            return {
                "success": True,
                "message": "成功",
                "data": result
            }
        except Exception as e:
            return {"success": False, "message": f"查询商品列表失败：{str(e)}", "data": None}

    def get_exchange_item_by_id(self, product_id: int):
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            product = self.db.get_by_id('t_exchange_product', 'product_id', product_id)
            self.db.close_database()
            if not product:
                return {"success": False, "message": "商品不存在", "data": None}
            return {
                "success": True,
                "message": "成功",
                "data": product
            }
        except Exception as e:
            return {"success": False, "message": f"查询商品详情失败：{str(e)}", "data": None}

    def product_exists(self, product_id: int) -> dict:
        result = self.get_exchange_item_by_id(product_id)
        return {
            "success": result["success"],
            "message": result["message"],
            "data": {"exists": result["success"] and result["data"] is not None}
        }

    def create_exchange_product(self, data: dict) -> dict:
        required_fields = ['name', 'points_required']
        for field in required_fields:
            if field not in data:
                return {"success": False, "message": f"缺少必要字段：{field}", "data": None}
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            now = datetime.now()
            insert_data = {
                'name': data['name'],
                'description': data.get('description'),
                'points_required': data['points_required'],
                'image_url': data.get('image_url'),
                'stock': data.get('stock', 0),
                'status': data.get('status', 1),
                'created_at': now
            }
            success = self.db.insert('t_exchange_product', insert_data)
            product_id = self.db.get_last_insert_id()
            self.db.close_database()
            if success:
                return {"success": True, "message": "商品添加成功", "data": {"product_id": product_id, **insert_data}}
            else:
                return {"success": False, "message": "插入失败", "data": None}
        except Exception as e:
            return {"success": False, "message": f"新增商品失败：{str(e)}", "data": None}

    def update_exchange_product(self, product_id: int, data: dict) -> dict:
        allowed_fields = {'name', 'description', 'points_required', 'image_url', 'stock', 'status'}
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        if not update_data:
            return {"success": False, "message": "没有有效更新字段", "data": None}
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            success = self.db.update('t_exchange_product', 'product_id', product_id, update_data)
            self.db.close_database()
            if success:
                return {"success": True, "message": "商品信息更新成功", "data": {"product_id": product_id, **update_data}}
            else:
                return {"success": False, "message": "更新失败，商品不存在", "data": None}
        except Exception as e:
            return {"success": False, "message": f"更新商品失败：{str(e)}", "data": None}

    def update_product_stock(self, product_id: int, stock: int) -> dict:
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            success = self.db.update('t_exchange_product', 'product_id', product_id, {'stock': stock})
            self.db.close_database()
            if success:
                return {"success": True, "message": "库存更新成功", "data": {"product_id": product_id, "stock": stock}}
            else:
                return {"success": False, "message": "更新失败，商品不存在", "data": None}
        except Exception as e:
            return {"success": False, "message": f"更新库存失败：{str(e)}", "data": None}

    def toggle_product_status(self, product_id: int, status: int) -> dict:
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            success = self.db.update('t_exchange_product', 'product_id', product_id, {'status': status})
            self.db.close_database()
            if success:
                status_text = "上架" if status == 1 else "下架"
                return {"success": True, "message": f"商品已{status_text}", "data": {"product_id": product_id, "status": status}}
            else:
                return {"success": False, "message": "操作失败，商品不存在", "data": None}
        except Exception as e:
            return {"success": False, "message": f"修改状态失败：{str(e)}", "data": None}

    def delete_exchange_product(self, product_id: int) -> dict:
        """删除商品（物理删除）"""
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            success = self.db.delete('t_exchange_product', 'product_id', product_id)
            self.db.close_database()
            if success:
                return {"success": True, "message": "商品已删除", "data": {"product_id": product_id}}
            else:
                return {"success": False, "message": "删除失败，商品不存在", "data": None}
        except Exception as e:
            return {"success": False, "message": f"删除商品失败：{str(e)}", "data": None}

    def get_product_stock(self, product_id: int) -> dict:
        result = self.get_exchange_item_by_id(product_id)
        if not result["success"]:
            return result
        product = result["data"]
        return {
            "success": True,
            "message": "成功",
            "data": {"product_id": product_id, "stock": int(product['stock'])}
        }

    def _adjust_stock_in_tx(self, product_id: int, delta: int) -> bool:
        try:
            product = self.db.get_by_id('t_exchange_product', 'product_id', product_id)
            if not product:
                return False
            new_stock = int(product['stock']) + delta
            if new_stock < 0:
                return False
            return self.db.update_tx('t_exchange_product', 'product_id', product_id, {'stock': new_stock})
        except Exception:
            return False
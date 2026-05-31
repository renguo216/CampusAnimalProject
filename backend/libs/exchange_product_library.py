# ===== backend/libs/exchange_product_library.py =====
"""
积分商品业务逻辑层
提供积分商品的增删改查、库存管理、上下架等核心功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response


class ExchangeProductLibrary:
    """
    积分商品业务逻辑库
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()

    def get_exchange_items(self, page=1, page_size=20):
        """
        获取积分商品列表（分页）
        只返回已上架的商品 (status = 1)
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
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
                return error_response("查询失败")
            return success_response("成功", data=result)
        except Exception as e:
            return error_response(f"查询商品列表失败：{str(e)}")

    def get_exchange_item_by_id(self, product_id: int):
        """
        根据商品ID查询详情
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            product = self.db.get_by_id('t_exchange_product', 'product_id', product_id)
            self.db.close_database()
            if not product:
                return error_response("商品不存在")
            return success_response("成功", data=product)
        except Exception as e:
            return error_response(f"查询商品详情失败：{str(e)}")

    def product_exists(self, product_id: int) -> dict:
        """
        检查商品是否存在
        """
        result = self.get_exchange_item_by_id(product_id)
        return success_response(result["message"], data={"exists": result["success"] and result["data"] is not None})

    def create_exchange_product(self, data: dict) -> dict:
        """
        新增积分商品
        必须包含 name 和 points_required 字段
        """
        required_fields = ['name', 'points_required']
        for field in required_fields:
            if field not in data:
                return error_response(f"缺少必要字段：{field}")
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
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
                return success_response("商品添加成功", data={"product_id": product_id, **insert_data})
            else:
                return error_response("插入失败")
        except Exception as e:
            return error_response(f"新增商品失败：{str(e)}")

    def update_exchange_product(self, product_id: int, data: dict) -> dict:
        """
        更新商品信息（仅允许修改指定字段）
        """
        allowed_fields = {'name', 'description', 'points_required', 'image_url', 'stock', 'status'}
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        if not update_data:
            return error_response("没有有效更新字段")
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            success = self.db.update('t_exchange_product', 'product_id', product_id, update_data)
            self.db.close_database()
            if success:
                return success_response("商品信息更新成功", data={"product_id": product_id, **update_data})
            else:
                return error_response("更新失败，商品不存在")
        except Exception as e:
            return error_response(f"更新商品失败：{str(e)}")

    def update_product_stock(self, product_id: int, stock: int) -> dict:
        """
        直接设置商品库存
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            success = self.db.update('t_exchange_product', 'product_id', product_id, {'stock': stock})
            self.db.close_database()
            if success:
                return success_response("库存更新成功", data={"product_id": product_id, "stock": stock})
            else:
                return error_response("更新失败，商品不存在")
        except Exception as e:
            return error_response(f"更新库存失败：{str(e)}")

    def toggle_product_status(self, product_id: int, status: int) -> dict:
        """
        切换商品上下架状态
        status: 1-上架，0-下架
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            success = self.db.update('t_exchange_product', 'product_id', product_id, {'status': status})
            self.db.close_database()
            if success:
                status_text = "上架" if status == 1 else "下架"
                return success_response(f"商品已{status_text}", data={"product_id": product_id, "status": status})
            else:
                return error_response("操作失败，商品不存在")
        except Exception as e:
            return error_response(f"修改状态失败：{str(e)}")

    def delete_exchange_product(self, product_id: int) -> dict:
        """
        删除商品（物理删除）
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            success = self.db.delete('t_exchange_product', 'product_id', product_id)
            self.db.close_database()
            if success:
                return success_response("商品已删除", data={"product_id": product_id})
            else:
                return error_response("删除失败，商品不存在")
        except Exception as e:
            return error_response(f"删除商品失败：{str(e)}")

    def get_product_stock(self, product_id: int) -> dict:
        """
        查询商品库存
        """
        result = self.get_exchange_item_by_id(product_id)
        if not result["success"]:
            return result
        product = result["data"]
        return success_response("成功", data={"product_id": product_id, "stock": int(product["stock"])})

    def _adjust_stock_in_tx(self, product_id: int, delta: int) -> bool:
        """
        事务内调整库存（内部方法）
        """
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
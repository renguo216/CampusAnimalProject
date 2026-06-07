# ===== backend/libs/exchange_library.py =====
"""
积分兑换业务逻辑层
负责兑换申请、审核发货、积分与库存操作（事务内）
商品管理相关的功能已委托至 exchange_product_library
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
from backend.libs.exchange_product_library import ExchangeProductLibrary

class ExchangeLibrary:
    def __init__(self):
        self.db = DatabaseManager()
        self.product_lib = ExchangeProductLibrary(db_manager=self.db)

    # ... 其余方法完全不变 ...

    # ==================== 用户操作 ====================

    def check_user_points(self, user_id: str) -> dict:
        """
        检查用户积分余额
        返回当前积分
        """
        try:
            print(f"检查用户积分, user_id: {user_id}")
            if not self.db.open_database():
<<<<<<< HEAD
                print("数据库连接失败")
=======
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706
                return error_response("数据库连接失败")
            user = self.db.get_by_id('t_user', 'user_id', user_id)
            self.db.close_database()
            print(f"查询到用户: {user}")
            if not user:
<<<<<<< HEAD
                print("用户不存在")
                return error_response("用户不存在")
            points = float(user["points"]) if user["points"] is not None else 0
            print(f"用户积分: {points}")
            return success_response("成功", data={"points": points})
        except Exception as e:
            print(f"查询积分异常: {e}")
            import traceback
            traceback.print_exc()
=======
                return error_response("用户不存在")
            return success_response("成功", data={"points": float(user["points"]) if user["points"] is not None else 0})
        except Exception as e:
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706
            return error_response(f"查询积分失败：{str(e)}")

    def submit_exchange(self, user_id: str, product_id: int) -> dict:
        """
        提交兑换申请
        流程：校验积分与库存 → 开启事务 → 扣积分 → 减库存 → 插入记录 → 提交
        事务失败自动回滚
        """
        try:
            print(f"开始提交兑换: user_id={user_id}, product_id={product_id}")
            # 1. 获取商品信息（委托给商品模块）
            product = self.product_lib.get_exchange_item_by_id(product_id)
            print(f"商品查询结果: {product}")
            if not product["success"]:
                return product
            product_data = product["data"]

            # 2. 检查库存
<<<<<<< HEAD
            stock = int(product_data['stock'])
            print(f"商品库存: {stock}")
            if stock <= 0:
                print("库存不足")
=======
            if int(product_data['stock']) <= 0:
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706
                return error_response("库存不足")

            # 3. 检查用户积分
            points_result = self.check_user_points(user_id)
            if not points_result["success"]:
                return points_result
            user_points = points_result["data"]["points"]
            points_required = float(product_data['points_required'])
            print(f"用户积分: {user_points}, 所需积分: {points_required}")
            if user_points < points_required:
<<<<<<< HEAD
                print("积分不足")
=======
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706
                return error_response("积分不足")

            # 4. 开启事务
            print("开始开启事务...")
            if not self.db.open_database():
<<<<<<< HEAD
                print("数据库连接失败")
=======
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706
                return error_response("数据库连接失败")
            if not self.db.begin_transaction():
                self.db.close_database()
                return error_response("事务开启失败")

            try:
                print("开始执行扣积分...")
                # 扣积分
                new_points = user_points - points_required
                print(f"新积分: {new_points}")
                self.db.update_tx('t_user', 'user_id', user_id, {'points': new_points})
                print("扣积分成功")

                # 减库存（委托给商品模块的事务内方法）
                print("开始扣库存...")
                if not self.product_lib._adjust_stock_in_tx(product_id, -1):
                    raise Exception("库存扣减失败")
                print("扣库存成功")

                # 插入兑换记录
                print("开始插入兑换记录...")
                now = datetime.now()
                exchange_data = {
                    'user_id': user_id,
                    'product_id': product_id,
                    'points_used': points_required,
                    'status': 0,
                    'created_at': now,
                    'updated_at': now
                }
                print(f"兑换数据: {exchange_data}")
                if not self.db.insert_tx('t_exchange', exchange_data):
                    raise Exception("插入兑换记录失败")
                print("插入兑换记录成功")

                # 获取自增ID
                exchange_id = self.db.get_last_insert_id()
                print(f"兑换ID: {exchange_id}")
                if not exchange_id:
                    raise Exception("获取兑换ID失败")

                print("提交事务...")
                self.db.commit()
<<<<<<< HEAD
                print("事务提交成功")
=======
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706
                return success_response(
                    "兑换申请提交成功",
                    data={
                        "exchange_id": exchange_id,
                        "points_used": points_required,
                        "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                    }
                )
            except Exception as e:
                print(f"兑换失败，回滚事务: {e}")
                import traceback
                traceback.print_exc()
                self.db.rollback()
                return error_response(f"兑换失败：{str(e)}")
            finally:
                self.db.close_database()
        except Exception as e:
            return error_response(f"兑换处理异常：{str(e)}")

    def cancel_exchange(self, exchange_id: int, user_id: str = None) -> dict:
        """
        用户取消兑换（状态设为2，返还积分，增加库存）
        仅允许本人取消，或管理员取消（user_id 可为空）
        """
        return self._update_exchange_status(exchange_id, 2, user_id)

    def _update_exchange_status(self, exchange_id: int, new_status: int, user_id: str = None, review_comment: str = None) -> dict:
        """
        内部方法：更新兑换状态，并执行积分/库存回调（适用于取消/拒绝/完成）
        new_status: 1=完成，2=取消/拒绝
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            exchange = self.db.get_by_id('t_exchange', 'exchange_id', exchange_id)
            if not exchange:
                self.db.close_database()
                return error_response("兑换记录不存在")

            # 检查当前状态（只有待发货 status=0 可以操作）
            if exchange['status'] != 0:
                self.db.close_database()
                return error_response("当前状态不允许此操作")

            if new_status == 2:
                # 取消/拒绝：需要检查权限（如果是用户取消，需验证 user_id）
                if user_id and exchange['user_id'] != user_id:
                    self.db.close_database()
                    return error_response("无权取消他人兑换")

            # 开启事务
            if not self.db.begin_transaction():
                self.db.close_database()
                return error_response("事务开启失败")

            try:
                now = datetime.now()
                update_data = {
                    'status': new_status,
                    'updated_at': now
                }

                # 如果是取消/拒绝(status=2)，需要返还积分和恢复库存
                if new_status == 2:
                    points_used = float(exchange['points_used'])
                    user = self.db.get_by_id('t_user', 'user_id', exchange['user_id'])
                    if user:
                        new_points = float(user['points']) + points_used
                        self.db.update_tx('t_user', 'user_id', exchange['user_id'], {'points': new_points})

                    product_id = exchange['product_id']
                    # 恢复库存（委托给商品模块的事务内方法）
                    if not self.product_lib._adjust_stock_in_tx(product_id, 1):
                        raise Exception("库存恢复失败")

                    # 如果有审核意见，一并写入
                    if review_comment:
                        update_data['review_comment'] = review_comment
                        update_data['reviewed_at'] = now

                # 更新兑换记录状态
                self.db.update_tx('t_exchange', 'exchange_id', exchange_id, update_data)
                self.db.commit()
                return success_response("操作成功", data={"exchange_id": exchange_id, "status": new_status})
            except Exception as e:
                self.db.rollback()
                return error_response(f"操作失败：{str(e)}")
            finally:
                self.db.close_database()
        except Exception as e:
            return error_response(f"操作异常：{str(e)}")

    def complete_exchange(self, exchange_id: int):
        """
        管理员完成发货（状态设为1）
        """
        return self._update_exchange_status(exchange_id, 1)

    def reject_exchange(self, exchange_id: int, review_comment: str = None):
        """
        管理员拒绝兑换（状态设为2，返还积分，恢复库存）
        可选填写审核意见
        """
        return self._update_exchange_status(exchange_id, 2, None, review_comment)

    # ==================== 记录查询 ====================

    def get_user_exchanges(self, user_id: str, page=1, page_size=20) -> dict:
        """
        查询指定用户的兑换记录（联表显示商品名称）
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            offset = (page - 1) * page_size
            sql = """
                SELECT e.*, p.name AS product_name, p.image_url AS product_image
                FROM t_exchange e
                JOIN t_exchange_product p ON e.product_id = p.product_id
                WHERE e.user_id = %s
                ORDER BY e.created_at DESC
                LIMIT %s OFFSET %s
            """
            records = self.db.execute_raw_sql(sql, (user_id, page_size, offset))
            count_sql = "SELECT COUNT(*) AS total FROM t_exchange WHERE user_id = %s"
            count_result = self.db.execute_raw_sql(count_sql, (user_id,))
            total = count_result[0]['total'] if count_result else 0
            self.db.close_database()
<<<<<<< HEAD
            
            # 转换数据格式匹配前端
            status_map = {0: 'pending', 1: 'completed', 2: 'cancelled'}
            status_text_map = {0: '待发货', 1: '已完成', 2: '已取消'}
            
            formatted_records = []
            for r in records or []:
                created_at = r.get('created_at')
                if hasattr(created_at, 'strftime'):
                    exchange_time = created_at.strftime("%Y-%m-%d %H:%M")
                else:
                    exchange_time = str(created_at)[:16]
                
                formatted_records.append({
                    'id': r.get('exchange_id'),
                    'productName': r.get('product_name', ''),
                    'exchangeTime': exchange_time,
                    'points': int(r.get('points_used', 0)),
                    'status': status_map.get(r.get('status', 0), 'pending'),
                    'statusText': status_text_map.get(r.get('status', 0), '待发货')
                })
            
            return success_response("成功", data=formatted_records)
=======
            return success_response(
                "成功",
                data={
                    "records": records if records else [],
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            )
>>>>>>> e75cee203baac6a3459ff90901bf40335feb4706
        except Exception as e:
            return error_response(f"查询兑换记录失败：{str(e)}")

    def get_all_exchanges(self, page=1, page_size=20) -> dict:
        """
        管理员查询所有兑换记录（联表显示商品名称和用户昵称）
        """
        try:
            if not self.db.open_database():
                return error_response("数据库连接失败")
            offset = (page - 1) * page_size
            sql = """
                SELECT e.*, u.nickname AS user_nickname, p.name AS product_name, p.image_url AS product_image
                FROM t_exchange e
                JOIN t_user u ON e.user_id = u.user_id
                JOIN t_exchange_product p ON e.product_id = p.product_id
                ORDER BY e.created_at DESC
                LIMIT %s OFFSET %s
            """
            records = self.db.execute_raw_sql(sql, (page_size, offset))
            count_sql = "SELECT COUNT(*) AS total FROM t_exchange"
            count_result = self.db.execute_raw_sql(count_sql)
            total = count_result[0]['total'] if count_result else 0
            self.db.close_database()
            return success_response(
                "成功",
                data={
                    "records": records if records else [],
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            )
        except Exception as e:
            return error_response(f"查询所有兑换记录失败：{str(e)}")

    
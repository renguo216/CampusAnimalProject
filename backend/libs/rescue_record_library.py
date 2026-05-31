# ===== backend/libs/rescue_record_library.py =====
"""
救助记录业务逻辑层
提供救助记录的创建、修改、删除、查询、状态管理等功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
from backend.libs.animal_library import AnimalLibrary
import uuid
import json
import requests
from backend.utils.ai_http_client import detect_species, extract_features


class RescueRecordLibrary:
    """
    救助记录业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        """初始化：创建数据库管理器实例"""
        self.db = DatabaseManager()

    # ==================== 创建与删除 ====================

    def create_rescue_record(self, user_id: str, title: str = None,
                             description: str = None, location: str = None,
                             found_location_text: str = None,
                             need_type: str = None,
                             photo_urls: str = None,
                             location_lat: float = None,
                             location_lng: float = None,
                             animal_name: str = None,
                             pet_id: int = None,
                             priority: int = 0) -> dict:
        """
        创建救助记录（普通用户上报）
        - 验证用户存在且激活
        - 生成 record_id，插入 t_rescuerecord 记录（status=0 待接单）
        - 仅普通用户（role=1）或志愿者（role=2）可上报

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 1. 验证用户存在且激活
            user = self.db.get_by_id("t_user", "user_id", user_id)
            if not user:
                return error_response("用户不存在")
            if user.get("is_active") == 0:
                return error_response("用户已被封禁，无法创建救助记录")

            # 2. 生成记录编号
            record_id = str(uuid.uuid4()).replace("-", "")[:32]
            now = datetime.now()

            # 2.5. AI自动识别动物种类填充 animal_name（若未提供且有图片）
            if not animal_name and photo_urls:
                try:
                    photo_list = json.loads(photo_urls)
                    if isinstance(photo_list, list) and len(photo_list) > 0:
                        first_photo_url = photo_list[0]
                        resp = requests.get(first_photo_url, timeout=5)
                        if resp.status_code == 200:
                            species_result = detect_species(resp.content)
                            if species_result.get('success'):
                                animal_name = species_result.get('breed_name') or species_result.get('category_name')
                except Exception as e:
                    print(f"AI识别动物种类失败（不影响创建）：{e}")
                    # 不抛出异常，继续创建

            # 3. 插入救助记录
            data = {
                "record_id": record_id,
                "user_id": user_id,
                "title": title,
                "description": description,
                "location": location,
                "found_location_text": found_location_text,
                "need_type": need_type,
                "photo_urls": photo_urls,
                "location_lat": location_lat,
                "location_lng": location_lng,
                "animal_name": animal_name,
                "pet_id": pet_id,
                "priority": priority,
                "status": 0,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.insert("t_rescuerecord", data):
                return error_response("创建救助记录失败")

            return success_response(
                "救助记录创建成功，等待志愿者接单",
                data={
                    "record_id": record_id,
                    "status": 0,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            return error_response(f"创建救助记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def update_rescue_record(self, record_id: str, user_id: str,
                             title: str = None, description: str = None,
                             location: str = None,
                             found_location_text: str = None,
                             need_type: str = None,
                             photo_urls: str = None,
                             location_lat: float = None,
                             location_lng: float = None,
                             animal_name: str = None,
                             priority: int = None) -> dict:
        """
        修改救助记录内容（仅允许上报人或接单志愿者在终态前修改）
        - 终态：已完成（status=3）或已关闭（status=4）

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            record = self.db.get_by_id("t_rescuerecord", "record_id", record_id)
            if not record:
                return error_response("救助记录不存在")

            # 验证权限：上报人或接单志愿者
            if record.get("user_id") != user_id and record.get("helper_id") != user_id:
                user = self.db.get_by_id("t_user", "user_id", user_id)
                if not user or user.get("role") != 3:
                    return error_response("无权修改此救助记录")

            # 验证状态：非终态
            if record.get("status") in (3, 4):
                return error_response("已完成或已关闭的救助记录无法修改")

            # 构造更新字段
            update_data = {"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if location is not None:
                update_data["location"] = location
            if found_location_text is not None:
                update_data["found_location_text"] = found_location_text
            if need_type is not None:
                update_data["need_type"] = need_type
            if photo_urls is not None:
                update_data["photo_urls"] = photo_urls
            if location_lat is not None:
                update_data["location_lat"] = location_lat
            if location_lng is not None:
                update_data["location_lng"] = location_lng
            if animal_name is not None:
                update_data["animal_name"] = animal_name
            if priority is not None:
                update_data["priority"] = priority

            if not self.db.update("t_rescuerecord", "record_id", record_id, update_data):
                return error_response("修改救助记录失败")

            return success_response(
                "救助记录已修改",
                data={"record_id": record_id, "updated_at": update_data["updated_at"]}
            )
        except Exception as e:
            return error_response(f"修改救助记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def delete_rescue_record(self, record_id: str, user_id: str) -> dict:
        """
        软删除救助记录（仅允许上报人或管理员）
        将 is_deleted 设为 1

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            record = self.db.get_by_id("t_rescuerecord", "record_id", record_id)
            if not record:
                return error_response("救助记录不存在")

            # 验证权限：上报人或管理员
            if record.get("user_id") != user_id:
                user = self.db.get_by_id("t_user", "user_id", user_id)
                if not user or user.get("role") != 3:
                    return error_response("无权删除此救助记录")

            now = datetime.now()
            update_data = {
                "is_deleted": 1,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_rescuerecord", "record_id", record_id, update_data):
                return error_response("删除救助记录失败")

            return success_response(
                "救助记录已删除",
                data={"record_id": record_id, "deleted_at": now.strftime("%Y-%m-%d %H:%M:%S")}
            )
        except Exception as e:
            return error_response(f"删除救助记录失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 查询操作 ====================

    def get_rescue_record_by_id(self, record_id: str) -> dict:
        """
        根据记录编号查询救助记录详情（含上报人、志愿者、动物信息）
        - 默认不包含已软删除的记录

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            record = self.db.get_by_id("t_rescuerecord", "record_id", record_id)
            if not record or record.get("is_deleted") == 1:
                return error_response("救助记录不存在")

            # 关联查询上报人、志愿者、动物信息
            user = self.db.get_by_id("t_user", "user_id", record.get("user_id"))
            helper = self.db.get_by_id("t_user", "user_id", record.get("helper_id")) if record.get("helper_id") else None
            animal = self.db.get_by_id("t_animal", "pet_id", record.get("pet_id")) if record.get("pet_id") else None
            resolver = self.db.get_by_id("t_user", "user_id", record.get("resolved_by")) if record.get("resolved_by") else None

            data = {
                "record_id": record.get("record_id"),
                "user_id": record.get("user_id"),
                "user_nickname": user.get("nickname") if user else None,
                "user_avatar": user.get("avatarURL") if user else None,
                "helper_id": record.get("helper_id"),
                "helper_nickname": helper.get("nickname") if helper else None,
                "helper_avatar": helper.get("avatarURL") if helper else None,
                "pet_id": record.get("pet_id"),
                "pet_name": animal.get("name") if animal else None,
                "title": record.get("title"),
                "location": record.get("location"),
                "found_location_text": record.get("found_location_text"),
                "description": record.get("description"),
                "need_type": record.get("need_type"),
                "photo_urls": record.get("photo_urls"),
                "priority": record.get("priority"),
                "animal_name": record.get("animal_name"),
                "location_lat": float(record.get("location_lat")) if record.get("location_lat") is not None else None,
                "location_lng": float(record.get("location_lng")) if record.get("location_lng") is not None else None,
                "status": record.get("status"),
                "resolved_by": record.get("resolved_by"),
                "resolver_nickname": resolver.get("nickname") if resolver else None,
                "created_at": record.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if record.get("created_at") else None,
                "updated_at": record.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if record.get("updated_at") else None,
                "completed_at": record.get("completed_at").strftime("%Y-%m-%d %H:%M:%S") if record.get("completed_at") else None
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询救助记录详情失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_user_rescues(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        分页查询指定用户上报的救助记录（按时间倒序，不含软删除）

        :return: dict {"success": bool, "message": str, "data": {"records": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_rescuerecord",
                page=page,
                page_size=page_size,
                where_clause="user_id = %s AND is_deleted = 0",
                params=(user_id,),
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"records": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            items = self._format_records_list(result["data"])
            data = {
                "records": items,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询用户救助记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_helper_rescues(self, helper_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        分页查询指定志愿者接单的救助记录（按时间倒序，不含软删除）

        :return: dict {"success": bool, "message": str, "data": {"records": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_rescuerecord",
                page=page,
                page_size=page_size,
                where_clause="helper_id = %s AND is_deleted = 0",
                params=(helper_id,),
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"records": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            items = self._format_records_list(result["data"])
            data = {
                "records": items,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询志愿者救助记录失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_animal_rescue_history(self, pet_id: int, page: int = 1, page_size: int = 20) -> dict:
        """
        分页查询指定动物的所有救助历史（按时间倒序，不含软删除）

        :return: dict {"success": bool, "message": str, "data": {"records": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            result = self.db.get_paginated(
                table_name="t_rescuerecord",
                page=page,
                page_size=page_size,
                where_clause="pet_id = %s AND is_deleted = 0",
                params=(pet_id,),
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"records": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            items = self._format_records_list(result["data"])
            data = {
                "records": items,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询动物救助历史失败：{str(e)}")
        finally:
            self.db.close_database()

    def get_all_rescues(self, page: int = 1, page_size: int = 20,
                        status_filter: int = None) -> dict:
        """
        管理员查看所有救助记录（分页，按时间倒序，不含软删除）
        可指定状态筛选

        :return: dict {"success": bool, "message": str, "data": {"records": list, "total": int, "page": int, "page_size": int}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            where_clause = "is_deleted = 0"
            params = []
            if status_filter is not None:
                where_clause += " AND status = %s"
                params.append(status_filter)

            result = self.db.get_paginated(
                table_name="t_rescuerecord",
                page=page,
                page_size=page_size,
                where_clause=where_clause,
                params=tuple(params) if params else None,
                order_by="created_at DESC"
            )

            if not result or not result.get("data"):
                data = {"records": [], "total": 0, "page": page, "page_size": page_size}
                return success_response("成功", data=data)

            items = self._format_records_list(result["data"])
            data = {
                "records": items,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"查询所有救助记录失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 状态管理 ====================

    def _validate_status_transition(self, current_status: int, new_status: int) -> bool:
        """
        内部方法：校验状态转移是否合法
        状态转移规则：
        0-待接单 → 1-救助中（志愿者接单） / 4-已关闭
        1-救助中 → 2-待确认（标记完成） / 4-已关闭
        2-待确认 → 3-已完成（确认完成） / 1-救助中（退回继续救助） / 4-已关闭
        3-已完成 → （终态，不可再变化）
        4-已关闭 → （终态，不可再变化）
        """
        transitions = {
            0: {1, 4},
            1: {2, 4},
            2: {1, 3, 4},
            3: set(),
            4: set()
        }
        return new_status in transitions.get(current_status, set())

    def update_rescue_status(self, record_id: str, operator_id: str, new_status: int,
                             helper_id: str = None) -> dict:
        """
        更新救助状态（通用方法，含状态转移合法性校验）

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            record = self.db.get_by_id("t_rescuerecord", "record_id", record_id)
            if not record or record.get("is_deleted") == 1:
                return error_response("救助记录不存在")

            current_status = record.get("status")

            # 校验状态转移合法性
            if not self._validate_status_transition(current_status, new_status):
                status_map = {0: "待接单", 1: "救助中", 2: "待确认", 3: "已完成", 4: "已关闭"}
                return error_response(
                    f"不允许从「{status_map.get(current_status, '未知')}」变更为「{status_map.get(new_status, '未知')}」"
                )

            # 校验权限
            user = self.db.get_by_id("t_user", "user_id", operator_id)
            if not user:
                return error_response("操作者不存在")

            is_reporter = (record.get("user_id") == operator_id)
            is_helper = (record.get("helper_id") == operator_id)
            is_admin = (user.get("role") == 3)
            is_volunteer = (user.get("role") == 2)

            # 接单：必须是志愿者或管理员
            if current_status == 0 and new_status == 1:
                if not (is_volunteer or is_admin):
                    return error_response("仅志愿者或管理员可以接单")

            # 标记完成：必须是上报人或接单志愿者
            elif current_status == 1 and new_status == 2:
                if not (is_reporter or is_helper):
                    return error_response("仅上报人或接单志愿者可以标记完成")

            # 确认完成：必须是管理员
            elif current_status == 2 and new_status == 3:
                if not is_admin:
                    return error_response("仅管理员可以确认完成")

            # 关闭：必须是上报人或管理员
            elif new_status == 4:
                if not (is_reporter or is_admin):
                    return error_response("仅上报人或管理员可以关闭救助记录")

            # 退回继续救助（2→1）：必须是管理员
            elif current_status == 2 and new_status == 1:
                if not is_admin:
                    return error_response("仅管理员可以退回救助记录")

            # 构造更新数据
            now = datetime.now()
            update_data = {
                "status": new_status,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }

            # 接单时设置 helper_id
            if current_status == 0 and new_status == 1 and helper_id:
                update_data["helper_id"] = helper_id

            # 进入终态时设置 resolved_by 和 completed_at
            if new_status in (3, 4):
                update_data["resolved_by"] = operator_id
                update_data["completed_at"] = now.strftime("%Y-%m-%d %H:%M:%S")

            if not self.db.update("t_rescuerecord", "record_id", record_id, update_data):
                return error_response("更新状态失败")

            return success_response(
                "状态更新成功",
                data={
                    "record_id": record_id,
                    "status": new_status,
                    "updated_at": update_data["updated_at"]
                }
            )
        except Exception as e:
            return error_response(f"更新状态失败：{str(e)}")
        finally:
            self.db.close_database()

    def claim_rescue(self, record_id: str, helper_id: str) -> dict:
        """
        志愿者接单
        将 status 从 0（待接单）变为 1（救助中）
        并设置 helper_id

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        return self.update_rescue_status(record_id, helper_id, 1, helper_id=helper_id)

    def complete_rescue(self, record_id: str, operator_id: str) -> dict:
        """
        标记救助完成（待确认）
        将 status 从 1（救助中）变为 2（待确认）

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        return self.update_rescue_status(record_id, operator_id, 2)

    def confirm_rescue(self, record_id: str, admin_id: str) -> dict:
        """
        管理员确认救助完成
        将 status 从 2（待确认）变为 3（已完成）

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        return self.update_rescue_status(record_id, admin_id, 3)

    def close_rescue(self, record_id: str, operator_id: str) -> dict:
        """
        关闭救助记录
        将 status 变为 4（已关闭），可从 0/1/2 状态关闭

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        return self.update_rescue_status(record_id, operator_id, 4)

    def link_animal(self, record_id: str, pet_id: int, operator_id: str) -> dict:
        """
        关联动物档案到救助记录（救助完成后建立关联）
        使用统一后的 AnimalLibrary API

        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            record = self.db.get_by_id("t_rescuerecord", "record_id", record_id)
            if not record or record.get("is_deleted") == 1:
                return error_response("救助记录不存在")

            # 验证动物存在（使用统一后的 API）
            animal_lib = AnimalLibrary()
            animal_result = animal_lib.get_animal_by_id(pet_id)
            if not animal_result["success"]:
                return error_response("动物档案不存在")

            now = datetime.now()
            update_data = {
                "pet_id": pet_id,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            if not self.db.update("t_rescuerecord", "record_id", record_id, update_data):
                return error_response("关联动物失败")

            # 关联成功后，从救助记录图片中提取特征向量并更新动物档案
            try:
                photo_urls_str = record.get("photo_urls")
                if photo_urls_str:
                    photo_list = json.loads(photo_urls_str)
                    if isinstance(photo_list, list) and len(photo_list) > 0:
                        first_photo_url = photo_list[0]
                        resp = requests.get(first_photo_url, timeout=5)
                        if resp.status_code == 200:
                            features_result = extract_features(resp.content)
                            if features_result.get('success'):
                                vector_json = json.dumps(features_result.get('features'))
                                vector_result = animal_lib.update_animal_vector(pet_id, vector_json)
                                if not vector_result["success"]:
                                    print(f"提取特征向量更新动物档案失败：{vector_result['message']}")
            except Exception as e:
                print(f"提取特征向量更新动物档案失败（不影响关联）：{e}")

            return success_response(
                "已关联动物档案",
                data={"record_id": record_id, "pet_id": pet_id, "updated_at": update_data["updated_at"]}
            )
        except Exception as e:
            return error_response(f"关联动物失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 统计查询 ====================

    def get_rescue_status_count(self) -> dict:
        """
        获取各状态救助记录统计（用于管理看板，不含软删除）

        :return: dict {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            sql = """SELECT status, COUNT(*) AS count
                     FROM t_rescuerecord
                     WHERE is_deleted = 0
                     GROUP BY status"""
            results = self.db.execute_raw_sql(sql)
            count_by_status = {}
            if results:
                for row in results:
                    count_by_status[str(row["status"])] = row["count"]

            # 补全所有状态（若某状态无记录则为0）
            for s in [0, 1, 2, 3, 4]:
                if str(s) not in count_by_status:
                    count_by_status[str(s)] = 0

            total = sum(count_by_status.values())
            data = {
                "total": total,
                "pending": count_by_status["0"],       # 待接单
                "in_progress": count_by_status["1"],   # 救助中
                "to_confirm": count_by_status["2"],    # 待确认
                "completed": count_by_status["3"],     # 已完成
                "closed": count_by_status["4"]         # 已关闭
            }
            return success_response("成功", data=data)
        except Exception as e:
            return error_response(f"统计查询失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 内部辅助方法 ====================

    def _format_records_list(self, rows: list) -> list:
        """
        格式化救助记录列表（统一时间字段、关联用户信息）
        """
        if not rows:
            return []
        formatted = []
        for row in rows:
            user = self.db.get_by_id("t_user", "user_id", row.get("user_id"))
            helper = self.db.get_by_id("t_user", "user_id", row.get("helper_id")) if row.get("helper_id") else None
            animal = self.db.get_by_id("t_animal", "pet_id", row.get("pet_id")) if row.get("pet_id") else None
            resolver = self.db.get_by_id("t_user", "user_id", row.get("resolved_by")) if row.get("resolved_by") else None

            formatted.append({
                "record_id": row.get("record_id"),
                "user_id": row.get("user_id"),
                "user_nickname": user.get("nickname") if user else None,
                "user_avatar": user.get("avatarURL") if user else None,
                "helper_id": row.get("helper_id"),
                "helper_nickname": helper.get("nickname") if helper else None,
                "helper_avatar": helper.get("avatarURL") if helper else None,
                "pet_id": row.get("pet_id"),
                "pet_name": animal.get("name") if animal else None,
                "title": row.get("title"),
                "location": row.get("location"),
                "found_location_text": row.get("found_location_text"),
                "description": row.get("description"),
                "need_type": row.get("need_type"),
                "photo_urls": row.get("photo_urls"),
                "priority": row.get("priority"),
                "animal_name": row.get("animal_name"),
                "status": row.get("status"),
                "resolved_by": row.get("resolved_by"),
                "resolver_nickname": resolver.get("nickname") if resolver else None,
                "created_at": row.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("created_at") else None,
                "updated_at": row.get("updated_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("updated_at") else None,
                "completed_at": row.get("completed_at").strftime("%Y-%m-%d %H:%M:%S") if row.get("completed_at") else None
            })
        return formatted
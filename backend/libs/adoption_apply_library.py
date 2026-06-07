"""
领养申请业务逻辑层

依赖：utils/db_manager.py 中的 DatabaseManager
      libs/user_library.py 中的 UserLibrary
      libs/animal_library.py 中的 AnimalLibrary

"""
from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
from backend.libs.user_library import UserLibrary
from backend.libs.animal_library import AnimalLibrary
import uuid


class AdoptionApplyLibrary:
    """
    领养申请业务逻辑库（组合模式）
    持有 DatabaseManager、UserLibrary、AnimalLibrary 实例
    """

    def __init__(self):
        """初始化：创建数据库管理器、用户库、动物库实例"""
        self.db = DatabaseManager()
        self.user_lib = UserLibrary()
        self.animal_lib = AnimalLibrary()

    # ==================== 核心功能 ====================

    def submit_adoption_application(self, user_id, pet_id, content=""):
        """
        提交领养申请
        :param user_id: 申请人ID
        :param pet_id: 动物ID
        :param content: 申请理由（非必填）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        # 1. 检查用户是否存在（使用统一后的 API）
        user_result = self.user_lib.get_user_by_account(user_id)
        if not user_result["success"]:
            return error_response("错误：用户不存在")

        # 2. 检查动物是否存在（使用统一后的 API）
        animal_result = self.animal_lib.get_animal_by_id(pet_id)
        if not animal_result["success"]:
            return error_response("错误：动物不存在")

        animal = animal_result["data"]

        # 3. 检查动物是否允许领养（status=1 表示已领养）
        if animal["status"] == 1:
            return error_response("错误：该动物已被领养")

        # 4. 检查重复申请
        duplicate_result = self._check_duplicate_application(user_id, pet_id)
        if not duplicate_result["success"]:
            return duplicate_result
        if duplicate_result["data"]["is_duplicate"]:
            return error_response(
                "错误：您已提交过对该动物的领养申请，请勿重复提交",
                data={"apply_id": duplicate_result["data"]["apply_id"]}
            )

        # 5. 生成 apply_id 并写入数据库
        apply_id = str(uuid.uuid4()).replace("-", "")[:32]
        now = datetime.now()

        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = """INSERT INTO t_adoptionapply (apply_id, pet_id, user_id, status, content, created_at)
                VALUES (%s, %s, %s, 0, %s, %s)"""
        result = self.db.execute_raw_sql(sql, (apply_id, pet_id, user_id, content, now))
        self.db.close_database()

        if result is None:
            return error_response("错误：数据库插入失败")

        return success_response(
            "领养申请提交成功",
            data={"apply_id": apply_id}
        )

    def cancel_adoption_application(self, apply_id, user_id):
        """
        取消领养申请（仅申请人可取消待审核的申请）
        :param apply_id: 申请编号
        :param user_id: 当前操作用户ID
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        # 1. 查询申请是否存在
        sql_get = "SELECT user_id, status FROM t_adoptionapply WHERE apply_id = %s"
        result = self.db.execute_raw_sql(sql_get, (apply_id,))

        if not result:
            self.db.close_database()
            return error_response("错误：申请不存在")

        apply = result[0]

        # 2. 检查申请人是否匹配
        if apply['user_id'] != user_id:
            self.db.close_database()
            return error_response("错误：无权取消他人申请")

        # 3. 检查申请状态是否为待审核
        if apply['status'] != 0:
            self.db.close_database()
            return error_response("错误：只能取消待审核的申请")

        # 4. 更新状态为已取消（status=2）
        sql_update = "UPDATE t_adoptionapply SET status = 2 WHERE apply_id = %s"
        self.db.execute_raw_sql(sql_update, (apply_id,))
        self.db.close_database()

        return success_response(
            f"领养申请 {apply_id} 已取消",
            data={"apply_id": apply_id, "status": 2}
        )

    def get_application_by_id(self, apply_id):
        """
        根据申请编号查询领养申请详情
        :param apply_id: 申请编号
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = """SELECT a.*,
                        u.nickname AS applicant_nickname,
                        u.avatarURL AS applicant_avatar,
                        p.name AS pet_name,
                        p.breed AS pet_breed,
                        p.photo_urls AS pet_photo_urls,
                        p.status AS pet_status
                FROM t_adoptionapply a
                JOIN t_user u ON a.user_id = u.user_id
                JOIN t_animal p ON a.pet_id = p.pet_id
                WHERE a.apply_id = %s"""
        result = self.db.execute_raw_sql(sql, (apply_id,))
        self.db.close_database()

        if not result:
            return error_response("申请不存在")

        row = result[0]
        return success_response(
            "成功",
            data={
                "apply_id": row["apply_id"],
                "pet_id": row["pet_id"],
                "user_id": row["user_id"],
                "applicant_nickname": row["applicant_nickname"],
                "applicant_avatar": row["applicant_avatar"],
                "pet_name": row["pet_name"],
                "pet_breed": row["pet_breed"],
                "pet_photo_urls": row["pet_photo_urls"],
                "pet_status": row["pet_status"],
                "status": row["status"],
                "content": row["content"],
                "review_comment": row["review_comment"],
                "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else None
            }
        )

    def get_user_applications(self, user_id, page=1, page_size=20):
        """
        查看用户全部领养申请（按时间倒序，支持分页）
        :return: dict {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        offset = (page - 1) * page_size

        sql_data = """SELECT a.*,
                             u.nickname AS applicant_nickname,
                             u.avatarURL AS applicant_avatar,
                             p.name AS pet_name,
                             p.breed AS pet_breed,
                             p.photo_urls AS pet_photo_urls,
                             p.status AS pet_status
                      FROM t_adoptionapply a
                      JOIN t_user u ON a.user_id = u.user_id
                      JOIN t_animal p ON a.pet_id = p.pet_id
                      WHERE a.user_id = %s
                      ORDER BY a.created_at DESC
                      LIMIT %s OFFSET %s"""
        records = self.db.execute_raw_sql(sql_data, (user_id, page_size, offset))

        sql_count = "SELECT COUNT(*) AS total FROM t_adoptionapply WHERE user_id = %s"
        count_result = self.db.execute_raw_sql(sql_count, (user_id,))
        total = count_result[0]["total"] if count_result else 0

        self.db.close_database()

        applications = []
        if records:
            for row in records:
                applications.append({
                    "apply_id": row["apply_id"],
                    "pet_id": row["pet_id"],
                    "user_id": row["user_id"],
                    "applicant_nickname": row["applicant_nickname"],
                    "applicant_avatar": row["applicant_avatar"],
                    "pet_name": row["pet_name"],
                    "pet_breed": row["pet_breed"],
                    "pet_photo_urls": row["pet_photo_urls"],
                    "pet_status": row["pet_status"],
                    "status": row["status"],
                    "content": row["content"],
                    "review_comment": row["review_comment"],
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else None
                })

        return success_response(
            "成功",
            data={
                "applications": applications,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )

    def get_animal_applications(self, pet_id, page=1, page_size=20):
        """
        查看某动物全部领养申请（按时间倒序，支持分页）
        :return: dict {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        offset = (page - 1) * page_size

        sql_data = """SELECT a.*,
                             u.nickname AS applicant_nickname,
                             u.avatarURL AS applicant_avatar,
                             p.name AS pet_name,
                             p.breed AS pet_breed,
                             p.photo_urls AS pet_photo_urls,
                             p.status AS pet_status
                      FROM t_adoptionapply a
                      JOIN t_user u ON a.user_id = u.user_id
                      JOIN t_animal p ON a.pet_id = p.pet_id
                      WHERE a.pet_id = %s
                      ORDER BY a.created_at DESC
                      LIMIT %s OFFSET %s"""
        records = self.db.execute_raw_sql(sql_data, (pet_id, page_size, offset))

        sql_count = "SELECT COUNT(*) AS total FROM t_adoptionapply WHERE pet_id = %s"
        count_result = self.db.execute_raw_sql(sql_count, (pet_id,))
        total = count_result[0]["total"] if count_result else 0

        self.db.close_database()

        applications = []
        if records:
            for row in records:
                applications.append({
                    "apply_id": row["apply_id"],
                    "pet_id": row["pet_id"],
                    "user_id": row["user_id"],
                    "applicant_nickname": row["applicant_nickname"],
                    "applicant_avatar": row["applicant_avatar"],
                    "pet_name": row["pet_name"],
                    "pet_breed": row["pet_breed"],
                    "pet_photo_urls": row["pet_photo_urls"],
                    "pet_status": row["pet_status"],
                    "status": row["status"],
                    "content": row["content"],
                    "review_comment": row["review_comment"],
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else None
                })

        return success_response(
            "成功",
            data={
                "applications": applications,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )

    def get_all_applications(self, page=1, page_size=20):
        """
        查看所有领养申请（按时间倒序，支持分页）
        :return: dict {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        offset = (page - 1) * page_size

        sql_data = """SELECT a.*,
                             u.nickname AS applicant_nickname,
                             u.avatarURL AS applicant_avatar,
                             p.name AS pet_name,
                             p.breed AS pet_breed,
                             p.photo_urls AS pet_photo_urls,
                             p.status AS pet_status
                      FROM t_adoptionapply a
                      JOIN t_user u ON a.user_id = u.user_id
                      JOIN t_animal p ON a.pet_id = p.pet_id
                      ORDER BY a.created_at DESC
                      LIMIT %s OFFSET %s"""
        records = self.db.execute_raw_sql(sql_data, (page_size, offset))

        sql_count = "SELECT COUNT(*) AS total FROM t_adoptionapply"
        count_result = self.db.execute_raw_sql(sql_count, ())
        total = count_result[0]["total"] if count_result else 0

        self.db.close_database()

        applications = []
        if records:
            for row in records:
                applications.append({
                    "apply_id": row["apply_id"],
                    "pet_id": row["pet_id"],
                    "user_id": row["user_id"],
                    "applicant_nickname": row["applicant_nickname"],
                    "applicant_avatar": row["applicant_avatar"],
                    "pet_name": row["pet_name"],
                    "pet_breed": row["pet_breed"],
                    "pet_photo_urls": row["pet_photo_urls"],
                    "pet_status": row["pet_status"],
                    "status": row["status"],
                    "content": row["content"],
                    "review_comment": row["review_comment"],
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else None
                })

        return success_response(
            "成功",
            data={
                "applications": applications,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )

    def approve_application(self, apply_id, reviewer_id, review_comment=""):
        """
        审核通过领养申请
        :param apply_id: 申请编号
        :param reviewer_id: 审核人ID
        :param review_comment: 审核意见
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql_get = "SELECT pet_id, status FROM t_adoptionapply WHERE apply_id = %s"
        result = self.db.execute_raw_sql(sql_get, (apply_id,))

        if not result:
            self.db.close_database()
            return error_response("错误：申请不存在")

        apply = result[0]

        if apply["status"] != 0:
            self.db.close_database()
            return error_response("错误：只能审核待审核状态的申请")

        pet_id = apply["pet_id"]

        sql_update = """UPDATE t_adoptionapply
                         SET status = 1, review_comment = %s
                         WHERE apply_id = %s"""
        self.db.execute_raw_sql(sql_update, (review_comment, apply_id))
        self.db.close_database()

        # 同步更新动物状态为已领养
        animal_result = self.animal_lib.update_animal_status(pet_id, 1)
        if not animal_result["success"]:
            print(f"警告：申请已通过，但更新动物 {pet_id} 状态失败")

        return success_response(
            f"领养申请 {apply_id} 已审核通过",
            data={"apply_id": apply_id, "status": 1}
        )

    def reject_application(self, apply_id, review_comment=""):
        """
        审核拒绝领养申请
        :param apply_id: 申请编号
        :param review_comment: 驳回理由
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql_get = "SELECT status FROM t_adoptionapply WHERE apply_id = %s"
        result = self.db.execute_raw_sql(sql_get, (apply_id,))

        if not result:
            self.db.close_database()
            return error_response("错误：申请不存在")

        apply = result[0]

        if apply["status"] != 0:
            self.db.close_database()
            return error_response("错误：只能驳回待审核状态的申请")

        sql_update = """UPDATE t_adoptionapply
                         SET status = 2, review_comment = %s
                         WHERE apply_id = %s"""
        self.db.execute_raw_sql(sql_update, (review_comment, apply_id))
        self.db.close_database()

        return success_response(
            f"领养申请 {apply_id} 已驳回",
            data={"apply_id": apply_id, "status": 2}
        )

    # ==================== 内部方法 ====================

    def _check_duplicate_application(self, user_id, pet_id):
        """
        检查是否存在重复申请（同一用户对同一动物是否有待审核的申请）
        内部方法，返回统一格式
        :return: dict {"success": bool, "message": str, "data": {"is_duplicate": bool, "apply_id": str or None}}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = """SELECT apply_id
                 FROM t_adoptionapply
                 WHERE user_id = %s
                   AND pet_id = %s
                   AND status = 0
                 LIMIT 1"""
        result = self.db.execute_raw_sql(sql, (user_id, pet_id))
        self.db.close_database()

        if result and len(result) > 0:
            return success_response(
                "存在重复申请",
                data={"is_duplicate": True, "apply_id": result[0]["apply_id"]}
            )
        return success_response(
            "无重复申请",
            data={"is_duplicate": False, "apply_id": None}
        )
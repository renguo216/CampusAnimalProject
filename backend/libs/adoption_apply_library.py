"""
领养申请业务逻辑层

依赖：utils/db_manager.py 中的 DatabaseManager
      libs/user_library.py 中的 UserLibrary
      libs/animal_library.py 中的 AnimalLibrary

"""
from datetime import datetime
from backend.utils.db_manager import DatabaseManager
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

    # ==================== 核心功能（后续逐步实现） ====================
    def submit_adoption_application(self, user_id, pet_id, content=""):
        """
        提交领养申请

        业务流程：
        1. 检查用户是否存在（调用 user_lib.get_user_by_account）
        2. 检查动物是否存在（调用 animal_lib.get_animal_by_id）
        3. 检查动物是否允许领养（status != 1 即可申请）
        4. 检查是否重复申请（调用 check_duplicate_application）
        5. 生成 apply_id（UUID），写入 t_adoptionapply 表
        6. 返回 apply_id

        :param user_id: 申请人ID
        :param pet_id: 动物ID
        :param content: 申请理由（非必填）
        :return: 成功返回 apply_id (str)，失败返回 False/None
        """
        # 1. 检查用户是否存在
        user = self.user_lib.get_user_by_account(user_id)
        if not user:
            print("错误：用户不存在")
            return False
        # 2. 检查动物是否存在
        animal = self.animal_lib.get_animal_by_id(pet_id)
        if not animal:
            print("错误：动物不存在")
            return False
        # 3. 检查动物是否允许领养（status=1 表示已领养，不允许再次申请）
        if animal.status == 1:
            print("错误：该动物已被领养")
            return False
        # 4. 检查重复申请（待审核状态）
        if self.check_duplicate_application(user_id, pet_id):
            print("错误：您已提交过对该动物的领养申请，请勿重复提交")
            return False
        # 5. 生成 apply_id 并写入数据库
        apply_id = str(uuid.uuid4()).replace("-", "")[:32]
        now = datetime.now()

        if not self.db.open_database():
            return False
        
        sql = """INSERT INTO t_adoptionapply (apply_id, pet_id, user_id, status, content, created_at)
                VALUES (%s, %s, %s, 0, %s, %s)"""
        result = self.db.execute_raw_sql(sql, (apply_id, pet_id, user_id, content, now))
        self.db.close_database()
        # execute_raw_sql 返回的是查询结果，INSERT 成功后返回空列表 []
        # 若 INSERT 失败，返回 None
        if result is None:
            print("错误：数据库插入失败")
            return False

        print(f"领养申请提交成功，申请编号：{apply_id}")
        return apply_id

    def cancel_adoption_application(self, apply_id, user_id):
        """
        取消领养申请（仅申请人可取消待审核的申请）
        业务流程：
        1. 检查申请是否存在
        2. 检查申请人是否匹配
        3. 检查申请状态是否为待审核（status=0）
        4. 更新 status = 2（视为自动驳回/取消）
        注意：不直接删除，保留记录供追溯
        :param apply_id: 申请编号
        :param user_id: 当前操作用户ID（用于校验是否为申请人）
        :return: 成功返回 True，失败返回 False
        """
        if not self.db.open_database():
            return False

        # 1. 查询申请是否存在
        sql_get = "SELECT user_id, status FROM t_adoptionapply WHERE apply_id = %s"
        result = self.db.execute_raw_sql(sql_get, (apply_id,))

        if not result:
            self.db.close_database()
            print("错误：申请不存在")
            return False

        apply = result[0]

        # 2. 检查申请人是否匹配
        if apply['user_id'] != user_id:
            self.db.close_database()
            print("错误：无权取消他人申请")
            return False

        # 3. 检查申请状态是否为待审核
        if apply['status'] != 0:
            self.db.close_database()
            print("错误：只能取消待审核的申请")
            return False

        # 4. 更新状态为已取消（status=2 表示驳回/取消，此处统一用 2）
        sql_update = "UPDATE t_adoptionapply SET status = 2 WHERE apply_id = %s"
        self.db.execute_raw_sql(sql_update, (apply_id,))
        self.db.close_database()

        print(f"领养申请 {apply_id} 已取消")
        return True

    def get_application_by_id(self, apply_id):
        """
        根据申请编号查询领养申请详情

        返回结果包含：
        - 申请信息（所有字段）
        - 申请人信息（nickname, avatarURL）
        - 动物信息（name, breed, photo_urls 等）

        :param apply_id: 申请编号
        :return: 字典形式的申请详情，或 None（未找到）
        """
        if not self.db.open_database():
            return None

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
            return None

        row = result[0]
        return {
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

    def get_user_applications(self, user_id, page=1, page_size=20):
        """
        查看用户全部领养申请（按时间倒序，支持分页）

        :param user_id: 用户ID
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: 字典包含 applications（列表）、total（总数）、page、page_size
                 失败返回 None
        """
        if not self.db.open_database():
            return None

        offset = (page - 1) * page_size

        # 1. 查询当前页数据
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

        # 2. 查询总数
        sql_count = "SELECT COUNT(*) AS total FROM t_adoptionapply WHERE user_id = %s"
        count_result = self.db.execute_raw_sql(sql_count, (user_id,))
        total = count_result[0]["total"] if count_result else 0

        self.db.close_database()

        # 3. 格式化返回
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

        return {
            "applications": applications,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_animal_applications(self, pet_id, page=1, page_size=20):
        """
        查看某动物全部领养申请（按时间倒序，支持分页）

        :param pet_id: 动物ID
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: 字典包含 applications（列表）、total、page、page_size
                 失败返回 None
        """
        if not self.db.open_database():
            return None

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

        return {
            "applications": applications,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def approve_application(self, apply_id, reviewer_id, review_comment=""):
        """
        审核通过领养申请

        业务流程：
        1. 检查申请是否存在且为待审核状态（status=0）
        2. 更新申请状态为通过（status=1），记录审核意见
        3. 同步更新动物状态为已领养（调用 animal_lib.update_animal_status）
        4. 若有其他待审核申请，可选是否将其驳回（当前不自动处理）

        :param apply_id: 申请编号
        :param reviewer_id: 审核人ID（用于权限校验，当前层不存储）
        :param review_comment: 审核意见（可选）
        :return: 成功返回 True，失败返回 False
        """
        if not self.db.open_database():
            return False

        # 1. 查询申请是否存在，获取关联动物ID和当前状态
        sql_get = "SELECT pet_id, status FROM t_adoptionapply WHERE apply_id = %s"
        result = self.db.execute_raw_sql(sql_get, (apply_id,))

        if not result:
            self.db.close_database()
            print("错误：申请不存在")
            return False

        apply = result[0]

        # 2. 检查是否为待审核状态
        if apply["status"] != 0:
            self.db.close_database()
            print("错误：只能审核待审核状态的申请")
            return False

        pet_id = apply["pet_id"]

        # 3. 更新申请状态为通过
        sql_update = """UPDATE t_adoptionapply
                         SET status = 1, review_comment = %s
                         WHERE apply_id = %s"""
        self.db.execute_raw_sql(sql_update, (review_comment, apply_id))

        self.db.close_database()

        # 4. 同步更新动物状态为已领养（调用 AnimalLibrary）
        animal_updated = self.animal_lib.update_animal_status(pet_id, 1)
        if not animal_updated:
            print(f"警告：申请已通过，但更新动物 {pet_id} 状态失败")
            # 不返回 False，因为申请本身已成功通过

        print(f"领养申请 {apply_id} 已审核通过")
        return True

    def reject_application(self, apply_id, review_comment=""):
        """
        审核拒绝领养申请

        业务流程：
        1. 检查申请是否存在且为待审核状态（status=0）
        2. 更新申请状态为驳回（status=2），记录审核意见
        3. 不改变动物状态（动物仍可被其他人申请）

        :param apply_id: 申请编号
        :param review_comment: 驳回理由（可选）
        :return: 成功返回 True，失败返回 False
        """
        if not self.db.open_database():
            return False

        # 1. 查询申请是否存在
        sql_get = "SELECT status FROM t_adoptionapply WHERE apply_id = %s"
        result = self.db.execute_raw_sql(sql_get, (apply_id,))

        if not result:
            self.db.close_database()
            print("错误：申请不存在")
            return False

        apply = result[0]

        # 2. 检查是否为待审核状态
        if apply["status"] != 0:
            self.db.close_database()
            print("错误：只能驳回待审核状态的申请")
            return False

        # 3. 更新状态为驳回
        sql_update = """UPDATE t_adoptionapply
                         SET status = 2, review_comment = %s
                         WHERE apply_id = %s"""
        self.db.execute_raw_sql(sql_update, (review_comment, apply_id))
        self.db.close_database()

        print(f"领养申请 {apply_id} 已驳回")
        return True

    def check_duplicate_application(self, user_id, pet_id):
        """
        检查是否存在重复申请（同一用户对同一动物是否有待审核的申请）
        业务规则：
        - 仅检查 status=0（待审核）的申请
        - 已通过的（status=1）或已驳回的（status=2）不视为重复

        :param user_id: 申请人ID
        :param pet_id: 动物ID
        :return: 存在重复返回 True，否则返回 False
        """
        if not self.db.open_database():
            return False  # 数据库连接失败视为无重复

        sql = """SELECT COUNT(*) AS cnt
                 FROM t_adoptionapply
                 WHERE user_id = %s
                   AND pet_id = %s
                   AND status = 0"""
        result = self.db.execute_raw_sql(sql, (user_id, pet_id))
        self.db.close_database()

        if result and result[0]['cnt'] > 0:
            return True
        return False


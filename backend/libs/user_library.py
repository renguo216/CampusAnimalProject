from backend.utils.db_manager import DatabaseManager
from backend.model.user import User
import uuid

class UserLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    # === 基础核心操作 ===
    def get_user_by_account(self, user_id):
        """根据账号精确查询用户信息，返回 User 对象"""
        if not self.db.open_database():
            return None
        user_data = self.db.get_by_id('t_user', 'user_id', user_id)
        self.db.close_database()
        if user_data:
            return User(**user_data)
        return None

    def verify_user_validity(self, user_id):
        """验证用户是否存在（检查账号是否在数据库里）"""
        return self.get_user_by_account(user_id) is not None

    def register_user(self, user_id, nickname, avatar_url=None, role=0):
        if self.get_user_by_account(user_id):
            return False
        data = {
            'user_id': user_id,
            'nickname': nickname,
            'avatarURL': avatar_url,
            'role': role,
            'points': 0,
            'identityNo': uuid.uuid4().hex[:12],  # ✅ 单独生成短ID
            'level': 1
        }
        if not self.db.open_database():
            return False
        success = self.db.insert('t_user', data)
        self.db.close_database()
        return success

    def update_user_info(self, user_id, update_data):
        """通用更新用户信息方法（增加存在性检查）"""
        # 先检查用户是否存在
        if not self.get_user_by_account(user_id):
            return False  # 用户不存在，返回失败
        if not self.db.open_database():
            return False
        success = self.db.update('t_user', 'user_id', user_id, update_data)
        self.db.close_database()
        return success

    # === 专用辅助方法 ===
    def update_role(self, user_id, new_role):
        """专门修改用户角色（用于从游客升级为志愿者）"""
        return self.update_user_info(user_id, {'role': new_role})

    def increment_points(self, user_id, points):
        """增加用户积分（由其他模块调用，如完成救助加10分）"""
        user = self.get_user_by_account(user_id)
        if not user:
            return False
        new_points = user.points + points
        return self.update_user_info(user_id, {'points': new_points})

    def add_points(self, user_id, delta):
        """在原有积分基础上增加指定分数（delta可为负数）"""
        user = self.get_user_by_account(user_id)
        if not user:
            return False
        new_points = user.points + delta
        return self.update_user_info(user_id, {'points': new_points})

    def get_volunteers_ranking(self, limit=10):
        """获取积分最高的前N名志愿者（用于排行榜）"""
        if not self.db.open_database():
            return []
        sql = """
            SELECT * FROM t_user 
            WHERE role = 2 
            ORDER BY points DESC 
            LIMIT %s
        """
        results = self.db.execute_raw_sql(sql, (limit,))
        self.db.close_database()
        return [User(**row) for row in results] if results else []
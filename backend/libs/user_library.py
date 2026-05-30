from backend.utils.db_manager import DatabaseManager
from backend.model.user import User
import uuid
from datetime import datetime

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

    def register_user(self, user_id, nickname, avatar_url=None, role=1):
        """
        注册新用户
        默认角色为 1（普通用户），无游客模式。
        """
        if self.get_user_by_account(user_id):
            return False
        
        # 根据角色初始化相关字段
        volunteer_id = None
        admin_id = None
        level = None
        if role == 2:    # 志愿者
            level = 1
        elif role == 3:  # 管理员
            admin_id = uuid.uuid4().hex[:12]

        data = {
            'user_id': user_id,
            'nickname': nickname,
            'avatarURL': avatar_url,
            'role': role,
            'points': 0,
            'volunteer_id': volunteer_id,
            'admin_id': admin_id,
            'level': level,
            'phone_number': None,
            'like_count': 0,
            'follower_count': 0,
            'following_count': 0,
            'is_active': 1,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if not self.db.open_database():
            return False
        success = self.db.insert('t_user', data)
        self.db.close_database()
        return success

    def update_user_info(self, user_id, update_data):
        """通用更新用户信息方法（增加存在性检查）"""
        if not self.get_user_by_account(user_id):
            return False
        if not self.db.open_database():
            return False
        success = self.db.update('t_user', 'user_id', user_id, update_data)
        self.db.close_database()
        return success

    # === 专用辅助方法 ===
    def update_role(self, user_id, new_role):
        """
        修改用户角色，并自动调整关联字段
        1->普通用户, 2->志愿者, 3->管理员
        """
        user = self.get_user_by_account(user_id)
        if not user:
            return False
        
        update_data = {'role': new_role}
        # 根据目标角色调整相关字段
        if new_role == 2:  # 升级为志愿者
            update_data['level'] = 1
            update_data['admin_id'] = None
        elif new_role == 3:  # 升级为管理员
            update_data['level'] = None
            update_data['volunteer_id'] = None
            update_data['admin_id'] = uuid.uuid4().hex[:12]
        else:  # 降级为普通用户
            update_data['level'] = None
            update_data['volunteer_id'] = None
            update_data['admin_id'] = None
        
        return self.update_user_info(user_id, update_data)

    def set_volunteer_id(self, user_id, volunteer_id):
        """为志愿者设置编号（管理员后台调用）"""
        return self.update_user_info(user_id, {'volunteer_id': volunteer_id})

    def set_admin_id(self, user_id, admin_id):
        """为管理员设置工号（开发者直接调用）"""
        return self.update_user_info(user_id, {'admin_id': admin_id})

    def toggle_active_status(self, user_id, is_active):
        """设置用户激活状态：0-封禁，1-正常"""
        return self.update_user_info(user_id, {'is_active': is_active})

    def update_user_stats(self, user_id, like_count=None, follower_count=None, following_count=None):
        """
        更新用户的统计数据（获赞、关注、粉丝数）
        API层调用，用于同步社交互动数据
        """
        update_data = {}
        if like_count is not None:
            update_data['like_count'] = like_count
        if follower_count is not None:
            update_data['follower_count'] = follower_count
        if following_count is not None:
            update_data['following_count'] = following_count
        if not update_data:
            return False
        return self.update_user_info(user_id, update_data)

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

    def get_user_profile(self, user_id):
        """
        获取用户个人中心完整信息（包含统计数据）
        用于“我的”页面展示
        """
        user = self.get_user_by_account(user_id)
        if not user:
            return None
        return {
            'user_id': user.user_id,
            'nickname': user.nickname,
            'avatarURL': user.avatarURL,
            'role': user.role,
            'points': user.points,
            'volunteer_id': user.volunteer_id,
            'admin_id': user.admin_id,
            'level': user.level,
            'like_count': user.like_count,
            'follower_count': user.follower_count,
            'following_count': user.following_count,
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
        }
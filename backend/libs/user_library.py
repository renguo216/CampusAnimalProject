from backend.utils.db_manager import DatabaseManager

class UserLibrary:
    """
    UserLibrary 操作类
    对应文档：3.5.2 数据操作类设计 - (1) 针对 User 类
    主要支持 T-User 表的特有业务逻辑。
    """

    def __init__(self):
        self.db = DatabaseManager()

    def verify_user_validity(self, user_id):
        """
        验证用户输入的账号与密码是否合法（对应文档接口）
        注意：由于本系统使用微信 OpenID 作为 user_id，无需传统密码验证。
        此方法实现为检查用户是否存在于数据库中。
        """
        if not self.db.open_database():
            return False
        user = self.db.get_by_id('t_user', 'user_id', user_id)
        self.db.close_database()
        return user is not None

    def get_user_by_account(self, user_id):
        """
        根据账号精确查询用户信息（对应文档接口）
        """
        if not self.db.open_database():
            return None
        user = self.db.get_by_id('t_user', 'user_id', user_id)
        self.db.close_database()
        return user

    def register_user(self, user_id, nickname, role=1):
        """
        注册新用户（已修复：避免重复关闭数据库连接）
        """
        # 1. 先检查用户是否存在（这会自动打开并关闭连接）
        if self.get_user_by_account(user_id):
            print(f"用户 {user_id} 已存在")
            return False  # 直接返回，不要再尝试关闭连接！

        # 2. 如果用户不存在，重新打开连接插入数据
        if not self.db.open_database():
            return False
        data = {
            'user_id': user_id,
            'nickname': nickname,
            'role': role
        }
        success = self.db.insert('t_user', data)
        self.db.close_database()  # 只有在这里才需要关闭连接
        return success

    def update_user_info(self, user_id, update_data):
        """
        更新用户信息（补充方法）
        :param update_data: 要更新的字段字典，例如 {'nickname': '新昵称', 'avatarURL': '新头像'}
        """
        if not self.db.open_database():
            return False
        success = self.db.update('t_user', 'user_id', user_id, update_data)
        self.db.close_database()
        return success
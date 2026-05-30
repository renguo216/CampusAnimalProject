# ===== backend/libs/comment_library.py =====
"""
评论业务逻辑层
提供评论增删查、楼中楼回复、点赞等功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from backend.utils.db_manager import DatabaseManager
from backend.model.comment import Comment
from datetime import datetime


class CommentLibrary:
    """
    评论业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        self.db = DatabaseManager()

    # ==================== 基础核心操作 ====================

    def create_comment(self, post_id, user_id, content, parent_comment_id=None):
        """
        对帖子发表评论（支持楼中楼回复）
        :param post_id: 帖子ID
        :param user_id: 评论人ID
        :param content: 评论内容
        :param parent_comment_id: 父评论ID（可选，用于回复）
        :return: 成功返回 Comment 对象，失败返回 False
        """
        if not post_id or not user_id or not content:
            return False

        if not self.db.open_database():
            return False

        # 1. 验证帖子是否存在且已审核通过
        post_check_sql = "SELECT 1 FROM t_post WHERE post_id = %s AND status = 1"
        post_exists = self.db.execute_raw_sql(post_check_sql, (post_id,))
        if not post_exists:
            self.db.close_database()
            return False

        # 2. 如果传了父评论ID，验证其存在且属于同一帖子
        if parent_comment_id is not None:
            parent_check_sql = "SELECT 1 FROM t_comment WHERE comment_id = %s AND post_id = %s"
            parent_exists = self.db.execute_raw_sql(parent_check_sql, (parent_comment_id, post_id))
            if not parent_exists:
                self.db.close_database()
                return False

        # 3. 插入评论
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_sql = """
            INSERT INTO t_comment (post_id, user_id, content, parent_comment_id, like_count, created_at)
            VALUES (%s, %s, %s, %s, 0, %s)
        """
        self.db.execute_raw_sql(insert_sql, (post_id, user_id, content, parent_comment_id, now))

        # 4. 获取自增ID
        comment_id_result = self.db.execute_raw_sql("SELECT LAST_INSERT_ID() AS id")
        comment_id = comment_id_result[0]['id'] if comment_id_result else None

        # 5. 更新帖子评论数
        update_count_sql = "UPDATE t_post SET comment_count = comment_count + 1 WHERE post_id = %s"
        self.db.execute_raw_sql(update_count_sql, (post_id,))

        self.db.close_database()

        if comment_id is None:
            return False

        return Comment(
            comment_id=comment_id,
            post_id=post_id,
            user_id=user_id,
            content=content,
            parent_comment_id=parent_comment_id,
            like_count=0,
            created_at=now
        )

    def delete_comment(self, comment_id, user_id):
        """
        删除评论（仅评论作者可删除）
        同步更新 t_post.comment_count - 1
        :param comment_id: 评论ID
        :param user_id: 操作用户ID（用于验证归属）
        :return: 成功返回 True，失败返回 False
        """
        if not comment_id or not user_id:
            return False

        if not self.db.open_database():
            return False

        # 1. 查询评论信息（验证归属并获取 post_id）
        check_sql = "SELECT user_id, post_id FROM t_comment WHERE comment_id = %s"
        result = self.db.execute_raw_sql(check_sql, (comment_id,))
        if not result:
            self.db.close_database()
            return False

        comment = result[0]
        if comment['user_id'] != user_id:
            self.db.close_database()
            return False

        post_id = comment['post_id']

        # 2. 删除评论（子回复将通过外键 ON DELETE CASCADE 自动删除）
        del_sql = "DELETE FROM t_comment WHERE comment_id = %s"
        self.db.execute_raw_sql(del_sql, (comment_id,))

        # 3. 更新帖子评论数（防止负数）
        update_sql = "UPDATE t_post SET comment_count = GREATEST(comment_count - 1, 0) WHERE post_id = %s"
        self.db.execute_raw_sql(update_sql, (post_id,))

        self.db.close_database()
        return True

    def admin_delete_comment(self, comment_id, admin_user_id):
        """
        管理员删除违规评论（绕过归属验证）
        同步更新 t_post.comment_count - 1
        :param comment_id: 评论ID
        :param admin_user_id: 管理员用户ID
        :return: 成功返回 True，失败返回 False
        """
        if not comment_id or not admin_user_id:
            return False

        if not self.db.open_database():
            return False

        # 1. 验证操作用户是否为管理员（role = 3）
        role_check_sql = "SELECT role FROM t_user WHERE user_id = %s"
        role_result = self.db.execute_raw_sql(role_check_sql, (admin_user_id,))
        if not role_result or role_result[0]['role'] != 3:
            self.db.close_database()
            return False

        # 2. 查询评论存在性并获取 post_id
        check_sql = "SELECT post_id FROM t_comment WHERE comment_id = %s"
        result = self.db.execute_raw_sql(check_sql, (comment_id,))
        if not result:
            self.db.close_database()
            return False

        post_id = result[0]['post_id']

        # 3. 删除评论（子回复级联删除）
        del_sql = "DELETE FROM t_comment WHERE comment_id = %s"
        self.db.execute_raw_sql(del_sql, (comment_id,))

        # 4. 更新帖子评论数
        update_sql = "UPDATE t_post SET comment_count = GREATEST(comment_count - 1, 0) WHERE post_id = %s"
        self.db.execute_raw_sql(update_sql, (post_id,))

        self.db.close_database()
        return True

    # ==================== 查询方法 ====================

    def get_comment_by_id(self, comment_id):
        """
        根据评论ID精确查询
        :param comment_id: 评论ID
        :return: Comment 对象 或 None
        """
        if not comment_id:
            return None

        if not self.db.open_database():
            return None

        sql = "SELECT * FROM t_comment WHERE comment_id = %s"
        result = self.db.execute_raw_sql(sql, (comment_id,))
        self.db.close_database()

        if not result:
            return None

        data = result[0]
        return Comment(
            comment_id=data['comment_id'],
            post_id=data['post_id'],
            user_id=data['user_id'],
            content=data['content'],
            parent_comment_id=data.get('parent_comment_id'),
            like_count=data.get('like_count', 0),
            created_at=data.get('created_at')
        )

    def get_post_comments(self, post_id, page=1, page_size=20):
        """
        获取帖子的评论列表（按时间升序）
        支持分页
        :param post_id: 帖子ID
        :param page: 页码（从1开始）
        :param page_size: 每页数量
        :return: 成功返回 Comment 对象列表，失败返回 []
        """
        if not post_id:
            return []

        if not self.db.open_database():
            return []

        offset = (page - 1) * page_size
        sql = """SELECT * FROM t_comment
                 WHERE post_id = %s
                 ORDER BY created_at ASC
                 LIMIT %s OFFSET %s"""
        results = self.db.execute_raw_sql(sql, (post_id, page_size, offset))
        self.db.close_database()

        if not results:
            return []

        comments = []
        for data in results:
            comments.append(Comment(
                comment_id=data['comment_id'],
                post_id=data['post_id'],
                user_id=data['user_id'],
                content=data['content'],
                parent_comment_id=data.get('parent_comment_id'),
                like_count=data.get('like_count', 0),
                created_at=data.get('created_at')
            ))
        return comments

    def get_user_comments(self, user_id, page=1, page_size=20):
        """
        查看用户发表的评论历史（按时间倒序）
        支持分页
        :param user_id: 用户ID
        :param page: 页码
        :param page_size: 每页数量
        :return: 成功返回 Comment 对象列表，失败返回 []
        """
        if not user_id:
            return []

        if not self.db.open_database():
            return []

        offset = (page - 1) * page_size
        sql = """SELECT * FROM t_comment
                 WHERE user_id = %s
                 ORDER BY created_at DESC
                 LIMIT %s OFFSET %s"""
        results = self.db.execute_raw_sql(sql, (user_id, page_size, offset))
        self.db.close_database()

        if not results:
            return []

        comments = []
        for data in results:
            comments.append(Comment(
                comment_id=data['comment_id'],
                post_id=data['post_id'],
                user_id=data['user_id'],
                content=data['content'],
                parent_comment_id=data.get('parent_comment_id'),
                like_count=data.get('like_count', 0),
                created_at=data.get('created_at')
            ))
        return comments

    def get_comment_replies(self, comment_id):
        """
        获取某条评论的所有子回复（楼中楼回复列表，按时间升序）
        :param comment_id: 父评论ID
        :return: 成功返回 Comment 对象列表，失败返回 []
        """
        if not comment_id:
            return []

        if not self.db.open_database():
            return []

        sql = """SELECT * FROM t_comment
                 WHERE parent_comment_id = %s
                 ORDER BY created_at ASC"""
        results = self.db.execute_raw_sql(sql, (comment_id,))
        self.db.close_database()

        if not results:
            return []

        comments = []
        for data in results:
            comments.append(Comment(
                comment_id=data['comment_id'],
                post_id=data['post_id'],
                user_id=data['user_id'],
                content=data['content'],
                parent_comment_id=data.get('parent_comment_id'),
                like_count=data.get('like_count', 0),
                created_at=data.get('created_at')
            ))
        return comments

    # ==================== 回复与点赞 ====================

    def reply_comment(self, post_id, user_id, content, parent_comment_id):
        """
        回复评论（楼中楼回复）
        内部调用 create_comment 并设置 parent_comment_id
        :param post_id: 帖子ID
        :param user_id: 回复人ID
        :param content: 回复内容
        :param parent_comment_id: 被回复的评论ID
        :return: 成功返回 Comment 对象，失败返回 False
        """
        return self.create_comment(post_id, user_id, content, parent_comment_id)

    def toggle_comment_like(self, comment_id, user_id):
        """
        切换评论点赞状态（已赞则取消，未赞则点赞）
        通过 t_like 表实现，同时更新 t_comment.like_count
        :param comment_id: 评论ID
        :param user_id: 操作人ID
        :return: 点赞成功返回 True，取消点赞返回 False，操作失败返回 None
        """
        if not comment_id or not user_id:
            return None

        if not self.db.open_database():
            return None

        # 1. 检查评论是否存在
        check_sql = "SELECT 1 FROM t_comment WHERE comment_id = %s"
        exists = self.db.execute_raw_sql(check_sql, (comment_id,))
        if not exists:
            self.db.close_database()
            return None

        # 2. 检查是否已点赞
        like_sql = "SELECT 1 FROM t_like WHERE comment_id = %s AND user_id = %s AND post_id IS NULL"
        liked = self.db.execute_raw_sql(like_sql, (comment_id, user_id))

        if liked:
            # 取消点赞
            del_sql = "DELETE FROM t_like WHERE comment_id = %s AND user_id = %s AND post_id IS NULL"
            self.db.execute_raw_sql(del_sql, (comment_id, user_id))
            update_sql = "UPDATE t_comment SET like_count = GREATEST(like_count - 1, 0) WHERE comment_id = %s"
            self.db.execute_raw_sql(update_sql, (comment_id,))
            self.db.close_database()
            return False
        else:
            # 点赞
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            insert_sql = "INSERT INTO t_like (comment_id, user_id, created_at, post_id) VALUES (%s, %s, %s, NULL)"
            self.db.execute_raw_sql(insert_sql, (comment_id, user_id, now))
            update_sql = "UPDATE t_comment SET like_count = like_count + 1 WHERE comment_id = %s"
            self.db.execute_raw_sql(update_sql, (comment_id,))
            self.db.close_database()
            return True
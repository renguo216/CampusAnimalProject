# ===== backend/libs/comment_library.py =====
"""
评论业务逻辑层
提供评论增删查、楼中楼回复、点赞等功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from backend.utils.db_manager import DatabaseManager
from backend.model.comment import Comment
from backend.utils.response import success_response, error_response
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
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not post_id or not user_id or not content:
            return error_response("参数不能为空")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        # 1. 验证帖子是否存在且已审核通过
        post_check_sql = "SELECT 1 FROM t_post WHERE post_id = %s AND status = 1"
        post_exists = self.db.execute_raw_sql(post_check_sql, (post_id,))
        if not post_exists:
            self.db.close_database()
            return error_response("帖子不存在或未通过审核")

        # 2. 如果传了父评论ID，验证其存在且属于同一帖子
        if parent_comment_id is not None:
            parent_check_sql = "SELECT 1 FROM t_comment WHERE comment_id = %s AND post_id = %s"
            parent_exists = self.db.execute_raw_sql(parent_check_sql, (parent_comment_id, post_id))
            if not parent_exists:
                self.db.close_database()
                return error_response("父评论不存在或不属于该帖子")

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
            return error_response("获取评论ID失败")

        return success_response(
            "评论成功",
            data={
                "comment_id": comment_id,
                "post_id": post_id,
                "user_id": user_id,
                "content": content,
                "parent_comment_id": parent_comment_id,
                "like_count": 0,
                "created_at": now
            }
        )

    def delete_comment(self, comment_id, user_id):
        """
        删除评论（仅评论作者可删除）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not comment_id or not user_id:
            return error_response("参数不能为空")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        check_sql = "SELECT user_id, post_id FROM t_comment WHERE comment_id = %s"
        result = self.db.execute_raw_sql(check_sql, (comment_id,))
        if not result:
            self.db.close_database()
            return error_response("评论不存在")

        comment = result[0]
        if comment['user_id'] != user_id:
            self.db.close_database()
            return error_response("无权删除他人评论")

        post_id = comment['post_id']

        del_sql = "DELETE FROM t_comment WHERE comment_id = %s"
        self.db.execute_raw_sql(del_sql, (comment_id,))

        update_sql = "UPDATE t_post SET comment_count = GREATEST(comment_count - 1, 0) WHERE post_id = %s"
        self.db.execute_raw_sql(update_sql, (post_id,))

        self.db.close_database()
        return success_response("评论已删除", data={"comment_id": comment_id})

    def admin_delete_comment(self, comment_id, admin_user_id):
        """
        管理员删除违规评论（绕过归属验证）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not comment_id or not admin_user_id:
            return error_response("参数不能为空")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        role_check_sql = "SELECT role FROM t_user WHERE user_id = %s"
        role_result = self.db.execute_raw_sql(role_check_sql, (admin_user_id,))
        if not role_result or role_result[0]['role'] != 3:
            self.db.close_database()
            return error_response("无权操作，仅管理员可删除")

        check_sql = "SELECT post_id FROM t_comment WHERE comment_id = %s"
        result = self.db.execute_raw_sql(check_sql, (comment_id,))
        if not result:
            self.db.close_database()
            return error_response("评论不存在")

        post_id = result[0]['post_id']

        del_sql = "DELETE FROM t_comment WHERE comment_id = %s"
        self.db.execute_raw_sql(del_sql, (comment_id,))

        update_sql = "UPDATE t_post SET comment_count = GREATEST(comment_count - 1, 0) WHERE post_id = %s"
        self.db.execute_raw_sql(update_sql, (post_id,))

        self.db.close_database()
        return success_response("评论已删除", data={"comment_id": comment_id})

    # ==================== 查询方法（统一格式） ====================

    def get_comment_by_id(self, comment_id):
        """
        根据评论ID精确查询
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not comment_id:
            return error_response("评论ID不能为空")

        comment = self._get_comment_by_id(comment_id)
        if not comment:
            return error_response("评论不存在")

        return success_response("成功", data=self._comment_to_dict(comment))

    def get_post_comments(self, post_id, page=1, page_size=20):
        """
        获取帖子的评论列表（按时间升序）
        :return: dict {"success": bool, "message": str, "data": {"comments": list, "total": int, "page": int, "page_size": int}}
        """
        if not post_id:
            return error_response("帖子ID不能为空")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        offset = (page - 1) * page_size

        # 查询数据
        sql = """SELECT * FROM t_comment
                 WHERE post_id = %s
                 ORDER BY created_at ASC
                 LIMIT %s OFFSET %s"""
        results = self.db.execute_raw_sql(sql, (post_id, page_size, offset))

        # 查询总数
        count_sql = "SELECT COUNT(*) AS total FROM t_comment WHERE post_id = %s"
        count_result = self.db.execute_raw_sql(count_sql, (post_id,))
        total = count_result[0]["total"] if count_result else 0

        self.db.close_database()

        comments = []
        if results:
            for data in results:
                comment = Comment(
                    comment_id=data['comment_id'],
                    post_id=data['post_id'],
                    user_id=data['user_id'],
                    content=data['content'],
                    parent_comment_id=data.get('parent_comment_id'),
                    like_count=data.get('like_count', 0),
                    created_at=data.get('created_at')
                )
                comments.append(self._comment_to_dict(comment))

        return success_response(
            "成功",
            data={
                "comments": comments,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )

    def get_user_comments(self, user_id, page=1, page_size=20):
        """
        查看用户发表的评论历史（按时间倒序）
        :return: dict {"success": bool, "message": str, "data": {"comments": list, "total": int, "page": int, "page_size": int}}
        """
        if not user_id:
            return error_response("用户ID不能为空")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        offset = (page - 1) * page_size

        sql = """SELECT * FROM t_comment
                 WHERE user_id = %s
                 ORDER BY created_at DESC
                 LIMIT %s OFFSET %s"""
        results = self.db.execute_raw_sql(sql, (user_id, page_size, offset))

        count_sql = "SELECT COUNT(*) AS total FROM t_comment WHERE user_id = %s"
        count_result = self.db.execute_raw_sql(count_sql, (user_id,))
        total = count_result[0]["total"] if count_result else 0

        self.db.close_database()

        comments = []
        if results:
            for data in results:
                comment = Comment(
                    comment_id=data['comment_id'],
                    post_id=data['post_id'],
                    user_id=data['user_id'],
                    content=data['content'],
                    parent_comment_id=data.get('parent_comment_id'),
                    like_count=data.get('like_count', 0),
                    created_at=data.get('created_at')
                )
                comments.append(self._comment_to_dict(comment))

        return success_response(
            "成功",
            data={
                "comments": comments,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )

    def get_comment_replies(self, comment_id):
        """
        获取某条评论的所有子回复
        :return: dict {"success": bool, "message": str, "data": {"replies": list}}
        """
        if not comment_id:
            return error_response("评论ID不能为空")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        sql = """SELECT * FROM t_comment
                 WHERE parent_comment_id = %s
                 ORDER BY created_at ASC"""
        results = self.db.execute_raw_sql(sql, (comment_id,))
        self.db.close_database()

        replies = []
        if results:
            for data in results:
                comment = Comment(
                    comment_id=data['comment_id'],
                    post_id=data['post_id'],
                    user_id=data['user_id'],
                    content=data['content'],
                    parent_comment_id=data.get('parent_comment_id'),
                    like_count=data.get('like_count', 0),
                    created_at=data.get('created_at')
                )
                replies.append(self._comment_to_dict(comment))

        return success_response("成功", data={"replies": replies})

    # ==================== 回复与点赞 ====================

    def reply_comment(self, post_id, user_id, content, parent_comment_id):
        """
        回复评论（楼中楼回复）
        内部调用 create_comment
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        return self.create_comment(post_id, user_id, content, parent_comment_id)

    def toggle_comment_like(self, comment_id, user_id):
        """
        切换评论点赞状态
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not comment_id or not user_id:
            return error_response("参数不能为空")

        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            # 1. 检查评论是否存在且所属帖子可见
            comment_sql = """SELECT c.user_id, p.status
                             FROM t_comment c
                             JOIN t_post p ON c.post_id = p.post_id
                             WHERE c.comment_id = %s"""
            comment_result = self.db.execute_raw_sql(comment_sql, (comment_id,))
            if not comment_result:
                return error_response("评论不存在")
            if comment_result[0]["status"] != 1:
                return error_response("所属帖子不可见")

            comment_author_id = comment_result[0]["user_id"]

            # 2. 检查是否已点赞（使用新版 t_like 表结构：target_type, target_id, is_deleted）
            check_sql = ("SELECT like_id FROM t_like "
                         "WHERE user_id = %s AND target_id = %s AND target_type = 'comment' AND is_deleted = 0")
            existing = self.db.execute_raw_sql(check_sql, (user_id, str(comment_id)))

            if existing:
                # 3.1 取消点赞（软删除）
                del_sql = ("UPDATE t_like SET is_deleted = 1 "
                           "WHERE user_id = %s AND target_id = %s AND target_type = 'comment'")
                self.db.execute_raw_sql(del_sql, (user_id, str(comment_id)))

                self.db.execute_raw_sql(
                    "UPDATE t_comment SET like_count = GREATEST(like_count - 1, 0) WHERE comment_id = %s",
                    (comment_id,)
                )

                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = GREATEST(like_count - 1, 0) WHERE user_id = %s",
                    (comment_author_id,)
                )

                return success_response("取消点赞", data={"is_liked": False})
            else:
                # 3.2 点赞
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                insert_sql = ("INSERT INTO t_like (target_type, target_id, user_id, created_at) "
                              "VALUES ('comment', %s, %s, %s)")
                self.db.execute_raw_sql(insert_sql, (str(comment_id), user_id, now))

                self.db.execute_raw_sql(
                    "UPDATE t_comment SET like_count = like_count + 1 WHERE comment_id = %s",
                    (comment_id,)
                )

                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = like_count + 1 WHERE user_id = %s",
                    (comment_author_id,)
                )

                return success_response("点赞成功", data={"is_liked": True})
        except Exception as e:
            return error_response(f"点赞操作失败：{str(e)}")
        finally:
            self.db.close_database()

    def check_user_liked_post(self, user_id, post_id):
        """
        检查用户是否已点赞帖子
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")
        try:
            sql = ("SELECT 1 FROM t_like WHERE user_id = %s AND target_id = %s "
                    "AND target_type = 'post' AND is_deleted = 0 LIMIT 1")
            result = self.db.execute_raw_sql(sql, (user_id, post_id))
            is_liked = len(result) > 0 if result else False
            return success_response("成功", data={"is_liked": is_liked})
        except Exception as e:
            return error_response(f"查询失败：{str(e)}")
        finally:
            self.db.close_database()

    def check_user_liked_comment(self, user_id, comment_id):
        """
        检查用户是否已点赞评论
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")
        try:
            sql = ("SELECT 1 FROM t_like WHERE user_id = %s AND target_id = %s "
                    "AND target_type = 'comment' AND is_deleted = 0 LIMIT 1")
            result = self.db.execute_raw_sql(sql, (user_id, comment_id))
            is_liked = len(result) > 0 if result else False
            return success_response("成功", data={"is_liked": is_liked})
        except Exception as e:
            return error_response(f"查询失败：{str(e)}")
        finally:
            self.db.close_database()

    # ==================== 内部辅助方法 ====================

    def _get_comment_by_id(self, comment_id):
        """
        内部方法：根据评论ID精确查询，返回 Comment 对象或 None
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

    def _comment_to_dict(self, comment):
        """
        内部方法：将 Comment 对象序列化为字典
        """
        return {
            "comment_id": comment.comment_id,
            "post_id": comment.post_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "parent_comment_id": comment.parent_comment_id,
            "like_count": comment.like_count,
            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S") if comment.created_at else None
        }
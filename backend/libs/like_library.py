# ===== backend/libs/like_library.py =====
"""
点赞业务逻辑层
提供帖子/评论点赞、取消点赞、查询点赞状态、查询点赞数量等功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager


class LikeLibrary:
    """
    点赞业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        self.db = DatabaseManager()

    # ==================== 点赞/取消点赞 ====================

    def toggle_like_post(self, post_id: str, user_id: str) -> dict:
        """
        切换帖子点赞状态（已赞则取消，未赞则点赞）
        同时更新 t_post.like_count 和帖子作者的 t_user.like_count
        """
        if not self.db.open_database():
            return {"success": False, "message": "数据库连接失败", "data": None}

        try:
            # 1. 检查帖子是否存在且已审核（status=1）
            post_sql = "SELECT user_id FROM t_post WHERE post_id = %s AND status = 1"
            post_result = self.db.execute_raw_sql(post_sql, (post_id,))
            if not post_result:
                return {"success": False, "message": "帖子不存在或不可见", "data": None}

            post_author_id = post_result[0]["user_id"]

            # 2. 检查是否已点赞（利用唯一索引，但此处手动判断）
            check_sql = ("SELECT like_id FROM t_like "
                         "WHERE user_id = %s AND target_id = %s AND target_type = 'post' AND is_deleted = 0")
            existing = self.db.execute_raw_sql(check_sql, (user_id, post_id))

            if existing:
                # 已点赞 → 取消点赞（软删除）
                del_sql = ("UPDATE t_like SET is_deleted = 1 "
                           "WHERE user_id = %s AND target_id = %s AND target_type = 'post'")
                self.db.execute_raw_sql(del_sql, (user_id, post_id))

                # 更新帖子点赞数
                self.db.execute_raw_sql(
                    "UPDATE t_post SET like_count = GREATEST(like_count - 1, 0) WHERE post_id = %s",
                    (post_id,)
                )

                # 更新帖子作者获赞总数
                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = GREATEST(like_count - 1, 0) WHERE user_id = %s",
                    (post_author_id,)
                )

                return {"success": True, "message": "取消点赞", "data": {"is_liked": False}}
            else:
                # 未点赞 → 点赞
                now = datetime.now()
                insert_sql = ("INSERT INTO t_like (target_type, target_id, user_id, created_at) "
                              "VALUES ('post', %s, %s, %s)")
                self.db.execute_raw_sql(insert_sql, (post_id, user_id, now))

                # 更新帖子点赞数
                self.db.execute_raw_sql(
                    "UPDATE t_post SET like_count = like_count + 1 WHERE post_id = %s",
                    (post_id,)
                )

                # 更新帖子作者获赞总数
                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = like_count + 1 WHERE user_id = %s",
                    (post_author_id,)
                )

                return {"success": True, "message": "点赞成功", "data": {"is_liked": True}}

        except Exception as e:
            return {"success": False, "message": f"点赞操作失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def toggle_like_comment(self, comment_id: int, user_id: str) -> dict:
        """
        切换评论点赞状态（已赞则取消，未赞则点赞）
        同时更新 t_comment.like_count 和评论作者的 t_user.like_count
        """
        if not self.db.open_database():
            return {"success": False, "message": "数据库连接失败", "data": None}

        try:
            # 1. 检查评论是否存在及其所属帖子是否审核通过
            comment_sql = """SELECT c.user_id, p.status
                             FROM t_comment c
                             JOIN t_post p ON c.post_id = p.post_id
                             WHERE c.comment_id = %s"""
            comment_result = self.db.execute_raw_sql(comment_sql, (comment_id,))
            if not comment_result:
                return {"success": False, "message": "评论不存在", "data": None}
            if comment_result[0]["status"] != 1:
                return {"success": False, "message": "所属帖子不可见", "data": None}

            comment_author_id = comment_result[0]["user_id"]

            # 2. 检查是否已点赞
            check_sql = ("SELECT like_id FROM t_like "
                         "WHERE user_id = %s AND target_id = %s AND target_type = 'comment' AND is_deleted = 0")
            existing = self.db.execute_raw_sql(check_sql, (user_id, str(comment_id)))

            if existing:
                # 取消点赞（软删除）
                del_sql = ("UPDATE t_like SET is_deleted = 1 "
                           "WHERE user_id = %s AND target_id = %s AND target_type = 'comment'")
                self.db.execute_raw_sql(del_sql, (user_id, str(comment_id)))

                # 更新评论点赞数
                self.db.execute_raw_sql(
                    "UPDATE t_comment SET like_count = GREATEST(like_count - 1, 0) WHERE comment_id = %s",
                    (comment_id,)
                )

                # 更新评论作者获赞总数
                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = GREATEST(like_count - 1, 0) WHERE user_id = %s",
                    (comment_author_id,)
                )

                return {"success": True, "message": "取消点赞", "data": {"is_liked": False}}
            else:
                # 点赞
                now = datetime.now()
                insert_sql = ("INSERT INTO t_like (target_type, target_id, user_id, created_at) "
                              "VALUES ('comment', %s, %s, %s)")
                self.db.execute_raw_sql(insert_sql, (str(comment_id), user_id, now))

                # 更新评论点赞数
                self.db.execute_raw_sql(
                    "UPDATE t_comment SET like_count = like_count + 1 WHERE comment_id = %s",
                    (comment_id,)
                )

                # 更新评论作者获赞总数
                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = like_count + 1 WHERE user_id = %s",
                    (comment_author_id,)
                )

                return {"success": True, "message": "点赞成功", "data": {"is_liked": True}}

        except Exception as e:
            return {"success": False, "message": f"点赞评论失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    # ==================== 查询点赞数量 ====================

    def get_post_like_count(self, post_id: str) -> dict:
        """查询帖子点赞数量"""
        if not self.db.open_database():
            return {"success": False, "message": "数据库连接失败", "data": None}

        try:
            sql = "SELECT like_count FROM t_post WHERE post_id = %s"
            result = self.db.execute_raw_sql(sql, (post_id,))
            count = result[0]["like_count"] if result else 0
            return {"success": True, "message": "成功", "data": {"count": count}}
        except Exception as e:
            return {"success": False, "message": f"查询失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def get_comment_like_count(self, comment_id: int) -> dict:
        """查询评论点赞数量"""
        if not self.db.open_database():
            return {"success": False, "message": "数据库连接失败", "data": None}

        try:
            sql = "SELECT like_count FROM t_comment WHERE comment_id = %s"
            result = self.db.execute_raw_sql(sql, (comment_id,))
            count = result[0]["like_count"] if result else 0
            return {"success": True, "message": "成功", "data": {"count": count}}
        except Exception as e:
            return {"success": False, "message": f"查询失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    # ==================== 检查是否已点赞 ====================

    def check_user_liked_post(self, user_id: str, post_id: str) -> bool:
        """检查用户是否已点赞帖子"""
        if not self.db.open_database():
            return False
        try:
            sql = ("SELECT 1 FROM t_like WHERE user_id = %s AND target_id = %s "
                   "AND target_type = 'post' AND is_deleted = 0 LIMIT 1")
            result = self.db.execute_raw_sql(sql, (user_id, post_id))
            return len(result) > 0 if result else False
        except Exception:
            return False
        finally:
            self.db.close_database()

    def check_user_liked_comment(self, user_id: str, comment_id: int) -> bool:
        """检查用户是否已点赞评论"""
        if not self.db.open_database():
            return False
        try:
            sql = ("SELECT 1 FROM t_like WHERE user_id = %s AND target_id = %s "
                   "AND target_type = 'comment' AND is_deleted = 0 LIMIT 1")
            result = self.db.execute_raw_sql(sql, (user_id, str(comment_id)))
            return len(result) > 0 if result else False
        except Exception:
            return False
        finally:
            self.db.close_database()

    # ==================== 查询用户已点赞列表 ====================

    def get_user_liked_list(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """查询用户已点赞的帖子/评论列表（分页）"""
        if not self.db.open_database():
            return {"success": False, "message": "数据库连接失败", "data": None}

        try:
            offset = (page - 1) * page_size
            # 查询点赞记录，同时通过 LEFT JOIN 获取帖子/评论的标题摘要信息
            sql = """SELECT l.like_id,
                            l.target_type,
                            l.target_id,
                            l.created_at,
                            p.content AS post_content,
                            c.content AS comment_content
                     FROM t_like l
                     LEFT JOIN t_post p ON l.target_id = p.post_id AND l.target_type = 'post'
                     LEFT JOIN t_comment c ON l.target_id = c.comment_id AND l.target_type = 'comment'
                     WHERE l.user_id = %s AND l.is_deleted = 0
                     ORDER BY l.created_at DESC
                     LIMIT %s OFFSET %s"""
            items = self.db.execute_raw_sql(sql, (user_id, page_size, offset))

            # 计算总数
            count_sql = "SELECT COUNT(*) AS total FROM t_like WHERE user_id = %s AND is_deleted = 0"
            total_result = self.db.execute_raw_sql(count_sql, (user_id,))
            total = total_result[0]["total"] if total_result else 0

            data = {
                "items": self._format_liked_items(items),
                "total": total,
                "page": page,
                "page_size": page_size
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"查询失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    # ==================== 获取某目标点赞用户列表 ====================

    def get_post_liked_users(self, post_id: str, page: int = 1, page_size: int = 20) -> dict:
        """获取点赞某帖子的用户列表（分页）"""
        if not self.db.open_database():
            return {"success": False, "message": "数据库连接失败", "data": None}

        try:
            offset = (page - 1) * page_size
            sql = """SELECT u.user_id, u.nickname, u.avatarURL, l.created_at AS liked_time
                     FROM t_like l
                     JOIN t_user u ON l.user_id = u.user_id
                     WHERE l.target_id = %s AND l.target_type = 'post' AND l.is_deleted = 0
                     ORDER BY l.created_at DESC
                     LIMIT %s OFFSET %s"""
            users = self.db.execute_raw_sql(sql, (post_id, page_size, offset))

            count_sql = ("SELECT COUNT(*) AS total FROM t_like "
                         "WHERE target_id = %s AND target_type = 'post' AND is_deleted = 0")
            total_result = self.db.execute_raw_sql(count_sql, (post_id,))
            total = total_result[0]["total"] if total_result else 0

            data = {
                "users": users,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"查询失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    def get_comment_liked_users(self, comment_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取点赞某评论的用户列表（分页）"""
        if not self.db.open_database():
            return {"success": False, "message": "数据库连接失败", "data": None}

        try:
            offset = (page - 1) * page_size
            sql = """SELECT u.user_id, u.nickname, u.avatarURL, l.created_at AS liked_time
                     FROM t_like l
                     JOIN t_user u ON l.user_id = u.user_id
                     WHERE l.target_id = %s AND l.target_type = 'comment' AND l.is_deleted = 0
                     ORDER BY l.created_at DESC
                     LIMIT %s OFFSET %s"""
            users = self.db.execute_raw_sql(sql, (str(comment_id), page_size, offset))

            count_sql = ("SELECT COUNT(*) AS total FROM t_like "
                         "WHERE target_id = %s AND target_type = 'comment' AND is_deleted = 0")
            total_result = self.db.execute_raw_sql(count_sql, (str(comment_id),))
            total = total_result[0]["total"] if total_result else 0

            data = {
                "users": users,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            return {"success": True, "message": "成功", "data": data}
        except Exception as e:
            return {"success": False, "message": f"查询失败：{str(e)}", "data": None}
        finally:
            self.db.close_database()

    # ==================== 内部辅助方法 ====================

    def _format_liked_items(self, items: list) -> list:
        """格式化用户点赞列表"""
        if not items:
            return []
        formatted = []
        for item in items:
            if item["target_type"] == "post":
                target_summary = item.get("post_content", "")[:50] if item.get("post_content") else ""
            else:
                target_summary = item.get("comment_content", "")[:50] if item.get("comment_content") else ""
            formatted.append({
                "like_id": item["like_id"],
                "target_type": item["target_type"],
                "target_id": item["target_id"],
                "target_summary": target_summary,
                "created_at": item["created_at"].strftime("%Y-%m-%d %H:%M:%S") if item["created_at"] else None
            })
        return formatted
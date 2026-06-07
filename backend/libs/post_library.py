# ===== backend/libs/post_library.py =====
"""
帖子（社区动态）业务逻辑层
提供帖子增删查、点赞、评论等核心功能
依赖：utils/db_manager.py 中的 DatabaseManager 基类
"""

from datetime import datetime
from backend.utils.db_manager import DatabaseManager
from backend.utils.response import success_response, error_response
import uuid
import json
import requests
from backend.utils.ai_http_client import detect_species


class PostLibrary:
    """
    帖子业务逻辑库（组合模式）
    持有 DatabaseManager 实例，通过 self.db 操作数据库
    """

    def __init__(self):
        self.db = DatabaseManager()

    # ==================== 帖子增删查 ====================

    def create_post(self, user_id: str, content: str = "", image_urls: str = None) -> dict:
        """
        发布帖子
        AI图片内容审核：默认通过，若图片非猫狗则待审核
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            post_id = str(uuid.uuid4()).replace("-", "")[:32]
            now = datetime.now()

            # AI图片内容审核：默认通过，若图片非猫狗则待审核
            initial_status = 1
            if image_urls:
                try:
                    url_list = json.loads(image_urls)
                    if isinstance(url_list, list):
                        for url in url_list:
                            try:
                                resp = requests.get(url, timeout=5)
                                if resp.status_code == 200:
                                    result = detect_species(resp.content)
                                    if result.get("success") and result.get("category") not in ("cat", "dog"):
                                        initial_status = 0
                                        break
                            except Exception as e:
                                print(f"单张图片审核失败，继续下一张：{e}")
                                continue
                except json.JSONDecodeError:
                    self.db.close_database()
                    return error_response("image_urls 格式错误，必须是 JSON 数组字符串")
                except Exception as e:
                    print(f"AI图片审核失败，默认通过（不影响发布）：{e}")

            sql = """INSERT INTO t_post (post_id, user_id, content, image_urls,
                     like_count, comment_count, share_count, status, created_at)
                     VALUES (%s, %s, %s, %s, 0, 0, 0, %s, %s)"""
            self.db.execute_raw_sql(sql, (post_id, user_id, content, image_urls, initial_status, now))
            self.db.close_database()
            return success_response(
                "帖子发布成功",
                data={
                    "post_id": post_id,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            self.db.close_database()
            return error_response(f"发布帖子失败：{str(e)}")

    def delete_post(self, post_id: str, user_id: str) -> dict:
        """
        删除帖子（仅允许发帖人自己删除）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            sql_check = "SELECT user_id FROM t_post WHERE post_id = %s"
            result = self.db.execute_raw_sql(sql_check, (post_id,))
            if not result:
                self.db.close_database()
                return error_response("帖子不存在")
            if result[0]["user_id"] != user_id:
                self.db.close_database()
                return error_response("无权删除他人帖子")

            sql_del = "DELETE FROM t_post WHERE post_id = %s"
            self.db.execute_raw_sql(sql_del, (post_id,))
            self.db.close_database()
            return success_response("帖子已删除", data={"post_id": post_id})
        except Exception as e:
            self.db.close_database()
            return error_response(f"删除帖子失败：{str(e)}")

    def get_post_by_id(self, post_id: str, current_user_id: str = None) -> dict:
        """
        获取单条帖子详情（含发帖人信息、是否已点赞）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            sql = """SELECT p.*, u.nickname, u.avatarURL
                     FROM t_post p
                     JOIN t_user u ON p.user_id = u.user_id
                     WHERE p.post_id = %s"""
            result = self.db.execute_raw_sql(sql, (post_id,))
            if not result:
                self.db.close_database()
                return error_response("帖子不存在")

            post = result[0]
            liked = False
            if current_user_id:
                like_sql = """SELECT 1 FROM t_like
                              WHERE target_id = %s AND user_id = %s
                              AND target_type = 'post' AND is_deleted = 0
                              LIMIT 1"""
                like_result = self.db.execute_raw_sql(like_sql, (post_id, current_user_id))
                liked = len(like_result) > 0 if like_result else False

            data = {
                "post_id": post["post_id"],
                "user_id": post["user_id"],
                "nickname": post["nickname"],
                "avatar_url": post["avatarURL"],
                "content": post["content"],
                "image_urls": post["image_urls"],
                "like_count": post["like_count"],
                "comment_count": post["comment_count"],
                "share_count": post["share_count"],
                "status": post["status"],
                "created_at": post["created_at"].strftime("%Y-%m-%d %H:%M:%S") if post["created_at"] else None,
                "is_liked_by_current_user": liked
            }
            self.db.close_database()
            return success_response("成功", data=data)
        except Exception as e:
            self.db.close_database()
            return error_response(f"查询帖子详情失败：{str(e)}")

    def get_posts_by_user(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        查询指定用户发布的所有帖子（按时间倒序）
        :return: dict {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            offset = (page - 1) * page_size
            sql = """SELECT p.*, u.nickname, u.avatarURL
                     FROM t_post p
                     JOIN t_user u ON p.user_id = u.user_id
                     WHERE p.user_id = %s AND p.status = 1
                     ORDER BY p.created_at DESC
                     LIMIT %s OFFSET %s"""
            posts = self.db.execute_raw_sql(sql, (user_id, page_size, offset))
            count_sql = "SELECT COUNT(*) AS total FROM t_post WHERE user_id = %s AND status = 1"
            count_result = self.db.execute_raw_sql(count_sql, (user_id,))
            total = count_result[0]["total"] if count_result else 0

            has_more = (page * page_size) < total
            
            self.db.close_database()
            return success_response(
                "成功",
                data={
                    "posts": self._format_posts_list(posts),
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "has_more": has_more
                }
            )
        except Exception as e:
            self.db.close_database()
            return error_response(f"查询用户帖子失败：{str(e)}")

    def get_all_posts(self, page: int = 1, page_size: int = 20) -> dict:
        """
        获取所有已审核通过的帖子（按时间倒序）
        :return: dict {"success": bool, "message": str, "data": dict}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            offset = (page - 1) * page_size
            sql = """SELECT p.*, u.nickname, u.avatarURL
                     FROM t_post p
                     JOIN t_user u ON p.user_id = u.user_id
                     WHERE p.status = 1
                     ORDER BY p.created_at DESC
                     LIMIT %s OFFSET %s"""
            posts = self.db.execute_raw_sql(sql, (page_size, offset))
            count_sql = "SELECT COUNT(*) AS total FROM t_post WHERE status = 1"
            count_result = self.db.execute_raw_sql(count_sql)
            total = count_result[0]["total"] if count_result else 0

            has_more = (page * page_size) < total
            
            self.db.close_database()
            return success_response(
                "成功",
                data={
                    "posts": self._format_posts_list(posts),
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "has_more": has_more
                }
            )
        except Exception as e:
            self.db.close_database()
            return error_response(f"查询所有帖子失败：{str(e)}")

    # ==================== 帖子详情页（含评论） ====================

    def get_post_detail_with_comments(self, post_id: str, current_user_id: str = None) -> dict:
        """
        获取帖子详情页全部内容（帖子 + 所有评论 + 当前用户点赞状态）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        # 1. 先获取帖子详情（它自己会处理连接）
        post_result = self.get_post_by_id(post_id, current_user_id)
        if not post_result["success"]:
            return post_result

        # 2. 打开新连接获取评论
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            comment_sql = """SELECT c.*, u.nickname, u.avatarURL
                             FROM t_comment c
                             JOIN t_user u ON c.user_id = u.user_id
                             WHERE c.post_id = %s
                             ORDER BY c.created_at ASC"""
            comments = self.db.execute_raw_sql(comment_sql, (post_id,))

            comment_list = []
            if comments:
                for c in comments:
                    comment_list.append({
                        "comment_id": c["comment_id"],
                        "user_id": c["user_id"],
                        "nickname": c["nickname"],
                        "avatar_url": c["avatarURL"],
                        "content": c["content"],
                        "created_at": c["created_at"].strftime("%Y-%m-%d %H:%M:%S") if c["created_at"] else None
                    })

            self.db.close_database()

            post_result["data"]["comments"] = comment_list
            post_result["data"]["comment_count"] = len(comment_list)
            return post_result
        except Exception as e:
            self.db.close_database()
            return error_response(f"获取帖子详情页失败：{str(e)}")

    # ==================== 评论功能 ====================

    def add_comment(self, post_id: str, user_id: str, content: str) -> dict:
        """
        对帖子添加评论
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            check_sql = "SELECT 1 FROM t_post WHERE post_id = %s AND status = 1"
            if not self.db.execute_raw_sql(check_sql, (post_id,)):
                self.db.close_database()
                return error_response("帖子不存在或未通过审核")

            now = datetime.now()
            insert_sql = """INSERT INTO t_comment (post_id, user_id, content, created_at)
                            VALUES (%s, %s, %s, %s)"""
            self.db.execute_raw_sql(insert_sql, (post_id, user_id, content, now))
            update_sql = "UPDATE t_post SET comment_count = comment_count + 1 WHERE post_id = %s"
            self.db.execute_raw_sql(update_sql, (post_id,))
            comment_id = self._get_last_insert_id()
            self.db.close_database()

            return success_response(
                "评论成功",
                data={
                    "comment_id": comment_id,
                    "post_id": post_id,
                    "content": content,
                    "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            self.db.close_database()
            return error_response(f"评论失败：{str(e)}")

    def delete_comment(self, comment_id: int, user_id: str) -> dict:
        """
        删除评论（仅限评论作者或管理员）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            check_sql = "SELECT user_id, post_id FROM t_comment WHERE comment_id = %s"
            result = self.db.execute_raw_sql(check_sql, (comment_id,))
            if not result:
                self.db.close_database()
                return error_response("评论不存在")

            comment = result[0]
            if comment["user_id"] != user_id:
                self.db.close_database()
                return error_response("无权删除他人评论")

            del_sql = "DELETE FROM t_comment WHERE comment_id = %s"
            self.db.execute_raw_sql(del_sql, (comment_id,))
            update_sql = "UPDATE t_post SET comment_count = GREATEST(comment_count - 1, 0) WHERE post_id = %s"
            self.db.execute_raw_sql(update_sql, (comment["post_id"],))
            self.db.close_database()

            return success_response("评论已删除", data={"comment_id": comment_id})
        except Exception as e:
            self.db.close_database()
            return error_response(f"删除评论失败：{str(e)}")

    # ==================== 点赞功能 ====================

    def toggle_like_post(self, post_id: str, user_id: str) -> dict:
        """
        切换帖子点赞状态（已赞则取消，未赞则点赞）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            check_sql = "SELECT 1 FROM t_post WHERE post_id = %s AND status = 1"
            if not self.db.execute_raw_sql(check_sql, (post_id,)):
                self.db.close_database()
                return error_response("帖子不存在或不可见")

            # 查询帖子作者
            author_sql = "SELECT user_id FROM t_post WHERE post_id = %s"
            author_result = self.db.execute_raw_sql(author_sql, (post_id,))
            post_author_id = author_result[0]["user_id"] if author_result else None

            like_sql = """SELECT like_id FROM t_like
                          WHERE target_id = %s AND user_id = %s
                          AND target_type = 'post' AND is_deleted = 0"""
            existing = self.db.execute_raw_sql(like_sql, (post_id, user_id))

            if existing:
                # 取消点赞
                del_sql = """UPDATE t_like SET is_deleted = 1
                             WHERE target_id = %s AND user_id = %s AND target_type = 'post'"""
                self.db.execute_raw_sql(del_sql, (post_id, user_id))
                update_sql = "UPDATE t_post SET like_count = GREATEST(like_count - 1, 0) WHERE post_id = %s"
                self.db.execute_raw_sql(update_sql, (post_id,))
                if post_author_id:
                    self.db.execute_raw_sql(
                        "UPDATE t_user SET like_count = GREATEST(like_count - 1, 0) WHERE user_id = %s",
                        (post_author_id,)
                    )
                self.db.close_database()
                return success_response("取消点赞", data={"is_liked": False})
            else:
                # 点赞
                now = datetime.now()
                insert_sql = """INSERT INTO t_like (target_type, target_id, user_id, created_at)
                                VALUES ('post', %s, %s, %s)"""
                self.db.execute_raw_sql(insert_sql, (post_id, user_id, now))
                update_sql = "UPDATE t_post SET like_count = like_count + 1 WHERE post_id = %s"
                self.db.execute_raw_sql(update_sql, (post_id,))
                if post_author_id:
                    self.db.execute_raw_sql(
                        "UPDATE t_user SET like_count = like_count + 1 WHERE user_id = %s",
                        (post_author_id,)
                    )
                self.db.close_database()
                return success_response("点赞成功", data={"is_liked": True})
        except Exception as e:
            self.db.close_database()
            return error_response(f"点赞操作失败：{str(e)}")

    def toggle_like_comment(self, comment_id: int, user_id: str) -> dict:
        """
        切换评论点赞状态（已赞则取消，未赞则点赞）
        :return: dict {"success": bool, "message": str, "data": dict or None}
        """
        if not self.db.open_database():
            return error_response("数据库连接失败")

        try:
            check_sql = """SELECT c.user_id, p.status
                           FROM t_comment c
                           JOIN t_post p ON c.post_id = p.post_id
                           WHERE c.comment_id = %s"""
            check_result = self.db.execute_raw_sql(check_sql, (comment_id,))
            if not check_result:
                self.db.close_database()
                return error_response("评论不存在或所属帖子不可见")
            if check_result[0]["status"] != 1:
                self.db.close_database()
                return error_response("评论不存在或所属帖子不可见")

            comment_author_id = check_result[0]["user_id"]

            like_sql = """SELECT like_id FROM t_like
                          WHERE target_id = %s AND user_id = %s
                          AND target_type = 'comment' AND is_deleted = 0"""
            existing = self.db.execute_raw_sql(like_sql, (str(comment_id), user_id))

            if existing:
                # 取消点赞
                del_sql = """UPDATE t_like SET is_deleted = 1
                             WHERE target_id = %s AND user_id = %s AND target_type = 'comment'"""
                self.db.execute_raw_sql(del_sql, (str(comment_id), user_id))
                self.db.execute_raw_sql(
                    "UPDATE t_comment SET like_count = GREATEST(like_count - 1, 0) WHERE comment_id = %s",
                    (comment_id,)
                )
                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = GREATEST(like_count - 1, 0) WHERE user_id = %s",
                    (comment_author_id,)
                )
                self.db.close_database()
                return success_response("取消点赞", data={"is_liked": False})
            else:
                # 点赞
                now = datetime.now()
                insert_sql = """INSERT INTO t_like (target_type, target_id, user_id, created_at)
                                VALUES ('comment', %s, %s, %s)"""
                self.db.execute_raw_sql(insert_sql, (str(comment_id), user_id, now))
                self.db.execute_raw_sql(
                    "UPDATE t_comment SET like_count = like_count + 1 WHERE comment_id = %s",
                    (comment_id,)
                )
                self.db.execute_raw_sql(
                    "UPDATE t_user SET like_count = like_count + 1 WHERE user_id = %s",
                    (comment_author_id,)
                )
                self.db.close_database()
                return success_response("点赞成功", data={"is_liked": True})
        except Exception as e:
            self.db.close_database()
            return error_response(f"点赞评论失败：{str(e)}")

    # ==================== 内部辅助方法 ====================

    def _format_posts_list(self, posts: list) -> list:
        """格式化帖子列表（统一时间、字段名）"""
        if not posts:
            return []
        formatted = []
        for p in posts:
            formatted.append({
                "post_id": p["post_id"],
                "user_id": p["user_id"],
                "nickname": p["nickname"],
                "avatar_url": p["avatarURL"],
                "content": p["content"],
                "image_urls": p["image_urls"],
                "like_count": p["like_count"],
                "comment_count": p["comment_count"],
                "share_count": p["share_count"],
                "status": p["status"],
                "created_at": p["created_at"].strftime("%Y-%m-%d %H:%M:%S") if p["created_at"] else None
            })
        return formatted

    def _get_last_insert_id(self) -> int:
        """获取最后一次 INSERT 操作的自增ID"""
        result = self.db.execute_raw_sql("SELECT LAST_INSERT_ID() AS id")
        return result[0]["id"] if result else 0
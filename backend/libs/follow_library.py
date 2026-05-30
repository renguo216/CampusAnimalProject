from datetime import datetime
from backend.utils.db_manager import DatabaseManager


class FollowLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    # ==================== 核心操作 ====================

    def follow_user(self, from_user_id: str, to_user_id: str) -> dict:
        """
        关注用户
        """
        try:
            if not from_user_id or not to_user_id:
                return {"success": False, "message": "参数不能为空", "data": None}
            if from_user_id == to_user_id:
                return {"success": False, "message": "不能关注自己", "data": None}

            # 用户有效性检查（事务外）
            from backend.libs.user_library import UserLibrary
            user_lib = UserLibrary()
            if not user_lib.verify_user_validity(from_user_id):
                return {"success": False, "message": "关注者不存在或已注销", "data": None}
            if not user_lib.verify_user_validity(to_user_id):
                return {"success": False, "message": "被关注者不存在或已注销", "data": None}

            # 检查是否已关注
            status_result = self.check_follow_status(from_user_id, to_user_id)
            if not status_result["success"]:
                return status_result
            if status_result["data"]["is_following"]:
                return {"success": True, "message": "已关注该用户，无需重复关注", "data": None}

            # 开启事务
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            if not self.db.begin_transaction():
                self.db.close_database()
                return {"success": False, "message": "事务开启失败", "data": None}

            try:
                now = datetime.now()

                # 插入关注记录
                follow_data = {
                    'from_user_id': from_user_id,
                    'to_user_id': to_user_id,
                    'created_at': now
                }
                if not self.db.insert_tx('t_follow', follow_data):
                    raise Exception("插入关注记录失败")

                follow_id = self.db.get_last_insert_id()
                if not follow_id:
                    raise Exception("获取关注ID失败")

                # 原子更新关注数（不先读后写）
                self.db.execute_raw_sql(
                    "UPDATE t_user SET following_count = following_count + 1 WHERE user_id = %s",
                    (from_user_id,)
                )
                self.db.execute_raw_sql(
                    "UPDATE t_user SET follower_count = follower_count + 1 WHERE user_id = %s",
                    (to_user_id,)
                )

                self.db.commit()
                return {
                    "success": True,
                    "message": "关注成功",
                    "data": {
                        "follow_id": follow_id,
                        "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            except Exception as e:
                self.db.rollback()
                return {"success": False, "message": f"关注失败：{str(e)}", "data": None}
            finally:
                self.db.close_database()
        except Exception as e:
            return {"success": False, "message": f"关注异常：{str(e)}", "data": None}

    def unfollow_user(self, from_user_id: str, to_user_id: str) -> dict:
        """
        取消关注用户
        """
        try:
            if not from_user_id or not to_user_id:
                return {"success": False, "message": "参数不能为空", "data": None}
            if from_user_id == to_user_id:
                return {"success": False, "message": "不能对自己操作", "data": None}

            from backend.libs.user_library import UserLibrary
            user_lib = UserLibrary()
            if not user_lib.verify_user_validity(from_user_id):
                return {"success": False, "message": "关注者不存在或已注销", "data": None}
            if not user_lib.verify_user_validity(to_user_id):
                return {"success": False, "message": "被关注者不存在或已注销", "data": None}

            status_result = self.check_follow_status(from_user_id, to_user_id)
            if not status_result["success"]:
                return status_result
            if not status_result["data"]["is_following"]:
                return {"success": False, "message": "尚未关注该用户，无法取消", "data": None}

            # 查询 follow_id（事务外）
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            follow_record = self.db.execute_raw_sql(
                "SELECT follow_id FROM t_follow WHERE from_user_id = %s AND to_user_id = %s LIMIT 1",
                (from_user_id, to_user_id)
            )
            if not follow_record:
                return {"success": False, "message": "未找到关注记录", "data": None}
            follow_id = follow_record[0]["follow_id"]

            # 开启事务
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}
            if not self.db.begin_transaction():
                self.db.close_database()
                return {"success": False, "message": "事务开启失败", "data": None}

            try:
                # 删除关注记录
                if not self.db.delete('t_follow', 'follow_id', follow_id):
                    raise Exception("删除关注记录失败")

                # 原子更新关注数
                self.db.execute_raw_sql(
                    "UPDATE t_user SET following_count = GREATEST(following_count - 1, 0) WHERE user_id = %s",
                    (from_user_id,)
                )
                self.db.execute_raw_sql(
                    "UPDATE t_user SET follower_count = GREATEST(follower_count - 1, 0) WHERE user_id = %s",
                    (to_user_id,)
                )

                self.db.commit()
                return {
                    "success": True,
                    "message": "取消关注成功",
                    "data": {"unfollowed": True}
                }
            except Exception as e:
                self.db.rollback()
                return {"success": False, "message": f"取消关注失败：{str(e)}", "data": None}
            finally:
                self.db.close_database()
        except Exception as e:
            return {"success": False, "message": f"取消关注异常：{str(e)}", "data": None}

    def check_follow_status(self, from_user_id: str, to_user_id: str) -> dict:
        """
        检查用户是否已关注另一个用户
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}

            result = self.db.execute_raw_sql(
                "SELECT 1 FROM t_follow WHERE from_user_id = %s AND to_user_id = %s LIMIT 1",
                (from_user_id, to_user_id)
            )
            is_following = bool(result)

            self.db.close_database()
            return {
                "success": True,
                "message": "成功",
                "data": {"is_following": is_following}
            }
        except Exception as e:
            return {"success": False, "message": f"查询关注状态失败：{str(e)}", "data": None}
        finally:
            if self.db.connection:
                self.db.close_database()

    # ==================== 列表查询 ====================

    def get_following_list(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        获取用户的关注列表（含互相关注标记）
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}

            offset = (page - 1) * page_size

            # 查询关注列表，并标记是否互相关注
            sql = """
                SELECT 
                    f.follow_id, f.created_at AS follow_time,
                    u.user_id, u.nickname, u.avatarURL, 
                    u.follower_count, u.following_count, u.like_count, u.is_active,
                    EXISTS(
                        SELECT 1 FROM t_follow f2 
                        WHERE f2.from_user_id = f.to_user_id AND f2.to_user_id = f.from_user_id
                    ) AS is_mutual
                FROM t_follow f
                JOIN t_user u ON f.to_user_id = u.user_id
                WHERE f.from_user_id = %s
                ORDER BY f.created_at DESC
                LIMIT %s OFFSET %s
            """
            records = self.db.execute_raw_sql(sql, (user_id, page_size, offset))

            count_sql = "SELECT COUNT(*) AS total FROM t_follow WHERE from_user_id = %s"
            count_result = self.db.execute_raw_sql(count_sql, (user_id,))
            total = count_result[0]["total"] if count_result else 0

            self.db.close_database()

            following_list = []
            if records:
                for r in records:
                    following_list.append({
                        "follow_id": r["follow_id"],
                        "follow_time": r["follow_time"].strftime("%Y-%m-%d %H:%M:%S") if r["follow_time"] else None,
                        "user_id": r["user_id"],
                        "nickname": r["nickname"],
                        "avatar_url": r["avatarURL"],
                        "follower_count": r["follower_count"],
                        "following_count": r["following_count"],
                        "like_count": r["like_count"],
                        "is_active": r["is_active"],
                        "is_mutual": bool(r.get("is_mutual", 0))
                    })

            return {
                "success": True,
                "message": "成功",
                "data": {
                    "records": following_list,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            }
        except Exception as e:
            return {"success": False, "message": f"查询关注列表失败：{str(e)}", "data": None}

    def get_follower_list(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """
        获取用户的粉丝列表（含"我是否已关注"标记）
        """
        try:
            if not self.db.open_database():
                return {"success": False, "message": "数据库连接失败", "data": None}

            offset = (page - 1) * page_size

            sql = """
                SELECT 
                    f.follow_id, f.created_at AS follow_time,
                    u.user_id, u.nickname, u.avatarURL,
                    u.follower_count, u.following_count, u.like_count, u.is_active,
                    EXISTS(
                        SELECT 1 FROM t_follow f2 
                        WHERE f2.from_user_id = %s AND f2.to_user_id = f.from_user_id
                    ) AS is_following_back
                FROM t_follow f
                JOIN t_user u ON f.from_user_id = u.user_id
                WHERE f.to_user_id = %s
                ORDER BY f.created_at DESC
                LIMIT %s OFFSET %s
            """
            records = self.db.execute_raw_sql(sql, (user_id, user_id, page_size, offset))

            count_sql = "SELECT COUNT(*) AS total FROM t_follow WHERE to_user_id = %s"
            count_result = self.db.execute_raw_sql(count_sql, (user_id,))
            total = count_result[0]["total"] if count_result else 0

            self.db.close_database()

            follower_list = []
            if records:
                for r in records:
                    follower_list.append({
                        "follow_id": r["follow_id"],
                        "follow_time": r["follow_time"].strftime("%Y-%m-%d %H:%M:%S") if r["follow_time"] else None,
                        "user_id": r["user_id"],
                        "nickname": r["nickname"],
                        "avatar_url": r["avatarURL"],
                        "follower_count": r["follower_count"],
                        "following_count": r["following_count"],
                        "like_count": r["like_count"],
                        "is_active": r["is_active"],
                        "is_following_back": bool(r.get("is_following_back", 0))
                    })

            return {
                "success": True,
                "message": "成功",
                "data": {
                    "records": follower_list,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            }
        except Exception as e:
            return {"success": False, "message": f"查询粉丝列表失败：{str(e)}", "data": None}

    # ==================== 数量统计 ====================

    def get_following_count(self, user_id: str) -> dict:
        try:
            from backend.libs.user_library import UserLibrary
            user_lib = UserLibrary()
            user_profile = user_lib.get_user_profile(user_id)
            if not user_profile:
                return {"success": False, "message": "用户不存在", "data": None}
            return {
                "success": True,
                "message": "成功",
                "data": {"following_count": user_profile["following_count"]}
            }
        except Exception as e:
            return {"success": False, "message": f"查询关注数量失败：{str(e)}", "data": None}

    def get_follower_count(self, user_id: str) -> dict:
        try:
            from backend.libs.user_library import UserLibrary
            user_lib = UserLibrary()
            user_profile = user_lib.get_user_profile(user_id)
            if not user_profile:
                return {"success": False, "message": "用户不存在", "data": None}
            return {
                "success": True,
                "message": "成功",
                "data": {"follower_count": user_profile["follower_count"]}
            }
        except Exception as e:
            return {"success": False, "message": f"查询粉丝数量失败：{str(e)}", "data": None}
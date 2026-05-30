# ===== backend/tests/test_like_library.py =====
"""
测试 LikeLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_like_library
"""
from backend.libs.like_library import LikeLibrary
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    like_lib = LikeLibrary()
    user_lib = UserLibrary()
    db = like_lib.db

    # 测试账号
    user_a = f"test_user_{uuid.uuid4().hex[:8]}"  # 点赞者
    user_b = f"test_user_{uuid.uuid4().hex[:8]}"  # 帖子作者
    user_c = f"test_user_{uuid.uuid4().hex[:8]}"  # 评论作者
    post_id = f"test_post_{uuid.uuid4().hex[:8]}"
    fake_post_id = f"test_post_{uuid.uuid4().hex[:8]}"
    fake_comment_id = 99999999

    # ======== 清理旧数据 & 注册测试用户 ========
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_like WHERE user_id LIKE 'test_user_%'")
        db.execute_raw_sql("DELETE FROM t_comment WHERE user_id LIKE 'test_user_%' OR post_id LIKE 'test_post_%'")
        db.execute_raw_sql("DELETE FROM t_post WHERE user_id LIKE 'test_user_%' OR post_id LIKE 'test_post_%'")
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_user_%'")
        db.close_database()
    else:
        print("[FAIL] 数据库连接失败，测试终止")
        return

    for uid in [user_a, user_b, user_c]:
        user_lib.delete_user(uid)
        if not user_lib.register_user(uid, f"nick_{uid}"):
            print(f"[FAIL] 注册用户 {uid} 失败，测试终止")
            return

    # 插入测试帖子（B发的，status=1）和评论（C发的）
    if db.open_database():
        db.execute_raw_sql(
            "INSERT INTO t_post (post_id, user_id, content, status, created_at) VALUES (%s, %s, %s, 1, NOW())",
            (post_id, user_b, "测试帖子内容")
        )
        db.execute_raw_sql(
            "INSERT INTO t_comment (post_id, user_id, content, created_at) VALUES (%s, %s, %s, NOW())",
            (post_id, user_c, "测试评论内容")
        )
        comment_id = db.get_last_insert_id()
        db.close_database()
        print(f"已创建测试帖子={post_id}, 评论ID={comment_id}")
    else:
        print("[FAIL] 数据库连接失败，测试终止")
        return

    if not comment_id:
        print("[FAIL] 获取评论ID失败，测试终止")
        return

    print("\n" + "=" * 50 + "\n  开始测试 LikeLibrary\n" + "=" * 50)

    # ========== 1. 帖子点赞/取消点赞 ==========
    print("\n1. 测试帖子点赞 (toggle_like_post)...")

    # 1.1 点赞
    result = like_lib.toggle_like_post(post_id, user_a)
    if result["success"] and result["data"].get("is_liked") is True:
        log_pass("A点赞B的帖子", "点赞成功 is_liked=True")
    else:
        log_fail("A点赞B的帖子", f"失败: {result}")

    # 1.2 再次点赞 → 取消
    result = like_lib.toggle_like_post(post_id, user_a)
    if result["success"] and result["data"].get("is_liked") is False:
        log_pass("A再次点赞 → 取消", "取消点赞 is_liked=False")
    else:
        log_fail("A再次点赞 → 取消", f"失败: {result}")

    # 1.3 第三次点赞 → 再次点赞
    result = like_lib.toggle_like_post(post_id, user_a)
    if result["success"] and result["data"].get("is_liked") is True:
        log_pass("A第三次点赞", "再次点赞成功 is_liked=True")
    else:
        log_fail("A第三次点赞", f"失败: {result}")

    # 1.4 无效帖子
    result = like_lib.toggle_like_post(fake_post_id, user_a)
    if not result["success"] and "帖子不存在" in result["message"]:
        log_pass("点赞无效帖子", "返回帖子不存在")
    else:
        log_fail("点赞无效帖子", f"结果异常: {result}")

    # ========== 2. 评论点赞/取消点赞 ==========
    print("\n2. 测试评论点赞 (toggle_like_comment)...")

    # 2.1 点赞评论
    result = like_lib.toggle_like_comment(comment_id, user_a)
    if result["success"] and result["data"].get("is_liked") is True:
        log_pass("A点赞C的评论", "点赞成功 is_liked=True")
    else:
        log_fail("A点赞C的评论", f"失败: {result}")

    # 2.2 再次点赞 → 取消
    result = like_lib.toggle_like_comment(comment_id, user_a)
    if result["success"] and result["data"].get("is_liked") is False:
        log_pass("A再次点赞评论 → 取消", "取消点赞 is_liked=False")
    else:
        log_fail("A再次点赞评论 → 取消", f"失败: {result}")

    # 2.3 无效评论
    result = like_lib.toggle_like_comment(fake_comment_id, user_a)
    if not result["success"] and "评论不存在" in result["message"]:
        log_pass("点赞无效评论", "返回评论不存在")
    else:
        log_fail("点赞无效评论", f"结果异常: {result}")

    # ========== 3. 查询帖子点赞数 ==========
    print("\n3. 测试查询帖子点赞数 (get_post_like_count)...")

    # 此时帖子处于点赞状态（1.3），count=1
    result = like_lib.get_post_like_count(post_id)
    if result["success"] and result["data"]["count"] == 1:
        log_pass("帖子点赞数", "count=1")
    else:
        log_fail("帖子点赞数", f"结果异常: {result}")

    # 取消后查询
    like_lib.toggle_like_post(post_id, user_a)
    result = like_lib.get_post_like_count(post_id)
    if result["success"] and result["data"]["count"] == 0:
        log_pass("取消后帖子点赞数", "count=0")
    else:
        log_fail("取消后帖子点赞数", f"结果异常: {result}")

    # ========== 4. 查询评论点赞数 ==========
    print("\n4. 测试查询评论点赞数 (get_comment_like_count)...")

    # 此时评论处于取消状态（2.2），count=0
    result = like_lib.get_comment_like_count(comment_id)
    if result["success"] and result["data"]["count"] == 0:
        log_pass("评论点赞数", "count=0")
    else:
        log_fail("评论点赞数", f"结果异常: {result}")

    # 点赞后查询
    like_lib.toggle_like_comment(comment_id, user_a)
    result = like_lib.get_comment_like_count(comment_id)
    if result["success"] and result["data"]["count"] == 1:
        log_pass("点赞后评论点赞数", "count=1")
    else:
        log_fail("点赞后评论点赞数", f"结果异常: {result}")

    # ========== 5. 检查是否已点赞 ==========
    print("\n5. 测试检查点赞状态...")

    # 5.1 帖子
    like_lib.toggle_like_post(post_id, user_a)  # 确保点赞
    is_liked = like_lib.check_user_liked_post(user_a, post_id)
    if is_liked is True:
        log_pass("A是否点赞帖子", "True")
    else:
        log_fail("A是否点赞帖子", f"结果={is_liked}")

    like_lib.toggle_like_post(post_id, user_a)  # 取消
    is_liked = like_lib.check_user_liked_post(user_a, post_id)
    if is_liked is False:
        log_pass("A取消后是否点赞帖子", "False")
    else:
        log_fail("A取消后是否点赞帖子", f"结果={is_liked}")

    # 5.2 评论
    is_liked = like_lib.check_user_liked_comment(user_a, comment_id)
    if is_liked is True:
        log_pass("A是否点赞评论", "True")
    else:
        log_fail("A是否点赞评论", f"结果={is_liked}")

    like_lib.toggle_like_comment(comment_id, user_a)  # 取消
    is_liked = like_lib.check_user_liked_comment(user_a, comment_id)
    if is_liked is False:
        log_pass("A取消后是否点赞评论", "False")
    else:
        log_fail("A取消后是否点赞评论", f"结果={is_liked}")

    # ========== 6. 用户点赞列表 ==========
    print("\n6. 测试用户点赞列表 (get_user_liked_list)...")

    # 重新点赞帖子和评论，确保列表有数据
    like_lib.toggle_like_post(post_id, user_a)
    like_lib.toggle_like_comment(comment_id, user_a)

    result = like_lib.get_user_liked_list(user_a, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("A的点赞列表", f"total={result['data']['total']}")
        types = [i["target_type"] for i in result["data"]["items"]]
        if "post" in types and "comment" in types:
            log_pass("点赞列表类型", "包含 post 和 comment")
        else:
            log_fail("点赞列表类型", f"types={types}")
    else:
        log_fail("A的点赞列表", f"结果异常: {result}")

    # 分页
    result = like_lib.get_user_liked_list(user_a, page=1, page_size=1)
    if result["success"] and len(result["data"]["items"]) == 1:
        log_pass("点赞列表分页 limit=1", "返回1条")
    else:
        log_fail("点赞列表分页 limit=1", f"返回{len(result['data']['items'])}条")

    # ========== 7. 帖子点赞用户列表 ==========
    print("\n7. 测试帖子点赞用户列表 (get_post_liked_users)...")

    result = like_lib.get_post_liked_users(post_id, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("帖子点赞用户", f"total={result['data']['total']}")
        if any(u["user_id"] == user_a for u in result["data"]["users"]):
            log_pass("帖子点赞用户包含A", "是")
        else:
            log_fail("帖子点赞用户包含A", "否")
    else:
        log_fail("帖子点赞用户", f"结果异常: {result}")

    result = like_lib.get_post_liked_users(post_id, page=1, page_size=1)
    if result["success"] and len(result["data"]["users"]) == 1:
        log_pass("帖子点赞用户分页 limit=1", "返回1条")
    else:
        log_fail("帖子点赞用户分页 limit=1", f"返回{len(result['data']['users'])}条")

    # ========== 8. 评论点赞用户列表 ==========
    print("\n8. 测试评论点赞用户列表 (get_comment_liked_users)...")

    result = like_lib.get_comment_liked_users(comment_id, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("评论点赞用户", f"total={result['data']['total']}")
        if any(u["user_id"] == user_a for u in result["data"]["users"]):
            log_pass("评论点赞用户包含A", "是")
        else:
            log_fail("评论点赞用户包含A", "否")
    else:
        log_fail("评论点赞用户", f"结果异常: {result}")

    result = like_lib.get_comment_liked_users(comment_id, page=1, page_size=1)
    if result["success"] and len(result["data"]["users"]) == 1:
        log_pass("评论点赞用户分页 limit=1", "返回1条")
    else:
        log_fail("评论点赞用户分页 limit=1", f"返回{len(result['data']['users'])}条")

    # ========== 9. 清理 ==========
    print("\n9. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_like WHERE user_id IN (%s, %s, %s)", (user_a, user_b, user_c))
        db.execute_raw_sql("DELETE FROM t_comment WHERE post_id = %s OR user_id IN (%s, %s, %s)", (post_id, user_a, user_b, user_c))
        db.execute_raw_sql("DELETE FROM t_post WHERE post_id = %s OR user_id IN (%s, %s, %s)", (post_id, user_a, user_b, user_c))
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id IN (%s, %s, %s)", (user_a, user_b, user_c))
        db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
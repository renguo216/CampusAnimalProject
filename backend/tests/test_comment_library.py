# ===== backend/tests/test_comment_library.py =====
"""
测试 CommentLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_comment_library
"""
from backend.libs.comment_library import CommentLibrary
from backend.libs.post_library import PostLibrary
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    comment_lib = CommentLibrary()
    post_lib = PostLibrary()
    user_lib = UserLibrary()

    # ======== 清理旧测试数据 ========
    if comment_lib.db.open_database():
        # 删除所有测试评论（关联的点赞会级联删除）
        comment_lib.db.execute_raw_sql("DELETE FROM t_comment WHERE user_id LIKE 'test_comment_user_%'")
        # 删除测试帖子
        comment_lib.db.execute_raw_sql("DELETE FROM t_post WHERE user_id LIKE 'test_comment_user_%'")
        # 删除测试用户
        comment_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_comment_user_%'")
        comment_lib.db.close_database()
        print("已清理旧测试数据")
    # =================================

    # ======== 准备测试数据 ========
    test_user1_id = f"test_comment_user_{uuid.uuid4().hex[:6]}"
    test_user2_id = f"test_comment_user_{uuid.uuid4().hex[:6]}"
    test_admin_id = f"test_comment_user_{uuid.uuid4().hex[:6]}"
    test_nickname1 = "评论人A"
    test_nickname2 = "评论人B"
    test_admin_nickname = "管理员"

    print("\n" + "=" * 50 + "\n  开始测试 CommentLibrary\n" + "=" * 50)

    # 0. 准备测试用户
    print("\n0. 准备测试用户...")
    user_lib.register_user(test_user1_id, test_nickname1, role=1)
    user_lib.register_user(test_user2_id, test_nickname2, role=1)
    user_lib.register_user(test_admin_id, test_admin_nickname, role=3)  # 管理员
    log_pass("注册测试用户", f"user1={test_user1_id}, user2={test_user2_id}, admin={test_admin_id}")

    # 准备测试帖子
    post_result = post_lib.create_post(test_user1_id, "测试帖子内容")
    test_post_id = post_result["data"]["post_id"] if post_result["success"] else None
    if not test_post_id:
        print("错误：帖子创建失败，测试终止")
        return
    log_pass("创建测试帖子", f"post_id={test_post_id}")

    # ========== 1. 创建评论 ==========
    print("\n1. 测试创建评论 (create_comment)...")
    # 1.1 正常创建评论
    content1 = "好可爱的猫！"
    comment1 = comment_lib.create_comment(test_post_id, test_user2_id, content1)
    if comment1 and comment1.comment_id:
        log_pass(f"用户2对帖子发表评论，content='{content1}'", f"comment_id={comment1.comment_id}")
        test_comment_id = comment1.comment_id
    else:
        log_fail("用户2对帖子发表评论", "返回 False")
        test_comment_id = None

    # 1.2 创建楼中楼回复
    reply_content = "真的吗？在哪里看到的？"
    reply = comment_lib.reply_comment(test_post_id, test_user1_id, reply_content, test_comment_id)
    if reply and reply.comment_id:
        log_pass(f"用户1回复评论，parent_comment_id={test_comment_id}", f"reply_comment_id={reply.comment_id}")
        test_reply_id = reply.comment_id
    else:
        log_fail("用户1回复评论", "返回 False")
        test_reply_id = None

    # 1.3 失败场景：帖子不存在
    invalid_comment = comment_lib.create_comment("non_exist_post", test_user2_id, "测试")
    if not invalid_comment:
        log_pass("对不存在的帖子发表评论", "返回 False")
    else:
        log_fail("对不存在的帖子发表评论", f"返回 {invalid_comment}，预期 False")

    # 1.4 失败场景：父评论不属于同一帖子
    wrong_parent = comment_lib.create_comment(test_post_id, test_user2_id, "错误回复", parent_comment_id=999999)
    if not wrong_parent:
        log_pass("父评论不属于当前帖子", "返回 False")
    else:
        log_fail("父评论不属于当前帖子", f"返回 {wrong_parent}，预期 False")

    # ========== 2. 查询评论 ==========
    print("\n2. 测试查询评论 (get_comment_by_id)...")
    # 2.1 查询存在的评论
    comment = comment_lib.get_comment_by_id(test_comment_id)
    if comment and comment.comment_id == test_comment_id:
        log_pass(f"按ID查询评论，comment_id={test_comment_id}", f"content='{comment.content}'")
    else:
        log_fail(f"按ID查询评论，comment_id={test_comment_id}", f"返回 {comment}，预期非None")

    # 2.2 查询不存在的评论
    none_comment = comment_lib.get_comment_by_id(999999)
    if none_comment is None:
        log_pass("查询不存在的评论", "返回 None")
    else:
        log_fail("查询不存在的评论", f"返回 {none_comment}，预期 None")

    # ========== 3. 获取帖子评论列表 ==========
    print("\n3. 测试获取帖子评论列表 (get_post_comments)...")
    # 3.1 正常获取（应包含2条评论：一条顶级评论，一条回复）
    comments = comment_lib.get_post_comments(test_post_id, page=1, page_size=10)
    if len(comments) >= 2:
        log_pass(f"获取帖子评论列表，post_id={test_post_id}", f"返回 {len(comments)} 条评论")
    else:
        log_fail(f"获取帖子评论列表，post_id={test_post_id}", f"返回 {len(comments)} 条评论，预期 >=2")

    # 3.2 分页测试
    page1 = comment_lib.get_post_comments(test_post_id, page=1, page_size=1)
    if len(page1) == 1:
        log_pass("分页获取第1页，page_size=1", f"返回 {len(page1)} 条评论")
    else:
        log_fail("分页获取第1页，page_size=1", f"返回 {len(page1)} 条，预期1条")

    # ========== 4. 获取评论回复列表 ==========
    print("\n4. 测试获取评论回复列表 (get_comment_replies)...")
    replies = comment_lib.get_comment_replies(test_comment_id)
    if len(replies) >= 1:
        log_pass(f"获取父评论 {test_comment_id} 的回复", f"返回 {len(replies)} 条回复")
    else:
        log_fail(f"获取父评论 {test_comment_id} 的回复", f"返回 {len(replies)} 条回复，预期 >=1")

    # ========== 5. 获取用户评论历史 ==========
    print("\n5. 测试获取用户评论历史 (get_user_comments)...")
    user_comments = comment_lib.get_user_comments(test_user2_id, page=1, page_size=10)
    if len(user_comments) >= 1:
        log_pass(f"获取用户 {test_user2_id} 的评论历史", f"返回 {len(user_comments)} 条记录")
    else:
        log_fail(f"获取用户 {test_user2_id} 的评论历史", f"返回 {len(user_comments)} 条，预期 >=1")

    # ========== 6. 切换评论点赞 ==========
    print("\n6. 测试切换评论点赞 (toggle_comment_like)...")
    # 6.1 点赞（当前未点赞）
    like_result = comment_lib.toggle_comment_like(test_comment_id, test_user1_id)
    if like_result is True:
        log_pass("用户1点赞评论", f"返回 {like_result}（True）")
    else:
        log_fail("用户1点赞评论", f"返回 {like_result}，预期 True")

    # 6.2 取消点赞（已点赞）
    unlike_result = comment_lib.toggle_comment_like(test_comment_id, test_user1_id)
    if unlike_result is False:
        log_pass("用户1取消点赞", f"返回 {unlike_result}（False）")
    else:
        log_fail("用户1取消点赞", f"返回 {unlike_result}，预期 False")

    # 6.3 对不存在的评论点赞
    none_like = comment_lib.toggle_comment_like(999999, test_user1_id)
    if none_like is None:
        log_pass("对不存在的评论点赞", f"返回 None")
    else:
        log_fail("对不存在的评论点赞", f"返回 {none_like}，预期 None")

    # ========== 7. 删除评论（普通用户） ==========
    print("\n7. 测试删除评论 (delete_comment)...")
    # 7.1 删除自己的评论
    if test_comment_id:
        del_result = comment_lib.delete_comment(test_comment_id, test_user2_id)
        if del_result:
            log_pass(f"用户2删除自己的评论", f"返回 True")
        else:
            log_fail(f"用户2删除自己的评论", f"返回 False")

    # 7.2 删除别人的评论（应失败）
    if test_reply_id:
        del_other = comment_lib.delete_comment(test_reply_id, test_user2_id)
        if not del_other:
            log_pass(f"用户2删除用户1的评论", f"返回 False")
        else:
            log_fail(f"用户2删除用户1的评论", f"返回 True，预期 False")

    # 7.3 删除不存在的评论
    del_none = comment_lib.delete_comment(999999, test_user1_id)
    if not del_none:
        log_pass("删除不存在的评论", "返回 False")
    else:
        log_fail("删除不存在的评论", "返回 True，预期 False")

    # ========== 8. 测试管理员删除评论 ==========
    print("\n8. 测试管理员删除评论 (admin_delete_comment)...")

    # --- 修复方案：创建一个全新的临时评论用于此测试，避免被之前的测试级联删除 ---
    temp_comment = comment_lib.create_comment(test_post_id, test_user1_id, "这是管理员要删除的临时评论")
    if temp_comment:
        temp_comment_id = temp_comment.comment_id
    else:
        log_fail("创建用于管理员删除测试的临时评论失败", "返回 False")
        temp_comment_id = None

    # 8.1 管理员正常删除
    if temp_comment_id:
        admin_del_result = comment_lib.admin_delete_comment(temp_comment_id, test_admin_id)
        if admin_del_result:
            log_pass(f"管理员删除评论 {temp_comment_id}", f"返回 True")
        else:
            log_fail(f"管理员删除评论 {temp_comment_id}", f"返回 False，预期 True")
    # ----------------------------------------------------------------

    # 8.2 管理员删除不存在的评论
    admin_del_none = comment_lib.admin_delete_comment(999999, test_admin_id)
    if not admin_del_none:
        log_pass("管理员删除不存在的评论", "返回 False")
    else:
        log_fail("管理员删除不存在的评论", "返回 True，预期 False")

    # 8.3 非管理员使用管理员删除接口（应失败）
    non_admin_del = comment_lib.admin_delete_comment(test_reply_id, test_user1_id)
    if not non_admin_del:
        log_pass("非管理员调用管理员删除接口", "返回 False")
    else:
        log_fail("非管理员调用管理员删除接口", "返回 True，预期 False")
    
    # ========== 9. 清理测试数据 ==========
    print("\n9. 清理测试数据...")
    if comment_lib.db.open_database():
        # 清理评论（外键级联删除点赞）
        comment_lib.db.execute_raw_sql("DELETE FROM t_comment WHERE user_id LIKE 'test_comment_user_%'")
        comment_lib.db.execute_raw_sql("DELETE FROM t_post WHERE user_id LIKE 'test_comment_user_%'")
        comment_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_comment_user_%'")
        comment_lib.db.close_database()
        log_pass("清理测试数据", f"删除所有 test_comment_user_* 数据")
    else:
        log_fail("清理测试数据", "数据库连接失败，请手动删除")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
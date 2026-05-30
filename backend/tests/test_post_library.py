# ===== backend/tests/test_post_library.py =====
"""
测试 PostLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_post_library
"""
from backend.libs.post_library import PostLibrary
from backend.libs.user_library import UserLibrary
from backend.utils.db_manager import DatabaseManager
import uuid

def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")
def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")

def main():
    post_lib = PostLibrary()
    user_lib = UserLibrary()

    # ======== 清理旧测试数据 ========
    if post_lib.db.open_database():
        # 删除所有测试帖子（关联的评论、点赞会级联删除）
        post_lib.db.execute_raw_sql("DELETE FROM t_like WHERE post_id IN (SELECT post_id FROM t_post WHERE user_id LIKE 'test_post_user_%')")
        post_lib.db.execute_raw_sql("DELETE FROM t_comment WHERE post_id IN (SELECT post_id FROM t_post WHERE user_id LIKE 'test_post_user_%')")
        post_lib.db.execute_raw_sql("DELETE FROM t_post WHERE user_id LIKE 'test_post_user_%'")
        # 删除测试用户
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_post_user_%'")
        post_lib.db.close_database()
        print("已清理旧测试数据")
    # =================================

    test_user1_id = f"test_post_user_{uuid.uuid4().hex[:6]}"
    test_user2_id = f"test_post_user_{uuid.uuid4().hex[:6]}"
    test_nickname1 = "发帖人A"
    test_nickname2 = "发帖人B"

    print("\n" + "="*50 + "\n  开始测试 PostLibrary\n" + "="*50)

    # ========== 0. 准备测试用户 ==========
    print("\n0. 准备测试用户...")
    user_lib.register_user(test_user1_id, test_nickname1, role=1)
    user_lib.register_user(test_user2_id, test_nickname2, role=1)
    log_pass("注册两个测试用户", f"user1={test_user1_id}, user2={test_user2_id}")

    # ========== 1. 发布帖子 ==========
    print("\n1. 测试发布帖子 (create_post)...")
    content1 = "今天在图书馆门口看到一只橘猫，好可爱！"
    image_urls1 = '["http://example.com/img1.jpg","http://example.com/img2.jpg"]'
    result = post_lib.create_post(test_user1_id, content1, image_urls1)
    if result["success"]:
        post_id1 = result["data"]["post_id"]
        log_pass(f"发帖，user_id={test_user1_id}, content={content1[:10]}...", 
                 f"success=True, post_id={post_id1}")
    else:
        log_fail(f"发帖，user_id={test_user1_id}", f"success=False, message={result['message']}")
        post_id1 = None

    # 发布第二个帖子（无图片）
    result2 = post_lib.create_post(test_user1_id, "第二篇测试帖子")
    if result2["success"]:
        post_id2 = result2["data"]["post_id"]
        log_pass("发帖（无图片）", f"success=True, post_id={post_id2}")
    else:
        log_fail("发帖（无图片）", f"success=False, message={result2['message']}")
        post_id2 = None

    # 发布一条属于 user2 的帖子（用于后续权限测试）
    result3 = post_lib.create_post(test_user2_id, "这是用户B的帖子")
    if result3["success"]:
        post_id3 = result3["data"]["post_id"]
        log_pass("用户B发帖", f"success=True, post_id={post_id3}")
    else:
        log_fail("用户B发帖", f"success=False")
        post_id3 = None

    # ========== 2. 查询帖子 by ID ==========
    print("\n2. 测试查询帖子 (get_post_by_id)...")
    # 2.1 查询存在的帖子（不带 current_user_id）
    res = post_lib.get_post_by_id(post_id1)
    if res["success"] and res["data"]["post_id"] == post_id1:
        log_pass(f"查询帖子，post_id={post_id1}", 
                 f"success=True, nickname={res['data']['nickname']}, like_count={res['data']['like_count']}")
    else:
        log_fail(f"查询帖子，post_id={post_id1}", f"success={res['success']}")

    # 2.2 查询不存在的帖子
    res = post_lib.get_post_by_id("non_exist_post_id")
    if not res["success"]:
        log_pass("查询不存在的帖子", f"success=False, message={res['message']}")
    else:
        log_fail("查询不存在的帖子", f"success=True（预期False）")

    # 2.3 查询帖子并检测是否点赞（未点赞时）
    res = post_lib.get_post_by_id(post_id1, current_user_id=test_user2_id)
    if res["success"] and res["data"]["is_liked_by_current_user"] == False:
        log_pass(f"查询帖子并检测点赞状态（未点赞）", f"is_liked=False")
    else:
        log_fail(f"查询帖子并检测点赞状态（未点赞）", f"is_liked={res['data'].get('is_liked_by_current_user') if res['success'] else 'error'}")

    # ========== 3. 按用户查询帖子 ==========
    print("\n3. 测试按用户查询帖子 (get_posts_by_user)...")
    # 3.1 user1 的帖子（应至少有2条）
    res = post_lib.get_posts_by_user(test_user1_id, page=1, page_size=10)
    if res["success"] and res["data"]["total"] >= 2:
        log_pass(f"按用户查询帖子，user_id={test_user1_id}", 
                 f"total={res['data']['total']}, posts数量={len(res['data']['posts'])}")
    else:
        log_fail(f"按用户查询帖子，user_id={test_user1_id}", 
                 f"success={res['success']}, total={res['data']['total'] if res['success'] else 'N/A'}")

    # 3.2 空用户（没有任何帖子）
    empty_user = f"test_post_user_{uuid.uuid4().hex[:6]}"
    user_lib.register_user(empty_user, "空用户", role=1)
    res = post_lib.get_posts_by_user(empty_user)
    if res["success"] and res["data"]["total"] == 0:
        log_pass(f"查询无帖子的用户", f"total=0")
    else:
        log_fail(f"查询无帖子的用户", f"total={res['data']['total'] if res['success'] else 'N/A'}（预期0）")

    # ========== 4. 获取所有帖子 ==========
    print("\n4. 测试获取所有帖子 (get_all_posts)...")
    res = post_lib.get_all_posts(page=1, page_size=10)
    if res["success"] and res["data"]["total"] >= 3:
        log_pass("获取所有帖子", f"total={res['data']['total']}, posts数量={len(res['data']['posts'])}")
        # 验证时间倒序
        if len(res['data']['posts']) >= 2:
            t1 = res['data']['posts'][0]['created_at']
            t2 = res['data']['posts'][1]['created_at']
            if t1 >= t2:
                log_pass("帖子按时间倒序排列", f"第一个时间={t1}, 第二个时间={t2}")
            else:
                log_fail("帖子按时间倒序排列", f"第一个时间={t1}, 第二个时间={t2}（应 t1>=t2）")
    else:
        log_fail("获取所有帖子", f"success={res['success']}, total={res['data']['total'] if res['success'] else 'N/A'}")

    # ========== 5. 点赞帖子 ==========
    print("\n5. 测试点赞帖子 (toggle_like_post)...")
    # 5.1 点赞
    res = post_lib.toggle_like_post(post_id1, test_user2_id)
    if res["success"] and res["data"]["is_liked"] == True:
        log_pass("用户B点赞帖子A", f"success=True, is_liked=True")
    else:
        log_fail("用户B点赞帖子A", f"success={res['success']}, data={res.get('data')}")

    # 5.2 取消点赞
    res = post_lib.toggle_like_post(post_id1, test_user2_id)
    if res["success"] and res["data"]["is_liked"] == False:
        log_pass("用户B取消点赞帖子A", f"success=True, is_liked=False")
    else:
        log_fail("用户B取消点赞帖子A", f"success={res['success']}, data={res.get('data')}")

    # 5.3 对不存在的帖子点赞
    res = post_lib.toggle_like_post("non_exist_post_id", test_user2_id)
    if not res["success"]:
        log_pass("对不存在的帖子点赞", f"success=False, message={res['message']}")
    else:
        log_fail("对不存在的帖子点赞", f"success=True（预期False）")

    # ========== 6. 评论 ==========
    print("\n6. 测试评论功能 (add_comment / delete_comment)...")
    # 6.1 正常添加评论
    comment_content = "这只猫我也见过！"
    res = post_lib.add_comment(post_id1, test_user2_id, comment_content)
    if res["success"]:
        comment_id = res["data"]["comment_id"]
        log_pass(f"用户B对帖子A添加评论", f"success=True, comment_id={comment_id}, content={comment_content}")
    else:
        log_fail("用户B对帖子A添加评论", f"success=False, message={res['message']}")
        comment_id = None

    # 6.2 添加第二条评论（同一用户可多次评论）
    comment_content2 = "真的吗？我在哪看到的？"
    res = post_lib.add_comment(post_id1, test_user1_id, comment_content2)
    if res["success"]:
        comment_id2 = res["data"]["comment_id"]
        log_pass(f"用户A对帖子A添加第二条评论", f"success=True, comment_id={comment_id2}")
    else:
        log_fail("用户A添加第二条评论", f"success=False")
        comment_id2 = None

    # 6.3 评论不存在的帖子
    res = post_lib.add_comment("non_exist_post_id", test_user1_id, "测试")
    if not res["success"]:
        log_pass("评论不存在的帖子", f"success=False, message={res['message']}")
    else:
        log_fail("评论不存在的帖子", f"success=True（预期False）")

    # 6.4 删除评论（正常删除）
    if comment_id:
        res = post_lib.delete_comment(comment_id, test_user2_id)
        if res["success"]:
            log_pass("删除自己的评论", f"success=True, comment_id={comment_id}")
        else:
            log_fail("删除自己的评论", f"success=False, message={res['message']}")

    # 6.5 删除别人的评论（应失败）
    if comment_id2:
        res = post_lib.delete_comment(comment_id2, test_user2_id)
        if not res["success"] and "无权" in res["message"]:
            log_pass("用户B尝试删除用户A的评论", f"success=False, message={res['message']}")
        else:
            log_fail("用户B尝试删除用户A的评论", f"success={res['success']}（预期False）")

    # 6.6 删除不存在的评论
    res = post_lib.delete_comment(999999, test_user1_id)
    if not res["success"]:
        log_pass("删除不存在的评论", f"success=False, message={res['message']}")
    else:
        log_fail("删除不存在的评论", f"success=True（预期False）")

    # ========== 7. 点赞评论 ==========
    print("\n7. 测试点赞评论 (toggle_like_comment)...")
    # 重新添加一条评论用于测试点赞
    res = post_lib.add_comment(post_id1, test_user1_id, "点赞测试评论")
    if res["success"]:
        comment_id_for_like = res["data"]["comment_id"]
    else:
        comment_id_for_like = None

    if comment_id_for_like:
        # 7.1 点赞评论
        res = post_lib.toggle_like_comment(comment_id_for_like, test_user2_id)
        if res["success"] and res["data"]["is_liked"] == True:
            log_pass("用户B点赞评论", f"success=True, is_liked=True")
        else:
            log_fail("用户B点赞评论", f"success={res['success']}, data={res.get('data')}")

        # 7.2 取消点赞评论
        res = post_lib.toggle_like_comment(comment_id_for_like, test_user2_id)
        if res["success"] and res["data"]["is_liked"] == False:
            log_pass("用户B取消点赞评论", f"success=True, is_liked=False")
        else:
            log_fail("用户B取消点赞评论", f"success={res['success']}, data={res.get('data')}")

    # 7.3 点赞不存在的评论
    res = post_lib.toggle_like_comment(999999, test_user1_id)
    if not res["success"]:
        log_pass("点赞不存在的评论", f"success=False, message={res['message']}")
    else:
        log_fail("点赞不存在的评论", f"success=True（预期False）")

    # ========== 8. 帖子详情页（含评论） ==========
    print("\n8. 测试帖子详情页 (get_post_detail_with_comments)...")
    # 8.1 正常详情页（带 current_user_id 判断已点赞情况）
    # 先让 user2 对 post_id1 点赞，以便检测 is_liked
    post_lib.toggle_like_post(post_id1, test_user2_id)  # 点赞
    res = post_lib.get_post_detail_with_comments(post_id1, current_user_id=test_user2_id)
    if res["success"]:
        data = res["data"]
        # 应该有评论（之前删除了 comment_id，还剩 comment_id2 和刚才添加的点赞测试评论）
        if len(data["comments"]) >= 1 and data["is_liked_by_current_user"] == True:
            log_pass("获取帖子详情页（含评论和点赞状态）", 
                     f"comment_count={data['comment_count']}, is_liked={data['is_liked_by_current_user']}")
        else:
            log_fail("获取帖子详情页（含评论和点赞状态）", 
                     f"comment_count={data['comment_count']}, is_liked={data['is_liked_by_current_user']}")
    else:
        log_fail("获取帖子详情页", f"success=False, message={res['message']}")

    # 8.2 不存在的帖子
    res = post_lib.get_post_detail_with_comments("non_exist_id")
    if not res["success"]:
        log_pass("获取不存在的帖子详情页", f"success=False, message={res['message']}")
    else:
        log_fail("获取不存在的帖子详情页", f"success=True（预期False）")

    # ========== 9. 删除帖子 ==========
    print("\n9. 测试删除帖子 (delete_post)...")
    # 9.1 正常删除（帖子作者自己删除）
    if post_id1:
        res = post_lib.delete_post(post_id1, test_user1_id)
        if res["success"]:
            log_pass(f"用户A删除自己的帖子A", f"success=True, post_id={post_id1}")
        else:
            log_fail(f"用户A删除自己的帖子A", f"success=False, message={res['message']}")

    # 9.2 删除别人帖子（应失败）
    if post_id2:
        res = post_lib.delete_post(post_id2, test_user2_id)
        if not res["success"] and "无权" in res["message"]:
            log_pass("用户B尝试删除用户A的帖子", f"success=False, message={res['message']}")
        else:
            log_fail("用户B尝试删除用户A的帖子", f"success={res['success']}（预期False）")

    # 9.3 删除不存在的帖子
    res = post_lib.delete_post("non_exist_post_id", test_user1_id)
    if not res["success"]:
        log_pass("删除不存在的帖子", f"success=False, message={res['message']}")
    else:
        log_fail("删除不存在的帖子", f"success=True（预期False）")

    # ========== 10. 清理测试数据 ==========
    print("\n10. 清理测试数据...")
    if post_lib.db.open_database():
        # 只需删除帖子，相关的点赞和评论会通过外键约束 (ON DELETE CASCADE) 自动清理
        post_lib.db.execute_raw_sql("DELETE FROM t_post WHERE user_id LIKE 'test_post_user_%'")
        post_lib.db.close_database()
        
        # 单独清理用户（注意：需要用 user_lib 打开连接）
        if user_lib.db.open_database():
            user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_post_user_%'")
            user_lib.db.close_database()
        
        log_pass("清理测试数据", f"删除所有 test_post_user_* 数据")
    else:
        log_fail("清理测试数据", "数据库连接失败，请手动删除")

if __name__ == "__main__":
    main()
# ===== backend/tests/test_follow_library.py =====
"""
测试 FollowLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_follow_library
"""
from backend.libs.follow_library import FollowLibrary
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    follow_lib = FollowLibrary()
    user_lib = UserLibrary()
    db = follow_lib.db

    # ======== 准备测试用户 ========
    user_a = f"test_user_{uuid.uuid4().hex[:8]}"
    user_b = f"test_user_{uuid.uuid4().hex[:8]}"
    user_c = f"test_user_{uuid.uuid4().hex[:8]}"

    # 1) 清理旧测试数据
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_follow WHERE from_user_id LIKE 'test_user_%' OR to_user_id LIKE 'test_user_%'"
        )
        db.execute_raw_sql(
            "DELETE FROM t_user WHERE user_id LIKE 'test_user_%'"
        )
        db.close_database()
        print("已清理旧测试数据")
    else:
        print("[FAIL] 数据库连接失败，测试终止")
        return

    # 2) 通过 UserLibrary 注册 3 个测试用户（字段与表结构完全匹配）
    for uid in [user_a, user_b, user_c]:
        # 先尝试物理删除（防残留）
        user_lib.delete_user(uid)
        success = user_lib.register_user(uid, f"nick_{uid}")
        if not success:
            print(f"[FAIL] 注册用户 {uid} 失败，测试终止")
            return

    print(f"已创建测试用户: A={user_a}, B={user_b}, C={user_c}")

    print("\n" + "=" * 50 + "\n  开始测试 FollowLibrary\n" + "=" * 50)

    # ========== 1. 关注用户 ==========
    print("\n1. 测试关注用户 (follow_user)...")

    # 1.1 正常关注：A 关注 B
    result = follow_lib.follow_user(user_a, user_b)
    if result["success"] and result["data"] and result["data"].get("follow_id"):
        log_pass(f"A关注B ({user_a} -> {user_b})", "成功")
    else:
        log_fail("A关注B", f"失败: {result['message']}")

    # 1.2 重复关注：A 再次关注 B
    result = follow_lib.follow_user(user_a, user_b)
    if result["success"] and "已关注" in result["message"]:
        log_pass("A重复关注B", "返回已关注提示")
    else:
        log_fail("A重复关注B", f"结果异常: {result['message']}")

    # 1.3 关注自己
    result = follow_lib.follow_user(user_a, user_a)
    if not result["success"] and "不能关注自己" in result["message"]:
        log_pass("A关注自己", "返回不能关注自己")
    else:
        log_fail("A关注自己", f"结果异常: {result['message']}")

    # 1.4 空参数
    result = follow_lib.follow_user("", user_b)
    if not result["success"] and "参数不能为空" in result["message"]:
        log_pass("from_user_id为空", "返回参数不能为空")
    else:
        log_fail("from_user_id为空", f"结果异常: {result['message']}")

    result = follow_lib.follow_user(user_a, "")
    if not result["success"] and "参数不能为空" in result["message"]:
        log_pass("to_user_id为空", "返回参数不能为空")
    else:
        log_fail("to_user_id为空", f"结果异常: {result['message']}")

    # 1.5 无效用户（不存在的用户）
    fake_user = f"test_user_{uuid.uuid4().hex[:8]}"
    result = follow_lib.follow_user(fake_user, user_b)
    if not result["success"] and "关注者不存在" in result["message"]:
        log_pass("无效关注者", "返回关注者不存在")
    else:
        log_fail("无效关注者", f"结果异常: {result['message']}")

    result = follow_lib.follow_user(user_a, fake_user)
    if not result["success"] and "被关注者不存在" in result["message"]:
        log_pass("无效被关注者", "返回被关注者不存在")
    else:
        log_fail("无效被关注者", f"结果异常: {result['message']}")

    # ========== 2. 检查关注状态 ==========
    print("\n2. 测试检查关注状态 (check_follow_status)...")

    # 2.1 已关注
    result = follow_lib.check_follow_status(user_a, user_b)
    if result["success"] and result["data"]["is_following"]:
        log_pass("A->B 关注状态", "is_following=True")
    else:
        log_fail("A->B 关注状态", f"结果异常: {result}")

    # 2.2 未关注
    result = follow_lib.check_follow_status(user_b, user_a)
    if result["success"] and not result["data"]["is_following"]:
        log_pass("B->A 关注状态", "is_following=False")
    else:
        log_fail("B->A 关注状态", f"结果异常: {result}")

    # 2.3 空参数（代码内未做空校验，SQL 查不到返回 False）
    result = follow_lib.check_follow_status("", user_b)
    if result["success"] and not result["data"]["is_following"]:
        log_pass("空参数查询状态", "返回成功且 is_following=False")
    else:
        log_fail("空参数查询状态", f"结果异常: {result}")

    # ========== 3. 获取关注列表 ==========
    print("\n3. 测试获取关注列表 (get_following_list)...")

    # 先让 B 也关注 A，制造互相关注场景
    follow_lib.follow_user(user_b, user_a)

    result = follow_lib.get_following_list(user_a, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("A的关注列表", f"total={result['data']['total']}")
        records = result["data"]["records"]
        b_record = next((r for r in records if r["user_id"] == user_b), None)
        if b_record and b_record.get("is_mutual"):
            log_pass("互相关注标记", "B记录 is_mutual=True")
        else:
            log_fail("互相关注标记", f"B记录={b_record}")
    else:
        log_fail("A的关注列表", f"结果异常: {result}")

    # 分页测试
    result = follow_lib.get_following_list(user_a, page=1, page_size=1)
    if result["success"] and len(result["data"]["records"]) == 1:
        log_pass("分页 limit=1", "返回1条")
    else:
        log_fail("分页 limit=1", f"返回{len(result['data']['records'])}条")

    # ========== 4. 获取粉丝列表 ==========
    print("\n4. 测试获取粉丝列表 (get_follower_list)...")

    result = follow_lib.get_follower_list(user_b, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("B的粉丝列表", f"total={result['data']['total']}")
        records = result["data"]["records"]
        a_record = next((r for r in records if r["user_id"] == user_a), None)
        if a_record and a_record.get("is_following_back"):
            log_pass("is_following_back 标记", "A记录 is_following_back=True")
        else:
            log_fail("is_following_back 标记", f"A记录={a_record}")
    else:
        log_fail("B的粉丝列表", f"结果异常: {result}")

    # 分页测试
    result = follow_lib.get_follower_list(user_b, page=1, page_size=1)
    if result["success"] and len(result["data"]["records"]) == 1:
        log_pass("粉丝分页 limit=1", "返回1条")
    else:
        log_fail("粉丝分页 limit=1", f"返回{len(result['data']['records'])}条")

    # ========== 5. 获取关注/粉丝数量 ==========
    print("\n5. 测试获取数量统计 (get_following_count / get_follower_count)...")

    result_fc = follow_lib.get_following_count(user_a)
    result_frc = follow_lib.get_follower_count(user_b)
    if (result_fc["success"] and result_fc["data"]["following_count"] == 1 and
        result_frc["success"] and result_frc["data"]["follower_count"] == 1):
        log_pass("A关注数=1, B粉丝数=1", "验证成功")
    else:
        log_fail("数量统计", f"A关注数={result_fc}, B粉丝数={result_frc}")

    # 无效用户
    result = follow_lib.get_following_count(fake_user)
    if not result["success"] and "用户不存在" in result["message"]:
        log_pass("无效用户关注数", "返回用户不存在")
    else:
        log_fail("无效用户关注数", f"结果异常: {result}")

    result = follow_lib.get_follower_count(fake_user)
    if not result["success"] and "用户不存在" in result["message"]:
        log_pass("无效用户粉丝数", "返回用户不存在")
    else:
        log_fail("无效用户粉丝数", f"结果异常: {result}")

    # ========== 6. 取消关注 ==========
    print("\n6. 测试取消关注 (unfollow_user)...")

    # 6.1 正常取消：A 取消关注 B
    result = follow_lib.unfollow_user(user_a, user_b)
    if result["success"] and result["data"].get("unfollowed"):
        log_pass("A取消关注B", "成功")
    else:
        log_fail("A取消关注B", f"失败: {result['message']}")

    # 6.2 重复取消：A 再次取消关注 B（此时已未关注）
    result = follow_lib.unfollow_user(user_a, user_b)
    if not result["success"] and "尚未关注" in result["message"]:
        log_pass("A重复取消关注B", "返回尚未关注")
    else:
        log_fail("A重复取消关注B", f"结果异常: {result['message']}")

    # 6.3 对自己操作
    result = follow_lib.unfollow_user(user_a, user_a)
    if not result["success"] and "不能对自己操作" in result["message"]:
        log_pass("A取消关注自己", "返回不能对自己操作")
    else:
        log_fail("A取消关注自己", f"结果异常: {result['message']}")

    # 6.4 空参数
    result = follow_lib.unfollow_user("", user_b)
    if not result["success"] and "参数不能为空" in result["message"]:
        log_pass("取消关注空from", "返回参数不能为空")
    else:
        log_fail("取消关注空from", f"结果异常: {result['message']}")

    # 6.5 无效用户
    result = follow_lib.unfollow_user(fake_user, user_b)
    if not result["success"] and "关注者不存在" in result["message"]:
        log_pass("取消关注无效用户", "返回关注者不存在")
    else:
        log_fail("取消关注无效用户", f"结果异常: {result['message']}")

    # 6.6 取消关注后状态检查
    result = follow_lib.check_follow_status(user_a, user_b)
    if result["success"] and not result["data"]["is_following"]:
        log_pass("取消后状态检查", "is_following=False")
    else:
        log_fail("取消后状态检查", f"结果异常: {result}")

    # ========== 7. 数量变化验证 ==========
    print("\n7. 测试数量变化验证...")

    # A 已取消关注 B，此时 A 的关注数应为 0
    # B 仍关注 A，所以 B 关注数=1，A 粉丝数=1
    result_fc_a = follow_lib.get_following_count(user_a)
    result_fc_b = follow_lib.get_following_count(user_b)
    result_frc_a = follow_lib.get_follower_count(user_a)
    result_frc_b = follow_lib.get_follower_count(user_b)

    if (result_fc_a["success"] and result_fc_a["data"]["following_count"] == 0 and
        result_fc_b["success"] and result_fc_b["data"]["following_count"] == 1 and
        result_frc_a["success"] and result_frc_a["data"]["follower_count"] == 1 and
        result_frc_b["success"] and result_frc_b["data"]["follower_count"] == 0):
        log_pass("取消后数量变化", "A关注=0, B关注=1, A粉丝=1, B粉丝=0")
    else:
        log_fail("取消后数量变化",
                 f"A关注={result_fc_a['data']}, B关注={result_fc_b['data']}, "
                 f"A粉丝={result_frc_a['data']}, B粉丝={result_frc_b['data']}")

    # ========== 8. 清理测试数据 ==========
    print("\n8. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_follow WHERE from_user_id IN (%s, %s, %s) OR to_user_id IN (%s, %s, %s)",
            (user_a, user_b, user_c, user_a, user_b, user_c)
        )
        db.execute_raw_sql(
            "DELETE FROM t_user WHERE user_id IN (%s, %s, %s)",
            (user_a, user_b, user_c)
        )
        db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
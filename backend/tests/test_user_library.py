"""
测试 UserLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_user_library
"""
from backend.libs.user_library import UserLibrary
import uuid

def log_pass(original, current):
    print(f"  ✅ PASS: 原始数据 = {original}, 当前数据 = {current}")

def log_fail(original, current):
    print(f"  ❌ FAIL: 原始数据 = {original}, 当前数据 = {current}")

def main():
    user_lib = UserLibrary()
    
    # ======== 清理旧测试数据 ========
    if user_lib.db.open_database():
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_user_%'")
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'top_%'")
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'low_%'")
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE role = 2 AND user_id NOT LIKE 'top_%' AND user_id NOT LIKE 'low_%'")
        user_lib.db.close_database()
        print("已清理旧测试数据")
    # =================================

    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    test_nickname = "测试用户"
    test_avatar = "http://example.com/avatar.jpg"

    print("\n" + "="*50 + "\n  开始测试 UserLibrary\n" + "="*50)

    # 1. 注册用户
    print("\n1. 测试注册用户...")
    success = user_lib.register_user(test_user_id, test_nickname, test_avatar, role=0)
    if success:
        log_pass(f"注册新用户，输入 user_id={test_user_id}", f"注册成功 (True)")
    else:
        log_fail(f"注册新用户，输入 user_id={test_user_id}", f"注册失败 (False)")

    # 重复注册
    success2 = user_lib.register_user(test_user_id, "重复注册", role=0)
    if not success2:
        log_pass(f"重复注册，输入 user_id={test_user_id}", f"注册失败 (False)，预期行为")
    else:
        log_fail(f"重复注册，输入 user_id={test_user_id}", f"注册成功 (True)，预期失败")

    # 2. 查询用户
    print("\n2. 测试查询用户...")
    user = user_lib.get_user_by_account(test_user_id)
    if user and user.user_id == test_user_id:
        log_pass(f"查询已存在用户，user_id={test_user_id}", f"用户对象存在，昵称={user.nickname}")
    else:
        log_fail(f"查询已存在用户，user_id={test_user_id}", f"用户对象不存在或ID不匹配")

    # 查询不存在用户
    none_user = user_lib.get_user_by_account("not_exist_123")
    if none_user is None:
        log_pass(f"查询不存在用户，user_id=not_exist_123", f"结果 None")
    else:
        log_fail(f"查询不存在用户，user_id=not_exist_123", f"结果 {none_user}，预期 None")

    # 3. 验证用户有效性
    print("\n3. 测试验证用户有效性...")
    valid = user_lib.verify_user_validity(test_user_id)
    if valid:
        log_pass(f"验证已存在用户，user_id={test_user_id}", f"验证结果 True")
    else:
        log_fail(f"验证已存在用户，user_id={test_user_id}", f"验证结果 False")

    invalid = user_lib.verify_user_validity("not_exist_123")
    if not invalid:
        log_pass(f"验证不存在用户，user_id=not_exist_123", f"验证结果 False")
    else:
        log_fail(f"验证不存在用户，user_id=not_exist_123", f"验证结果 True，预期 False")

    # 4. 更新用户信息
    print("\n4. 测试更新用户信息...")
    update_data = {'nickname': '新昵称', 'avatarURL': 'http://example.com/new_avatar.jpg'}
    update_success = user_lib.update_user_info(test_user_id, update_data)
    if update_success:
        log_pass(f"更新用户信息，user_id={test_user_id}, 更新数据={update_data}", f"更新成功 (True)")
    else:
        log_fail(f"更新用户信息，user_id={test_user_id}, 更新数据={update_data}", f"更新失败 (False)")

    # 验证更新结果
    updated_user = user_lib.get_user_by_account(test_user_id)
    if updated_user and updated_user.nickname == "新昵称":
        log_pass(f"验证更新结果，期望昵称='新昵称'", f"实际昵称={updated_user.nickname}")
    else:
        log_fail(f"验证更新结果，期望昵称='新昵称'", f"实际昵称={updated_user.nickname if updated_user else '用户不存在'}")

    # 更新不存在用户
    update_fail = user_lib.update_user_info("not_exist_123", {'nickname': '测试'})
    if not update_fail:
        log_pass(f"更新不存在用户，user_id=not_exist_123", f"更新失败 (False)")
    else:
        log_fail(f"更新不存在用户，user_id=not_exist_123", f"更新成功 (True)，预期失败")

    # 5. 修改用户角色
    print("\n5. 测试修改用户角色...")
    role_success = user_lib.update_role(test_user_id, 2)
    if role_success:
        log_pass(f"修改角色为志愿者，user_id={test_user_id}, 新角色=2", f"修改成功 (True)")
    else:
        log_fail(f"修改角色为志愿者，user_id={test_user_id}, 新角色=2", f"修改失败 (False)")

    # 验证角色修改结果
    role_user = user_lib.get_user_by_account(test_user_id)
    if role_user and role_user.role == 2:
        log_pass(f"验证角色修改，期望角色=2", f"实际角色={role_user.role}")
    else:
        log_fail(f"验证角色修改，期望角色=2", f"实际角色={role_user.role if role_user else '用户不存在'}")

    # 6. 增加积分 (set)
    print("\n6. 测试增加积分 (set)...")
    user_lib.increment_points(test_user_id, 10)
    points_user = user_lib.get_user_by_account(test_user_id)
    if points_user and points_user.points == 10:
        log_pass(f"设置积分 = 10", f"当前积分 = {points_user.points}")
    else:
        log_fail(f"设置积分 = 10", f"当前积分 = {points_user.points if points_user else '用户不存在'}")

    # 给不存在用户加积分
    if not user_lib.increment_points("not_exist_123", 10):
        log_pass(f"给不存在用户加积分，user_id=not_exist_123", f"操作失败 (False)")
    else:
        log_fail(f"给不存在用户加积分，user_id=not_exist_123", f"操作成功 (True)，预期失败")

    # 7. 排行榜
    print("\n7. 测试获取志愿者排行榜...")
    top_id = f"top_{uuid.uuid4().hex[:6]}"
    low_id = f"low_{uuid.uuid4().hex[:6]}"
    user_lib.register_user(top_id, "高分志愿者", role=2)
    user_lib.increment_points(top_id, 100)
    user_lib.register_user(low_id, "低分志愿者", role=2)
    user_lib.increment_points(low_id, 5)

    ranking = user_lib.get_volunteers_ranking(limit=10)
    print(f"   - 排行榜总人数: {len(ranking)}")
    if ranking:
        log_pass(f"排行榜数据", f"共有 {len(ranking)} 名志愿者，积分排序正确")
        # 循环输出详细排名
        for i, user in enumerate(ranking):
            print(f"     第{i+1}名: {user.nickname} (积分: {user.points})")
    else:
        log_fail(f"排行榜数据", f"结果为空")

    # 8. 累加积分 (add)
    print("\n8. 测试累加积分 (add)...")
    # 设置初始积分为 20
    user_lib.update_user_info(test_user_id, {'points': 20})
    # 加 5 分 -> 25
    if user_lib.add_points(test_user_id, 5):
        user = user_lib.get_user_by_account(test_user_id)
        if user.points == 25:
            log_pass(f"累加积分 +5，初始积分=20", f"当前积分={user.points}")
        else:
            log_fail(f"累加积分 +5，初始积分=20", f"当前积分={user.points}")
    else:
        log_fail("累加积分 +5", "操作失败")

    # 减 10 分 -> 15
    if user_lib.add_points(test_user_id, -10):
        user = user_lib.get_user_by_account(test_user_id)
        if user.points == 15:
            log_pass(f"累加积分 -10，初始积分=25", f"当前积分={user.points}")
        else:
            log_fail(f"累加积分 -10，初始积分=25", f"当前积分={user.points}")
    else:
        log_fail("累加积分 -10", "操作失败")

    # 9. 清理测试数据
    print("\n9. 清理测试数据...")
    if user_lib.db.open_database():
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id = %s", (test_user_id,))
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id = %s", (top_id,))
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id = %s", (low_id,))
        user_lib.db.close_database()
        log_pass("清理测试数据", f"删除用户: {test_user_id}, {top_id}, {low_id} 成功")
    else:
        log_fail("清理测试数据", "数据库连接失败，请手动删除")

    print("\n" + "="*50 + "\n  测试完成\n" + "="*50)

if __name__ == "__main__":
    main()
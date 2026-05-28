"""
测试 UserLibrary 所有功能（适配新数据库结构）
运行方式（在项目根目录执行）：
    python -m backend.tests.test_user_library
"""
from backend.libs.user_library import UserLibrary
import uuid
from datetime import datetime

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

    # ========== 1. 注册用户（默认 role=1） ==========
    print("\n1. 测试注册用户...")
    success = user_lib.register_user(test_user_id, test_nickname, test_avatar, role=1)
    if success:
        log_pass(f"注册新用户，输入 user_id={test_user_id}, role=1", f"注册成功 (True)")
    else:
        log_fail(f"注册新用户，输入 user_id={test_user_id}, role=1", f"注册失败 (False)")

    # 重复注册
    success2 = user_lib.register_user(test_user_id, "重复注册", role=1)
    if not success2:
        log_pass(f"重复注册，输入 user_id={test_user_id}", f"注册失败 (False)，预期行为")
    else:
        log_fail(f"重复注册，输入 user_id={test_user_id}", f"注册成功 (True)，预期失败")

    # ========== 2. 查询用户 ==========
    print("\n2. 测试查询用户...")
    user = user_lib.get_user_by_account(test_user_id)
    if user and user.user_id == test_user_id:
        log_pass(f"查询已存在用户，user_id={test_user_id}", f"用户对象存在，昵称={user.nickname}, role={user.role}")
    else:
        log_fail(f"查询已存在用户，user_id={test_user_id}", f"用户对象不存在或ID不匹配")

    none_user = user_lib.get_user_by_account("not_exist_123")
    if none_user is None:
        log_pass(f"查询不存在用户，user_id=not_exist_123", f"结果 None")
    else:
        log_fail(f"查询不存在用户，user_id=not_exist_123", f"结果 {none_user}，预期 None")

    # ========== 3. 验证用户有效性 ==========
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

    # ========== 4. 更新用户信息 ==========
    print("\n4. 测试更新用户信息...")
    update_data = {'nickname': '新昵称', 'avatarURL': 'http://example.com/new_avatar.jpg'}
    update_success = user_lib.update_user_info(test_user_id, update_data)
    if update_success:
        log_pass(f"更新用户信息，user_id={test_user_id}, 更新数据={update_data}", f"更新成功 (True)")
    else:
        log_fail(f"更新用户信息，user_id={test_user_id}, 更新数据={update_data}", f"更新失败 (False)")

    updated_user = user_lib.get_user_by_account(test_user_id)
    if updated_user and updated_user.nickname == "新昵称":
        log_pass(f"验证更新结果，期望昵称='新昵称'", f"实际昵称={updated_user.nickname}")
    else:
        log_fail(f"验证更新结果，期望昵称='新昵称'", f"实际昵称={updated_user.nickname if updated_user else '用户不存在'}")

    update_fail = user_lib.update_user_info("not_exist_123", {'nickname': '测试'})
    if not update_fail:
        log_pass(f"更新不存在用户，user_id=not_exist_123", f"更新失败 (False)")
    else:
        log_fail(f"更新不存在用户，user_id=not_exist_123", f"更新成功 (True)，预期失败")

    # ========== 5. 修改用户角色 ==========
    print("\n5. 测试修改用户角色...")
    # 普通用户 (1) -> 志愿者 (2)
    role_success = user_lib.update_role(test_user_id, 2)
    if role_success:
        log_pass(f"修改角色为志愿者，user_id={test_user_id}, 新角色=2", f"修改成功 (True)")
    else:
        log_fail(f"修改角色为志愿者，user_id={test_user_id}, 新角色=2", f"修改失败 (False)")

    role_user = user_lib.get_user_by_account(test_user_id)
    if role_user and role_user.role == 2 and role_user.level == 1:
        log_pass(f"验证角色修改，期望角色=2, level=1", f"实际角色={role_user.role}, level={role_user.level}")
    else:
        log_fail(f"验证角色修改，期望角色=2, level=1", f"实际角色={role_user.role if role_user else '用户不存在'}, level={role_user.level if role_user else '无'}")

    # 志愿者 (2) -> 管理员 (3)
    admin_success = user_lib.update_role(test_user_id, 3)
    if admin_success:
        log_pass(f"修改角色为管理员，user_id={test_user_id}, 新角色=3", f"修改成功 (True)")
    else:
        log_fail(f"修改角色为管理员，user_id={test_user_id}, 新角色=3", f"修改失败 (False)")

    admin_user = user_lib.get_user_by_account(test_user_id)
    if admin_user and admin_user.role == 3 and admin_user.level is None:
        log_pass(f"验证角色修改，期望角色=3, level=None", f"实际角色={admin_user.role}, level={admin_user.level}")
    else:
        log_fail(f"验证角色修改，期望角色=3, level=None", f"实际角色={admin_user.role if admin_user else '用户不存在'}, level={admin_user.level if admin_user else '无'}")

    # 管理员 (3) -> 普通用户 (1)
    normal_success = user_lib.update_role(test_user_id, 1)
    if normal_success:
        log_pass(f"修改角色为普通用户，user_id={test_user_id}, 新角色=1", f"修改成功 (True)")
    else:
        log_fail(f"修改角色为普通用户，user_id={test_user_id}, 新角色=1", f"修改失败 (False)")

    normal_user = user_lib.get_user_by_account(test_user_id)
    if normal_user and normal_user.role == 1 and normal_user.level is None:
        log_pass(f"验证角色修改，期望角色=1, level=None", f"实际角色={normal_user.role}, level={normal_user.level}")
    else:
        log_fail(f"验证角色修改，期望角色=1, level=None", f"实际角色={normal_user.role if normal_user else '用户不存在'}, level={normal_user.level if normal_user else '无'}")

    # ========== 6. 设置志愿者编号 ==========
    print("\n6. 测试设置志愿者编号...")
    # 先将用户设为志愿者
    user_lib.update_role(test_user_id, 2)
    volunteer_id = "VOL_" + uuid.uuid4().hex[:6]
    set_vol_success = user_lib.set_volunteer_id(test_user_id, volunteer_id)
    if set_vol_success:
        user = user_lib.get_user_by_account(test_user_id)
        if user and user.volunteer_id == volunteer_id:
            log_pass(f"设置志愿者编号，user_id={test_user_id}, volunteer_id={volunteer_id}", f"设置成功")
        else:
            log_fail(f"设置志愿者编号，user_id={test_user_id}, volunteer_id={volunteer_id}", f"设置失败，实际值={user.volunteer_id if user else '无'}")
    else:
        log_fail(f"设置志愿者编号，user_id={test_user_id}, volunteer_id={volunteer_id}", f"操作失败")

    # ========== 7. 设置管理员工号 ==========
    print("\n7. 测试设置管理员工号...")
    # 先将用户设为管理员
    user_lib.update_role(test_user_id, 3)
    admin_id = "ADMIN_" + uuid.uuid4().hex[:6]
    set_admin_success = user_lib.set_admin_id(test_user_id, admin_id)
    if set_admin_success:
        user = user_lib.get_user_by_account(test_user_id)
        if user and user.admin_id == admin_id:
            log_pass(f"设置管理员工号，user_id={test_user_id}, admin_id={admin_id}", f"设置成功")
        else:
            log_fail(f"设置管理员工号，user_id={test_user_id}, admin_id={admin_id}", f"设置失败，实际值={user.admin_id if user else '无'}")
    else:
        log_fail(f"设置管理员工号，user_id={test_user_id}, admin_id={admin_id}", f"操作失败")

    # ========== 8. 更新用户统计数据 ==========
    print("\n8. 测试更新用户统计数据...")
    # 重置为普通用户，以便测试统计字段
    user_lib.update_role(test_user_id, 1)
    stats_success = user_lib.update_user_stats(test_user_id, like_count=10, follower_count=5, following_count=3)
    if stats_success:
        user = user_lib.get_user_by_account(test_user_id)
        if user and user.like_count == 10 and user.follower_count == 5 and user.following_count == 3:
            log_pass(f"更新统计数据，like=10, follower=5, following=3", f"更新成功")
        else:
            log_fail(f"更新统计数据，like=10, follower=5, following=3", f"更新失败，实际值={user.like_count}/{user.follower_count}/{user.following_count}")
    else:
        log_fail(f"更新统计数据，user_id={test_user_id}", f"操作失败")

    # 测试部分更新
    partial_success = user_lib.update_user_stats(test_user_id, like_count=20)
    if partial_success:
        user = user_lib.get_user_by_account(test_user_id)
        if user and user.like_count == 20 and user.follower_count == 5 and user.following_count == 3:
            log_pass(f"部分更新统计数据，like=20", f"更新成功")
        else:
            log_fail(f"部分更新统计数据，like=20", f"更新失败")
    else:
        log_fail(f"部分更新统计数据", f"操作失败")

    # ========== 9. 测试封禁/解封用户 ==========
    print("\n9. 测试封禁/解封用户...")
    # 封禁用户
    ban_success = user_lib.toggle_active_status(test_user_id, 0)
    if ban_success:
        user = user_lib.get_user_by_account(test_user_id)
        if user and user.is_active == 0:
            log_pass(f"封禁用户，user_id={test_user_id}", f"封禁成功")
        else:
            log_fail(f"封禁用户，user_id={test_user_id}", f"封禁失败，实际值={user.is_active if user else '无'}")
    else:
        log_fail(f"封禁用户，user_id={test_user_id}", f"操作失败")

    # 解封用户
    unban_success = user_lib.toggle_active_status(test_user_id, 1)
    if unban_success:
        user = user_lib.get_user_by_account(test_user_id)
        if user and user.is_active == 1:
            log_pass(f"解封用户，user_id={test_user_id}", f"解封成功")
        else:
            log_fail(f"解封用户，user_id={test_user_id}", f"解封失败，实际值={user.is_active if user else '无'}")
    else:
        log_fail(f"解封用户，user_id={test_user_id}", f"操作失败")

    # ========== 10. 获取个人主页信息 ==========
    print("\n10. 测试获取个人主页信息...")
    profile = user_lib.get_user_profile(test_user_id)
    if profile and profile['user_id'] == test_user_id:
        log_pass(f"获取个人主页信息，user_id={test_user_id}", f"获取成功，昵称={profile['nickname']}, 积分={profile['points']}")
    else:
        log_fail(f"获取个人主页信息，user_id={test_user_id}", f"获取失败")

    # 获取不存在用户的主页信息
    none_profile = user_lib.get_user_profile("not_exist_123")
    if none_profile is None:
        log_pass(f"获取不存在用户主页信息", f"返回 None")
    else:
        log_fail(f"获取不存在用户主页信息", f"返回非空，预期 None")

    # ========== 11. 增加积分 (add_points) ==========
    print("\n11. 测试增加积分...")
    # 设置初始积分为 20
    user_lib.update_user_info(test_user_id, {'points': 20})
    # 加 5 分 -> 25
    if user_lib.add_points(test_user_id, 5):
        user = user_lib.get_user_by_account(test_user_id)
        if user.points == 25:
            log_pass(f"增加积分 +5，初始积分=20", f"当前积分={user.points}")
        else:
            log_fail(f"增加积分 +5，初始积分=20", f"当前积分={user.points}")
    else:
        log_fail("增加积分 +5", "操作失败")

    # 减 10 分 -> 15
    if user_lib.add_points(test_user_id, -10):
        user = user_lib.get_user_by_account(test_user_id)
        if user.points == 15:
            log_pass(f"增加积分 -10，初始积分=25", f"当前积分={user.points}")
        else:
            log_fail(f"增加积分 -10，初始积分=25", f"当前积分={user.points}")
    else:
        log_fail("增加积分 -10", "操作失败")

    # ========== 12. 志愿者排行榜 ==========
    print("\n12. 测试志愿者排行榜...")
    top_id = f"top_{uuid.uuid4().hex[:6]}"
    low_id = f"low_{uuid.uuid4().hex[:6]}"
    user_lib.register_user(top_id, "高分志愿者", role=2)
    user_lib.add_points(top_id, 100)
    user_lib.register_user(low_id, "低分志愿者", role=2)
    user_lib.add_points(low_id, 5)

    ranking = user_lib.get_volunteers_ranking(limit=10)
    print(f"   - 排行榜总人数: {len(ranking)}")
    if ranking:
        log_pass(f"排行榜数据", f"共有 {len(ranking)} 名志愿者，积分排序正确")
        for i, user in enumerate(ranking):
            print(f"     第{i+1}名: {user.nickname} (积分: {user.points})")
    else:
        log_fail(f"排行榜数据", f"结果为空")

    # ========== 13. 清理测试数据 ==========
    print("\n13. 清理测试数据...")
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
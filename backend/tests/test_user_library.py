# ===== backend/tests/test_user_library.py =====
"""
测试 UserLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_user_library
"""
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    user_lib = UserLibrary()
    db = user_lib.db

    # ======== 清理旧测试数据 ========
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_points_log WHERE user_id LIKE 'test_user_%'")
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_user_%'")
        db.close_database()
        print("已清理旧测试数据")

    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    test_nickname = "测试用户"
    test_avatar = "http://example.com/avatar.jpg"

    print("\n" + "=" * 50 + "\n  开始测试 UserLibrary\n" + "=" * 50)

    # ========== 1. 注册用户 ==========
    print("\n1. 测试注册用户 (register_user)...")

    # 1.1 正常注册（普通用户）
    success = user_lib.register_user(test_user_id, test_nickname, test_avatar, role=1)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user and user.role == 1 and user.volunteer_id is None and user.level is None:
            log_pass(f"注册普通用户，user_id={test_user_id}", f"role=1, volunteer_id=None, level=None")
        else:
            log_fail("注册普通用户", f"role={user.role if user else '无'}, volunteer_id={user.volunteer_id if user else '无'}")
    else:
        log_fail("注册普通用户", "返回 False")

    # 1.2 重复注册
    success2 = user_lib.register_user(test_user_id, "重复注册", role=1)
    if not success2:
        log_pass("重复注册", "返回 False，预期行为")
    else:
        log_fail("重复注册", "返回 True，预期失败")

    # 1.3 非法角色
    success3 = user_lib.register_user(f"test_user_{uuid.uuid4().hex[:8]}", "非法角色", role=99)
    if not success3:
        log_pass("注册非法角色(99)", "返回 False")
    else:
        log_fail("注册非法角色(99)", "返回 True")

    # 1.4 注册志愿者
    vol_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    success4 = user_lib.register_user(vol_user_id, "测试志愿者", role=2)
    if success4:
        user = user_lib.get_user_by_account(vol_user_id)
        if user and user.role == 2 and user.volunteer_id and user.volunteer_id.startswith('VOL_') and user.level == 1:
            log_pass(f"注册志愿者，user_id={vol_user_id}", f"role=2, volunteer_id={user.volunteer_id}, level=1")
        else:
            log_fail("注册志愿者", f"volunteer_id={user.volunteer_id if user else '无'}, level={user.level if user else '无'}")
    else:
        log_fail("注册志愿者", "返回 False")

    # ========== 2. 查询用户 ==========
    print("\n2. 测试查询用户 (get_user_by_account / verify_user_validity)...")

    user = user_lib.get_user_by_account(test_user_id)
    if user and user.user_id == test_user_id:
        log_pass("查询存在用户", f"nickname={user.nickname}")
    else:
        log_fail("查询存在用户", "未找到")

    none_user = user_lib.get_user_by_account("not_exist_123")
    if none_user is None:
        log_pass("查询不存在用户", "返回 None")
    else:
        log_fail("查询不存在用户", f"返回 {none_user}")

    if user_lib.verify_user_validity(test_user_id):
        log_pass("验证有效用户", "返回 True")
    else:
        log_fail("验证有效用户", "返回 False")

    if not user_lib.verify_user_validity("not_exist_123"):
        log_pass("验证不存在用户", "返回 False")
    else:
        log_fail("验证不存在用户", "返回 True")

    # ========== 3. 更新用户信息 ==========
    print("\n3. 测试更新用户信息 (update_user_info)...")

    # 3.1 正常更新白名单字段
    success = user_lib.update_user_info(test_user_id, {'nickname': '新昵称', 'avatarURL': 'http://new.jpg'})
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.nickname == '新昵称' and user.avatarURL == 'http://new.jpg':
            log_pass("更新昵称和头像", "更新成功")
        else:
            log_fail("更新昵称和头像", f"nickname={user.nickname}, avatarURL={user.avatarURL}")
    else:
        log_fail("更新昵称和头像", "返回 False")

    # 3.2 更新非法字段（应被过滤）
    old_points = user.points
    success = user_lib.update_user_info(test_user_id, {'points': 99999, 'role': 3})
    if not success:
        log_pass("更新非法字段(points/role)", "被正确拒绝")
    else:
        user = user_lib.get_user_by_account(test_user_id)
        if user.points == old_points and user.role == 1:
            log_pass("更新非法字段", "字段被过滤，未修改")
        else:
            log_fail("更新非法字段", f"points={user.points}, role={user.role}")

    # 3.3 更新不存在用户
    if not user_lib.update_user_info("not_exist", {'nickname': 'test'}):
        log_pass("更新不存在用户", "返回 False")
    else:
        log_fail("更新不存在用户", "返回 True")

    # ========== 4. 角色切换 ==========
    print("\n4. 测试角色切换 (update_role)...")

    # 4.1 普通用户 -> 志愿者
    success = user_lib.update_role(test_user_id, 2)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.role == 2 and user.volunteer_id and user.level == 1 and user.admin_id is None:
            log_pass("1->2 切换志愿者", f"role=2, volunteer_id={user.volunteer_id}, level=1")
        else:
            log_fail("1->2 切换志愿者", f"role={user.role}, volunteer_id={user.volunteer_id}, level={user.level}")
    else:
        log_fail("1->2 切换志愿者", "返回 False")

    # 4.2 志愿者 -> 管理员
    old_vol_id = user_lib.get_user_by_account(test_user_id).volunteer_id
    success = user_lib.update_role(test_user_id, 3)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.role == 3 and user.volunteer_id is None and user.level is None:
            log_pass("2->3 切换管理员", f"role=3, volunteer_id=None, level=None")
        else:
            log_fail("2->3 切换管理员", f"role={user.role}, volunteer_id={user.volunteer_id}")
    else:
        log_fail("2->3 切换管理员", "返回 False")

    # 4.3 管理员 -> 普通用户
    success = user_lib.update_role(test_user_id, 1)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.role == 1 and user.volunteer_id is None and user.admin_id is None and user.level is None:
            log_pass("3->1 切换普通用户", "role=1, 所有编号清空")
        else:
            log_fail("3->1 切换普通用户", f"role={user.role}, admin_id={user.admin_id}")
    else:
        log_fail("3->1 切换普通用户", "返回 False")

    # 4.4 非法角色
    if not user_lib.update_role(test_user_id, 99):
        log_pass("切换非法角色(99)", "返回 False")
    else:
        log_fail("切换非法角色(99)", "返回 True")

    # ========== 5. 设置管理员工号 ==========
    print("\n5. 测试设置管理员工号 (set_admin_id)...")

    # 先切回管理员
    user_lib.update_role(test_user_id, 3)
    success = user_lib.set_admin_id(test_user_id, "ADMIN_001")
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.admin_id == "ADMIN_001":
            log_pass("设置工号 ADMIN_001", "设置成功")
        else:
            log_fail("设置工号", f"admin_id={user.admin_id}")
    else:
        log_fail("设置工号", "返回 False")

    # 5.2 给普通用户设置工号（应失败）
    user_lib.update_role(test_user_id, 1)
    if not user_lib.set_admin_id(test_user_id, "ADMIN_002"):
        log_pass("给普通用户设工号", "返回 False，权限校验通过")
    else:
        log_fail("给普通用户设工号", "返回 True")

    # 5.3 空工号
    user_lib.update_role(test_user_id, 3)
    if not user_lib.set_admin_id(test_user_id, ""):
        log_pass("设置空工号", "返回 False")
    else:
        log_fail("设置空工号", "返回 True")

    # ========== 6. 积分系统 ==========
    print("\n6. 测试积分系统 (add_points / get_points_history)...")

    # 重置为普通用户，初始积分0
    user_lib.update_role(test_user_id, 1)
    user_lib._raw_update(test_user_id, {'points': 0})

    # 6.1 增加积分
    success = user_lib.add_points(test_user_id, 100, reason="签到奖励")
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.points == 100:
            log_pass("增加积分 +100", "points=100")
        else:
            log_fail("增加积分 +100", f"points={user.points}")
    else:
        log_fail("增加积分 +100", "返回 False")

    # 6.2 扣减积分
    success = user_lib.add_points(test_user_id, -30, reason="兑换商品")
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.points == 70:
            log_pass("扣减积分 -30", "points=70")
        else:
            log_fail("扣减积分 -30", f"points={user.points}")
    else:
        log_fail("扣减积分 -30", "返回 False")

    # 6.3 扣到负数（应失败）
    if not user_lib.add_points(test_user_id, -999, reason="恶意扣减"):
        log_pass("扣减至负数", "返回 False，边界保护生效")
    else:
        log_fail("扣减至负数", "返回 True，积分可能为负")

    # 6.4 查询积分流水
    history = user_lib.get_points_history(test_user_id)
    if isinstance(history, dict) and "logs" in history:
        total = history.get("total", 0) if isinstance(history, dict) else len(history)
        if total >= 2:
            log_pass("查询积分流水", f"共 {total} 条记录")
        else:
            log_fail("查询积分流水", f"共 {total} 条，预期>=2")
    else:
        log_fail("查询积分流水", "查询失败")

    # ========== 7. 封禁/注销/删除 ==========
    print("\n7. 测试封禁/注销/删除...")

    # 7.1 封禁
    success = user_lib.toggle_active_status(test_user_id, 0)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.is_active == 0:
            log_pass("封禁用户", "is_active=0")
        else:
            log_fail("封禁用户", f"is_active={user.is_active}")
    else:
        log_fail("封禁用户", "返回 False")

    # 验证封禁后 verify_user_validity 返回 False
    if not user_lib.verify_user_validity(test_user_id):
        log_pass("验证封禁用户有效性", "返回 False")
    else:
        log_fail("验证封禁用户有效性", "返回 True")

    # 7.2 解封
    user_lib.toggle_active_status(test_user_id, 1)
    if user_lib.verify_user_validity(test_user_id):
        log_pass("解封用户", "验证通过")
    else:
        log_fail("解封用户", "验证失败")

    # 7.3 注销（逻辑删除）
    success = user_lib.deactivate_user(test_user_id)
    if success and not user_lib.verify_user_validity(test_user_id):
        log_pass("注销用户", "is_active=0，验证失败")
    else:
        log_fail("注销用户", "失败")

    # 7.4 物理删除
    del_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    user_lib.register_user(del_user_id, "待删除用户", role=1)
    success = user_lib.delete_user(del_user_id)
    if success and user_lib.get_user_by_account(del_user_id) is None:
        log_pass("物理删除用户", "删除成功")
    else:
        log_fail("物理删除用户", "失败")

    # 7.5 删除不存在用户
    if not user_lib.delete_user("not_exist"):
        log_pass("删除不存在用户", "返回 False")
    else:
        log_fail("删除不存在用户", "返回 True")

    # 7.6 非法状态值
    if not user_lib.toggle_active_status(test_user_id, 2):
        log_pass("设置非法状态(2)", "返回 False")
    else:
        log_fail("设置非法状态(2)", "返回 True")

    # ========== 8. 统计数据 ==========
    print("\n8. 测试统计数据...")

    # 恢复用户
    user_lib.toggle_active_status(test_user_id, 1)

    # 8.1 全量更新
    success = user_lib.update_user_stats(test_user_id, like_count=10, follower_count=5, following_count=3)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.like_count == 10 and user.follower_count == 5 and user.following_count == 3:
            log_pass("全量更新统计", "like=10, follower=5, following=3")
        else:
            log_fail("全量更新统计", f"like={user.like_count}, follower={user.follower_count}")
    else:
        log_fail("全量更新统计", "返回 False")

    # 8.2 部分更新
    success = user_lib.update_user_stats(test_user_id, like_count=20)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.like_count == 20 and user.follower_count == 5:
            log_pass("部分更新统计", "like=20, follower保持5")
        else:
            log_fail("部分更新统计", f"like={user.like_count}, follower={user.follower_count}")

    # 8.3 负数截断
    success = user_lib.update_user_stats(test_user_id, like_count=-5)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.like_count == 0:
            log_pass("负数截断", "like_count=0")
        else:
            log_fail("负数截断", f"like_count={user.like_count}")

    # 8.4 原子增量
    success = user_lib.increment_user_stats(test_user_id, like_delta=5, follower_delta=-2)
    if success:
        user = user_lib.get_user_by_account(test_user_id)
        if user.like_count == 5 and user.follower_count == 3:
            log_pass("原子增量", "like=5, follower=3")
        else:
            log_fail("原子增量", f"like={user.like_count}, follower={user.follower_count}")

    # ========== 9. 志愿者排行榜 ==========
    print("\n9. 测试志愿者排行榜...")

    # 准备数据：创建高分和低分志愿者
    top_id = f"test_user_{uuid.uuid4().hex[:8]}"
    low_id = f"test_user_{uuid.uuid4().hex[:8]}"
    user_lib.register_user(top_id, "高分志愿者", role=2)
    user_lib.register_user(low_id, "低分志愿者", role=2)
    user_lib.add_points(top_id, 1000)
    user_lib.add_points(low_id, 10)

    ranking = user_lib.get_volunteers_ranking(limit=10)
    if ranking and len(ranking) >= 2:
        # 验证排序：高分在前
        points_list = [u.points for u in ranking]
        if points_list == sorted(points_list, reverse=True):
            log_pass("排行榜排序", "按积分降序正确")
        else:
            log_fail("排行榜排序", f"顺序错误: {points_list}")

        # 验证高分志愿者在榜
        top_in_rank = any(u.user_id == top_id for u in ranking)
        if top_in_rank:
            log_pass("高分志愿者在榜", f"points={next(u.points for u in ranking if u.user_id == top_id)}")
        else:
            log_fail("高分志愿者在榜", "未找到")
    else:
        log_fail("排行榜", f"共 {len(ranking)} 条，预期>=2")

    # 9.2 封禁的志愿者不应出现在榜
    user_lib.toggle_active_status(top_id, 0)
    ranking2 = user_lib.get_volunteers_ranking(limit=10)
    if not any(u.user_id == top_id for u in ranking2):
        log_pass("封禁志愿者不在榜", "过滤正确")
    else:
        log_fail("封禁志愿者不在榜", "仍在排行榜中")

    # ========== 10. 个人主页 ==========
    print("\n10. 测试个人主页 (get_user_profile)...")

    profile = user_lib.get_user_profile(test_user_id)
    if profile and profile['user_id'] == test_user_id:
        log_pass("获取个人主页", f"nickname={profile['nickname']}, points={profile['points']}")
    else:
        log_fail("获取个人主页", "失败")

    none_profile = user_lib.get_user_profile("not_exist")
    if none_profile is None:
        log_pass("获取不存在用户主页", "返回 None")
    else:
        log_fail("获取不存在用户主页", "返回非空")

    # ========== 11. 清理测试数据 ==========
    print("\n11. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_points_log WHERE user_id LIKE 'test_user_%'")
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_user_%'")
        db.close_database()
        log_pass("清理测试数据", "完成")
    else:
        log_fail("清理测试数据", "数据库连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
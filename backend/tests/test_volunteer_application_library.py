# ===== backend/tests/test_volunteer_application_library.py =====
"""
测试 VolunteerApplicationLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_volunteer_application_library
"""
from backend.libs.volunteer_application_library import VolunteerApplicationLibrary
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    app_lib = VolunteerApplicationLibrary()
    user_lib = UserLibrary()
    db = app_lib.db

    # 测试账号
    user_a = f"test_user_{uuid.uuid4().hex[:8]}"      # 普通用户（申请人）
    volunteer = f"test_user_{uuid.uuid4().hex[:8]}"   # 已是志愿者
    admin = f"test_user_{uuid.uuid4().hex[:8]}"       # 管理员
    banned = f"test_user_{uuid.uuid4().hex[:8]}"      # 封禁用户

    # ======== 清理旧数据 & 注册测试用户 ========
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_volunteer_application WHERE user_id LIKE 'test_user_%'"
        )
        db.execute_raw_sql(
            "DELETE FROM t_user WHERE user_id LIKE 'test_user_%'"
        )
        db.close_database()
    else:
        print("[FAIL] 数据库连接失败，测试终止")
        return

    for uid, role in [(user_a, 1), (volunteer, 2), (admin, 3), (banned, 1)]:
        user_lib.delete_user(uid)
        if not user_lib.register_user(uid, f"nick_{uid}", role=role):
            print(f"[FAIL] 注册用户 {uid} (role={role}) 失败，测试终止")
            return

    # 封禁 banned
    user_lib.toggle_active_status(banned, 0)

    print(f"已创建测试用户: A={user_a}, Volunteer={volunteer}, Admin={admin}, Banned={banned}(已封禁)")

    print("\n" + "=" * 50 + "\n  开始测试 VolunteerApplicationLibrary\n" + "=" * 50)

    # ========== 1. 提交志愿者申请 ==========
    print("\n1. 测试提交申请 (submit_volunteer_application)...")

    # 1.1 正常提交
    result = app_lib.submit_volunteer_application(user_a, apply_content="我想成为志愿者")
    if result["success"] and result["data"] and result["data"].get("application_id"):
        app1 = result["data"]["application_id"]
        log_pass("A提交申请", f"成功 application_id={app1}")
    else:
        log_fail("A提交申请", f"失败: {result}")
        return

    # 1.2 重复提交（已有待审核）
    result = app_lib.submit_volunteer_application(user_a, apply_content="再次提交")
    if not result["success"] and "已提交过" in result["message"]:
        log_pass("A重复提交", "返回已提交过申请")
    else:
        log_fail("A重复提交", f"结果异常: {result}")

    # 1.3 已是志愿者提交
    result = app_lib.submit_volunteer_application(volunteer, apply_content="test")
    if not result["success"] and "已经是志愿者" in result["message"]:
        log_pass("Volunteer提交申请", "返回已经是志愿者")
    else:
        log_fail("Volunteer提交申请", f"结果异常: {result}")

    # 1.4 管理员提交
    result = app_lib.submit_volunteer_application(admin, apply_content="test")
    if not result["success"] and "管理员无需申请" in result["message"]:
        log_pass("Admin提交申请", "返回管理员无需申请")
    else:
        log_fail("Admin提交申请", f"结果异常: {result}")

    # 1.5 封禁用户提交
    result = app_lib.submit_volunteer_application(banned, apply_content="test")
    if not result["success"] and "封禁" in result["message"]:
        log_pass("Banned提交申请", "返回用户已被封禁")
    else:
        log_fail("Banned提交申请", f"结果异常: {result}")

    # 1.6 无效用户提交
    fake_user = f"test_user_{uuid.uuid4().hex[:8]}"
    result = app_lib.submit_volunteer_application(fake_user, apply_content="test")
    if not result["success"] and "用户不存在" in result["message"]:
        log_pass("无效用户提交", "返回用户不存在")
    else:
        log_fail("无效用户提交", f"结果异常: {result}")

    # ========== 2. 查询申请详情 ==========
    print("\n2. 测试查询申请详情 (get_application_by_id)...")

    # 2.1 查询存在的
    result = app_lib.get_application_by_id(app1)
    if result["success"] and result["data"]["application_id"] == app1:
        log_pass(f"查询存在申请 {app1}", "成功")
    else:
        log_fail("查询存在申请", f"失败: {result}")

    # 2.2 查询不存在的
    fake_app = 999999
    result = app_lib.get_application_by_id(fake_app)
    if not result["success"] and "申请记录不存在" in result["message"]:
        log_pass("查询不存在申请", "返回不存在")
    else:
        log_fail("查询不存在申请", f"结果异常: {result}")

    # ========== 3. 修改申请内容 ==========
    print("\n3. 测试修改申请 (update_volunteer_application)...")

    # 3.1 正常修改
    result = app_lib.update_volunteer_application(app1, user_a, apply_content="修改后的理由")
    if result["success"]:
        detail = app_lib.get_application_by_id(app1)
        if detail["success"] and detail["data"]["apply_content"] == "修改后的理由":
            log_pass("A修改自己的申请", "验证成功")
        else:
            log_fail("A修改自己的申请", f"验证失败: {detail}")
    else:
        log_fail("A修改自己的申请", f"失败: {result}")

    # 3.2 修改他人申请
    result = app_lib.update_volunteer_application(app1, admin, apply_content="越权修改")
    if not result["success"] and "无权修改" in result["message"]:
        log_pass("Admin修改A的申请", "返回无权修改")
    else:
        log_fail("Admin修改A的申请", f"结果异常: {result}")

    # 3.3 修改不存在
    result = app_lib.update_volunteer_application(fake_app, user_a, "test")
    if not result["success"] and "申请记录不存在" in result["message"]:
        log_pass("修改不存在申请", "返回不存在")
    else:
        log_fail("修改不存在申请", f"结果异常: {result}")

    # ========== 4. 撤销申请 ==========
    print("\n4. 测试撤销申请 (cancel_volunteer_application)...")

    # 先提交一个新的用于撤销
    result_new = app_lib.submit_volunteer_application(banned, apply_content="待撤销")
    # 上面会失败因为 banned 已封禁，换个普通用户
    # 先把 banned 解封
    user_lib.toggle_active_status(banned, 1)
    result_new = app_lib.submit_volunteer_application(banned, apply_content="待撤销")
    if result_new["success"]:
        app2 = result_new["data"]["application_id"]

        # 4.1 正常撤销
        result = app_lib.cancel_volunteer_application(app2, banned)
        if result["success"] and result["data"]["status"] == 3:
            log_pass("Banned撤销自己的申请", "成功 status=3")
        else:
            log_fail("Banned撤销自己的申请", f"失败: {result}")

        # 4.2 撤销他人申请
        result = app_lib.cancel_volunteer_application(app1, banned)
        if not result["success"] and "无权撤销" in result["message"]:
            log_pass("Banned撤销A的申请", "返回无权撤销")
        else:
            log_fail("Banned撤销A的申请", f"结果异常: {result}")
    else:
        log_fail("提交待撤销申请", f"失败: {result_new}")

    # 4.3 撤销不存在
    result = app_lib.cancel_volunteer_application(fake_app, user_a)
    if not result["success"] and "申请记录不存在" in result["message"]:
        log_pass("撤销不存在申请", "返回不存在")
    else:
        log_fail("撤销不存在申请", f"结果异常: {result}")

    # 再把 banned 封禁回去（保持初始状态）
    user_lib.toggle_active_status(banned, 0)

    # ========== 5. 查询申请状态 ==========
    print("\n5. 测试查询申请状态 (get_application_status)...")
    print("  [NOTE] 若此处失败，请检查是否已修复 get_application_status 的数据库连接BUG")

    # 5.1 查询待审核
    result = app_lib.get_application_status(app1)
    if result["success"] and result["data"]["status"] == 0 and result["data"]["status_text"] == "待审核":
        log_pass("查询app1状态", "status=0 待审核")
    else:
        log_fail("查询app1状态", f"结果异常: {result}")

    # 5.2 查询不存在
    result = app_lib.get_application_status(fake_app)
    if not result["success"] and "申请记录不存在" in result["message"]:
        log_pass("查询不存在状态", "返回不存在")
    else:
        log_fail("查询不存在状态", f"结果异常: {result}")

    # ========== 6. 管理员审核通过 ==========
    print("\n6. 测试审核通过 (approve_application)...")

    # 6.1 正常通过
    result = app_lib.approve_application(app1, admin, review_comment="审核通过")
    if result["success"] and result["data"]["status"] == 1:
        log_pass("Admin通过app1", "成功 status=1")
    else:
        log_fail("Admin通过app1", f"失败: {result}")

    # 6.2 验证用户角色已变为志愿者
    result = app_lib.get_volunteer_info(user_a)
    if result["success"] and result["data"]["volunteer_id"]:
        log_pass("A已升级为志愿者", f"volunteer_id={result['data']['volunteer_id']}")
    else:
        log_fail("A已升级为志愿者", f"结果异常: {result}")

    # 6.3 重复通过
    result = app_lib.approve_application(app1, admin)
    if not result["success"] and "仅待审核" in result["message"]:
        log_pass("重复通过", "返回仅待审核可以通过")
    else:
        log_fail("重复通过", f"结果异常: {result}")

    # 6.4 非管理员通过
    # 先让 volunteer 提交一个申请
    # 先把 volunteer 降级为普通用户
    user_lib.update_role(volunteer, 1)
    result_new = app_lib.submit_volunteer_application(volunteer, apply_content="test")
    if result_new["success"]:
        app3 = result_new["data"]["application_id"]
        result = app_lib.approve_application(app3, user_a)
        if not result["success"] and "仅管理员" in result["message"]:
            log_pass("非管理员审核", "返回仅管理员可以审核")
        else:
            log_fail("非管理员审核", f"结果异常: {result}")
    else:
        log_fail("Volunteer提交申请", f"失败: {result_new}")

    # 6.5 通过不存在
    result = app_lib.approve_application(fake_app, admin)
    if not result["success"] and "申请记录不存在" in result["message"]:
        log_pass("通过不存在申请", "返回不存在")
    else:
        log_fail("通过不存在申请", f"结果异常: {result}")

    # ========== 7. 管理员驳回 ==========
    print("\n7. 测试驳回 (reject_application)...")

    # 7.1 正常驳回
    result = app_lib.reject_application(app3, admin, reason="不符合条件")
    if result["success"] and result["data"]["status"] == 2:
        log_pass("Admin驳回app3", "成功 status=2")
    else:
        log_fail("Admin驳回app3", f"失败: {result}")

    # 7.2 重复驳回
    result = app_lib.reject_application(app3, admin, reason="再次驳回")
    if not result["success"] and "仅待审核" in result["message"]:
        log_pass("重复驳回", "返回仅待审核可以驳回")
    else:
        log_fail("重复驳回", f"结果异常: {result}")

    # 7.3 非管理员驳回
    result = app_lib.reject_application(app1, volunteer, reason="test")
    if not result["success"] and "仅管理员" in result["message"]:
        log_pass("非管理员驳回", "返回仅管理员可以审核")
    else:
        log_fail("非管理员驳回", f"结果异常: {result}")

    # ========== 8. 查询用户申请列表 ==========
    print("\n8. 测试查询用户申请列表 (get_user_applications)...")

    # A 现在有 app1（已通过），可能还有别的
    result = app_lib.get_user_applications(user_a, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("A的申请列表", f"total={result['data']['total']}")
    else:
        log_fail("A的申请列表", f"结果异常: {result}")

    # 分页
    result = app_lib.get_user_applications(user_a, page=1, page_size=1)
    if result["success"] and len(result["data"]["applications"]) == 1:
        log_pass("分页 limit=1", "返回1条")
    else:
        log_fail("分页 limit=1", f"返回{len(result['data']['applications'])}条")

    # ========== 9. 查询所有申请（管理员视角） ==========
    print("\n9. 测试查询所有申请 (get_all_applications)...")

    result = app_lib.get_all_applications(page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("查询所有申请", f"total={result['data']['total']}")
    else:
        log_fail("查询所有申请", f"结果异常: {result}")

    # 按状态筛选
    result = app_lib.get_all_applications(page=1, page_size=20, status_filter=1)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("筛选状态1(已通过)", f"total={result['data']['total']}")
    else:
        log_fail("筛选状态1", f"结果异常: {result}")

    result = app_lib.get_all_applications(page=1, page_size=20, status_filter=2)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("筛选状态2(已驳回)", f"total={result['data']['total']}")
    else:
        log_fail("筛选状态2", f"结果异常: {result}")

    # ========== 10. 查询待审核列表 ==========
    print("\n10. 测试查询待审核列表 (get_pending_applications)...")

    result = app_lib.get_pending_applications(page=1, page_size=20)
    if result["success"]:
        log_pass("待审核列表", f"total={result['data']['total']}")
    else:
        log_fail("待审核列表", f"结果异常: {result}")

    # ========== 11. 志愿者信息查询 ==========
    print("\n11. 测试志愿者信息查询...")
    print("  [NOTE] 若此处失败，请检查是否已修复 get_volunteer_info/number/level 的数据库连接BUG")

    # 11.1 查询志愿者信息
    result = app_lib.get_volunteer_info(user_a)
    if result["success"] and result["data"]["user_id"] == user_a:
        log_pass("查询A的志愿者信息", "成功")
    else:
        log_fail("查询A的志愿者信息", f"失败: {result}")

    # 11.2 查询非志愿者
    result = app_lib.get_volunteer_info(admin)
    if not result["success"] and "不是志愿者" in result["message"]:
        log_pass("查询Admin志愿者信息", "返回不是志愿者")
    else:
        log_fail("查询Admin志愿者信息", f"结果异常: {result}")

    # 11.3 查询志愿者编号
    result = app_lib.get_volunteer_number(user_a)
    if result["success"] and result["data"]["volunteer_id"]:
        log_pass("查询A的志愿者编号", f"成功 {result['data']['volunteer_id']}")
    else:
        log_fail("查询A的志愿者编号", f"失败: {result}")

    # 11.4 查询非志愿者编号
    result = app_lib.get_volunteer_number(admin)
    if result["success"] and result["data"]["volunteer_id"] is None:
        log_pass("查询Admin志愿者编号", "返回None")
    else:
        log_fail("查询Admin志愿者编号", f"结果异常: {result}")

    # 11.5 查询志愿者等级
    result = app_lib.get_volunteer_level(user_a)
    if result["success"] and result["data"]["level"] == 1:
        log_pass("查询A的志愿者等级", "level=1")
    else:
        log_fail("查询A的志愿者等级", f"结果异常: {result}")

    # ========== 12. 更新志愿者等级 ==========
    print("\n12. 测试更新志愿者等级 (update_volunteer_level)...")

    # 12.1 正常更新
    result = app_lib.update_volunteer_level(user_a, 3, admin)
    if result["success"] and result["data"]["level"] == 3:
        log_pass("Admin更新A等级为3", "成功")
    else:
        log_fail("Admin更新A等级为3", f"失败: {result}")

    # 12.2 验证
    result = app_lib.get_volunteer_level(user_a)
    if result["success"] and result["data"]["level"] == 3:
        log_pass("验证A等级", "level=3")
    else:
        log_fail("验证A等级", f"结果异常: {result}")

    # 12.3 非管理员更新
    result = app_lib.update_volunteer_level(user_a, 5, volunteer)
    if not result["success"] and "仅管理员" in result["message"]:
        log_pass("非管理员更新等级", "返回仅管理员可以修改")
    else:
        log_fail("非管理员更新等级", f"结果异常: {result}")

    # 12.4 更新非志愿者等级
    result = app_lib.update_volunteer_level(admin, 2, admin)
    if not result["success"] and "不是志愿者" in result["message"]:
        log_pass("更新非志愿者等级", "返回不是志愿者")
    else:
        log_fail("更新非志愿者等级", f"结果异常: {result}")

    # 12.5 无效等级
    result = app_lib.update_volunteer_level(user_a, 0, admin)
    if not result["success"] and "正整数" in result["message"]:
        log_pass("更新等级为0", "返回等级必须为正整数")
    else:
        log_fail("更新等级为0", f"结果异常: {result}")

    # ========== 13. 统计功能 ==========
    print("\n13. 测试统计功能...")

    # 13.1 各状态申请数量
    result = app_lib.count_applications_by_status()
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("各状态统计", f"total={result['data']['total']}")
    else:
        log_fail("各状态统计", f"结果异常: {result}")

    # 13.2 已批准志愿者人数
    result = app_lib.count_approved_volunteers()
    if result["success"] and result["data"]["count"] >= 1:
        log_pass("已批准志愿者人数", f"count={result['data']['count']}")
    else:
        log_fail("已批准志愿者人数", f"结果异常: {result}")

    # ========== 14. 清理 ==========
    print("\n14. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_volunteer_application WHERE user_id IN (%s, %s, %s, %s)",
            (user_a, volunteer, admin, banned)
        )
        db.execute_raw_sql(
            "DELETE FROM t_user WHERE user_id IN (%s, %s, %s, %s)",
            (user_a, volunteer, admin, banned)
        )
        db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
# ===== backend/tests/test_reimbursement_library.py =====
"""
测试 ReimbursementLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_reimbursement_library
"""
from backend.libs.reimbursement_library import ReimbursementLibrary
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    reimb_lib = ReimbursementLibrary()
    user_lib = UserLibrary()
    db = reimb_lib.db

    # 测试账号
    user_a = f"test_user_{uuid.uuid4().hex[:8]}"
    user_b = f"test_user_{uuid.uuid4().hex[:8]}"
    admin = f"test_admin_{uuid.uuid4().hex[:8]}"

    # ======== 清理旧数据 & 注册测试用户 ========
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_reimbursement WHERE user_id LIKE 'test_user_%' OR user_id LIKE 'test_admin_%'"
        )
        db.execute_raw_sql(
            "DELETE FROM t_user WHERE user_id LIKE 'test_user_%' OR user_id LIKE 'test_admin_%'"
        )
        db.close_database()
    else:
        print("[FAIL] 数据库连接失败，测试终止")
        return

    for uid, role in [(user_a, 1), (user_b, 1), (admin, 3)]:
        user_lib.delete_user(uid)
        if not user_lib.register_user(uid, f"nick_{uid}", role=role):
            print(f"[FAIL] 注册用户 {uid} (role={role}) 失败，测试终止")
            return

    # 封禁 user_b（用于测试封禁用户提交）
    user_lib.toggle_active_status(user_b, 0)

    print(f"已创建测试用户: A={user_a}, B={user_b}(已封禁), Admin={admin}")

    print("\n" + "=" * 50 + "\n  开始测试 ReimbursementLibrary\n" + "=" * 50)

    # ========== 1. 提交报销申请 ==========
    print("\n1. 测试提交报销 (submit_reimbursement)...")

    # 1.1 正常提交
    result = reimb_lib.submit_reimbursement(
        user_a, 100.50, type_="医疗费", description="看病", receipt_urls='["url1"]'
    )
    if result["success"] and result["data"] and result["data"].get("reimb_id"):
        reimb1 = result["data"]["reimb_id"]
        log_pass("A提交报销", f"成功 reimb_id={reimb1}")
    else:
        log_fail("A提交报销", f"失败: {result}")
        return

    # 再提交一个用于后续测试
    result2 = reimb_lib.submit_reimbursement(user_a, 200.00, type_="运输费")
    if result2["success"]:
        reimb2 = result2["data"]["reimb_id"]
        log_pass("A再提交报销", f"成功 reimb_id={reimb2}")
    else:
        log_fail("A再提交报销", f"失败: {result2}")
        return

    # 1.2 无效用户
    fake_user = f"test_user_{uuid.uuid4().hex[:8]}"
    result = reimb_lib.submit_reimbursement(fake_user, 50.0)
    if not result["success"] and "用户不存在" in result["message"]:
        log_pass("无效用户提交", "返回用户不存在")
    else:
        log_fail("无效用户提交", f"结果异常: {result}")

    # 1.3 封禁用户
    result = reimb_lib.submit_reimbursement(user_b, 50.0)
    if not result["success"] and "封禁" in result["message"]:
        log_pass("封禁用户提交", "返回用户已被封禁")
    else:
        log_fail("封禁用户提交", f"结果异常: {result}")

    # ========== 2. 修改报销申请 ==========
    print("\n2. 测试修改报销 (update_reimbursement)...")

    # 2.1 正常修改
    result = reimb_lib.update_reimbursement(
        reimb1, user_a, amount=150.00, description="修改后说明"
    )
    if result["success"]:
        detail = reimb_lib.get_reimbursement_by_id(reimb1)
        if (detail["success"] and detail["data"]["amount"] == 150.00
                and detail["data"]["description"] == "修改后说明"):
            log_pass("A修改自己的报销", "验证成功 amount=150.00")
        else:
            log_fail("A修改自己的报销", f"验证失败: {detail}")
    else:
        log_fail("A修改自己的报销", f"失败: {result}")

    # 2.2 修改他人报销
    result = reimb_lib.update_reimbursement(reimb1, user_b, amount=999.00)
    if not result["success"] and "无权修改" in result["message"]:
        log_pass("B修改A的报销", "返回无权修改")
    else:
        log_fail("B修改A的报销", f"结果异常: {result}")

    # 2.3 修改不存在的报销
    fake_reimb = f"test_reimb_{uuid.uuid4().hex[:8]}"
    result = reimb_lib.update_reimbursement(fake_reimb, user_a, amount=1.00)
    if not result["success"] and "报销记录不存在" in result["message"]:
        log_pass("修改不存在报销", "返回不存在")
    else:
        log_fail("修改不存在报销", f"结果异常: {result}")

    # ========== 3. 撤销报销申请 ==========
    print("\n3. 测试撤销报销 (cancel_reimbursement)...")

    # 3.1 正常撤销 reimb2
    result = reimb_lib.cancel_reimbursement(reimb2, user_a)
    if result["success"] and result["data"].get("status") == 3:
        log_pass("A撤销自己的报销", "成功 status=3")
    else:
        log_fail("A撤销自己的报销", f"失败: {result}")

    # 3.2 撤销他人报销
    result = reimb_lib.cancel_reimbursement(reimb1, user_b)
    if not result["success"] and "无权撤销" in result["message"]:
        log_pass("B撤销A的报销", "返回无权撤销")
    else:
        log_fail("B撤销A的报销", f"结果异常: {result}")

    # 3.3 撤销已审核的报销（先把 reimb1 通过）
    reimb_lib.approve_reimbursement(reimb1, admin)
    result = reimb_lib.cancel_reimbursement(reimb1, user_a)
    if not result["success"] and "仅待审核" in result["message"]:
        log_pass("撤销已审核报销", "返回仅待审核可以撤销")
    else:
        log_fail("撤销已审核报销", f"结果异常: {result}")

    # 3.4 撤销不存在的
    result = reimb_lib.cancel_reimbursement(fake_reimb, user_a)
    if not result["success"] and "报销记录不存在" in result["message"]:
        log_pass("撤销不存在报销", "返回不存在")
    else:
        log_fail("撤销不存在报销", f"结果异常: {result}")

    # ========== 4. 查询报销详情 ==========
    print("\n4. 测试查询报销详情 (get_reimbursement_by_id)...")

    # 4.1 查询存在的（reimb1 已通过）
    result = reimb_lib.get_reimbursement_by_id(reimb1)
    if result["success"] and result["data"]["reimb_id"] == reimb1:
        log_pass(f"查询存在报销 {reimb1}", "成功")
    else:
        log_fail("查询存在报销", f"失败: {result}")

    # 4.2 查询不存在的
    result = reimb_lib.get_reimbursement_by_id(fake_reimb)
    if not result["success"] and "报销记录不存在" in result["message"]:
        log_pass("查询不存在报销", "返回不存在")
    else:
        log_fail("查询不存在报销", f"结果异常: {result}")

    # ========== 5. 查询用户报销列表 ==========
    print("\n5. 测试查询用户报销列表 (get_user_reimbursements)...")

    # 先再提交一个给 A，确保列表有数据
    result3 = reimb_lib.submit_reimbursement(user_a, 50.0)
    reimb3 = result3["data"]["reimb_id"] if result3["success"] else None

    result = reimb_lib.get_user_reimbursements(user_a, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("A的报销列表", f"total={result['data']['total']}")
    else:
        log_fail("A的报销列表", f"结果异常: {result}")

    # 分页
    result = reimb_lib.get_user_reimbursements(user_a, page=1, page_size=1)
    if result["success"] and len(result["data"]["reimbursements"]) == 1:
        log_pass("分页 limit=1", "返回1条")
    else:
        log_fail("分页 limit=1", f"返回{len(result['data']['reimbursements'])}条")

    # ========== 6. 查询所有报销（管理员视角） ==========
    print("\n6. 测试查询所有报销 (get_all_reimbursements)...")

    result = reimb_lib.get_all_reimbursements(page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("查询所有报销", f"total={result['data']['total']}")
    else:
        log_fail("查询所有报销", f"结果异常: {result}")

    # 按状态筛选（status=0 待审核）
    if reimb3:
        result = reimb_lib.get_all_reimbursements(page=1, page_size=20, status_filter=0)
        if result["success"] and result["data"]["total"] >= 1:
            log_pass("筛选状态0", f"total={result['data']['total']}")
        else:
            log_fail("筛选状态0", f"结果异常: {result}")

    # 按状态筛选（status=1 已通过）
    result = reimb_lib.get_all_reimbursements(page=1, page_size=20, status_filter=1)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("筛选状态1", f"total={result['data']['total']}")
    else:
        log_fail("筛选状态1", f"结果异常: {result}")

    # 按状态筛选（status=3 已撤销）
    result = reimb_lib.get_all_reimbursements(page=1, page_size=20, status_filter=3)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("筛选状态3", f"total={result['data']['total']}")
    else:
        log_fail("筛选状态3", f"结果异常: {result}")

    # ========== 7. 管理员审核通过 ==========
    print("\n7. 测试审核通过 (approve_reimbursement)...")

    # 7.1 通过 reimb3（它是待审核）
    if reimb3:
        result = reimb_lib.approve_reimbursement(reimb3, admin, review_comment="同意报销")
        if result["success"] and result["data"]["status"] == 1:
            log_pass("Admin通过reimb3", "成功 status=1")
        else:
            log_fail("Admin通过reimb3", f"失败: {result}")
    else:
        log_fail("Admin通过reimb3", "reimb3未创建")

    # 7.2 重复通过（reimb1 已经是已通过）
    result = reimb_lib.approve_reimbursement(reimb1, admin)
    if not result["success"] and "仅待审核" in result["message"]:
        log_pass("重复通过已审核", "返回仅待审核可以通过")
    else:
        log_fail("重复通过已审核", f"结果异常: {result}")

    # 7.3 通过不存在的
    result = reimb_lib.approve_reimbursement(fake_reimb, admin)
    if not result["success"] and "报销记录不存在" in result["message"]:
        log_pass("通过不存在报销", "返回不存在")
    else:
        log_fail("通过不存在报销", f"结果异常: {result}")

    # ========== 8. 管理员驳回 ==========
    print("\n8. 测试驳回 (reject_reimbursement)...")

    # 先提交一个新的用于驳回
    result_new = reimb_lib.submit_reimbursement(user_a, 75.0, type_="餐饮费")
    if result_new["success"]:
        reimb4 = result_new["data"]["reimb_id"]

        # 8.1 正常驳回
        result = reimb_lib.reject_reimbursement(reimb4, admin, reason="票据不全")
        if result["success"] and result["data"]["status"] == 2:
            log_pass("Admin驳回reimb4", "成功 status=2")
        else:
            log_fail("Admin驳回reimb4", f"失败: {result}")

        # 8.2 重复驳回
        result = reimb_lib.reject_reimbursement(reimb4, admin, reason="再次驳回")
        if not result["success"] and "仅待审核" in result["message"]:
            log_pass("重复驳回", "返回仅待审核可以驳回")
        else:
            log_fail("重复驳回", f"结果异常: {result}")
    else:
        log_fail("提交待驳回报销", f"失败: {result_new}")

    # 8.3 驳回不存在的
    result = reimb_lib.reject_reimbursement(fake_reimb, admin, reason="test")
    if not result["success"] and "报销记录不存在" in result["message"]:
        log_pass("驳回不存在报销", "返回不存在")
    else:
        log_fail("驳回不存在报销", f"结果异常: {result}")

    # ========== 9. 查询报销状态 ==========
    print("\n9. 测试查询报销状态 (get_reimbursement_status)...")
    print("  [NOTE] 若此处全部失败，请检查是否已修复 get_reimbursement_status 的数据库连接BUG")

    # 9.1 查询已通过
    result = reimb_lib.get_reimbursement_status(reimb1)
    if result["success"] and result["data"]["status"] == 1 and result["data"]["status_text"] == "已通过":
        log_pass("查询已通过状态", "status=1 已通过")
    else:
        log_fail("查询已通过状态", f"结果异常: {result}")

    # 9.2 查询已撤销
    result = reimb_lib.get_reimbursement_status(reimb2)
    if result["success"] and result["data"]["status"] == 3 and result["data"]["status_text"] == "已撤销":
        log_pass("查询已撤销状态", "status=3 已撤销")
    else:
        log_fail("查询已撤销状态", f"结果异常: {result}")

    # 9.3 查询不存在
    result = reimb_lib.get_reimbursement_status(fake_reimb)
    if not result["success"] and "报销记录不存在" in result["message"]:
        log_pass("查询不存在状态", "返回不存在")
    else:
        log_fail("查询不存在状态", f"结果异常: {result}")

    # ========== 10. 统计报销数量 ==========
    print("\n10. 测试统计报销数量 (get_reimbursement_count_by_status)...")

    # 10.1 全部统计
    result = reimb_lib.get_reimbursement_count_by_status()
    if result["success"] and result["data"]["total"] >= 4:
        log_pass("全部统计", f"total={result['data']['total']}")
    else:
        log_fail("全部统计", f"结果异常: {result}")

    # 10.2 按状态统计
    result = reimb_lib.get_reimbursement_count_by_status(status=1)
    if result["success"] and result["data"]["count"] >= 2:
        log_pass("统计状态1", f"count={result['data']['count']}")
    else:
        log_fail("统计状态1", f"结果异常: {result}")

    # ========== 11. 清理 ==========
    print("\n11. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_reimbursement WHERE user_id IN (%s, %s, %s)",
            (user_a, user_b, admin)
        )
        db.execute_raw_sql(
            "DELETE FROM t_user WHERE user_id IN (%s, %s, %s)",
            (user_a, user_b, admin)
        )
        db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
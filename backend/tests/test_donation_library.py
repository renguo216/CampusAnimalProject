# ===== backend/tests/test_donation_library.py =====
"""
测试 DonationLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_donation_library
"""
from backend.libs.donation_library import DonationLibrary
from backend.libs.user_library import UserLibrary
from backend.utils.db_manager import DatabaseManager
import uuid
from datetime import datetime


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    donation_lib = DonationLibrary()
    user_lib = UserLibrary()
    db = donation_lib.db

    # ======== 清理旧测试数据 ========
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_donation WHERE user_id LIKE 'test_donation_user_%'")
        db.execute_raw_sql("DELETE FROM t_donation_project WHERE title LIKE '测试项目_%'")
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_donation_user_%'")
        db.close_database()
        print("已清理旧测试数据")
    else:
        print("⚠️ 清理旧数据时数据库连接失败")

    # ======== 准备测试数据 ========
    test_user_id = f"test_donation_user_{uuid.uuid4().hex[:6]}"
    test_user2_id = f"test_donation_user_{uuid.uuid4().hex[:6]}"
    test_admin_id = f"test_donation_user_{uuid.uuid4().hex[:6]}"
    test_nickname = "测试捐赠人"
    test_nickname2 = "测试捐赠人2"
    test_admin_nickname = "测试管理员"
    test_avatar = "http://example.com/avatar.jpg"

    # 核心测试变量：必须在所有测试逻辑之前定义
    test_project_id = 1
    test_amount = 50.00

    # 注册用户
    user_lib.register_user(test_user_id, test_nickname, test_avatar, role=1)
    user_lib.register_user(test_user2_id, test_nickname2, test_avatar, role=1)
    user_lib.register_user(test_admin_id, test_admin_nickname, test_avatar, role=3)
    log_pass("准备测试用户", f"user1={test_user_id}, user2={test_user2_id}, admin={test_admin_id}")

    # 创建测试募捐项目（进行中 status=1）
    test_project_title = f"测试项目_{uuid.uuid4().hex[:6]}"
    project_insert_sql = """INSERT INTO t_donation_project (project_id, title, description, target_amount, current_amount, participant_count, status, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    if db.open_database():
        db.execute_raw_sql(project_insert_sql, (1, test_project_title, "这是一个测试项目", 1000.00, 0.00, 0, 1, datetime.now()))
        db.close_database()
        log_pass("创建测试项目", f"project_id=1, title={test_project_title}")
    else:
        log_fail("创建测试项目", "数据库连接失败")

    # ========== 1. 测试检查重复捐赠（无重复） ==========
    print("\n" + "=" * 50 + "\n  开始测试 DonationLibrary\n" + "=" * 50)
    print("\n1. 测试检查重复捐赠 (check_duplicate_donation)...")
    db.open_database()  # 显式打开连接，供 check_duplicate_donation 使用
    result = donation_lib.check_duplicate_donation(test_user_id, test_project_id)
    db.close_database()
    if result["success"] and not result["data"]["is_duplicate"]:
        log_pass("检查无重复捐赠", "is_duplicate=False")
    else:
        log_fail("检查无重复捐赠", f"is_duplicate={result['data']['is_duplicate']}")

    # ========== 2. 测试提交捐赠 ==========
    print("\n2. 测试提交捐赠 (submit_donation)...")
    # 2.1 正常提交
    result = donation_lib.submit_donation(test_user_id, test_project_id, test_amount)
    if result["success"]:
        donation_id = result["data"]["donation_id"]
        log_pass(f"用户 {test_user_id} 提交捐赠，金额={test_amount}", f"返回 donation_id={donation_id}, status=0")
    else:
        log_fail("用户提交捐赠", f"失败，信息={result['message']}")
        donation_id = None

    # 2.2 用户不存在
    result = donation_lib.submit_donation("not_exist_user", test_project_id, 10.00)
    if not result["success"] and "用户不存在" in result["message"]:
        log_pass("用户不存在时提交捐赠", f"返回 False, message={result['message']}")
    else:
        log_fail("用户不存在时提交捐赠", f"返回 {result['success']}, message={result['message']}")

    # 2.3 项目不存在
    result = donation_lib.submit_donation(test_user_id, 999999, 10.00)
    if not result["success"] and "募捐项目不存在" in result["message"]:
        log_pass("项目不存在时提交捐赠", f"返回 False, message={result['message']}")
    else:
        log_fail("项目不存在时提交捐赠", f"返回 {result['success']}, message={result['message']}")

    # 2.4 重复提交
    result = donation_lib.submit_donation(test_user_id, test_project_id, 20.00)
    if not result["success"] and "重复提交" in result["message"]:
        log_pass("重复提交捐赠", f"返回 False, message={result['message']}")
    else:
        log_fail("重复提交捐赠", f"返回 {result['success']}，预期 False")

    # ========== 3. 测试查询捐赠详情 ==========
    print("\n3. 测试查询捐赠详情 (get_donation_by_id)...")
    # 3.1 查询已存在的捐赠
    if donation_id:
        detail = donation_lib.get_donation_by_id(donation_id)
        if detail["success"] and detail["data"]["donation_id"] == donation_id:
            log_pass(f"查询已存在捐赠，donation_id={donation_id}", f"返回捐赠详情，金额={detail['data']['amount']}, status={detail['data']['status']}")
        else:
            log_fail("查询已存在捐赠", "失败")
    else:
        log_fail("查询已存在捐赠，但 donation_id 为空", "")

    # 3.2 查询不存在的捐赠
    result = donation_lib.get_donation_by_id("not_exist_donation")
    if not result["success"] and "捐赠记录不存在" in result["message"]:
        log_pass("查询不存在的捐赠", f"返回 False, message={result['message']}")
    else:
        log_fail("查询不存在的捐赠", f"返回 {result['success']}，预期 False")

    # ========== 4. 测试用户捐赠列表 ==========
    print("\n4. 测试用户捐赠列表 (get_user_donations)...")
    result = donation_lib.get_user_donations(test_user_id, page=1, page_size=10)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass(f"查询用户 {test_user_id} 的捐赠列表", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("查询用户捐赠列表", f"失败或条数不对，total={result['data']['total']}")

    # ========== 5. 测试项目捐赠列表 ==========
    print("\n5. 测试项目捐赠列表 (get_project_donations)...")
    result = donation_lib.get_project_donations(test_project_id, page=1, page_size=10)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass(f"查询项目 {test_project_id} 的捐赠列表", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("查询项目捐赠列表", f"失败或条数不对，total={result['data']['total']}")

    # ========== 6. 测试管理员审核通过 ==========
    print("\n6. 测试管理员审核通过 (approve_donation)...")
    if donation_id:
        result = donation_lib.approve_donation(donation_id, test_admin_id)
        if result["success"]:
            log_pass(f"管理员审核通过捐赠 {donation_id}", "返回 True, status 更新为 1")
        else:
            log_fail("管理员审核通过捐赠", f"失败，message={result['message']}")

        # 验证状态
        detail = donation_lib.get_donation_by_id(donation_id)
        if detail["success"] and detail["data"]["status"] == 1:
            log_pass("验证捐赠状态", "status 已更新为 1")
        else:
            log_fail("验证捐赠状态", f"status 未更新为 1, 当前={detail['data']['status']}")
    else:
        log_fail("管理员审核通过捐赠，但 donation_id 为空", "")

    # ========== 7. 测试管理员驳回捐赠 ==========
    print("\n7. 测试管理员驳回捐赠 (reject_donation)...")
    # 创建一条新的待审核捐赠用于驳回测试
    new_donation_result = donation_lib.submit_donation(test_user2_id, test_project_id, 30.00)
    if new_donation_result["success"]:
        new_donation_id = new_donation_result["data"]["donation_id"]
        result = donation_lib.reject_donation(new_donation_id, test_admin_id, "金额不符合规定")
        if result["success"]:
            log_pass(f"管理员驳回捐赠 {new_donation_id}", "返回 True, status 更新为 2, review_comment='金额不符合规定'")
            # 验证状态
            detail = donation_lib.get_donation_by_id(new_donation_id)
            if detail["success"] and detail["data"]["status"] == 2:
                log_pass("验证驳回状态", "status 已更新为 2")
            else:
                log_fail("验证驳回状态", f"status 未更新为 2")
        else:
            log_fail("管理员驳回捐赠", f"失败，message={result['message']}")
    else:
        log_fail("创建用于驳回的捐赠失败", f"message={new_donation_result['message']}")

    # ========== 8. 测试取消捐赠 ==========
    print("\n8. 测试取消捐赠 (cancel_donation)...")
    # 创建一条新的待审核捐赠用于取消测试
    cancel_donation_result = donation_lib.submit_donation(test_user2_id, test_project_id, 15.00)
    if cancel_donation_result["success"]:
        cancel_donation_id = cancel_donation_result["data"]["donation_id"]
        result = donation_lib.cancel_donation(cancel_donation_id, test_user2_id)
        if result["success"]:
            log_pass(f"用户 {test_user2_id} 取消捐赠 {cancel_donation_id}", "返回 True, status 更新为 3")
            # 验证状态
            detail = donation_lib.get_donation_by_id(cancel_donation_id)
            if detail["success"] and detail["data"]["status"] == 3:
                log_pass("验证取消状态", "status 已更新为 3")
            else:
                log_fail("验证取消状态", f"status 未更新为 3")
        else:
            log_fail("用户取消捐赠", f"失败，message={result['message']}")
    else:
        log_fail("创建用于取消的捐赠失败", f"message={cancel_donation_result['message']}")

    # ========== 9. 测试项目统计 ==========
    print("\n9. 测试项目统计 (get_donation_summary_by_project)...")
    result = donation_lib.get_donation_summary_by_project(test_project_id)
    if result["success"]:
        data = result["data"]
        log_pass(f"获取项目 {test_project_id} 统计", f"总金额={data['total_amount']}, 参与人数={data['participant_count']}")
    else:
        log_fail("获取项目统计", f"失败，message={result['message']}")

    # ========== 10. 测试管理员获取所有捐赠 ==========
    print("\n10. 测试管理员获取所有捐赠 (get_all_donations)...")
    # 10.1 不筛选状态
    result = donation_lib.get_all_donations(page=1, page_size=10)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("获取所有捐赠记录（无筛选）", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("获取所有捐赠记录", f"失败或条数不对，total={result['data']['total']}")

    # 10.2 按状态筛选
    result = donation_lib.get_all_donations(page=1, page_size=10, status_filter=1)
    if result["success"]:
        log_pass("按状态筛选捐赠记录（status=1）", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("按状态筛选捐赠记录（status=1）", f"失败，message={result['message']}")

    # ========== 11. 清理测试数据 ==========
    print("\n11. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_donation WHERE user_id LIKE 'test_donation_user_%'")
        db.execute_raw_sql("DELETE FROM t_donation_project WHERE title LIKE '测试项目_%'")
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_donation_user_%'")
        db.close_database()
        log_pass("清理测试数据", "删除所有 test_donation_user_* 数据")
    else:
        log_fail("清理测试数据", "数据库连接失败，请手动删除")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
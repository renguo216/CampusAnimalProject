# ===== backend/tests/test_donation_project_library.py =====
"""
测试 DonationProjectLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_donation_project_library
"""
from backend.libs.donation_project_library import DonationProjectLibrary
from backend.utils.db_manager import DatabaseManager
import uuid
from datetime import datetime


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    project_lib = DonationProjectLibrary()
    db = project_lib.db

    # ======== 清理旧测试数据 ========
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_donation_project WHERE title LIKE '测试项目_%'")
        db.close_database()
        print("已清理旧测试数据")
    else:
        print("⚠️ 清理旧数据时数据库连接失败")

    # ======== 准备测试数据 ========
    test_title = f"测试项目_{uuid.uuid4().hex[:6]}"
    test_description = "这是一个测试募捐项目"
    test_target_amount = 1000.00

    # ========== 1. 测试创建募捐项目 ==========
    print("\n" + "=" * 50 + "\n  开始测试 DonationProjectLibrary\n" + "=" * 50)
    print("\n1. 测试创建募捐项目 (create_project)...")

    # 1.1 正常创建
    result = project_lib.create_project(test_title, test_description, test_target_amount)
    if result["success"] and result["data"] and result["data"].get("project_id"):
        project_id = result["data"]["project_id"]
        log_pass(f"创建募捐项目，title={test_title}", f"project_id={project_id}")
    else:
        log_fail("创建募捐项目", f"失败，message={result['message']}")
        project_id = None

    # 1.2 标题为空
    result = project_lib.create_project("", "描述", 100.0)
    if not result["success"] and "标题不能为空" in result["message"]:
        log_pass("标题为空时创建项目", f"返回 False, message={result['message']}")
    else:
        log_fail("标题为空时创建项目", f"返回 {result['success']}, message={result['message']}")

    # 1.3 标题为纯空格
    result = project_lib.create_project("   ", "描述", 100.0)
    if not result["success"] and "标题不能为空" in result["message"]:
        log_pass("标题为纯空格时创建项目", f"返回 False, message={result['message']}")
    else:
        log_fail("标题为纯空格时创建项目", f"返回 {result['success']}, message={result['message']}")

    # ========== 2. 测试查询募捐项目详情 ==========
    print("\n2. 测试查询募捐项目详情 (get_project_by_id)...")
    if project_id:
        result = project_lib.get_project_by_id(project_id)
        if result["success"] and result["data"]["project_id"] == project_id:
            log_pass(f"查询项目 {project_id}", f"title={result['data']['title']}, target_amount={result['data']['target_amount']}")
        else:
            log_fail("查询项目详情", f"失败，message={result['message']}")

        # 2.2 查询不存在的项目
        result = project_lib.get_project_by_id(999999)
        if not result["success"] and "不存在" in result["message"]:
            log_pass("查询不存在的项目", f"返回 False, message={result['message']}")
        else:
            log_fail("查询不存在的项目", f"返回 {result['success']}, message={result['message']}")
    else:
        log_fail("查询项目详情，但 project_id 为空", "")

    # ========== 3. 测试更新募捐项目 ==========
    print("\n3. 测试更新募捐项目 (update_project)...")
    if project_id:
        # 3.1 正常更新
        new_title = f"更新后的_{test_title}"
        update_data = {"title": new_title, "description": "更新后的描述", "target_amount": 2000.00}
        result = project_lib.update_project(project_id, update_data)
        if result["success"]:
            log_pass(f"更新项目 {project_id}", "返回 True")
            # 验证更新结果
            detail = project_lib.get_project_by_id(project_id)
            if detail["success"] and detail["data"]["title"] == new_title:
                log_pass("验证更新结果", f"title 已更新为 {new_title}")
            else:
                log_fail("验证更新结果", "title 未更新")
        else:
            log_fail("更新项目", f"失败，message={result['message']}")

        # 3.2 更新不存在的项目
        result = project_lib.update_project(999999, {"title": "不存在"})
        if not result["success"] and "不存在" in result["message"]:
            log_pass("更新不存在的项目", f"返回 False, message={result['message']}")
        else:
            log_fail("更新不存在的项目", f"返回 {result['success']}, message={result['message']}")

        # 3.3 更新不允许的字段（current_amount / participant_count 应该被过滤）
        result = project_lib.update_project(project_id, {"current_amount": 9999.00, "participant_count": 999})
        if not result["success"] and "没有需要更新的有效字段" in result["message"]:
            log_pass("更新不允许的字段", f"返回 False, message={result['message']}")
        else:
            detail = project_lib.get_project_by_id(project_id)
            if detail["success"] and detail["data"]["current_amount"] != 9999.00:
                log_pass("更新不允许的字段", "字段被正确过滤，未更新")
            else:
                log_fail("更新不允许的字段", f"current_amount 被错误更新为 {detail['data']['current_amount']}")

        # 3.4 空更新数据
        result = project_lib.update_project(project_id, {})
        if not result["success"] and "没有需要更新的有效字段" in result["message"]:
            log_pass("空更新数据", f"返回 False, message={result['message']}")
        else:
            log_fail("空更新数据", f"返回 {result['success']}, message={result['message']}")
    else:
        log_fail("更新项目测试，但 project_id 为空", "")

    # ========== 4. 测试获取所有募捐项目 ==========
    print("\n4. 测试获取所有募捐项目 (get_all_projects)...")
    result = project_lib.get_all_projects(page=1, page_size=10)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("获取所有项目列表", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("获取所有项目列表", f"失败或条数不对，total={result['data']['total']}")

    # ========== 5. 测试按状态筛选 ==========
    print("\n5. 测试按状态筛选 (get_projects_by_status)...")
    # 5.1 筛选进行中（status=1）
    result = project_lib.get_projects_by_status(status=1, page=1, page_size=10)
    if result["success"]:
        log_pass("筛选状态=1的项目", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("筛选状态=1的项目", f"失败，message={result['message']}")

    # 5.2 筛选已结束（status=0）
    result = project_lib.get_projects_by_status(status=0, page=1, page_size=10)
    if result["success"]:
        log_pass("筛选状态=0的项目", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("筛选状态=0的项目", f"失败，message={result['message']}")

    # ========== 6. 测试模糊搜索 ==========
    print("\n6. 测试模糊搜索 (search_projects_by_title)...")
    # 6.1 搜索存在的项目
    result = project_lib.search_projects_by_title(keyword=test_title[:4], page=1, page_size=10)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass(f"搜索关键字 '{test_title[:4]}'", f"共 {result['data']['total']} 条记录")
    else:
        log_fail("模糊搜索", f"失败或条数不对，total={result['data']['total']}")

    # 6.2 搜索不存在的项目
    result = project_lib.search_projects_by_title(keyword="不存在的项目关键字12345", page=1, page_size=10)
    if result["success"] and result["data"]["total"] == 0:
        log_pass("搜索不存在的项目", "共 0 条记录")
    else:
        log_fail("搜索不存在的项目", f"total={result['data']['total']}")

    # ========== 7. 测试项目统计摘要 ==========
    print("\n7. 测试项目统计摘要 (get_project_summary)...")
    if project_id:
        result = project_lib.get_project_summary(project_id)
        if result["success"] and result["data"]["project_id"] == project_id:
            data = result["data"]
            log_pass(f"获取项目 {project_id} 摘要",
                     f"target={data['target_amount']}, current={data['current_amount']}, "
                     f"completion={data['completion_percentage']}%, donations={data['total_donation_count']}")
        else:
            log_fail("获取项目统计摘要", f"失败，message={result['message']}")

        # 7.2 查询不存在的项目摘要
        result = project_lib.get_project_summary(999999)
        if not result["success"] and "不存在" in result["message"]:
            log_pass("获取不存在项目的摘要", f"返回 False, message={result['message']}")
        else:
            log_fail("获取不存在项目的摘要", f"返回 {result['success']}, message={result['message']}")
    else:
        log_fail("项目统计摘要测试，但 project_id 为空", "")

    # ========== 8. 测试删除募捐项目 ==========
    print("\n8. 测试删除募捐项目 (delete_project)...")
    # 先创建一个新项目用于删除测试
    delete_test_title = f"测试项目_删除_{uuid.uuid4().hex[:6]}"
    create_result = project_lib.create_project(delete_test_title, "用于删除测试", 500.00)
    if create_result["success"]:
        delete_project_id = create_result["data"]["project_id"]

        # 8.1 正常删除
        result = project_lib.delete_project(delete_project_id)
        if result["success"]:
            log_pass(f"删除项目 {delete_project_id}", "返回 True")
            # 验证已删除
            detail = project_lib.get_project_by_id(delete_project_id)
            if not detail["success"] and "不存在" in detail["message"]:
                log_pass("验证项目已删除", "项目确实已删除")
            else:
                log_fail("验证项目已删除", "项目仍然存在")
        else:
            log_fail("删除项目", f"失败，message={result['message']}")

    # 8.2 删除不存在的项目
    result = project_lib.delete_project(999999)
    if not result["success"] and "不存在" in result["message"]:
        log_pass("删除不存在的项目", f"返回 False, message={result['message']}")
    else:
        log_fail("删除不存在的项目", f"返回 {result['success']}, message={result['message']}")

    # ========== 9. 测试内部统计更新方法 ==========
    print("\n9. 测试内部统计更新 (_update_project_stats)...")
    # 创建一个新项目用于测试统计更新
    stats_test_title = f"测试项目_统计_{uuid.uuid4().hex[:6]}"
    create_result = project_lib.create_project(stats_test_title, "用于统计测试", 10000.00)
    if create_result["success"]:
        stats_project_id = create_result["data"]["project_id"]

        # 9.1 增加金额和人数
        success = project_lib._update_project_stats(stats_project_id, 500.00, 1)
        if success:
            log_pass("增加项目统计", "amount +500, participant +1")
            detail = project_lib.get_project_by_id(stats_project_id)
            if detail["success"] and detail["data"]["current_amount"] == 500.00 and detail["data"]["participant_count"] == 1:
                log_pass("验证增加统计结果", "current_amount=500.00, participant_count=1")
            else:
                log_fail("验证增加统计结果", f"current_amount={detail['data']['current_amount']}, participant_count={detail['data']['participant_count']}")
        else:
            log_fail("增加项目统计", "返回 False")

        # 9.2 减少金额和人数
        success = project_lib._update_project_stats(stats_project_id, -200.00, -1)
        if success:
            log_pass("减少项目统计", "amount -200, participant -1")
            detail = project_lib.get_project_by_id(stats_project_id)
            if detail["success"] and detail["data"]["current_amount"] == 300.00 and detail["data"]["participant_count"] == 0:
                log_pass("验证减少统计结果", "current_amount=300.00, participant_count=0")
            else:
                log_fail("验证减少统计结果", f"current_amount={detail['data']['current_amount']}, participant_count={detail['data']['participant_count']}")
        else:
            log_fail("减少项目统计", "返回 False")

        # 9.3 减少到负数（应该被限制为0）
        success = project_lib._update_project_stats(stats_project_id, -500.00, -1)
        if success:
            log_pass("减少到负数边界", "amount -500, participant -1")
            detail = project_lib.get_project_by_id(stats_project_id)
            if detail["success"] and detail["data"]["current_amount"] == 0.00 and detail["data"]["participant_count"] == 0:
                log_pass("验证边界限制", "current_amount=0.00, participant_count=0")
            else:
                log_fail("验证边界限制", f"current_amount={detail['data']['current_amount']}, participant_count={detail['data']['participant_count']}")
        else:
            log_fail("减少到负数边界", "返回 False")

        # 9.4 更新不存在的项目
        success = project_lib._update_project_stats(999999, 100.00, 1)
        if not success:
            log_pass("更新不存在项目的统计", "返回 False")
        else:
            log_fail("更新不存在项目的统计", "返回 True，预期 False")
    else:
        log_fail("创建用于统计测试的项目失败", f"message={create_result['message']}")

    # ========== 10. 清理测试数据 ==========
    print("\n10. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_donation_project WHERE title LIKE '测试项目_%'")
        db.close_database()
        log_pass("清理测试数据", "删除所有测试项目数据")
    else:
        log_fail("清理测试数据", "数据库连接失败，请手动删除")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
# ===== backend/tests/test_rescue_record_library.py =====
"""
测试 RescueRecordLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_rescue_record_library
"""
from backend.libs.rescue_record_library import RescueRecordLibrary
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    rescue_lib = RescueRecordLibrary()
    user_lib = UserLibrary()
    db = rescue_lib.db

    # 测试账号
    user_a = f"test_user_{uuid.uuid4().hex[:8]}"      # 普通用户（上报人）
    volunteer = f"test_user_{uuid.uuid4().hex[:8]}"   # 志愿者
    admin = f"test_user_{uuid.uuid4().hex[:8]}"       # 管理员
    banned = f"test_user_{uuid.uuid4().hex[:8]}"      # 封禁用户

    # ======== 清理旧数据 & 注册测试用户 ========
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_rescuerecord WHERE user_id LIKE 'test_user_%' OR helper_id LIKE 'test_user_%'"
        )
        db.execute_raw_sql(
            "DELETE FROM t_animal WHERE name LIKE 'test_animal_%'"
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

    # 插入测试动物
    if db.open_database():
        db.execute_raw_sql(
            "INSERT INTO t_animal (name, breed, status, created_at) VALUES (%s, %s, 0, NOW())",
            ("test_animal_cat", "cat")
        )
        pet_id = db.get_last_insert_id()
        db.close_database()
        print(f"已创建测试动物 pet_id={pet_id}")
    else:
        print("[FAIL] 数据库连接失败，测试终止")
        return

    print(f"已创建测试用户: A={user_a}, Volunteer={volunteer}, Admin={admin}, Banned={banned}(已封禁)")

    print("\n" + "=" * 50 + "\n  开始测试 RescueRecordLibrary\n" + "=" * 50)

    # ========== 1. 创建救助记录 ==========
    print("\n1. 测试创建救助记录 (create_rescue_record)...")

    # 1.1 正常创建
    result = rescue_lib.create_rescue_record(
        user_a, title="发现流浪猫", description="在食堂门口发现",
        location="食堂", found_location_text="第一食堂门口",
        need_type="救助", priority=1
    )
    if result["success"] and result["data"] and result["data"].get("record_id"):
        record1 = result["data"]["record_id"]
        log_pass("A创建救助记录", f"成功 record_id={record1}")
    else:
        log_fail("A创建救助记录", f"失败: {result}")
        return

    # 再创建一个用于后续测试
    result2 = rescue_lib.create_rescue_record(
        user_a, title="发现流浪狗", description="在图书馆后面",
        location="图书馆", need_type="救助"
    )
    if result2["success"]:
        record2 = result2["data"]["record_id"]
        log_pass("A再创建救助记录", f"成功 record_id={record2}")
    else:
        log_fail("A再创建救助记录", f"失败: {result2}")
        return

    # 1.2 无效用户
    fake_user = f"test_user_{uuid.uuid4().hex[:8]}"
    result = rescue_lib.create_rescue_record(fake_user, title="test")
    if not result["success"] and "用户不存在" in result["message"]:
        log_pass("无效用户创建", "返回用户不存在")
    else:
        log_fail("无效用户创建", f"结果异常: {result}")

    # 1.3 封禁用户
    result = rescue_lib.create_rescue_record(banned, title="test")
    if not result["success"] and "封禁" in result["message"]:
        log_pass("封禁用户创建", "返回用户已被封禁")
    else:
        log_fail("封禁用户创建", f"结果异常: {result}")

    # ========== 2. 查询救助记录详情 ==========
    print("\n2. 测试查询救助记录详情 (get_rescue_record_by_id)...")

    # 2.1 查询存在的
    result = rescue_lib.get_rescue_record_by_id(record1)
    if result["success"] and result["data"]["record_id"] == record1:
        log_pass(f"查询存在记录 {record1}", "成功")
    else:
        log_fail("查询存在记录", f"失败: {result}")

    # 2.2 查询不存在的
    fake_record = f"test_record_{uuid.uuid4().hex[:8]}"
    result = rescue_lib.get_rescue_record_by_id(fake_record)
    if not result["success"] and "救助记录不存在" in result["message"]:
        log_pass("查询不存在记录", "返回不存在")
    else:
        log_fail("查询不存在记录", f"结果异常: {result}")

    # ========== 3. 修改救助记录 ==========
    print("\n3. 测试修改救助记录 (update_rescue_record)...")

    # 3.1 正常修改
    result = rescue_lib.update_rescue_record(
        record1, user_a, title="修改后的标题", description="修改后的说明", priority=2
    )
    if result["success"]:
        detail = rescue_lib.get_rescue_record_by_id(record1)
        if (detail["success"] and detail["data"]["title"] == "修改后的标题"
                and detail["data"]["priority"] == 2):
            log_pass("A修改自己的记录", "验证成功")
        else:
            log_fail("A修改自己的记录", f"验证失败: {detail}")
    else:
        log_fail("A修改自己的记录", f"失败: {result}")

    # 3.2 修改他人记录
    result = rescue_lib.update_rescue_record(record1, volunteer, title="越权修改")
    if not result["success"] and "无权修改" in result["message"]:
        log_pass("Volunteer修改A的记录", "返回无权修改")
    else:
        log_fail("Volunteer修改A的记录", f"结果异常: {result}")

    # 3.3 修改不存在的
    result = rescue_lib.update_rescue_record(fake_record, user_a, title="test")
    if not result["success"] and "救助记录不存在" in result["message"]:
        log_pass("修改不存在记录", "返回不存在")
    else:
        log_fail("修改不存在记录", f"结果异常: {result}")

    # ========== 4. 志愿者接单 ==========
    print("\n4. 测试志愿者接单 (claim_rescue)...")

    # 4.1 正常接单
    result = rescue_lib.claim_rescue(record1, volunteer)
    if result["success"] and result["data"]["status"] == 1:
        log_pass("Volunteer接单record1", "成功 status=1")
    else:
        log_fail("Volunteer接单record1", f"失败: {result}")

    # 4.2 重复接单（已是救助中）
    result = rescue_lib.claim_rescue(record1, admin)
    if not result["success"] and "不允许" in result["message"]:
        log_pass("重复接单", "返回状态转移不合法")
    else:
        log_fail("重复接单", f"结果异常: {result}")

    # 4.3 接不存在的单
    result = rescue_lib.claim_rescue(fake_record, volunteer)
    if not result["success"] and "救助记录不存在" in result["message"]:
        log_pass("接不存在记录", "返回不存在")
    else:
        log_fail("接不存在记录", f"结果异常: {result}")

    # ========== 5. 标记完成（待确认） ==========
    print("\n5. 测试标记完成 (complete_rescue)...")

    # 5.1 上报人标记完成
    result = rescue_lib.complete_rescue(record1, user_a)
    if result["success"] and result["data"]["status"] == 2:
        log_pass("A标记record1完成", "成功 status=2")
    else:
        log_fail("A标记record1完成", f"失败: {result}")

    # 5.2 重复标记
    result = rescue_lib.complete_rescue(record1, user_a)
    if not result["success"] and "不允许" in result["message"]:
        log_pass("重复标记完成", "返回状态转移不合法")
    else:
        log_fail("重复标记完成", f"结果异常: {result}")

    # ========== 6. 管理员确认完成 ==========
    print("\n6. 测试确认完成 (confirm_rescue)...")

    # 6.1 正常确认（record1 此时是 status=2 待确认）
    result = rescue_lib.confirm_rescue(record1, admin)
    if result["success"] and result["data"]["status"] == 3:
        log_pass("Admin确认record1完成", "成功 status=3")
    else:
        log_fail("Admin确认record1完成", f"失败: {result}")

    # 6.2 非管理员确认（需要另一条 status=2 的记录）
    # 创建 -> 接单 -> 完成 -> 用 volunteer 去 confirm
    result_prep = rescue_lib.create_rescue_record(
        user_a, title="权限测试", description="用于测试非管理员confirm"
    )
    if result_prep["success"]:
        record_perm = result_prep["data"]["record_id"]
        rescue_lib.claim_rescue(record_perm, volunteer)
        rescue_lib.complete_rescue(record_perm, user_a)
        
        result = rescue_lib.confirm_rescue(record_perm, volunteer)
        if not result["success"] and "仅管理员" in result["message"]:
            log_pass("Volunteer确认完成", "返回仅管理员可以确认")
        else:
            log_fail("Volunteer确认完成", f"结果异常: {result}")
    else:
        log_fail("准备权限测试记录", f"失败: {result_prep}")

    # 6.3 重复确认已完成
    result = rescue_lib.confirm_rescue(record1, admin)
    if not result["success"] and "不允许" in result["message"]:
        log_pass("重复确认已完成", "返回状态转移不合法")
    else:
        log_fail("重复确认已完成", f"结果异常: {result}")

    # ========== 7. 关闭救助记录 ==========
    print("\n7. 测试关闭救助记录 (close_rescue)...")

    # 先让 volunteer 接单 record2，然后关闭
    rescue_lib.claim_rescue(record2, volunteer)

    # 7.1 上报人关闭
    result = rescue_lib.close_rescue(record2, user_a)
    if result["success"] and result["data"]["status"] == 4:
        log_pass("A关闭record2", "成功 status=4")
    else:
        log_fail("A关闭record2", f"失败: {result}")

    # 7.2 关闭已完成记录
    result = rescue_lib.close_rescue(record1, admin)
    if not result["success"] and "不允许" in result["message"]:
        log_pass("关闭已完成记录", "返回状态转移不合法")
    else:
        log_fail("关闭已完成记录", f"结果异常: {result}")

    # ========== 8. 关联动物档案 ==========
    print("\n8. 测试关联动物档案 (link_animal)...")

    # 8.1 正常关联
    result = rescue_lib.link_animal(record1, pet_id, admin)
    if result["success"]:
        detail = rescue_lib.get_rescue_record_by_id(record1)
        if detail["success"] and detail["data"]["pet_id"] == pet_id:
            log_pass("Admin关联动物到record1", f"成功 pet_id={pet_id}")
        else:
            log_fail("Admin关联动物到record1", f"验证失败: {detail}")
    else:
        log_fail("Admin关联动物到record1", f"失败: {result}")

    # 8.2 关联不存在动物
    result = rescue_lib.link_animal(record1, 999999, admin)
    if not result["success"] and "动物档案不存在" in result["message"]:
        log_pass("关联不存在动物", "返回不存在")
    else:
        log_fail("关联不存在动物", f"结果异常: {result}")

    # ========== 9. 软删除救助记录 ==========
    print("\n9. 测试软删除救助记录 (delete_rescue_record)...")

    # 9.1 上报人删除
    result = rescue_lib.delete_rescue_record(record2, user_a)
    if result["success"]:
        detail = rescue_lib.get_rescue_record_by_id(record2)
        if not detail["success"] and "不存在" in detail["message"]:
            log_pass("A删除record2", "成功（已软删除）")
        else:
            log_fail("A删除record2", f"仍能查询到: {detail}")
    else:
        log_fail("A删除record2", f"失败: {result}")

    # 9.2 删除他人记录
    result = rescue_lib.delete_rescue_record(record1, volunteer)
    if not result["success"] and "无权删除" in result["message"]:
        log_pass("Volunteer删除A的记录", "返回无权删除")
    else:
        log_fail("Volunteer删除A的记录", f"结果异常: {result}")

    # 9.3 删除不存在
    result = rescue_lib.delete_rescue_record(fake_record, user_a)
    if not result["success"] and "救助记录不存在" in result["message"]:
        log_pass("删除不存在记录", "返回不存在")
    else:
        log_fail("删除不存在记录", f"结果异常: {result}")

    # ========== 10. 查询用户救助记录列表 ==========
    print("\n10. 测试查询用户救助记录 (get_user_rescues)...")

    # 再创建一个给 A
    result_new = rescue_lib.create_rescue_record(user_a, title="新的救助", description="test")
    record3 = result_new["data"]["record_id"] if result_new["success"] else None

    result = rescue_lib.get_user_rescues(user_a, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("A的救助列表", f"total={result['data']['total']}")
    else:
        log_fail("A的救助列表", f"结果异常: {result}")

    # 分页
    result = rescue_lib.get_user_rescues(user_a, page=1, page_size=1)
    if result["success"] and len(result["data"]["records"]) == 1:
        log_pass("分页 limit=1", "返回1条")
    else:
        log_fail("分页 limit=1", f"返回{len(result['data']['records'])}条")

    # ========== 11. 查询志愿者救助记录 ==========
    print("\n11. 测试查询志愿者救助记录 (get_helper_rescues)...")

    result = rescue_lib.get_helper_rescues(volunteer, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("Volunteer的接单列表", f"total={result['data']['total']}")
    else:
        log_fail("Volunteer的接单列表", f"结果异常: {result}")

    # ========== 12. 查询动物救助历史 ==========
    print("\n12. 测试查询动物救助历史 (get_animal_rescue_history)...")

    result = rescue_lib.get_animal_rescue_history(pet_id, page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass(f"动物{pet_id}的救助历史", f"total={result['data']['total']}")
    else:
        log_fail("动物救助历史", f"结果异常: {result}")

    # ========== 13. 查询所有救助记录（管理员视角） ==========
    print("\n13. 测试查询所有救助记录 (get_all_rescues)...")

    result = rescue_lib.get_all_rescues(page=1, page_size=20)
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("查询所有记录", f"total={result['data']['total']}")
    else:
        log_fail("查询所有记录", f"结果异常: {result}")

    # 按状态筛选
    result = rescue_lib.get_all_rescues(page=1, page_size=20, status_filter=3)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("筛选状态3(已完成)", f"total={result['data']['total']}")
    else:
        log_fail("筛选状态3", f"结果异常: {result}")

    # ========== 14. 统计各状态数量 ==========
    print("\n14. 测试统计各状态数量 (get_rescue_status_count)...")

    result = rescue_lib.get_rescue_status_count()
    if result["success"] and result["data"]["total"] >= 2:
        log_pass("状态统计", f"total={result['data']['total']}")
    else:
        log_fail("状态统计", f"结果异常: {result}")

    # ========== 15. 清理 ==========
    print("\n15. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql(
            "DELETE FROM t_rescuerecord WHERE user_id IN (%s, %s, %s, %s) OR helper_id IN (%s, %s, %s, %s)",
            (user_a, volunteer, admin, banned, user_a, volunteer, admin, banned)
        )
        db.execute_raw_sql(
            "DELETE FROM t_animal WHERE name = %s",
            ("test_animal_cat",)
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
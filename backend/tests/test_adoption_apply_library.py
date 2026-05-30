"""
测试 AdoptionApplyLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_adoption_apply_library
"""
from backend.libs.adoption_apply_library import AdoptionApplyLibrary
from backend.libs.user_library import UserLibrary
from backend.libs.animal_library import AnimalLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS]: 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL]: 原始数据 = {original}, 当前数据 = {current}")


def main():
    apply_lib = AdoptionApplyLibrary()
    user_lib = UserLibrary()
    animal_lib = AnimalLibrary()

    # ======== 清理旧测试数据 ========
    if apply_lib.db.open_database():
        apply_lib.db.execute_raw_sql("DELETE FROM t_adoptionapply WHERE apply_id LIKE 'test_apply_%'")
        apply_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE '测试动物_%'")
        apply_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_apply_user_%'")
        apply_lib.db.close_database()
        print("已清理旧测试数据")
    # =================================

    # ======== 准备测试数据 ========
    test_user_id = f"test_apply_user_{uuid.uuid4().hex[:8]}"
    test_user2_id = f"test_apply_user_{uuid.uuid4().hex[:8]}"
    test_nickname = "测试申请人"
    test_nickname2 = "测试申请人2"
    test_avatar = "http://example.com/avatar.jpg"

    # 注册两个测试用户
    user_lib.register_user(test_user_id, test_nickname, test_avatar, role=1)
    user_lib.register_user(test_user2_id, test_nickname2, test_avatar, role=1)

    # 添加一个测试动物（可领养状态 status=0）
    test_pet_id = animal_lib.add_animal(
        name="测试动物_可领养",
        breed="田园猫",
        status=0,
        color="橘色",
        age=12,
        gender=1,
        description="一只温顺的橘猫"
    )

    # 添加一个已被领养的动物（status=1）
    adopted_pet_id = animal_lib.add_animal(
        name="测试动物_已领养",
        breed="哈士奇",
        status=1,
        color="黑白",
        age=24,
        gender=2,
        description="已被领养的狗"
    )
    print(f"测试数据准备完成：用户={test_user_id}, 用户2={test_user2_id}, 动物可领养={test_pet_id}, 动物已领养={adopted_pet_id}")
    # ==============================

    print("\n" + "=" * 50 + "\n  开始测试 AdoptionApplyLibrary\n" + "=" * 50)

    # ========== 1. 测试检查重复申请（无重复） ==========
    print("\n1. 测试检查重复申请（无重复）...")
    result = apply_lib.check_duplicate_application(test_user_id, test_pet_id)
    if not result:
        log_pass(f"检查无重复，user_id={test_user_id}, pet_id={test_pet_id}", f"返回 {result}")
    else:
        log_fail(f"检查无重复，user_id={test_user_id}, pet_id={test_pet_id}", f"返回 {result}，预期 False")

    # ========== 2. 测试检查重复申请（有重复） ==========
    print("\n2. 测试检查重复申请（有重复）...")
    apply_id = apply_lib.submit_adoption_application(test_user_id, test_pet_id, "想领养这只猫")
    result = apply_lib.check_duplicate_application(test_user_id, test_pet_id)
    if result:
        log_pass(f"检查有重复，user_id={test_user_id}, pet_id={test_pet_id}", f"返回 {result}")
    else:
        log_fail(f"检查有重复，user_id={test_user_id}, pet_id={test_pet_id}", f"返回 {result}，预期 True")

    # ========== 3. 测试提交申请 - 正常 ==========
    print("\n3. 测试提交申请 - 正常...")
    apply_id_2 = apply_lib.submit_adoption_application(test_user2_id, test_pet_id, "我也想要这只猫")
    if apply_id_2:
        log_pass(f"用户2提交申请，输入 user_id={test_user2_id}, pet_id={test_pet_id}", f"返回 apply_id={apply_id_2}")
    else:
        log_fail(f"用户2提交申请，输入 user_id={test_user2_id}, pet_id={test_pet_id}", f"返回 False，预期 apply_id")

    # ========== 4. 测试提交申请 - 用户不存在 ==========
    print("\n4. 测试提交申请 - 用户不存在...")
    result = apply_lib.submit_adoption_application("not_exist_user_xxx", test_pet_id, "测试")
    if not result:
        log_pass(f"用户不存在时提交申请，输入 user_id=not_exist_user_xxx", f"返回 {result}")
    else:
        log_fail(f"用户不存在时提交申请，输入 user_id=not_exist_user_xxx", f"返回 {result}，预期 False")

    # ========== 5. 测试提交申请 - 动物不存在 ==========
    print("\n5. 测试提交申请 - 动物不存在...")
    result = apply_lib.submit_adoption_application(test_user_id, 999999, "测试")
    if not result:
        log_pass(f"动物不存在时提交申请，输入 pet_id=999999", f"返回 {result}")
    else:
        log_fail(f"动物不存在时提交申请，输入 pet_id=999999", f"返回 {result}，预期 False")

    # ========== 6. 测试提交申请 - 动物已领养 ==========
    print("\n6. 测试提交申请 - 动物已领养...")
    result = apply_lib.submit_adoption_application(test_user_id, adopted_pet_id, "测试")
    if not result:
        log_pass(f"动物已领养时提交申请，输入 pet_id={adopted_pet_id}", f"返回 {result}")
    else:
        log_fail(f"动物已领养时提交申请，输入 pet_id={adopted_pet_id}", f"返回 {result}，预期 False")

    # ========== 7. 测试提交申请 - 重复提交 ==========
    print("\n7. 测试提交申请 - 重复提交...")
    result = apply_lib.submit_adoption_application(test_user_id, test_pet_id, "再次申请")
    if not result:
        log_pass(f"重复提交申请，user_id={test_user_id}, pet_id={test_pet_id}", f"返回 {result}")
    else:
        log_fail(f"重复提交申请，user_id={test_user_id}, pet_id={test_pet_id}", f"返回 {result}，预期 False")

    # ========== 8. 测试提交申请 - 空 content ==========
    print("\n8. 测试提交申请 - 空 content...")
    temp_user3_id = f"test_apply_user_{uuid.uuid4().hex[:8]}"
    user_lib.register_user(temp_user3_id, "临时用户3", test_avatar, role=1)
    result = apply_lib.submit_adoption_application(temp_user3_id, test_pet_id, "")
    if result:
        log_pass(f"空 content 提交申请，输入 content=''", f"返回 apply_id={result}")
    else:
        log_fail(f"空 content 提交申请，输入 content=''", f"返回 False，预期 apply_id")

    # ========== 9. 测试查看申请详情 - 正常 ==========
    print("\n9. 测试查看申请详情 - 正常...")
    detail = apply_lib.get_application_by_id(apply_id)
    if detail and detail["apply_id"] == apply_id:
        log_pass(f"查询申请详情，apply_id={apply_id}", f"返回数据包含 apply_id={detail['apply_id']}, 申请人={detail['applicant_nickname']}, 动物={detail['pet_name']}")
    else:
        log_fail(f"查询申请详情，apply_id={apply_id}", f"返回 {detail}，预期非空字典")

    # ========== 10. 测试查看申请详情 - 不存在 ==========
    print("\n10. 测试查看申请详情 - 不存在...")
    none_detail = apply_lib.get_application_by_id("not_exist_apply_xxx")
    if none_detail is None:
        log_pass(f"查询不存在的申请详情，apply_id=not_exist_apply_xxx", f"返回 None")
    else:
        log_fail(f"查询不存在的申请详情，apply_id=not_exist_apply_xxx", f"返回 {none_detail}，预期 None")

    # ========== 11. 测试查看用户申请列表 - 有数据 ==========
    print("\n11. 测试查看用户申请列表 - 有数据...")
    user_apps = apply_lib.get_user_applications(test_user_id, page=1, page_size=20)
    if user_apps and user_apps["total"] > 0:
        log_pass(f"查询用户 {test_user_id} 的申请列表", f"返回 {user_apps['total']} 条记录")
    else:
        log_fail(f"查询用户 {test_user_id} 的申请列表", f"返回 {user_apps}，预期至少1条记录")

    # ========== 12. 测试查看用户申请列表 - 无数据 ==========
    print("\n12. 测试查看用户申请列表 - 无数据...")
    empty_apps = apply_lib.get_user_applications("not_exist_user_no_apps", page=1, page_size=20)
    if empty_apps and empty_apps["total"] == 0:
        log_pass(f"查询无申请用户，user_id=not_exist_user_no_apps", f"返回 total={empty_apps['total']}")
    else:
        log_fail(f"查询无申请用户，user_id=not_exist_user_no_apps", f"返回 {empty_apps}，预期 total=0")

    # ========== 13. 测试查看用户申请列表 - 分页 ==========
    print("\n13. 测试查看用户申请列表 - 分页...")
    page1 = apply_lib.get_user_applications(test_user_id, page=1, page_size=1)
    page2 = apply_lib.get_user_applications(test_user_id, page=2, page_size=1)
    if page1 and len(page1["applications"]) == 1 and page1["page"] == 1:
        log_pass(f"分页查询第1页，page=1, page_size=1", f"返回 {len(page1['applications'])} 条，total={page1['total']}")
    else:
        log_fail(f"分页查询第1页，page=1, page_size=1", f"返回 {page1}，预期1条记录")
    if page2 and len(page2["applications"]) == 0:
        log_pass(f"分页查询第2页，page=2, page_size=1", f"返回 {len(page2['applications'])} 条（无数据）")
    else:
        log_fail(f"分页查询第2页，page=2, page_size=1", f"返回 {page2}，预期0条记录")

    # ========== 14. 测试查看动物申请列表 - 有数据 ==========
    print("\n14. 测试查看动物申请列表 - 有数据...")
    animal_apps = apply_lib.get_animal_applications(test_pet_id, page=1, page_size=20)
    if animal_apps and animal_apps["total"] >= 2:
        log_pass(f"查询动物 {test_pet_id} 的申请列表", f"返回 {animal_apps['total']} 条记录")
    else:
        log_fail(f"查询动物 {test_pet_id} 的申请列表", f"返回 {animal_apps}，预期至少2条记录")

    # ========== 15. 测试查看动物申请列表 - 无数据 ==========
    print("\n15. 测试查看动物申请列表 - 无数据...")
    empty_animal_apps = apply_lib.get_animal_applications(999999, page=1, page_size=20)
    if empty_animal_apps and empty_animal_apps["total"] == 0:
        log_pass(f"查询不存在的动物的申请列表，pet_id=999999", f"返回 total={empty_animal_apps['total']}")
    else:
        log_fail(f"查询不存在的动物的申请列表，pet_id=999999", f"返回 {empty_animal_apps}，预期 total=0")

       # ========== 16. 测试取消申请 - 正常 ==========
    print("\n16. 测试取消申请 - 正常...")
    # 创建一个全新的动物用于取消测试，避免与其他测试冲突
    cancel_pet_id = animal_lib.add_animal(
        name="测试动物_用于取消",
        breed="田园猫",
        status=0
    )
    cancel_apply_id = apply_lib.submit_adoption_application(test_user_id, cancel_pet_id, "待取消的申请")
    cancel_result = apply_lib.cancel_adoption_application(cancel_apply_id, test_user_id)
    if cancel_result:
        log_pass(f"取消申请，apply_id={cancel_apply_id}, user_id={test_user_id}", f"返回 {cancel_result}")
    else:
        log_fail(f"取消申请，apply_id={cancel_apply_id}, user_id={test_user_id}", f"返回 {cancel_result}，预期 True")
   
    # ========== 17. 测试取消申请 - 申请不存在 ==========
    print("\n17. 测试取消申请 - 申请不存在...")
    cancel_result = apply_lib.cancel_adoption_application("not_exist_apply_xxx", test_user_id)
    if not cancel_result:
        log_pass(f"取消不存在的申请，apply_id=not_exist_apply_xxx", f"返回 {cancel_result}")
    else:
        log_fail(f"取消不存在的申请，apply_id=not_exist_apply_xxx", f"返回 {cancel_result}，预期 False")

    # ========== 18. 测试取消申请 - 非本人 ==========
    print("\n18. 测试取消申请 - 非本人...")
    # 1. 先创建一个全新的动物，确保状态干净
    non_owner_pet_id = animal_lib.add_animal(
        name="取消申请非本人测试动物",
        breed="田园猫",
        status=0
    )
    # 2. 让 test_user_id 提交一个申请
    owner_apply_id = apply_lib.submit_adoption_application(test_user_id, non_owner_pet_id, "非本人取消测试")
    if not owner_apply_id:
        log_fail("创建测试申请失败，无法继续测试", "")
        return
    # 3. 让 test_user2_id 尝试取消这个申请（预期失败）
    cancel_result = apply_lib.cancel_adoption_application(owner_apply_id, test_user2_id)
    if not cancel_result:
        log_pass(f"非本人取消申请，apply_id={owner_apply_id}, 操作人={test_user2_id}, 申请人={test_user_id}", f"返回 {cancel_result}")
    else:
        log_fail(f"非本人取消申请，apply_id={owner_apply_id}, 操作人={test_user2_id}, 申请人={test_user_id}", f"返回 {cancel_result}，预期 False")
   
    # ========== 19. 测试取消申请 - 已通过 ==========
    print("\n19. 测试取消申请 - 已通过...")
    temp_pet_id = animal_lib.add_animal(name="测试动物_临时", breed="临时品种", status=0)
    temp_apply_id = apply_lib.submit_adoption_application(test_user_id, temp_pet_id, "审核通过后的取消测试")
    apply_lib.approve_application(temp_apply_id, test_user2_id, "同意领养")
    cancel_result = apply_lib.cancel_adoption_application(temp_apply_id, test_user_id)
    if not cancel_result:
        log_pass(f"已通过的申请取消失败", f"返回 {cancel_result}")
    else:
        log_fail(f"已通过的申请取消失败", f"返回 {cancel_result}，预期 False")

    # ========== 20. 测试审核通过 - 正常 ==========
    print("\n20. 测试审核通过 - 正常...")
    approve_pet_id = animal_lib.add_animal(name="测试动物_审核通过", breed="猫", status=0)
    approve_apply_id = apply_lib.submit_adoption_application(test_user2_id, approve_pet_id, "申请审核通过测试")
    approve_result = apply_lib.approve_application(approve_apply_id, test_user_id, "同意领养，请好好照顾")
    if approve_result:
        log_pass(f"审核通过申请，apply_id={approve_apply_id}", f"返回 {approve_result}")
    else:
        log_fail(f"审核通过申请，apply_id={approve_apply_id}", f"返回 {approve_result}，预期 True")

    # ========== 21. 测试审核通过 - 申请不存在 ==========
    print("\n21. 测试审核通过 - 申请不存在...")
    approve_result = apply_lib.approve_application("not_exist_apply_xxx", test_user_id, "测试")
    if not approve_result:
        log_pass(f"审核不存在的申请，apply_id=not_exist_apply_xxx", f"返回 {approve_result}")
    else:
        log_fail(f"审核不存在的申请，apply_id=not_exist_apply_xxx", f"返回 {approve_result}，预期 False")

        # ========== 22. 测试审核通过 - 非待审核状态... ==========
    print("\n22. 测试审核通过 - 非待审核状态...")
    # 1. 创建一个新动物和申请
    reject_state_pet_id = animal_lib.add_animal(
        name="审核通过非待审核测试动物",
        breed="猫",
        status=0
    )
    reject_state_apply_id = apply_lib.submit_adoption_application(test_user2_id, reject_state_pet_id, "非待审核状态测试")
    if not reject_state_apply_id:
        log_fail("创建测试申请失败，无法继续测试", "")
        return
    # 2. 先把这个申请驳回，使它的状态变为非待审核（status=2）
    apply_lib.reject_application(reject_state_apply_id, "先驳回")
    # 3. 尝试审核这个已驳回的申请（预期失败）
    approve_result = apply_lib.approve_application(reject_state_apply_id, test_user_id, "试图通过已驳回的")
    if not approve_result:
        log_pass(f"审核已驳回的申请，apply_id={reject_state_apply_id}", f"返回 {approve_result}")
    else:
        log_fail(f"审核已驳回的申请，apply_id={reject_state_apply_id}", f"返回 {approve_result}，预期 False")
    
    # ========== 23. 测试审核拒绝 - 正常 ==========
    print("\n23. 测试审核拒绝 - 正常...")
    # 创建一个全新的动物用于驳回测试，避免与其他测试冲突
    reject_pet_id = animal_lib.add_animal(
        name="测试动物_用于驳回",
        breed="猫",
        status=0
    )
    reject_apply_id = apply_lib.submit_adoption_application(test_user2_id, reject_pet_id, "申请驳回测试")
    reject_result = apply_lib.reject_application(reject_apply_id, "不符合领养条件")
    if reject_result:
        log_pass(f"驳回申请，apply_id={reject_apply_id}", f"返回 {reject_result}")
    else:
        log_fail(f"驳回申请，apply_id={reject_apply_id}", f"返回 {reject_result}，预期 True")
    
    # ========== 24. 测试审核拒绝 - 申请不存在 ==========
    print("\n24. 测试审核拒绝 - 申请不存在...")
    reject_result = apply_lib.reject_application("not_exist_apply_xxx", "测试")
    if not reject_result:
        log_pass(f"驳回不存在的申请，apply_id=not_exist_apply_xxx", f"返回 {reject_result}")
    else:
        log_fail(f"驳回不存在的申请，apply_id=not_exist_apply_xxx", f"返回 {reject_result}，预期 False")

    # ========== 25. 测试审核拒绝 - 非待审核状态... ==========
    print("\n25. 测试审核拒绝 - 非待审核状态...")
    # 1. 创建一个新动物和申请
    approve_state_pet_id = animal_lib.add_animal(
        name="审核拒绝非待审核测试动物",
        breed="猫",
        status=0
    )
    approve_state_apply_id = apply_lib.submit_adoption_application(test_user2_id, approve_state_pet_id, "已通过测试")
    if not approve_state_apply_id:
        log_fail("创建测试申请失败，无法继续测试", "")
        return
    # 2. 先把这个申请通过，使它的状态变为非待审核（status=1）
    apply_lib.approve_application(approve_state_apply_id, test_user_id, "先通过")
    # 3. 尝试拒绝这个已通过的申请（预期失败）
    reject_result = apply_lib.reject_application(approve_state_apply_id, "试图驳回已通过的")
    if not reject_result:
        log_pass(f"驳回已通过的申请，apply_id={approve_state_apply_id}", f"返回 {reject_result}")
    else:
        log_fail(f"驳回已通过的申请，apply_id={approve_state_apply_id}", f"返回 {reject_result}，预期 False")
     
     # ========== 26. 清理测试数据 ==========
    print("\n26. 清理测试数据...")
    if apply_lib.db.open_database():
        # 在清理动物时，把新的测试动物也包含进去
        apply_lib.db.execute_raw_sql("DELETE FROM t_adoptionapply WHERE apply_id LIKE 'test_apply_%'")
        apply_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE '测试动物_%'")
        apply_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_apply_user_%'")
        apply_lib.db.close_database()
        print("已清理测试数据")
    else:
        print("清理测试数据失败：数据库连接失败，请手动删除")


if __name__ == "__main__":
    main()
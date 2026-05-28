"""
测试 AnimalLibrary 所有功能（适配新数据库结构）
运行方式（在项目根目录执行）：
    python -m backend.tests.test_animal_library
"""
from backend.libs.animal_library import AnimalLibrary
import uuid
import json

def log_pass(original, current):
    print(f"  ✅ PASS: 原始数据 = {original}, 当前数据 = {current}")

def log_fail(original, current):
    print(f"  ❌ FAIL: 原始数据 = {original}, 当前数据 = {current}")

def main():
    animal_lib = AnimalLibrary()
    
    # ======== 清理旧测试数据 ========
    if animal_lib.db.open_database():
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_animal_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_adopted_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'similar_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'to_be_deleted_%'")
        animal_lib.db.close_database()
        print("已清理旧测试数据")
    # =================================

    print("\n" + "="*50 + "\n  开始测试 AnimalLibrary\n" + "="*50)

    # ========== 1. 添加动物（完整字段） ==========
    print("\n1. 测试添加动物（含所有新增字段）...")
    test_name = f"test_animal_{uuid.uuid4().hex[:8]}"
    test_breed = "中华田园猫"
    test_status = 0
    test_color = "橘色"
    test_age = 6
    test_gender = 1
    test_neutered = 0
    test_vaccinated = 1
    test_personality = "温顺撒娇"
    test_desc = "在图书馆附近发现的流浪猫"
    test_photos = '["http://example.com/cat1.jpg"]'
    test_location = "图书馆南门"

    pet_id = animal_lib.add_animal(
        name=test_name,
        breed=test_breed,
        status=test_status,
        color=test_color,
        age=test_age,
        gender=test_gender,
        is_neutered=test_neutered,
        is_vaccinated=test_vaccinated,
        personality=test_personality,
        description=test_desc,
        photo_urls=test_photos,
        found_location=test_location
    )
    if pet_id:
        log_pass(f"添加动物，name={test_name}, breed={test_breed}, status={test_status}", f"成功，返回 pet_id={pet_id}")
    else:
        log_fail(f"添加动物，name={test_name}, breed={test_breed}, status={test_status}", f"失败")

    # 反例：空名字
    invalid_name = animal_lib.add_animal("", "测试", 0)
    if not invalid_name:
        log_pass(f"添加动物，name='' (空字符串)", f"校验失败，返回 False")
    else:
        log_fail(f"添加动物，name='' (空字符串)", f"校验通过，返回 {invalid_name}，预期 False")

    # 反例：无效状态
    invalid_status = animal_lib.add_animal("测试动物", "测试", 5)
    if not invalid_status:
        log_pass(f"添加动物，status=5 (无效状态)", f"校验失败，返回 False")
    else:
        log_fail(f"添加动物，status=5 (无效状态)", f"校验通过，返回 {invalid_status}，预期 False")

    # ========== 2. 按ID查询（验证所有字段） ==========
    print("\n2. 测试按ID查询动物...")
    animal = animal_lib.get_animal_by_id(pet_id)
    if animal and animal.name == test_name and animal.color == test_color and animal.age == test_age:
        log_pass(f"按ID查询已存在动物，pet_id={pet_id}", f"找到动物，name={animal.name}, color={animal.color}, age={animal.age}, personality={animal.personality}")
    else:
        log_fail(f"按ID查询已存在动物，pet_id={pet_id}", f"未找到或数据不匹配")

    # 查询不存在ID
    none_animal = animal_lib.get_animal_by_id(999999)
    if none_animal is None:
        log_pass(f"按ID查询不存在动物，pet_id=999999", f"结果 None")
    else:
        log_fail(f"按ID查询不存在动物，pet_id=999999", f"结果 {none_animal}，预期 None")

    # ========== 3. 按名字模糊查询 ==========
    print("\n3. 测试按名字模糊查询动物...")
    animals = animal_lib.get_animal_by_name(test_name[:8])
    if len(animals) > 0:
        log_pass(f"按名字模糊查询，name_like={test_name[:8]}", f"找到 {len(animals)} 只动物")
    else:
        log_fail(f"按名字模糊查询，name_like={test_name[:8]}", f"未找到任何动物")

    none_animals = animal_lib.get_animal_by_name("不存在的名字")
    if len(none_animals) == 0:
        log_pass(f"按名字查询不存在动物，name='不存在的名字'", f"结果空列表")
    else:
        log_fail(f"按名字查询不存在动物，name='不存在的名字'", f"结果 {none_animals}，预期空列表")

    # ========== 4. 按状态筛选（含分页） ==========
    print("\n4. 测试按状态筛选动物档案（含分页）...")
    adopted_name = f"test_adopted_{uuid.uuid4().hex[:6]}"
    adopted_id = animal_lib.add_animal(adopted_name, "中华田园犬", status=1)
    if adopted_id:
        adopted_animals = animal_lib.get_animals_by_status(1)
        if len(adopted_animals) > 0:
            log_pass(f"按状态筛选，status=1", f"找到 {len(adopted_animals)} 只动物，包括 {adopted_name}")
        else:
            log_fail(f"按状态筛选，status=1", f"未找到任何动物")

        active_animals = animal_lib.get_animals_by_status(0)
        if len(active_animals) > 0:
            log_pass(f"按状态筛选，status=0", f"找到 {len(active_animals)} 只动物，包括 {test_name}")
        else:
            log_fail(f"按状态筛选，status=0", f"未找到任何动物")

        # 分页测试
        paged = animal_lib.get_animals_by_status(0, limit=1, offset=0)
        if len(paged) == 1:
            log_pass(f"分页测试，status=0, limit=1, offset=0", f"返回 {len(paged)} 条记录")
        else:
            log_fail(f"分页测试，status=0, limit=1, offset=0", f"返回 {len(paged)} 条记录，预期 1 条")
    else:
        log_fail("添加状态为1的测试动物失败", "无法继续测试按状态筛选")

    # ========== 5. 获取所有动物 ==========
    print("\n5. 测试获取所有动物档案（含分页）...")
    all_animals = animal_lib.get_all_animals()
    if len(all_animals) >= 2:
        log_pass(f"获取所有动物，limit=20", f"找到 {len(all_animals)} 只动物")
    else:
        log_fail(f"获取所有动物，limit=20", f"只找到 {len(all_animals)} 只动物，预期至少 2 只")

    paged_all = animal_lib.get_all_animals(limit=1)
    if len(paged_all) == 1:
        log_pass(f"获取所有动物，limit=1", f"返回 {len(paged_all)} 条记录")
    else:
        log_fail(f"获取所有动物，limit=1", f"返回 {len(paged_all)} 条记录，预期 1 条")

    # ========== 6. 更新动物状态 ==========
    print("\n6. 测试更新动物状态...")
    new_status = 2
    update_success = animal_lib.update_animal_status(pet_id, new_status)
    if update_success:
        log_pass(f"更新动物状态，pet_id={pet_id}, new_status={new_status}", f"更新成功")
    else:
        log_fail(f"更新动物状态，pet_id={pet_id}, new_status={new_status}", f"更新失败")

    updated = animal_lib.get_animal_by_id(pet_id)
    if updated and updated.status == new_status:
        log_pass(f"验证状态更新，期望 status={new_status}", f"实际 status={updated.status}")
    else:
        log_fail(f"验证状态更新，期望 status={new_status}", f"实际 status={updated.status if updated else '动物不存在'}")

    # 更新不存在动物
    update_fail = animal_lib.update_animal_status(999999, 1)
    if not update_fail:
        log_pass(f"更新不存在动物状态，pet_id=999999", f"更新失败 (False)")
    else:
        log_fail(f"更新不存在动物状态，pet_id=999999", f"更新成功 (True)，预期失败")

    # ========== 7. 更新动物向量 ==========
    print("\n7. 测试更新动物特征向量...")
    vector = [0.1, 0.2, 0.3, 0.4]
    vector_json = json.dumps(vector)
    vector_success = animal_lib.update_animal_vector(pet_id, vector_json)
    if vector_success:
        log_pass(f"更新动物向量，pet_id={pet_id}, vector={vector}", f"更新成功")
    else:
        log_fail(f"更新动物向量，pet_id={pet_id}, vector={vector}", f"更新失败")

    vector_animal = animal_lib.get_animal_by_id(pet_id)
    if vector_animal and vector_animal.vector == vector_json:
        log_pass(f"验证向量更新，期望 vector={vector_json}", f"实际 vector={vector_animal.vector}")
    else:
        log_fail(f"验证向量更新，期望 vector={vector_json}", f"实际 vector={vector_animal.vector if vector_animal else '动物不存在'}")

    # 更新不存在动物
    vector_fail = animal_lib.update_animal_vector(999999, vector_json)
    if not vector_fail:
        log_pass(f"更新不存在动物向量，pet_id=999999", f"更新失败 (False)")
    else:
        log_fail(f"更新不存在动物向量，pet_id=999999", f"更新成功 (True)，预期失败")

    # ========== 8. 通用更新方法（update_animal） ==========
    print("\n8. 测试通用更新方法（update_animal）...")
    new_name = f"updated_{uuid.uuid4().hex[:6]}"
    new_desc = "这是一只非常健康的橘猫，已接种疫苗。"
    update_data = {
        'name': new_name,
        'description': new_desc,
        'personality': '活泼好动'
    }
    update_success = animal_lib.update_animal(pet_id, update_data)
    if update_success:
        log_pass(f"通用更新动物，pet_id={pet_id}, 更新数据={update_data}", f"更新成功")
    else:
        log_fail(f"通用更新动物，pet_id={pet_id}, 更新数据={update_data}", f"更新失败")

    updated_animal = animal_lib.get_animal_by_id(pet_id)
    if updated_animal and updated_animal.name == new_name and updated_animal.description == new_desc:
        log_pass(f"验证通用更新结果，期望 name={new_name}, description={new_desc}", f"实际 name={updated_animal.name}, description={updated_animal.description}")
    else:
        log_fail(f"验证通用更新结果，期望 name={new_name}, description={new_desc}", f"实际 name={updated_animal.name if updated_animal else '无'}, description={updated_animal.description if updated_animal else '无'}")

    # 更新不存在动物
    update_fail = animal_lib.update_animal(999999, {'name': '测试'})
    if not update_fail:
        log_pass(f"通用更新不存在动物，pet_id=999999", f"更新失败 (False)")
    else:
        log_fail(f"通用更新不存在动物，pet_id=999999", f"更新成功 (True)，预期失败")

    # ========== 9. 相似动物搜索 ==========
    print("\n9. 测试相似动物搜索...")
    similar_name1 = f"similar_1_{uuid.uuid4().hex[:6]}"
    similar_vector1 = json.dumps([0.1, 0.2, 0.3, 0.4])
    similar_id1 = animal_lib.add_animal(similar_name1, "相似猫1", status=0, vector=similar_vector1)

    similar_name2 = f"similar_2_{uuid.uuid4().hex[:6]}"
    similar_vector2 = json.dumps([0.9, 0.8, 0.7, 0.6])
    similar_id2 = animal_lib.add_animal(similar_name2, "相似猫2", status=0, vector=similar_vector2)

    if similar_id1 and similar_id2:
        query_vector = [0.1, 0.2, 0.3, 0.4]
        similar = animal_lib.search_similar_animals(query_vector, limit=3)
        if len(similar) >= 2:
            log_pass(f"相似动物搜索，query_vector={query_vector}", f"找到 {len(similar)} 只相似动物，最相似的是 {similar[0].name}")
        else:
            log_fail(f"相似动物搜索，query_vector={query_vector}", f"找到 {len(similar)} 只动物，预期至少2只")
    else:
        log_fail("添加相似动物测试数据失败", "无法继续测试相似动物搜索")

    invalid = animal_lib.search_similar_animals("invalid_vector", limit=5)
    if len(invalid) == 0:
        log_pass(f"相似动物搜索，无效查询向量", f"返回空列表")
    else:
        log_fail(f"相似动物搜索，无效查询向量", f"返回非空列表，预期空列表")

    # ========== 10. 删除动物 ==========
    print("\n10. 测试删除动物...")
    delete_name = f"to_be_deleted_{uuid.uuid4().hex[:6]}"
    delete_id = animal_lib.add_animal(delete_name, "测试删除", status=0)
    if delete_id:
        delete_success = animal_lib.delete_animal(delete_id)
        if delete_success:
            log_pass(f"删除动物，pet_id={delete_id}", f"删除成功")
        else:
            log_fail(f"删除动物，pet_id={delete_id}", f"删除失败")

        deleted = animal_lib.get_animal_by_id(delete_id)
        if deleted is None:
            log_pass(f"验证删除，pet_id={delete_id}", f"动物已不存在")
        else:
            log_fail(f"验证删除，pet_id={delete_id}", f"动物仍然存在")
    else:
        log_fail("添加待删除测试动物失败", "无法继续测试删除功能")

    delete_fail = animal_lib.delete_animal(999999)
    if not delete_fail:
        log_pass(f"删除不存在动物，pet_id=999999", f"删除失败 (False)")
    else:
        log_fail(f"删除不存在动物，pet_id=999999", f"删除成功 (True)，预期失败")

    # ========== 11. 清理测试数据 ==========
    print("\n11. 清理测试数据...")
    if animal_lib.db.open_database():
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_animal_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_adopted_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'similar_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'to_be_deleted_%'")
        animal_lib.db.close_database()
        log_pass("清理测试数据", f"删除所有测试动物成功")
    else:
        log_fail("清理测试数据", "数据库连接失败，请手动删除")

    print("\n" + "="*50 + "\n  测试完成\n" + "="*50)

if __name__ == "__main__":
    main()
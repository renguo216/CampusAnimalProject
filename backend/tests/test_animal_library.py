# ===== backend/tests/test_animal_library.py =====
"""
测试 AnimalLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_animal_library
"""
from backend.libs.animal_library import AnimalLibrary
import uuid
import json


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    animal_lib = AnimalLibrary()

    # ======== 清理旧测试数据 ========
    if animal_lib.db.open_database():
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_animal_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_adopted_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'similar_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'to_be_deleted_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'photo_test_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'location_test_%'")
        animal_lib.db.close_database()
        print("已清理旧测试数据")

    print("\n" + "=" * 50 + "\n  开始测试 AnimalLibrary\n" + "=" * 50)

    # ========== 1. 添加动物 ==========
    print("\n1. 测试添加动物 (add_animal)...")

    test_name = f"test_animal_{uuid.uuid4().hex[:8]}"
    pet_id = animal_lib.add_animal(
        name=test_name,
        breed="中华田园猫",
        status=0,
        color="橘色",
        age=6,
        gender=1,
        is_neutered=0,
        is_vaccinated=1,
        personality="温顺撒娇",
        description="在图书馆附近发现的流浪猫",
        photo_urls='["http://example.com/cat1.jpg"]',
        found_location="图书馆南门"
    )
    if pet_id:
        log_pass(f"添加动物，name={test_name}", f"pet_id={pet_id}")
    else:
        log_fail("添加动物", "返回 False")

    # 1.2 空名字
    if not animal_lib.add_animal("", "测试", 0):
        log_pass("空名字", "返回 False")
    else:
        log_fail("空名字", "返回 True")

    # 1.3 非法状态
    if not animal_lib.add_animal("测试", "测试", status=5):
        log_pass("非法状态(5)", "返回 False")
    else:
        log_fail("非法状态(5)", "返回 True")

    # 1.4 非法性别
    if not animal_lib.add_animal("测试", "测试", gender=99):
        log_pass("非法性别(99)", "返回 False")
    else:
        log_fail("非法性别(99)", "返回 True")

    # 1.5 非法绝育状态
    if not animal_lib.add_animal("测试", "测试", is_neutered=99):
        log_pass("非法绝育状态(99)", "返回 False")
    else:
        log_fail("非法绝育状态(99)", "返回 True")

    # ========== 2. 按ID查询 ==========
    print("\n2. 测试按ID查询 (get_animal_by_id)...")
    if pet_id:
        animal = animal_lib.get_animal_by_id(pet_id)
        if animal and animal.name == test_name:
            log_pass(f"查询存在动物，pet_id={pet_id}", f"name={animal.name}")
        else:
            log_fail("查询存在动物", "未找到")

    none_animal = animal_lib.get_animal_by_id(999999)
    if none_animal is None:
        log_pass("查询不存在动物", "返回 None")
    else:
        log_fail("查询不存在动物", "返回非空")

    # ========== 3. 按名字模糊查询 ==========
    print("\n3. 测试按名字模糊查询 (get_animal_by_name)...")
    animals = animal_lib.get_animal_by_name(test_name[:8])
    if len(animals) >= 1:
        log_pass(f"模糊查询 '{test_name[:8]}'", f"找到 {len(animals)} 只")
    else:
        log_fail("模糊查询", "未找到")

    if len(animal_lib.get_animal_by_name("不存在的名字")) == 0:
        log_pass("查询不存在名字", "返回空列表")
    else:
        log_fail("查询不存在名字", "返回非空")

    # ========== 4. 按状态筛选（分页） ==========
    print("\n4. 测试按状态筛选 (get_animals_by_status)...")
    adopted_name = f"test_adopted_{uuid.uuid4().hex[:6]}"
    adopted_id = animal_lib.add_animal(adopted_name, "中华田园犬", status=1)

    result = animal_lib.get_animals_by_status(1, page=1, page_size=10)
    if result.get("total", 0) >= 1:
        log_pass("筛选 status=1", f"total={result['total']}")
    else:
        log_fail("筛选 status=1", f"total={result.get('total', 0)}")

    result = animal_lib.get_animals_by_status(0, page=1, page_size=10)
    if result.get("total", 0) >= 1:
        log_pass("筛选 status=0", f"total={result['total']}")
    else:
        log_fail("筛选 status=0", f"total={result.get('total', 0)}")

    # 非法状态
    result = animal_lib.get_animals_by_status(99)
    if result.get("total", 0) == 0:
        log_pass("筛选非法状态(99)", "返回空结果")
    else:
        log_fail("筛选非法状态(99)", "返回非空")

    # ========== 5. 获取所有动物（分页） ==========
    print("\n5. 测试获取所有动物 (get_all_animals)...")
    result = animal_lib.get_all_animals(page=1, page_size=10)
    if result.get("total", 0) >= 2:
        log_pass("获取所有动物", f"total={result['total']}")
    else:
        log_fail("获取所有动物", f"total={result.get('total', 0)}")

    result = animal_lib.get_all_animals(page=1, page_size=1)
    if len(result.get("animals", [])) == 1:
        log_pass("分页 limit=1", "返回1条")
    else:
        log_fail("分页 limit=1", f"返回{len(result.get('animals', []))}条")

    # ========== 6. 更新动物状态 ==========
    print("\n6. 测试更新状态 (update_animal_status)...")
    if pet_id:
        success = animal_lib.update_animal_status(pet_id, 2)
        if success:
            animal = animal_lib.get_animal_by_id(pet_id)
            if animal.status == 2:
                log_pass("更新状态为2", "status=2")
            else:
                log_fail("更新状态为2", f"status={animal.status}")
        else:
            log_fail("更新状态为2", "返回 False")

        # 非法状态
        if not animal_lib.update_animal_status(pet_id, 99):
            log_pass("更新非法状态(99)", "返回 False")
        else:
            log_fail("更新非法状态(99)", "返回 True")

    if not animal_lib.update_animal_status(999999, 1):
        log_pass("更新不存在动物", "返回 False")
    else:
        log_fail("更新不存在动物", "返回 True")

    # ========== 7. 更新向量 ==========
    print("\n7. 测试更新向量 (update_animal_vector)...")
    if pet_id:
        vector = json.dumps([0.1, 0.2, 0.3])
        success = animal_lib.update_animal_vector(pet_id, vector)
        if success:
            animal = animal_lib.get_animal_by_id(pet_id)
            if animal.vector == vector:
                log_pass("更新向量", "验证成功")
            else:
                log_fail("更新向量", "验证失败")
        else:
            log_fail("更新向量", "返回 False")

    # ========== 8. 通用更新（白名单） ==========
    print("\n8. 测试通用更新 (update_animal)...")
    if pet_id:
        new_name = f"updated_{uuid.uuid4().hex[:6]}"
        success = animal_lib.update_animal(pet_id, {
            'name': new_name,
            'description': '新描述',
            'personality': '新性格'
        })
        if success:
            animal = animal_lib.get_animal_by_id(pet_id)
            if animal.name == new_name:
                log_pass("通用更新", f"name={animal.name}")
            else:
                log_fail("通用更新", "name未更新")
        else:
            log_fail("通用更新", "返回 False")

        # 更新禁止字段
        if not animal_lib.update_animal(pet_id, {'pet_id': 99999, 'created_at': '2020-01-01'}):
            log_pass("更新禁止字段", "被正确拒绝")
        else:
            animal = animal_lib.get_animal_by_id(pet_id)
            if animal.pet_id == pet_id:
                log_pass("更新禁止字段", "字段被过滤")
            else:
                log_fail("更新禁止字段", "pet_id被修改")

    if not animal_lib.update_animal(999999, {'name': 'test'}):
        log_pass("更新不存在动物", "返回 False")
    else:
        log_fail("更新不存在动物", "返回 True")

    # ========== 9. 照片管理 ==========
    print("\n9. 测试照片管理 (add_photo / remove_photo)...")
    photo_pet_id = animal_lib.add_animal(
        f"photo_test_{uuid.uuid4().hex[:6]}",
        "测试照片",
        status=0,
        photo_urls='["http://old.jpg"]'
    )

    if photo_pet_id:
        # 添加照片
        success = animal_lib.add_photo(photo_pet_id, "http://new1.jpg")
        if success:
            animal = animal_lib.get_animal_by_id(photo_pet_id)
            photos = json.loads(animal.photo_urls)
            if "http://new1.jpg" in photos and "http://old.jpg" in photos:
                log_pass("添加照片", f"共{len(photos)}张")
            else:
                log_fail("添加照片", f"photos={photos}")
        else:
            log_fail("添加照片", "返回 False")

        # 重复添加（应去重）
        animal_lib.add_photo(photo_pet_id, "http://new1.jpg")
        animal = animal_lib.get_animal_by_id(photo_pet_id)
        photos = json.loads(animal.photo_urls)
        if photos.count("http://new1.jpg") == 1:
            log_pass("重复添加去重", "正确")
        else:
            log_fail("重复添加去重", f"出现{photos.count('http://new1.jpg')}次")

        # 删除照片
        success = animal_lib.remove_photo(photo_pet_id, "http://old.jpg")
        if success:
            animal = animal_lib.get_animal_by_id(photo_pet_id)
            photos = json.loads(animal.photo_urls)
            if "http://old.jpg" not in photos:
                log_pass("删除照片", "old.jpg已删除")
            else:
                log_fail("删除照片", "old.jpg仍在")
        else:
            log_fail("删除照片", "返回 False")

        # 删除不存在照片
        if not animal_lib.remove_photo(photo_pet_id, "http://not_exist.jpg"):
            log_pass("删除不存在照片", "返回 False")
        else:
            log_fail("删除不存在照片", "返回 True")

    # ========== 10. 按地点搜索 ==========
    print("\n10. 测试按地点搜索 (search_animals_by_location)...")
    loc_pet_id = animal_lib.add_animal(
        f"location_test_{uuid.uuid4().hex[:6]}",
        "地点测试",
        status=0,
        found_location="图书馆北门草丛"
    )

    result = animal_lib.search_animals_by_location("图书馆", page=1, page_size=10)
    if result.get("total", 0) >= 1:
        log_pass("搜索地点'图书馆'", f"total={result['total']}")
    else:
        log_fail("搜索地点'图书馆'", f"total={result.get('total', 0)}")

    result = animal_lib.search_animals_by_location("火星", page=1, page_size=10)
    if result.get("total", 0) == 0:
        log_pass("搜索地点'火星'", "返回空结果")
    else:
        log_fail("搜索地点'火星'", "返回非空")

    # ========== 11. 统计汇总 ==========
    print("\n11. 测试统计汇总 (get_animal_statistics)...")
    stats = animal_lib.get_animal_statistics()
    if stats:
        total = stats.get("total", 0)
        on_campus = stats.get("on_campus", 0)
        adopted = stats.get("adopted", 0)
        medical = stats.get("medical_needed", 0)
        if total >= on_campus + adopted + medical:
            log_pass("统计汇总", f"total={total}, 在校={on_campus}, 领养={adopted}, 医疗={medical}")
        else:
            log_fail("统计汇总", "数据不一致")
    else:
        log_fail("统计汇总", "返回 None")

    # ========== 12. 相似动物搜索 ==========
    print("\n12. 测试相似动物搜索 (search_similar_animals)...")
    sim1 = animal_lib.add_animal(f"similar_1_{uuid.uuid4().hex[:6]}", "相似猫1", status=0, vector=json.dumps([0.1, 0.2, 0.3]))
    sim2 = animal_lib.add_animal(f"similar_2_{uuid.uuid4().hex[:6]}", "相似猫2", status=0, vector=json.dumps([0.9, 0.8, 0.7]))

    if sim1 and sim2:
        results = animal_lib.search_similar_animals([0.1, 0.2, 0.3], limit=2)
        if len(results) >= 1 and results[0].name.startswith("similar_1"):
            log_pass("相似搜索", f"最相似={results[0].name}")
        else:
            log_fail("相似搜索", f"结果={results[0].name if results else '空'}")

    # 无效向量
    if len(animal_lib.search_similar_animals("invalid")) == 0:
        log_pass("无效向量搜索", "返回空列表")
    else:
        log_fail("无效向量搜索", "返回非空")

    # ========== 13. 删除动物 ==========
    print("\n13. 测试删除动物 (delete_animal)...")
    del_id = animal_lib.add_animal(f"to_be_deleted_{uuid.uuid4().hex[:6]}", "待删除", status=0)
    if del_id:
        success = animal_lib.delete_animal(del_id)
        if success and animal_lib.get_animal_by_id(del_id) is None:
            log_pass("删除动物", "删除成功")
        else:
            log_fail("删除动物", "删除失败或仍存在")

    if not animal_lib.delete_animal(999999):
        log_pass("删除不存在动物", "返回 False")
    else:
        log_fail("删除不存在动物", "返回 True")

    # ========== 14. 清理 ==========
    print("\n14. 清理测试数据...")
    if animal_lib.db.open_database():
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_animal_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'test_adopted_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'similar_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'to_be_deleted_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'photo_test_%'")
        animal_lib.db.execute_raw_sql("DELETE FROM t_animal WHERE name LIKE 'location_test_%'")
        animal_lib.db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
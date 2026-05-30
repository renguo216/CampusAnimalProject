# ===== backend/tests/test_exchange_product_library.py =====
"""
测试 ExchangeProductLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_exchange_product_library
"""
from backend.libs.exchange_product_library import ExchangeProductLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    product_lib = ExchangeProductLibrary()
    db = product_lib.db

    # ======== 清理旧测试数据 ========
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_exchange_product WHERE name LIKE '测试商品_%'")
        db.close_database()
        print("已清理旧测试数据")

    print("\n" + "=" * 50 + "\n  开始测试 ExchangeProductLibrary\n" + "=" * 50)

    # ========== 1. 创建商品 ==========
    print("\n1. 测试创建商品 (create_exchange_product)...")
    p1_name = f"测试商品_{uuid.uuid4().hex[:6]}"
    result = product_lib.create_exchange_product({
        "name": p1_name,
        "description": "测试描述",
        "points_required": 100,
        "image_url": "http://example.com/1.jpg",
        "stock": 10,
        "status": 1
    })
    if result["success"] and result["data"].get("product_id"):
        p1_id = result["data"]["product_id"]
        log_pass(f"创建商品 {p1_name}", f"product_id={p1_id}")
    else:
        log_fail("创建商品", f"失败，message={result['message']}")
        p1_id = None

    # 缺少 name
    result = product_lib.create_exchange_product({"points_required": 50})
    if not result["success"] and "name" in result["message"]:
        log_pass("缺少 name", "返回 False")
    else:
        log_fail("缺少 name", f"返回 {result['success']}")

    # 缺少 points_required
    result = product_lib.create_exchange_product({"name": "测试"})
    if not result["success"] and "points_required" in result["message"]:
        log_pass("缺少 points_required", "返回 False")
    else:
        log_fail("缺少 points_required", f"返回 {result['success']}")

    # ========== 2. 查询商品 ==========
    print("\n2. 测试查询商品...")
    if p1_id:
        result = product_lib.get_exchange_item_by_id(p1_id)
        if result["success"] and result["data"]["name"] == p1_name:
            log_pass(f"查询商品 {p1_id}", f"name={result['data']['name']}")
        else:
            log_fail("查询商品", "失败")

    result = product_lib.get_exchange_item_by_id(999999)
    if not result["success"] and "不存在" in result["message"]:
        log_pass("查询不存在商品", "返回 False")
    else:
        log_fail("查询不存在商品", f"返回 {result['success']}")

    # 存在性检查
    if p1_id:
        result = product_lib.product_exists(p1_id)
        if result["success"] and result["data"]["exists"]:
            log_pass(f"存在性检查 {p1_id}", "exists=True")
        else:
            log_fail("存在性检查", f"exists={result['data'].get('exists')}")

    # ========== 3. 查询在售列表 ==========
    print("\n3. 测试查询在售列表 (get_exchange_items)...")
    result = product_lib.get_exchange_items(page=1, page_size=10)
    if result["success"] and result["data"].get("total", 0) >= 1:
        log_pass("查询在售列表", f"total={result['data']['total']}")
    else:
        log_fail("查询在售列表", f"total={result['data'].get('total', 0)}")

    # ========== 4. 更新商品 ==========
    print("\n4. 测试更新商品 (update_exchange_product)...")
    if p1_id:
        result = product_lib.update_exchange_product(p1_id, {"name": "更新后名称", "stock": 20})
        if result["success"]:
            log_pass("更新商品", "返回 True")
            detail = product_lib.get_exchange_item_by_id(p1_id)
            if detail["success"] and detail["data"]["name"] == "更新后名称":
                log_pass("验证更新", "name=更新后名称")
            else:
                log_fail("验证更新", f"name={detail['data']['name'] if detail['success'] else '失败'}")
        else:
            log_fail("更新商品", "返回 False")

        # 非法字段
        result = product_lib.update_exchange_product(p1_id, {"illegal": "test"})
        if not result["success"] and "没有有效更新字段" in result["message"]:
            log_pass("更新非法字段", "被过滤")
        else:
            log_fail("更新非法字段", f"返回 {result['success']}")

    # 更新不存在
    result = product_lib.update_exchange_product(999999, {"name": "test"})
    if not result["success"]:
        log_pass("更新不存在商品", "返回 False")
    else:
        log_fail("更新不存在商品", "返回 True")

    # ========== 5. 库存管理 ==========
    print("\n5. 测试库存管理...")
    if p1_id:
        result = product_lib.update_product_stock(p1_id, 5)
        if result["success"]:
            log_pass("更新库存为5", "返回 True")
            stock = product_lib.get_product_stock(p1_id)
            if stock["success"] and stock["data"]["stock"] == 5:
                log_pass("验证库存", "stock=5")
            else:
                log_fail("验证库存", f"stock={stock['data']['stock'] if stock['success'] else '失败'}")
        else:
            log_fail("更新库存", "返回 False")

    result = product_lib.update_product_stock(999999, 5)
    if not result["success"]:
        log_pass("更新不存在库存", "返回 False")
    else:
        log_fail("更新不存在库存", "返回 True")

    # ========== 6. 上下架 ==========
    print("\n6. 测试上下架 (toggle_product_status)...")
    if p1_id:
        result = product_lib.toggle_product_status(p1_id, 0)
        if result["success"]:
            log_pass("下架商品", "返回 True")
        else:
            log_fail("下架商品", "返回 False")

        result = product_lib.toggle_product_status(p1_id, 1)
        if result["success"]:
            log_pass("上架商品", "返回 True")
        else:
            log_fail("上架商品", "返回 False")

    result = product_lib.toggle_product_status(999999, 0)
    if not result["success"]:
        log_pass("上下架不存在", "返回 False")
    else:
        log_fail("上下架不存在", "返回 True")

    # ========== 7. 删除商品 ==========
    print("\n7. 测试删除商品 (delete_exchange_product)...")
    p2_name = f"测试商品_{uuid.uuid4().hex[:6]}"
    result = product_lib.create_exchange_product({
        "name": p2_name, "points_required": 50, "stock": 5
    })
    if result["success"]:
        p2_id = result["data"]["product_id"]
        del_result = product_lib.delete_exchange_product(p2_id)
        if del_result["success"]:
            log_pass(f"删除商品 {p2_id}", "成功")
            check = product_lib.get_exchange_item_by_id(p2_id)
            if not check["success"]:
                log_pass("验证删除", "已不存在")
            else:
                log_fail("验证删除", "仍存在")
        else:
            log_fail("删除商品", "返回 False")

    result = product_lib.delete_exchange_product(999999)
    if not result["success"]:
        log_pass("删除不存在商品", "返回 False")
    else:
        log_fail("删除不存在商品", "返回 True")

    # ========== 8. 清理 ==========
    print("\n8. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_exchange_product WHERE name LIKE '测试商品_%'")
        db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
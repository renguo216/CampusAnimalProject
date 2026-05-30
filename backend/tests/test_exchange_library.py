# ===== backend/tests/test_exchange_library.py =====
"""
测试 ExchangeLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_exchange_library
"""
from backend.libs.exchange_library import ExchangeLibrary
from backend.libs.exchange_product_library import ExchangeProductLibrary
from backend.libs.user_library import UserLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    exchange_lib = ExchangeLibrary()
    product_lib = ExchangeProductLibrary()
    user_lib = UserLibrary()
    db = exchange_lib.db

    # ======== 清理旧测试数据 ========
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_exchange WHERE user_id LIKE 'test_ex_%'")
        db.execute_raw_sql("DELETE FROM t_exchange_product WHERE name LIKE '测试商品_%'")
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_ex_%'")
        db.close_database()
        print("已清理旧测试数据")

    # ======== 准备数据 ========
    u1 = f"test_ex_{uuid.uuid4().hex[:6]}"
    u2 = f"test_ex_{uuid.uuid4().hex[:6]}"
    admin = f"test_ex_{uuid.uuid4().hex[:6]}"
    user_lib.register_user(u1, "用户1", role=1)
    user_lib.register_user(u2, "用户2", role=1)
    user_lib.register_user(admin, "管理员", role=3)

    # 设置积分
    if db.open_database():
        db.execute_raw_sql("UPDATE t_user SET points = %s WHERE user_id = %s", (500, u1))
        db.execute_raw_sql("UPDATE t_user SET points = %s WHERE user_id = %s", (50, u2))
        db.close_database()

    # 创建商品
    p1 = product_lib.create_exchange_product({
        "name": f"测试商品_{uuid.uuid4().hex[:6]}",
        "points_required": 100,
        "stock": 5,
        "status": 1
    })
    p1_id = p1["data"]["product_id"] if p1["success"] else None

    p2 = product_lib.create_exchange_product({
        "name": f"测试商品_{uuid.uuid4().hex[:6]}",
        "points_required": 200,
        "stock": 0,
        "status": 1
    })
    p2_id = p2["data"]["product_id"] if p2["success"] else None

    print("\n" + "=" * 50 + "\n  开始测试 ExchangeLibrary\n" + "=" * 50)

    # ========== 1. 查询积分 ==========
    print("\n1. 测试查询积分 (check_user_points)...")
    result = exchange_lib.check_user_points(u1)
    if result["success"] and result["data"]["points"] == 500:
        log_pass("查询用户1积分", "points=500")
    else:
        log_fail("查询用户1积分", f"points={result['data']['points'] if result['success'] else '失败'}")

    result = exchange_lib.check_user_points("not_exist")
    if not result["success"] and "不存在" in result["message"]:
        log_pass("查询不存在用户", "返回 False")
    else:
        log_fail("查询不存在用户", f"返回 {result['success']}")

    # ========== 2. 提交兑换 ==========
    print("\n2. 测试提交兑换 (submit_exchange)...")
    ex1_id = None

    if p1_id:
        result = exchange_lib.submit_exchange(u1, p1_id)
        if result["success"]:
            ex1_id = result["data"]["exchange_id"]
            log_pass(f"用户1兑换商品1", f"exchange_id={ex1_id}")
            # 验证积分扣除
            pts = exchange_lib.check_user_points(u1)
            if pts["success"] and pts["data"]["points"] == 400:
                log_pass("验证积分扣除", "points=400")
            else:
                log_fail("验证积分扣除", f"points={pts['data']['points']}")
            # 验证库存减少
            stock = product_lib.get_product_stock(p1_id)
            if stock["success"] and stock["data"]["stock"] == 4:
                log_pass("验证库存减少", "stock=4")
            else:
                log_fail("验证库存减少", f"stock={stock['data']['stock'] if stock['success'] else '失败'}")
        else:
            log_fail("用户1兑换商品1", f"失败：{result['message']}")

    # 积分不足
    if p1_id:
        result = exchange_lib.submit_exchange(u2, p1_id)
        if not result["success"] and "积分不足" in result["message"]:
            log_pass("用户2积分不足", "返回 False")
        else:
            log_fail("用户2积分不足", f"返回 {result['success']}")

    # 库存不足
    if p2_id:
        result = exchange_lib.submit_exchange(u1, p2_id)
        if not result["success"] and "库存不足" in result["message"]:
            log_pass("商品2库存不足", "返回 False")
        else:
            log_fail("商品2库存不足", f"返回 {result['success']}")

    # 商品不存在
    result = exchange_lib.submit_exchange(u1, 999999)
    if not result["success"] and "不存在" in result["message"]:
        log_pass("兑换不存在商品", "返回 False")
    else:
        log_fail("兑换不存在商品", f"返回 {result['success']}")

    # ========== 3. 取消兑换 ==========
    print("\n3. 测试取消兑换 (cancel_exchange)...")
    ex2_id = None

    if p1_id:
        result = exchange_lib.submit_exchange(u1, p1_id)
        if result["success"]:
            ex2_id = result["data"]["exchange_id"]
            # 正常取消
            cancel = exchange_lib.cancel_exchange(ex2_id, u1)
            if cancel["success"]:
                log_pass(f"用户1取消兑换 {ex2_id}", "成功")
                # 验证积分返还
                pts = exchange_lib.check_user_points(u1)
                if pts["success"] and pts["data"]["points"] == 400:
                    log_pass("验证积分返还", "points=400")
                else:
                    log_fail("验证积分返还", f"points={pts['data']['points']}")
                # 验证库存恢复
                stock = product_lib.get_product_stock(p1_id)
                if stock["success"] and stock["data"]["stock"] == 4:
                    log_pass("验证库存恢复", "stock=4")
                else:
                    log_fail("验证库存恢复", f"stock={stock['data']['stock']}")
            else:
                log_fail("取消兑换", f"失败：{cancel['message']}")

    # 无权取消
    if ex1_id:
        result = exchange_lib.cancel_exchange(ex1_id, u2)
        if not result["success"] and "无权" in result["message"]:
            log_pass("用户2无权取消", "返回 False")
        else:
            log_fail("用户2无权取消", f"返回 {result['success']}")

    # 取消不存在
    result = exchange_lib.cancel_exchange(999999, u1)
    if not result["success"] and "不存在" in result["message"]:
        log_pass("取消不存在记录", "返回 False")
    else:
        log_fail("取消不存在记录", f"返回 {result['success']}")

    # ========== 4. 完成兑换 ==========
    print("\n4. 测试完成兑换 (complete_exchange)...")
    if ex1_id:
        result = exchange_lib.complete_exchange(ex1_id)
        if result["success"]:
            log_pass(f"完成兑换 {ex1_id}", "成功")
        else:
            log_fail("完成兑换", f"失败：{result['message']}")

    # 完成已取消的
    if ex2_id:
        result = exchange_lib.complete_exchange(ex2_id)
        if not result["success"] and "状态" in result["message"]:
            log_pass("完成已取消兑换", "返回 False")
        else:
            log_fail("完成已取消兑换", f"返回 {result['success']}")

    # ========== 5. 拒绝兑换 ==========
    print("\n5. 测试拒绝兑换 (reject_exchange)...")
    if p1_id:
        result = exchange_lib.submit_exchange(u1, p1_id)
        if result["success"]:
            ex3_id = result["data"]["exchange_id"]
            reject = exchange_lib.reject_exchange(ex3_id, "库存不足，拒绝兑换")
            if reject["success"]:
                log_pass(f"拒绝兑换 {ex3_id}", "成功，带审核意见")
                # 验证积分返还
                pts = exchange_lib.check_user_points(u1)
                if pts["success"] and pts["data"]["points"] == 400:
                    log_pass("拒绝后积分返还", "points=400")
                else:
                    log_fail("拒绝后积分返还", f"points={pts['data']['points']}")
            else:
                log_fail("拒绝兑换", f"失败：{reject['message']}")

    # 拒绝不存在
    result = exchange_lib.reject_exchange(999999, "测试")
    if not result["success"] and "不存在" in result["message"]:
        log_pass("拒绝不存在记录", "返回 False")
    else:
        log_fail("拒绝不存在记录", f"返回 {result['success']}")

    # ========== 6. 查询记录 ==========
    print("\n6. 测试查询兑换记录...")
    result = exchange_lib.get_user_exchanges(u1, page=1, page_size=10)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("查询用户1记录", f"total={result['data']['total']}")
    else:
        log_fail("查询用户1记录", f"total={result['data']['total'] if result['success'] else '失败'}")

    result = exchange_lib.get_all_exchanges(page=1, page_size=10)
    if result["success"] and result["data"]["total"] >= 1:
        log_pass("查询所有记录", f"total={result['data']['total']}")
    else:
        log_fail("查询所有记录", f"total={result['data']['total'] if result['success'] else '失败'}")

    # ========== 7. 清理 ==========
    print("\n7. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_exchange WHERE user_id LIKE 'test_ex_%'")
        db.execute_raw_sql("DELETE FROM t_exchange_product WHERE name LIKE '测试商品_%'")
        db.execute_raw_sql("DELETE FROM t_user WHERE user_id LIKE 'test_ex_%'")
        db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
"""
测试 NoticeLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_notice_library
"""
from backend.libs.notice_library import NoticeLibrary
import uuid
from datetime import datetime

def log_pass(original, current):
    print(f"  ✅ PASS: 原始数据 = {original}, 当前数据 = {current}")

def log_fail(original, current):
    print(f"  ❌ FAIL: 原始数据 = {original}, 当前数据 = {current}")

def main():
    notice_lib = NoticeLibrary()

    # ======== 清理旧测试数据 ========
    if notice_lib.db.open_database():
        # 删除所有以 test_notice_ 开头的公告，避免干扰
        notice_lib.db.execute_raw_sql("DELETE FROM t_notice WHERE title LIKE 'test_notice_%'")
        notice_lib.db.close_database()
        print("已清理旧测试数据")
    # =================================

    print("\n" + "="*50 + "\n  开始测试 NoticeLibrary\n" + "="*50)

    # ========== 1. 创建公告 ==========
    print("\n1. 测试创建公告...")
    test_title = f"test_notice_{uuid.uuid4().hex[:8]}"
    test_content = "这是一条测试公告内容，用于验证NoticeLibrary功能。"
    # 第一次创建
    success = notice_lib.create_notice(test_title, test_content)
    if success:
        log_pass(f"创建新公告，标题={test_title}", f"创建成功 (True)")
    else:
        log_fail(f"创建新公告，标题={test_title}", f"创建失败 (False)")

    # 创建另一条公告（用于后续列表测试）
    test_title2 = f"test_notice_{uuid.uuid4().hex[:8]}"
    test_content2 = "第二条测试公告。"
    success2 = notice_lib.create_notice(test_title2, test_content2)
    if success2:
        log_pass(f"创建第二条公告，标题={test_title2}", f"创建成功 (True)")
    else:
        log_fail(f"创建第二条公告，标题={test_title2}", f"创建失败 (False)")

    # ========== 2. 获取所有公告 ==========
    print("\n2. 测试获取所有公告列表...")
    all_notices = notice_lib.get_all_notices()
    if len(all_notices) >= 2:
        log_pass(f"获取所有公告，order_by='created_at DESC'", f"共找到 {len(all_notices)} 条公告")
        # 验证排序：第一条应该是最近创建的（我们刚创建的两条）
        if all_notices[0].title == test_title2 or all_notices[0].title == test_title:
            log_pass(f"公告排序验证", f"按时间倒序排列，最近创建的排在前面")
        else:
            log_fail(f"公告排序验证", f"排序不符合预期")
    else:
        log_fail(f"获取所有公告", f"找到 {len(all_notices)} 条公告，预期至少 2 条")

    # ========== 3. 获取最新公告 ==========
    print("\n3. 测试获取最新公告...")
    latest = notice_lib.get_latest_notice()
    if latest:
        log_pass(f"获取最新公告", f"最新公告标题: {latest.title}, 创建时间: {latest.created_at}")
        # 验证最新公告是否是我们最后创建的那条
        if latest.title == test_title2:
            log_pass(f"验证最新公告正确性", f"与最后创建的公告一致")
        else:
            log_fail(f"验证最新公告正确性", f"最新公告不是最后创建的")
    else:
        log_fail(f"获取最新公告", f"返回 None，预期有公告")

    # ========== 4. 按ID查询公告 ==========
    print("\n4. 测试按ID查询公告...")
    if all_notices:
        # 查询第一条公告
        target = all_notices[0]
        notice = notice_lib.get_notice_by_id(target.notice_id)
        if notice and notice.notice_id == target.notice_id:
            log_pass(f"按ID查询已存在公告，notice_id={target.notice_id}", f"查询成功，标题={notice.title}")
        else:
            log_fail(f"按ID查询已存在公告，notice_id={target.notice_id}", f"查询失败或数据不匹配")

        # 查询不存在的ID
        none_notice = notice_lib.get_notice_by_id("not_exist_123")
        if none_notice is None:
            log_pass(f"按ID查询不存在公告，notice_id='not_exist_123'", f"返回 None")
        else:
            log_fail(f"按ID查询不存在公告，notice_id='not_exist_123'", f"返回非None，预期 None")
    else:
        log_fail("获取公告列表失败", "无法进行按ID查询测试")

    # ========== 5. 删除公告 ==========
    print("\n5. 测试删除公告...")
    # 先查询所有公告，获取第一条公告ID
    if all_notices:
        target_notice = all_notices[-1]  # 取最后一条（第一条创建的）
        delete_success = notice_lib.delete_notice(target_notice.notice_id)
        if delete_success:
            log_pass(f"删除公告，notice_id={target_notice.notice_id}", f"删除成功 (True)")
        else:
            log_fail(f"删除公告，notice_id={target_notice.notice_id}", f"删除失败 (False)")

        # 验证删除后是否还存在
        deleted = notice_lib.get_notice_by_id(target_notice.notice_id)
        if deleted is None:
            log_pass(f"验证删除结果", f"公告已不存在")
        else:
            log_fail(f"验证删除结果", f"公告仍然存在")
    else:
        log_fail("获取公告列表失败", "无法进行删除测试")

    # ========== 6. 删除不存在公告 ==========
    print("\n6. 测试删除不存在公告...")
    delete_fail = notice_lib.delete_notice("not_exist_123")
    if not delete_fail:
        log_pass(f"删除不存在公告，notice_id='not_exist_123'", f"删除失败 (False)，预期行为")
    else:
        log_fail(f"删除不存在公告，notice_id='not_exist_123'", f"删除成功 (True)，预期失败")

    # ========== 7. 清理测试数据 ==========
    print("\n7. 清理测试数据...")
    if notice_lib.db.open_database():
        # 清理所有测试公告
        notice_lib.db.execute_raw_sql("DELETE FROM t_notice WHERE title LIKE 'test_notice_%'")
        notice_lib.db.close_database()
        log_pass("清理测试数据", f"删除所有测试公告成功")
    else:
        log_fail("清理测试数据", "数据库连接失败，请手动删除")

    print("\n" + "="*50 + "\n  测试完成\n" + "="*50)

if __name__ == "__main__":
    main()
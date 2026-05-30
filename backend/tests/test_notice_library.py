# ===== backend/tests/test_notice_library.py =====
"""
测试 NoticeLibrary 所有功能
运行方式（在项目根目录执行）：
    python -m backend.tests.test_notice_library
"""
from backend.libs.notice_library import NoticeLibrary
import uuid


def log_pass(original, current):
    print(f"  [PASS] 原始数据 = {original}, 当前数据 = {current}")


def log_fail(original, current):
    print(f"  [FAIL] 原始数据 = {original}, 当前数据 = {current}")


def main():
    notice_lib = NoticeLibrary()
    db = notice_lib.db

    # ======== 清理旧测试数据 ========
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_notice WHERE title LIKE 'test_notice_%'")
        db.close_database()
        print("已清理旧测试数据")

    print("\n" + "=" * 50 + "\n  开始测试 NoticeLibrary\n" + "=" * 50)

    # ========== 1. 创建公告 ==========
    print("\n1. 测试创建公告 (create_notice)...")

    # 1.1 普通公告
    t1 = f"test_notice_{uuid.uuid4().hex[:8]}"
    success = notice_lib.create_notice(t1, "普通公告内容", is_top=0)
    if success:
        log_pass(f"创建普通公告 {t1}", "成功")
    else:
        log_fail("创建普通公告", "失败")

    # 1.2 置顶公告
    t2 = f"test_notice_{uuid.uuid4().hex[:8]}"
    success = notice_lib.create_notice(t2, "置顶公告内容", is_top=1)
    if success:
        log_pass(f"创建置顶公告 {t2}", "成功")
    else:
        log_fail("创建置顶公告", "失败")

    # 1.3 空标题
    if not notice_lib.create_notice("", "内容"):
        log_pass("空标题", "返回 False")
    else:
        log_fail("空标题", "返回 True")

    # ========== 2. 获取所有公告（分页 + 置顶优先） ==========
    print("\n2. 测试获取所有公告 (get_all_notices)...")
    result = notice_lib.get_all_notices(page=1, page_size=10)
    if result["total"] >= 2:
        log_pass("获取公告列表", f"total={result['total']}")
        # 验证置顶排在最前
        if result["notices"][0].is_top == 1:
            log_pass("置顶优先排序", "第一条是置顶")
        else:
            log_fail("置顶优先排序", "第一条不是置顶")
    else:
        log_fail("获取公告列表", f"total={result['total']}")

    # 分页测试
    result = notice_lib.get_all_notices(page=1, page_size=1)
    if len(result["notices"]) == 1:
        log_pass("分页 limit=1", "返回1条")
    else:
        log_fail("分页 limit=1", f"返回{len(result['notices'])}条")

    # ========== 3. 获取最新公告 ==========
    print("\n3. 测试获取最新公告 (get_latest_notice)...")
    latest = notice_lib.get_latest_notice()
    if latest and latest.is_top == 1:
        log_pass("获取最新公告", f"置顶公告 {latest.title}")
    else:
        log_fail("获取最新公告", f"is_top={latest.is_top if latest else 'None'}")

    # ========== 4. 按ID查询 ==========
    print("\n4. 测试按ID查询 (get_notice_by_id)...")
    all_result = notice_lib.get_all_notices(page=1, page_size=10)
    if all_result["notices"]:
        nid = all_result["notices"][0].notice_id
        notice = notice_lib.get_notice_by_id(nid)
        if notice and notice.notice_id == nid:
            log_pass(f"查询存在公告 {nid}", "成功")
        else:
            log_fail("查询存在公告", "失败")

    none_notice = notice_lib.get_notice_by_id("not_exist")
    if none_notice is None:
        log_pass("查询不存在公告", "返回 None")
    else:
        log_fail("查询不存在公告", "返回非空")

    # ========== 5. 更新公告 ==========
    print("\n5. 测试更新公告 (update_notice)...")
    if all_result["notices"]:
        nid = all_result["notices"][0].notice_id
        # 更新标题和内容
        success = notice_lib.update_notice(nid, title="更新后标题", content="更新后内容")
        if success:
            updated = notice_lib.get_notice_by_id(nid)
            if updated.title == "更新后标题" and updated.content == "更新后内容":
                log_pass("更新标题和内容", "验证成功")
            else:
                log_fail("更新标题和内容", f"title={updated.title}, content={updated.content}")
        else:
            log_fail("更新标题和内容", "返回 False")

        # 更新置顶状态
        success = notice_lib.update_notice(nid, is_top=1)
        if success:
            updated = notice_lib.get_notice_by_id(nid)
            if updated.is_top == 1:
                log_pass("更新置顶状态", "is_top=1")
            else:
                log_fail("更新置顶状态", f"is_top={updated.is_top}")
        else:
            log_fail("更新置顶状态", "返回 False")

        # 空标题
        if not notice_lib.update_notice(nid, title=""):
            log_pass("更新空标题", "返回 False")
        else:
            log_fail("更新空标题", "返回 True")

    # 更新不存在
    if not notice_lib.update_notice("not_exist", title="test"):
        log_pass("更新不存在公告", "返回 False")
    else:
        log_fail("更新不存在公告", "返回 True")

    # ========== 6. 搜索公告 ==========
    print("\n6. 测试搜索公告 (search_notices_by_title)...")
    result = notice_lib.search_notices_by_title("更新后", page=1, page_size=10)
    if result["total"] >= 1:
        log_pass("搜索'更新后'", f"total={result['total']}")
    else:
        log_fail("搜索'更新后'", f"total={result['total']}")

    result = notice_lib.search_notices_by_title("火星", page=1, page_size=10)
    if result["total"] == 0:
        log_pass("搜索'火星'", "返回空")
    else:
        log_fail("搜索'火星'", f"total={result['total']}")

    # ========== 7. 删除公告 ==========
    print("\n7. 测试删除公告 (delete_notice)...")
    if all_result["notices"]:
        nid = all_result["notices"][-1].notice_id
        success = notice_lib.delete_notice(nid)
        if success and notice_lib.get_notice_by_id(nid) is None:
            log_pass(f"删除公告 {nid}", "成功")
        else:
            log_fail("删除公告", "失败或仍存在")

    if not notice_lib.delete_notice("not_exist"):
        log_pass("删除不存在公告", "返回 False")
    else:
        log_fail("删除不存在公告", "返回 True")

    # ========== 8. 清理 ==========
    print("\n8. 清理测试数据...")
    if db.open_database():
        db.execute_raw_sql("DELETE FROM t_notice WHERE title LIKE 'test_notice_%'")
        db.close_database()
        log_pass("清理数据", "完成")
    else:
        log_fail("清理数据", "连接失败")

    print("\n" + "=" * 50 + "\n  测试完成\n" + "=" * 50)


if __name__ == "__main__":
    main()
from backend.libs.user_library import UserLibrary

if __name__ == "__main__":
    user_lib = UserLibrary()

    # 先清理旧数据（方便多次测试）
    print("正在清理旧数据...")
    if user_lib.db.open_database():
        user_lib.db.execute_raw_sql("DELETE FROM t_user WHERE user_id = 'test_001'")
        user_lib.db.close_database()

    # 1. 测试注册用户
    if user_lib.register_user('test_001', '测试用户'):
        print("✅ 用户注册成功")
    else:
        print("❌ 用户注册失败")

    # 2. 测试查询用户
    user = user_lib.get_user_by_account('test_001')
    print(f"🔍 查到的用户: {user}")

    # 3. 测试验证用户有效性
    is_valid = user_lib.verify_user_validity('test_001')
    print(f"✅ 用户有效性验证: {is_valid}")

    # 4. 测试更新用户信息
    if user_lib.update_user_info('test_001', {'nickname': '修改后的昵称'}):
        print("✅ 用户信息更新成功")
    else:
        print("❌ 用户信息更新失败")
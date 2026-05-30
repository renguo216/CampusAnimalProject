import pymysql

# 替换成你 MySQL 的 root 密码
PASSWORD = '123456'

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password=PASSWORD,
        database='campus_animal'
    )
    print("✅ 数据库连接成功！")
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM t_user;")
        result = cursor.fetchall()
        print(f"t_user 表中有 {len(result)} 条记录")
    
    connection.close()
except Exception as e:
    print(f"❌ 连接失败: {e}")
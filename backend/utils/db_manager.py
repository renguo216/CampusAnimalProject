import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv

# 加载环境变量（如果你的密码等敏感信息存放在 .env 文件中）
load_dotenv()

class DatabaseManager:
    """
    通用数据操作基类（对应文档 3.5.2）
    封装了所有表公用的增删查改以及数据库连接管理操作。
    """

    def __init__(self, host=None, user=None, password=None, db_name=None):
        """
        初始化数据库连接参数
        支持从环境变量读取，也可直接传入
        """
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.user = user or os.getenv('DB_USER', 'root')
        self.password = password or os.getenv('DB_PASSWORD', '')
        self.db_name = db_name or os.getenv('DB_NAME', 'campus_animal')
        self.connection = None

    def open_database(self):
        """
        建立数据库连接（对应文档的 openDatabase）
        """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=DictCursor  # 让查询结果以字典形式返回，方便使用
            )
            print("数据库连接成功！")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False

    def close_database(self):
        """
        关闭数据库连接（对应文档的 closeDatabase）
        """
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭。")

    def insert(self, table_name, data_dict):
        """
        向指定表中插入一条记录（对应文档的 insert）
        :param table_name: 表名（字符串）
        :param data_dict: 要插入的数据（字典，键为字段名，值为字段值）
        :return: 成功返回 True，失败返回 False
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return False
        try:
            with self.connection.cursor() as cursor:
                columns = ', '.join(data_dict.keys())
                placeholders = ', '.join(['%s'] * len(data_dict))
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, list(data_dict.values()))
            self.connection.commit()
            print(f"成功插入一条记录到 {table_name}")
            return True
        except Exception as e:
            print(f"插入失败: {e}")
            return False

    def delete(self, table_name, id_key, id_value):
        """
        根据主键从指定表中删除一条记录（对应文档的 delete）
        :param table_name: 表名
        :param id_key: 主键字段名
        :param id_value: 主键的值
        :return: 成功返回 True，失败返回 False
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return False
        try:
            with self.connection.cursor() as cursor:
                sql = f"DELETE FROM {table_name} WHERE {id_key} = %s"
                cursor.execute(sql, (id_value,))
            self.connection.commit()
            print(f"成功从 {table_name} 删除 id={id_value} 的记录")
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            return False

    def update(self, table_name, id_key, id_value, data_dict):
        """
        根据主键更新指定表中的记录（对应文档的 update)
        :param table_name: 表名
        :param id_key: 主键字段名
        :param id_value: 主键的值
        :param data_dict: 要更新的数据（字典）
        :return: 成功返回 True,失败返回 False
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return False
        try:
            with self.connection.cursor() as cursor:
                set_clause = ', '.join([f"{key} = %s" for key in data_dict.keys()])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_key} = %s"
                cursor.execute(sql, list(data_dict.values()) + [id_value])
            self.connection.commit()
            print(f"成功更新 {table_name} 中 id={id_value} 的记录")
            return True
        except Exception as e:
            print(f"更新失败: {e}")
            return False

    def get_by_id(self, table_name, id_key, id_value):
        """
        根据主键从指定表中查询一条记录（对应文档的 getbyid）
        :param table_name: 表名
        :param id_key: 主键字段名
        :param id_value: 主键的值
        :return: 成功返回字典形式的记录，失败返回 None
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return None
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT * FROM {table_name} WHERE {id_key} = %s"
                cursor.execute(sql, (id_value,))
                result = cursor.fetchone()
                return result
        except Exception as e:
            print(f"查询失败: {e}")
            return None

    def get_all(self, table_name):
        """
        查询指定表的所有记录（额外补充方法，方便开发）
        :param table_name: 表名
        :return: 成功返回列表，失败返回 None
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return None
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT * FROM {table_name}"
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
        except Exception as e:
            print(f"查询失败: {e}")
            return None

    def execute_raw_sql(self, sql, params=None):
        """
        执行任意原生 SQL 语句，并自动提交更改（确保 DELETE/UPDATE 生效）
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchall()
                # ✅ 加上这一行，确保删除、更新立即生效
                self.connection.commit()
                return result
        except Exception as e:
            print(f"❌ SQL 执行失败: {e}")
            return None
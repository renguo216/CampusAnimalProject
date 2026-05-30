import pymysql
from pymysql.cursors import DictCursor
from pymysql.converters import conversions
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
            # 复制默认转换器，将 DECIMAL / NEWDECIMAL 自动转为 float，
            # 避免上层业务代码出现 decimal.Decimal + float 的 TypeError
            conv = conversions.copy()
            conv[pymysql.FIELD_TYPE.DECIMAL] = float
            conv[pymysql.FIELD_TYPE.NEWDECIMAL] = float

            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=DictCursor,  # 让查询结果以字典形式返回，方便使用
                conv=conv
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
            self.connection = None  # 置空，防止后续复用已关闭的连接
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
            if not self.connection:
                print("请先调用 open_database() 建立连接")
                return False
            try:
                with self.connection.cursor() as cursor:
                    sql = f"DELETE FROM {table_name} WHERE {id_key} = %s"
                    cursor.execute(sql, (str(id_value),))  # 加 str()
                    self.connection.commit()
                    if cursor.rowcount > 0:
                        print(f"✅ 成功从 {table_name} 删除 id={id_value} 的记录")
                        return True
                    else:
                        print(f"⚠️ 未找到 id={id_value} 的记录，删除失败")
                        return False
            except Exception as e:
                print(f"❌ 删除失败: {e}")
                return False
            
    def update(self, table_name, id_key, id_value, data_dict):
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return False
        try:
            with self.connection.cursor() as cursor:
                set_clause = ', '.join([f"{key} = %s" for key in data_dict.keys()])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_key} = %s"
                values = list(data_dict.values()) + [str(id_value)]
                cursor.execute(sql, values)
                self.connection.commit()
                
                # 验证：查询该记录是否存在（替代 rowcount，兼容 varchar 主键）
                verify_sql = f"SELECT 1 FROM {table_name} WHERE {id_key} = %s"
                cursor.execute(verify_sql, (str(id_value),))
                exists = cursor.fetchone() is not None
                
                if exists:
                    print(f"✅ 成功更新 {table_name} 中 id={id_value} 的记录")
                    return True
                else:
                    print(f"⚠️ 未找到 id={id_value} 的记录，更新失败")
                    return False
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False
        

    def get_by_id(self, table_name, id_key, id_value):
            if not self.connection:
                print("请先调用 open_database() 建立连接")
                return None
            try:
                with self.connection.cursor() as cursor:
                    sql = f"SELECT * FROM {table_name} WHERE {id_key} = %s"
                    cursor.execute(sql, (str(id_value),))  # 加 str()
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
        
    def insert_many(self, table_name, data_list):
        """
        批量向指定表中插入多条记录
        :param table_name: 表名
        :param data_list: 包含多个字典的列表，每个字典代表一行数据
        :return: 成功返回 True，失败返回 False
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return False
        if not data_list:
            return False
        try:
            # 获取第一个字典的键作为列名
            columns = ', '.join(data_list[0].keys())
            placeholders = ', '.join(['%s'] * len(data_list[0]))
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            # 将数据转换为列表的列表
            values = [list(item.values()) for item in data_list]
            
            with self.connection.cursor() as cursor:
                cursor.executemany(sql, values)
                self.connection.commit()
            print(f"成功批量插入 {len(data_list)} 条记录到 {table_name}")
            return True
        except Exception as e:
            print(f"批量插入失败: {e}")
            return False
        
    def get_paginated(self, table_name, page=1, page_size=20, where_clause=None, params=None, order_by=None):
        """
        分页查询通用方法
        :param table_name: 表名
        :param page: 页码，从1开始
        :param page_size: 每页记录数
        :param where_clause: WHERE 子句（不包含 WHERE 关键字），例如 "status = %s"
        :param params: WHERE 子句的参数，例如 (0,)
        :param order_by: 排序字段，例如 "created_at DESC"
        :return: 包含记录列表和总记录数的字典
        """
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return None
        
        offset = (page - 1) * page_size
        sql_count = f"SELECT COUNT(*) as total FROM {table_name}"
        sql_data = f"SELECT * FROM {table_name}"
        
        if where_clause:
            sql_count += f" WHERE {where_clause}"
            sql_data += f" WHERE {where_clause}"
        
        if order_by:
            sql_data += f" ORDER BY {order_by}"
        
        sql_data += f" LIMIT {page_size} OFFSET {offset}"
        
        try:
            with self.connection.cursor() as cursor:
                # 查询总记录数
                cursor.execute(sql_count, params)
                total = cursor.fetchone()['total']
                
                # 查询当前页数据
                cursor.execute(sql_data, params)
                results = cursor.fetchall()
                
            self.connection.commit()
            return {
                'data': results,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            print(f"分页查询失败: {e}")
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
        
    def begin_transaction(self):
        """开启事务（pymysql 默认即事务模式，只需确认连接存在）"""
        if not self.connection:
            return False
        return True

    def commit(self):
        """提交事务"""
        if not self.connection:
            return False
        self.connection.commit()
        return True

    def rollback(self):
        """回滚事务"""
        if not self.connection:
            return False
        self.connection.rollback()
        return True

    def get_last_insert_id(self):
        """获取最后插入的自增 ID"""
        if not self.connection:
            return None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT LAST_INSERT_ID() AS id")
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            print(f"获取 LAST_INSERT_ID 失败: {e}")
            return None

    def insert_tx(self, table_name, data_dict):
        """事务内插入（不自动 commit）"""
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return False
        try:
            with self.connection.cursor() as cursor:
                columns = ', '.join(data_dict.keys())
                placeholders = ', '.join(['%s'] * len(data_dict))
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, list(data_dict.values()))
            print(f"事务内插入一条记录到 {table_name}")
            return True
        except Exception as e:
            print(f"事务内插入失败: {e}")
            return False

    def update_tx(self, table_name, id_key, id_value, data_dict):
        """事务内更新（不自动 commit）"""
        if not self.connection:
            print("请先调用 open_database() 建立连接")
            return False
        try:
            with self.connection.cursor() as cursor:
                set_clause = ', '.join([f"{key} = %s" for key in data_dict.keys()])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_key} = %s"
                cursor.execute(sql, list(data_dict.values()) + [id_value])
            print(f"事务内更新 {table_name} 中 id={id_value} 的记录")
            return True
        except Exception as e:
            print(f"事务内更新失败: {e}")
            return False
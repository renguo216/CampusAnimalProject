from backend.utils.db_manager import DatabaseManager
from backend.model.animal import Animal
import json
import math

class AnimalLibrary:
    def __init__(self):
        self.db = DatabaseManager()

    # ========== 基础增删改查 ==========

    def add_animal(self, name, breed='未知', status=0, vector=None,
                   color=None, age=0, gender=0, is_neutered=0, is_vaccinated=0,
                   personality=None, description=None, photo_urls=None, found_location=None):
        """
        添加新动物档案（包含所有新增字段）
        :param name: 动物名字
        :param breed: 品种
        :param status: 状态 (0-在校, 1-已领养, 2-需医疗)
        :param vector: 特征向量 (JSON格式字符串)
        :param color: 毛色
        :param age: 年龄（单位：月）
        :param gender: 性别 (0-未知, 1-弟弟, 2-妹妹)
        :param is_neutered: 是否绝育 (0-未知, 1-是, 2-否)
        :param is_vaccinated: 是否疫苗 (0-未知, 1-是, 2-否)
        :param personality: 性格描述
        :param description: 详细描述
        :param photo_urls: 照片链接（JSON数组字符串）
        :param found_location: 发现地点
        :return: 成功返回 pet_id (int)，失败返回 False
        """
        # 校验
        if not name or len(name.strip()) == 0:
            print("错误：动物名字不能为空")
            return False
        if status not in [0, 1, 2]:
            print("错误：状态值必须是 0, 1 或 2")
            return False
        
        if not self.db.open_database():
            return False
        
        try:
            cursor = self.db.connection.cursor()
            # 构造插入语句，包含所有新字段
            sql = """
                INSERT INTO t_animal 
                (name, breed, status, vector, color, age, gender, is_neutered, is_vaccinated, personality, description, photo_urls, found_location, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(sql, (name, breed, status, vector, color, age, gender, is_neutered, is_vaccinated, personality, description, photo_urls, found_location))
            self.db.connection.commit()
            pet_id = cursor.lastrowid  # 获取自动生成的ID
            self.db.close_database()
            return pet_id
        except Exception as e:
            print(f"添加动物失败: {e}")
            self.db.close_database()
            return False

    def get_animal_by_id(self, pet_id):
        """
        根据 pet_id 精确查询动物档案
        :return: Animal 对象 或 None
        """
        if not self.db.open_database():
            return None
        data = self.db.get_by_id('t_animal', 'pet_id', pet_id)
        self.db.close_database()
        if data:
            return Animal(**data)
        return None

    def get_animal_by_name(self, name):
        """
        根据名字模糊查询动物档案
        :return: Animal 对象列表
        """
        if not self.db.open_database():
            return []
        sql = "SELECT * FROM t_animal WHERE name LIKE %s"
        results = self.db.execute_raw_sql(sql, (f'%{name}%',))
        self.db.close_database()
        return [Animal(**row) for row in results] if results else []

    def get_animals_by_status(self, status, limit=20, offset=0):
        """
        按状态筛选动物档案，支持分页
        :param status: 0-在校，1-已领养，2-需医疗
        :param limit: 每页数量
        :param offset: 偏移量
        :return: Animal 对象列表
        """
        if not self.db.open_database():
            return []
        sql = "SELECT * FROM t_animal WHERE status = %s LIMIT %s OFFSET %s"
        results = self.db.execute_raw_sql(sql, (status, limit, offset))
        self.db.close_database()
        return [Animal(**row) for row in results] if results else []
    
    def get_all_animals(self, limit=20, offset=0):
        """
        获取所有动物档案（支持分页）
        :return: Animal 对象列表
        """
        if not self.db.open_database():
            return []
        sql = "SELECT * FROM t_animal LIMIT %s OFFSET %s"
        results = self.db.execute_raw_sql(sql, (limit, offset))
        self.db.close_database()
        return [Animal(**row) for row in results] if results else []

    def update_animal(self, pet_id, update_data):
        """
        通用更新动物档案方法
        :param pet_id: 动物ID
        :param update_data: 包含要更新字段的字典 (如 {'name': '新名字', 'breed': '新品种', 'description': '新描述'})
        :return: 成功返回 True，失败返回 False
        """
        if not self.db.open_database():
            return False
        # 验证 update_data 包含的字段名是否有效（可选，如果相信调用者）
        success = self.db.update('t_animal', 'pet_id', pet_id, update_data)
        self.db.close_database()
        return success

    def update_animal_status(self, pet_id, new_status):
        """专门更新动物状态"""
        return self.update_animal(pet_id, {'status': new_status})

    def update_animal_vector(self, pet_id, vector):
        """
        更新动物特征向量（由AI模块调用）
        :param vector: JSON格式字符串
        """
        return self.update_animal(pet_id, {'vector': vector})

    def delete_animal(self, pet_id):
        """删除动物档案（慎用）"""
        if not self.db.open_database():
            return False
        success = self.db.delete('t_animal', 'pet_id', pet_id)
        self.db.close_database()
        return success

    # ========== 核心高级功能（AI 识别桥梁） ==========

    def search_similar_animals(self, query_vector, limit=5):
        """
        根据特征向量查找最相似的动物
        :param query_vector: 查询向量 (Python list 或 JSON 字符串)
        :param limit: 返回的最大数量
        :return: Animal 对象列表 (按相似度从高到低排序)
        """
        if not self.db.open_database():
            return []
        
        # 1. 获取所有有特征向量的动物
        sql = "SELECT * FROM t_animal WHERE vector IS NOT NULL"
        results = self.db.execute_raw_sql(sql)
        self.db.close_database()
        
        if not results:
            return []
            
        # 2. 处理查询向量
        if isinstance(query_vector, str):
            try:
                query_vector = json.loads(query_vector)
            except:
                return []  # 格式错误
        
        # 3. 计算相似度
        animals = []
        for row in results:
            try:
                db_vector = json.loads(row['vector'])
                similarity = self._cosine_similarity(query_vector, db_vector)
                animals.append((Animal(**row), similarity))
            except:
                continue  # 跳过格式不对的
        
        # 4. 排序并返回前 limit 个
        animals.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in animals[:limit]]

    def _cosine_similarity(self, vec1, vec2):
        """计算两个向量的余弦相似度（辅助方法）"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
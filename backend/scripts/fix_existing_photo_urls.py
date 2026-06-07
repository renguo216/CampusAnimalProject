#!/usr/bin/env python
"""修复数据库中已存在的photo_urls字段，将绝对URL改为相对路径"""
import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.db_manager import DatabaseManager

def fix_photo_urls():
    """修复t_animal表中photo_urls字段"""
    db = DatabaseManager()
    
    if not db.open_database():
        print("❌ 数据库连接失败")
        return
    
    try:
        # 查询所有动物记录
        sql = "SELECT pet_id, photo_urls FROM t_animal WHERE photo_urls IS NOT NULL"
        result = db.execute_raw_sql(sql)
        
        if not result:
            print("⚠️ 没有找到需要修复的记录")
            db.close_database()
            return
        
        print(f"🔍 找到 {len(result)} 条记录需要检查")
        
        fixed_count = 0
        
        for row in result:
            pet_id = row["pet_id"]
            photo_urls = row["photo_urls"]
            
            # 检查是否包含绝对URL
            if 'http://' in photo_urls or 'https://' in photo_urls:
                print(f"🐾 修复宠物 {pet_id} 的photo_urls...")
                
                # 使用正则表达式提取相对路径
                # 匹配 uploads/ 后面的文件名
                pattern = r'uploads/[^"\']+'
                matches = re.findall(pattern, photo_urls)
                
                if matches:
                    # 构建新的相对路径列表
                    new_urls = [f"/{match}" for match in matches]
                    new_photo_urls = json.dumps(new_urls)
                    
                    # 更新数据库
                    update_sql = "UPDATE t_animal SET photo_urls = %s WHERE pet_id = %s"
                    db.execute_raw_sql(update_sql, (new_photo_urls, pet_id))
                    fixed_count += 1
                    print(f"✅ 宠物 {pet_id} 修复完成")
                else:
                    print(f"⚠️ 宠物 {pet_id} 没有找到有效的图片URL")
        
        print(f"\n🎉 修复完成！共修复 {fixed_count} 条记录")
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close_database()

if __name__ == "__main__":
    print("=" * 60)
    print("修复数据库中photo_urls字段的绝对URL问题")
    print("=" * 60)
    fix_photo_urls()
    print("=" * 60)
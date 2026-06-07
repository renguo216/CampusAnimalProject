#!/usr/bin/env python
"""修复数据库中photo_urls字段的反引号问题"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.db_manager import DatabaseManager

def fix_photo_urls():
    """修复t_animal表中photo_urls字段的反引号问题"""
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
            
            # 检查是否包含反引号
            if '`' in photo_urls:
                print(f"🐾 修复宠物 {pet_id} 的photo_urls...")
                
                # 去除反引号
                cleaned = photo_urls.replace('`', '')
                
                try:
                    # 尝试解析JSON
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, list):
                        # 清理每个URL中的反引号和空格
                        cleaned_list = [url.strip().replace('`', '') for url in parsed]
                        cleaned = json.dumps(cleaned_list)
                except:
                    # 如果不是有效的JSON，直接去除反引号
                    pass
                
                # 更新数据库
                update_sql = "UPDATE t_animal SET photo_urls = %s WHERE pet_id = %s"
                db.execute_raw_sql(update_sql, (cleaned, pet_id))
                fixed_count += 1
                print(f"✅ 宠物 {pet_id} 修复完成")
        
        print(f"\n🎉 修复完成！共修复 {fixed_count} 条记录")
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close_database()

if __name__ == "__main__":
    print("=" * 60)
    print("修复数据库中photo_urls字段的反引号问题")
    print("=" * 60)
    fix_photo_urls()
    print("=" * 60)
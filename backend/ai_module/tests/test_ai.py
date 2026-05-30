"""
测试AI服务
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_service import AnimalAIService, AnimalDatabase

def test_ai():
    print("="*60)
    print("AI模块测试")
    print("="*60)
    
    # 初始化
    ai = AnimalAIService()
    db = AnimalDatabase()
    
    print(f"\n✅ AI服务初始化成功")
    print(f"📊 数据库已有 {len(db.features)} 个动物档案")
    
    # 检查是否有测试图片
    test_images = ['test.jpg', '../test.jpg', 'test_cat.jpg']
    found_img = None
    for img in test_images:
        if os.path.exists(img):
            found_img = img
            break
    
    if found_img:
        print(f"\n🔍 测试图片: {found_img}")
        result = ai.detect_species(found_img)
        print(f"   - 种类: {result['species']}")
        print(f"   - 置信度: {result['confidence']:.2%}")
    else:
        print("\n💡 提示: 可将测试图片命名为 test.jpg 放在当前目录")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_ai()

"""
AI服务模块 - 校园流浪动物智慧互助平台
支持：猫狗检测 + 品种识别
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
import numpy as np
import json
from typing import Dict, List, Optional

class AnimalAIService:
    def __init__(self):
        self.model = None
        self._load_models()
        
    def _load_models(self):
        print("="*50)
        print("正在加载模型...")
        self.model = ResNet50(weights='imagenet')
        print("✅ ResNet50模型加载成功")
        print("="*50)
    
    def detect_species(self, img_path: str) -> Dict:
        """
        检测动物种类和品种
        返回: {
            'success': True,
            'category': 'cat',  # 大类: cat/dog/other
            'breed': 'tabby',   # 具体品种
            'breed_name': '虎斑猫',  # 中文名称
            'confidence': 0.6079
        }
        """
        # 加载和预处理图片
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # 预测
        preds = self.model.predict(x, verbose=0)
        results = decode_predictions(preds, top=10)[0]
        
        # 猫的品种关键词
        cat_breeds = {
            'tabby': '虎斑猫',
            'tiger_cat': '虎猫',
            'egyptian_cat': '埃及猫',
            'persian_cat': '波斯猫',
            'siamese_cat': '暹罗猫',
            'lynx': '猞猁',
            'leopard': '豹猫',
            'cheetah': '猎豹',
            'jaguar': '美洲豹',
            'cougar': '美洲狮',
            'tiger': '老虎',
            'lion': '狮子'
        }
        
        # 狗的品种关键词
        dog_breeds = {
            'golden_retriever': '金毛寻回犬',
            'labrador_retriever': '拉布拉多',
            'german_shepherd': '德国牧羊犬',
            'husky': '哈士奇',
            'poodle': '贵宾犬',
            'bulldog': '斗牛犬',
            'beagle': '比格犬',
            'chihuahua': '吉娃娃',
            'doberman': '杜宾犬',
            'rottweiler': '罗威纳',
            'boxer': '拳师犬',
            'great_dane': '大丹犬',
            'saint_bernard': '圣伯纳犬',
            'border_collie': '边境牧羊犬',
            'collie': '柯利犬',
            'appenzell': '阿彭策尔山地犬',
            'english_springer': '英国史宾格犬',
            'bernese_mountain_dog': '伯恩山犬',
        }
        
        # 遍历预测结果，查找猫狗
        cat_score = 0
        dog_score = 0
        best_cat_breed = None
        best_dog_breed = None
        best_cat_breed_name = None
        best_dog_breed_name = None
        best_cat_score = 0
        best_dog_score = 0
        
        for _, label, score in results:
            label_lower = label.lower()
            
            # 检查猫
            for breed, ch_name in cat_breeds.items():
                if breed in label_lower or (breed.replace('_', ' ') in label_lower):
                    if score > best_cat_score:
                        best_cat_score = score
                        best_cat_breed = breed
                        best_cat_breed_name = ch_name
                    cat_score = max(cat_score, score)
                    break
            
            # 检查狗
            for breed, ch_name in dog_breeds.items():
                if breed in label_lower or (breed.replace('_', ' ') in label_lower):
                    if score > best_dog_score:
                        best_dog_score = score
                        best_dog_breed = breed
                        best_dog_breed_name = ch_name
                    dog_score = max(dog_score, score)
                    break
        
        # 判断结果
        if cat_score > dog_score and cat_score > 0.1:
            return {
                'success': True,
                'category': 'cat',
                'category_name': '猫',
                'breed': best_cat_breed or 'unknown_cat',
                'breed_name': best_cat_breed_name or '未知品种的猫',
                'confidence': float(cat_score),
                'top_predictions': [
                    {'label': label, 'score': float(score)} 
                    for _, label, score in results[:5]
                ]
            }
        elif dog_score > 0.1:
            return {
                'success': True,
                'category': 'dog',
                'category_name': '狗',
                'breed': best_dog_breed or 'unknown_dog',
                'breed_name': best_dog_breed_name or '未知品种的狗',
                'confidence': float(dog_score),
                'top_predictions': [
                    {'label': label, 'score': float(score)} 
                    for _, label, score in results[:5]
                ]
            }
        else:
            # 不是猫狗，返回最可能的识别结果
            best_label = results[0][1]
            best_score = results[0][2]
            return {
                'success': True,
                'category': 'other',
                'category_name': '其他',
                'breed': best_label,
                'breed_name': best_label,
                'confidence': float(best_score),
                'top_predictions': [
                    {'label': label, 'score': float(score)} 
                    for _, label, score in results[:5]
                ]
            }
    
    def extract_features(self, img_path: str) -> np.ndarray:
        """提取特征向量"""
        from tensorflow.keras.models import Model
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        layer_name = 'avg_pool'
        intermediate = Model(inputs=self.model.input, outputs=self.model.get_layer(layer_name).output)
        features = intermediate.predict(x, verbose=0)
        return features[0]
    
    def identify_animal(self, img_path: str, feature_db: List = None) -> Dict:
        """识别动物个体"""
        query_features = self.extract_features(img_path)
        
        if not feature_db or len(feature_db) == 0:
            return {
                'success': True,
                'animal_id': None,
                'is_new': True,
                'message': '首次识别'
            }
        
        similarities = []
        for feat in feature_db:
            sim = np.dot(query_features, feat) / (np.linalg.norm(query_features) * np.linalg.norm(feat) + 1e-8)
            similarities.append(sim)
        
        best_idx = np.argmax(similarities)
        best_sim = similarities[best_idx]
        
        if best_sim > 0.75:
            return {
                'success': True,
                'animal_id': f"ANIMAL_{best_idx+1:04d}",
                'confidence': float(best_sim),
                'is_new': False
            }
        else:
            return {
                'success': True,
                'animal_id': None,
                'is_new': True,
                'message': '未匹配'
            }


class AnimalDatabase:
    def __init__(self, db_path: str = "data/feature_db/feature_db.json"):
        self.db_path = db_path
        self.features = []
        self.metadata = []
        self._load()
    
    def _load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.features = [np.array(feat) for feat in data.get('features', [])]
                self.metadata = data.get('metadata', [])
            print(f"✅ 加载数据库成功，共 {len(self.features)} 个动物")
    
    def save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump({'features': [feat.tolist() for feat in self.features], 'metadata': self.metadata}, f)
    
    def add_animal(self, features: np.ndarray, info: Dict) -> str:
        animal_id = f"ANIMAL_{len(self.features)+1:04d}"
        info['animal_id'] = animal_id
        self.features.append(features)
        self.metadata.append(info)
        self.save()
        return animal_id
    
    def get_all_features(self) -> List:
        return self.features


if __name__ == "__main__":
    ai = AnimalAIService()
    result = ai.detect_species(r'D:\jupyter.jpg')
    print(f"识别结果: {result}")

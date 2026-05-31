#python -m backend.ai_module.flask_api
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_service import AnimalAIService, AnimalDatabase

app = Flask(__name__)
CORS(app)

print("正在加载AI模型...")
ai = AnimalAIService()
db = AnimalDatabase()
print("AI模型加载完成")

@app.route('/')
def root():
    return jsonify({"status": "ok", "service": "AI Service"})

@app.route('/detect-species', methods=['POST'])
def detect_species():
    """识别动物种类和品种"""
    file = request.files['file']
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    result = ai.detect_species(tmp_path)
    os.unlink(tmp_path)
    return jsonify(result)

@app.route('/identify', methods=['POST'])
def identify():
    """识别动物个体"""
    file = request.files['file']
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    result = ai.identify_animal(tmp_path, db.get_all_features())
    os.unlink(tmp_path)
    return jsonify(result)

@app.route('/add-animal', methods=['POST'])
def add_animal():
    """添加新动物到数据库"""
    file = request.files['file']
    species = request.form.get('species', 'unknown')
    location = request.form.get('location', 'unknown')
    breed = request.form.get('breed', 'unknown')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    features = ai.extract_features(tmp_path)
    animal_info = {
        'species': species,
        'breed': breed,
        'location': location,
        'first_seen': str(__import__('datetime').datetime.now())
    }
    animal_id = db.add_animal(features, animal_info)
    os.unlink(tmp_path)
    return jsonify({"success": True, "animal_id": animal_id})

@app.route('/extract-features', methods=['POST'])
def extract_features():
    """提取图片特征向量（供主项目Library调用）"""
    file = request.files['file']
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        features = ai.extract_features(tmp_path)
        return jsonify({
            "success": True,
            "features": features.tolist(),  # 将numpy数组转为列表
            "dimension": len(features)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        os.unlink(tmp_path)

@app.route('/animals', methods=['GET'])
def list_animals():
    """列出所有动物"""
    return jsonify({
        "success": True,
        "count": len(db.features),
        "animals": db.metadata
    })

@app.route('/stats', methods=['GET'])
def stats():
    """服务统计"""
    return jsonify({
        "total_animals": len(db.features),
        "model_loaded": ai.model is not None
    })

if __name__ == '__main__':
    print("="*50)
    print("启动AI服务...")
    print("服务地址: http://localhost:8001")
    print("接口列表:")
    print("  POST /detect-species  - 识别种类和品种")
    print("  POST /identify        - 识别个体")
    print("  POST /add-animal      - 添加动物")
    print("  POST /extract-features - 提取图片特征向量")
    print("  GET  /animals         - 动物列表")
    print("  GET  /stats           - 服务统计")
    print("="*50)
    app.run(host='0.0.0.0', port=8001, debug=False)
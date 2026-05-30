"""
AI API服务 - 供后端调用
FastAPI 版本
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_service import AnimalAIService, AnimalDatabase

app = FastAPI(
    title="校园流浪动物智慧互助平台 - AI服务",
    description="提供动物识别、特征提取等功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化AI服务
ai = AnimalAIService()
db = AnimalDatabase()

@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "AI Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/identify")
async def identify_animal(file: UploadFile = File(...)):
    """识别动物个体"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        result = ai.identify_animal(tmp_path, db.get_all_features())
        os.unlink(tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect-species")
async def detect_species(file: UploadFile = File(...)):
    """检测动物种类"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        result = ai.detect_species(tmp_path)
        os.unlink(tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-features")
async def extract_features(file: UploadFile = File(...)):
    """提取特征向量"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        features = ai.extract_features(tmp_path)
        os.unlink(tmp_path)
        return {
            "success": True,
            "feature_dim": len(features),
            "features": features.tolist()[:10]  # 只返回前10个值
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-animal")
async def add_animal(
    file: UploadFile = File(...),
    species: str = "unknown",
    location: str = "unknown"
):
    """添加新动物到数据库"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        features = ai.extract_features(tmp_path)
        animal_id = db.add_animal(features, {
            'species': species,
            'location': location
        })
        os.unlink(tmp_path)
        return {"success": True, "animal_id": animal_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/animals")
async def list_animals():
    """列出所有动物"""
    return {
        "success": True,
        "count": len(db.features),
        "animals": db.metadata
    }

@app.get("/stats")
async def get_stats():
    """获取服务统计信息"""
    return {
        "success": True,
        "stats": {
            "total_animals": len(db.features),
            "model_loaded": ai.identity_model is not None,
            "feature_dim": 2048
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("启动AI服务...")
    print("API文档: http://localhost:8001/docs")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8001)

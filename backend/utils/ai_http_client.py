"""
AI HTTP客户端
封装对 backend/ai_module/ 微服务的所有HTTP调用
所有函数返回字典：{"success": True/False, ...}
Library层只通过本模块与AI模块通信，不直接import任何AI框架
"""
import requests
import logging

logger = logging.getLogger(__name__)

AI_BASE_URL = "http://localhost:8001"
TIMEOUT = 5  # seconds

def detect_species(image_bytes: bytes) -> dict:
    """调用AI识别动物种类和品种"""
    try:
        resp = requests.post(
            f"{AI_BASE_URL}/detect-species",
            files={"file": image_bytes},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"AI detect_species failed: {e}")
        return {"success": False, "error": str(e)}

def extract_features(image_bytes: bytes) -> dict:
    """调用AI提取特征向量"""
    try:
        resp = requests.post(
            f"{AI_BASE_URL}/extract-features",
            files={"file": image_bytes},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"AI extract_features failed: {e}")
        return {"success": False, "error": str(e)}

def identify_animal(image_bytes: bytes) -> dict:
    """调用AI识别动物个体"""
    try:
        resp = requests.post(
            f"{AI_BASE_URL}/identify",
            files={"file": image_bytes},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"AI identify_animal failed: {e}")
        return {"success": False, "error": str(e)}

def add_animal_to_ai_db(image_bytes: bytes, species="unknown", location="unknown", breed="unknown") -> dict:
    """调用AI侧添加动物到其本地数据库（主项目不常用，保留接口）"""
    try:
        resp = requests.post(
            f"{AI_BASE_URL}/add-animal",
            files={"file": image_bytes},
            data={"species": species, "location": location, "breed": breed},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"AI add_animal failed: {e}")
        return {"success": False, "error": str(e)}
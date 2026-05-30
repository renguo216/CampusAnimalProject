"""
数据库与应用配置

集中管理数据库连接参数、JWT 密钥、文件上传路径等。
支持通过环境变量覆盖默认值。
"""
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """数据库连接配置"""
    HOST = os.getenv("DB_HOST", "localhost")
    USER = os.getenv("DB_USER", "root")
    PASSWORD = os.getenv("DB_PASSWORD", "")
    NAME = os.getenv("DB_NAME", "campus_animal")


class AppConfig:
    """应用通用配置"""
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24


class UploadConfig:
    """文件上传配置"""
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "mp4"}
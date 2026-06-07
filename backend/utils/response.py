# backend/utils/response.py
"""
全局统一响应格式
所有 library 公共方法必须返回此格式
"""

from typing import Optional, Any, Dict


def success_response(message: str = "成功", data: Any = None) -> dict:
    """成功响应"""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message: str, data: Any = None) -> dict:
    """失败响应"""
    return {
        "success": False,
        "message": message,
        "data": data
    }
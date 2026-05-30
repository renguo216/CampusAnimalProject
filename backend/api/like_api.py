"""
点赞独立 API 路由（可选）

职责：如需查看点赞历史等独立点赞功能，调用 LikeLibrary
调用关系：LikeAPI -> LikeLibrary -> DatabaseManager

路由前缀：/api/likes
标签：点赞
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/likes", tags=["点赞"])
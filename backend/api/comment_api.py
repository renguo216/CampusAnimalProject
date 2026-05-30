"""
评论独立 API 路由（可选）

职责：如需独立管理评论（如管理员后台删除任意评论），调用 CommentLibrary
调用关系：CommentAPI -> CommentLibrary -> DatabaseManager

路由前缀：/api/comments
标签：评论
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/comments", tags=["评论"])
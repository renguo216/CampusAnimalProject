"""
关注 API 路由

职责：关注/取关用户、关注列表、粉丝列表等 HTTP 请求，调用 FollowLibrary
调用关系：FollowAPI -> FollowLibrary -> DatabaseManager

路由前缀：/api/follows
标签：关注
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/follows", tags=["关注"])
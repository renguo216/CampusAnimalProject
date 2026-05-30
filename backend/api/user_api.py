"""
用户 API 路由

职责：接收用户相关 HTTP 请求，参数校验后调用 UserLibrary
调用关系：UserAPI -> UserLibrary -> DatabaseManager

路由前缀：/api/users
标签：用户
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/users", tags=["用户"])
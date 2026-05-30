"""
公告 API 路由

职责：公告 CRUD 相关 HTTP 请求，参数校验后调用 NoticeLibrary
调用关系：NoticeAPI -> NoticeLibrary -> DatabaseManager

路由前缀：/api/notices
标签：公告
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/notices", tags=["公告"])
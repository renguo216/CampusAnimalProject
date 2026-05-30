"""
救助记录 API 路由

职责：救助记录 CRUD 相关 HTTP 请求，参数校验后调用 RescueRecordLibrary
调用关系：RescueRecordAPI -> RescueRecordLibrary -> DatabaseManager

路由前缀：/api/rescue-records
标签：救助记录
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/rescue-records", tags=["救助记录"])
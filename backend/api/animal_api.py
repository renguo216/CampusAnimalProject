"""
动物 API 路由

职责：动物信息 CRUD 相关 HTTP 请求，参数校验后调用 AnimalLibrary
调用关系：AnimalAPI -> AnimalLibrary -> DatabaseManager

路由前缀：/api/animals
标签：动物
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/animals", tags=["动物"])
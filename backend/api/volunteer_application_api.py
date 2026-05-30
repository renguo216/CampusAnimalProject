"""
志愿者申请 API 路由

职责：志愿者申请提交、审核等 HTTP 请求，参数校验后调用 VolunteerApplicationLibrary
调用关系：VolunteerApplicationAPI -> VolunteerApplicationLibrary -> DatabaseManager

路由前缀：/api/volunteer-applications
标签：志愿者申请
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/volunteer-applications", tags=["志愿者申请"])
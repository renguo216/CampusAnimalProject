"""
领养申请 API 路由

职责：领养申请提交、审核等 HTTP 请求，参数校验后调用 AdoptionApplyLibrary
调用关系：AdoptionApplyAPI -> AdoptionApplyLibrary -> DatabaseManager

路由前缀：/api/adoption-applies
标签：领养申请
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/adoption-applies", tags=["领养申请"])
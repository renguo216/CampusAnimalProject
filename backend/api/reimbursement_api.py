"""
报销 API 路由

职责：报销申请提交、审核等 HTTP 请求，参数校验后调用 ReimbursementLibrary
调用关系：ReimbursementAPI -> ReimbursementLibrary -> DatabaseManager

路由前缀：/api/reimbursements
标签：报销
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/reimbursements", tags=["报销"])
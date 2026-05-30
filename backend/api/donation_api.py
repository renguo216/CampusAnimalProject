"""
捐赠 API 路由

职责：捐赠记录提交、查询等 HTTP 请求，参数校验后调用 DonationLibrary
调用关系：DonationAPI -> DonationLibrary -> DatabaseManager

路由前缀：/api/donations
标签：捐赠
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/donations", tags=["捐赠"])
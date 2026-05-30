"""
捐赠项目 API 路由

职责：捐赠项目 CRUD 相关 HTTP 请求，参数校验后调用 DonationProjectLibrary
调用关系：DonationProjectAPI -> DonationProjectLibrary -> DatabaseManager

路由前缀：/api/donation-projects
标签：捐赠项目
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/donation-projects", tags=["捐赠项目"])
"""
兑换商品 API 路由

职责：兑换商品 CRUD 相关 HTTP 请求，参数校验后调用 ExchangeProductLibrary
调用关系：ExchangeProductAPI -> ExchangeProductLibrary -> DatabaseManager

路由前缀：/api/exchange-products
标签：兑换商品
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/exchange-products", tags=["兑换商品"])
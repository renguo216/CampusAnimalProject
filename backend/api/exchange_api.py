"""
积分兑换 API 路由

职责：兑换记录查询、发起兑换等 HTTP 请求，参数校验后调用 ExchangeLibrary
调用关系：ExchangeAPI -> ExchangeLibrary -> DatabaseManager

路由前缀：/api/exchanges
标签：积分兑换
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/exchanges", tags=["积分兑换"])
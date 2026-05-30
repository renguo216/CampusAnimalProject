"""
用户认证依赖

职责：解析 JWT token，返回当前用户 ID。
提供 get_current_user_id 依赖，可在路由中通过 Depends 注入。
"""

from fastapi import Header, HTTPException, Depends
from typing import Optional


async def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    获取当前登录用户 ID

    从 Authorization 请求头解析用户身份。
    开发阶段可降级为从参数获取，便于测试。

    :return: 用户 ID 字符串
    :raises HTTPException: 未提供认证信息时返回 401
    """
    # TODO: 实现 JWT 解析逻辑
    # 临时方案：直接返回测试用户 ID（开发阶段使用）
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")

    # 从 token 中解析 user_id
    # user_id = decode_jwt(authorization)
    user_id = authorization  # 临时：将 Authorization 值当作 user_id

    return user_id


async def get_optional_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    获取当前用户 ID（可选）

    某些接口未登录也可访问（如查看帖子列表），
    此时如有登录信息则获取用户 ID，没有则返回 None。

    :return: 用户 ID 或 None
    """
    if not authorization:
        return None
    # user_id = decode_jwt(authorization)
    user_id = authorization  # 临时方案
    return user_id


async def require_admin(
    user_id: str = Depends(get_current_user_id)
) -> str:
    """
    要求当前用户为管理员

    在需要管理员权限的路由上通过 Depends 注入。
    """
    # TODO: 检查用户角色是否为管理员（role == 3）
    # from backend.libs.user_library import UserLibrary
    # lib = UserLibrary()
    # user = lib.get_user_by_account(user_id)
    # if not user or user.role != 3:
    #     raise HTTPException(status_code=403, detail="权限不足")
    return user_id


async def require_volunteer(
    user_id: str = Depends(get_current_user_id)
) -> str:
    """
    要求当前用户为志愿者或管理员

    在需要志愿者权限的路由上通过 Depends 注入。
    """
    # TODO: 检查用户角色是否为志愿者或管理员
    return user_id
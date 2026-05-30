"""
帖子 API 路由

职责：接收帖子相关 HTTP 请求，参数校验后调用 PostLibrary
调用关系：PostAPI -> PostLibrary -> DatabaseManager
禁止直接操作数据库或编写业务逻辑
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from typing import Optional

from backend.libs.post_library import PostLibrary
from backend.schemas.common import CommonResponse
from backend.schemas.post import (
    CreatePostRequest,
    AddCommentRequest,
    PostDetailResponse,
    PostListItem,
    ToggleLikeResponse,
    CommentResponse,
)
from backend.dependencies.auth import get_current_user_id, get_optional_user_id

router = APIRouter(prefix="/api", tags=["帖子"])

# ==================== 帖子增删查 ====================

@router.post(
    "/posts",
    response_model=CommonResponse,
    summary="发布帖子",
    description="当前用户发布一条新帖子，支持文字和图片。图片通过 image_urls 传入 JSON 数组字符串。",
)
async def create_post(
    req: CreatePostRequest,
    user_id: str = Depends(get_current_user_id),
):
    """发布帖子"""
    try:
        post_lib = PostLibrary()
        result = post_lib.create_post(
            user_id=user_id,
            content=req.content,
            image_urls=req.image_urls,
        )
        return result
    except Exception as e:
        return {"success": False, "message": f"服务器异常：{str(e)}", "data": None}


@router.get(
    "/posts",
    response_model=CommonResponse,
    summary="获取全部帖子（分页）",
    description="获取所有已审核通过的帖子，按发布时间倒序排列。可选分页参数。",
)
async def get_all_posts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    # current_user_id: Optional[str] = Depends(get_optional_user_id)  # 当前未在 get_all_posts 中使用
):
    """获取全部帖子"""
    try:
        post_lib = PostLibrary()
        result = post_lib.get_all_posts(page=page, page_size=page_size)
        return result
    except Exception as e:
        return {"success": False, "message": f"服务器异常：{str(e)}", "data": None}


@router.get(
    "/posts/{post_id}",
    response_model=CommonResponse,
    summary="获取帖子详情（含评论）",
    description="根据帖子 ID 获取完整详情，包括发帖人信息、所有评论、当前用户是否已点赞。",
)
async def get_post_detail(
    post_id: str = Path(..., description="帖子 ID"),
    current_user_id: Optional[str] = Depends(get_optional_user_id),
):
    """获取帖子详情"""
    try:
        post_lib = PostLibrary()
        result = post_lib.get_post_detail_with_comments(
            post_id=post_id,
            current_user_id=current_user_id,
        )
        return result
    except Exception as e:
        return {"success": False, "message": f"服务器异常：{str(e)}", "data": None}


@router.delete(
    "/posts/{post_id}",
    response_model=CommonResponse,
    summary="删除帖子",
    description="删除指定帖子，仅允许帖子作者本人删除。",
)
async def delete_post(
    post_id: str = Path(..., description="帖子 ID"),
    user_id: str = Depends(get_current_user_id),
):
    """删除帖子"""
    try:
        post_lib = PostLibrary()
        result = post_lib.delete_post(post_id=post_id, user_id=user_id)
        return result
    except Exception as e:
        return {"success": False, "message": f"服务器异常：{str(e)}", "data": None}

# ==================== 点赞 ====================

@router.post(
    "/posts/{post_id}/like",
    response_model=CommonResponse,
    summary="点赞/取消点赞帖子",
    description="切换当前用户对指定帖子的点赞状态（已赞则取消，未赞则点赞）。",
)
async def toggle_like_post(
    post_id: str = Path(..., description="帖子 ID"),
    user_id: str = Depends(get_current_user_id),
):
    """点赞或取消点赞"""
    try:
        post_lib = PostLibrary()
        result = post_lib.toggle_like_post(post_id=post_id, user_id=user_id)
        return result
    except Exception as e:
        return {"success": False, "message": f"服务器异常：{str(e)}", "data": None}

# ==================== 评论 ====================

@router.post(
    "/posts/{post_id}/comment",
    response_model=CommonResponse,
    summary="添加评论",
    description="对指定帖子添加一条评论。",
)
async def add_comment(
    post_id: str = Path(..., description="帖子 ID"),
    req: AddCommentRequest = ...,
    user_id: str = Depends(get_current_user_id),
):
    """添加评论"""
    try:
        post_lib = PostLibrary()
        result = post_lib.add_comment(
            post_id=post_id,
            user_id=user_id,
            content=req.content,
        )
        return result
    except Exception as e:
        return {"success": False, "message": f"服务器异常：{str(e)}", "data": None}

# ==================== 用户帖子列表 ====================

@router.get(
    "/users/{user_id}/posts",
    response_model=CommonResponse,
    summary="获取指定用户的帖子列表",
    description="查询某用户发布的所有已审核帖子，按时间倒序分页返回。",
)
async def get_user_posts(
    user_id: str = Path(..., description="用户 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    # current_user_id: Optional[str] = Depends(get_optional_user_id)  # 暂未使用
):
    """获取用户发布的帖子"""
    try:
        post_lib = PostLibrary()
        result = post_lib.get_posts_by_user(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        return result
    except Exception as e:
        return {"success": False, "message": f"服务器异常：{str(e)}", "data": None}
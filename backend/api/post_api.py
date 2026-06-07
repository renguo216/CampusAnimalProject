from flask import Blueprint, request, jsonify, g

from backend.libs.post_library import PostLibrary
from backend.dependencies.auth import login_required, get_optional_user_id

router = Blueprint('post', __name__)


@router.route('/posts', methods=['POST'])
@login_required
def create_post():
    user_id = g.current_user_id
    req = request.get_json()
    try:
        post_lib = PostLibrary()
        result = post_lib.create_post(
            user_id=user_id,
            content=req.get('content'),
            image_urls=req.get('image_urls'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/posts', methods=['GET'])
def get_all_posts():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        post_lib = PostLibrary()
        result = post_lib.get_all_posts(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/posts/<post_id>', methods=['GET'])
def get_post_detail(post_id):
    current_user_id = get_optional_user_id()
    try:
        post_lib = PostLibrary()
        result = post_lib.get_post_detail_with_comments(
            post_id=post_id,
            current_user_id=current_user_id,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/posts/<post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    user_id = g.current_user_id
    try:
        post_lib = PostLibrary()
        result = post_lib.delete_post(post_id=post_id, user_id=user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/posts/<post_id>/like', methods=['POST'])
@login_required
def toggle_like_post(post_id):
    user_id = g.current_user_id
    try:
        post_lib = PostLibrary()
        result = post_lib.toggle_like_post(post_id=post_id, user_id=user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/posts/<post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    user_id = g.current_user_id
    req = request.get_json()
    try:
        post_lib = PostLibrary()
        result = post_lib.add_comment(
            post_id=post_id,
            user_id=user_id,
            content=req.get('content'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/users/<user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        post_lib = PostLibrary()
        result = post_lib.get_posts_by_user(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

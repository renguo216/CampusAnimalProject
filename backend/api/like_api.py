from flask import Blueprint, request, jsonify, g

from backend.libs.like_library import LikeLibrary
from backend.dependencies.auth import login_required

router = Blueprint('like', __name__)


@router.route('/posts/<post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    user_id = g.current_user_id
    try:
        like_lib = LikeLibrary()
        result = like_lib.toggle_like_post(post_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/posts/<post_id>', methods=['DELETE'])
@login_required
def unlike_post(post_id):
    user_id = g.current_user_id
    try:
        like_lib = LikeLibrary()
        result = like_lib.toggle_like_post(post_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/user/<user_id>', methods=['GET'])
def get_user_likes(user_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        like_lib = LikeLibrary()
        result = like_lib.get_user_liked_list(user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

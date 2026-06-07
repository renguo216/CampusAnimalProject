from flask import Blueprint, request, jsonify, g

from backend.libs.follow_library import FollowLibrary
from backend.dependencies.auth import login_required

router = Blueprint('follow', __name__)


@router.route('/follow/<followed_id>', methods=['POST'])
@login_required
def follow_user(followed_id):
    user_id = g.current_user_id
    try:
        follow_lib = FollowLibrary()
        result = follow_lib.follow_user(user_id, followed_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<followed_id>', methods=['DELETE'])
@login_required
def unfollow_user(followed_id):
    user_id = g.current_user_id
    try:
        follow_lib = FollowLibrary()
        result = follow_lib.unfollow_user(user_id, followed_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/followers/<user_id>', methods=['GET'])
def get_followers(user_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        follow_lib = FollowLibrary()
        result = follow_lib.get_followers(user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/following/<user_id>', methods=['GET'])
def get_following(user_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        follow_lib = FollowLibrary()
        result = follow_lib.get_following(user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

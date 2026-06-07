from flask import Blueprint, request, jsonify, g

from backend.libs.comment_library import CommentLibrary
from backend.dependencies.auth import login_required

router = Blueprint('comment', __name__)


@router.route('', methods=['GET'])
def list_comments():
    post_id = request.args.get('post_id')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        comment_lib = CommentLibrary()
        result = comment_lib.get_comments_by_post(post_id=post_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    user_id = g.current_user_id
    try:
        comment_lib = CommentLibrary()
        result = comment_lib.delete_comment(comment_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

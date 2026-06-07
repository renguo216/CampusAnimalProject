from flask import Blueprint, request, jsonify

from backend.libs.notice_library import NoticeLibrary
from backend.dependencies.auth import login_required

router = Blueprint('notice', __name__)


@router.route('', methods=['GET'])
def list_notices():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        notice_lib = NoticeLibrary()
        result = notice_lib.get_all_notices(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<notice_id>', methods=['GET'])
def get_notice(notice_id):
    try:
        notice_lib = NoticeLibrary()
        result = notice_lib.get_notice_by_id(notice_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('', methods=['POST'])
@login_required
def create_notice():
    req = request.get_json()
    try:
        notice_lib = NoticeLibrary()
        result = notice_lib.create_notice(
            title=req.get('title'),
            content=req.get('content'),
            is_top=req.get('is_top', 0),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

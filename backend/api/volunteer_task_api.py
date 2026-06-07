from flask import Blueprint, request, jsonify, g

from backend.libs.volunteer_application_library import VolunteerApplicationLibrary
from backend.libs.rescue_record_library import RescueRecordLibrary
from backend.dependencies.auth import login_required

router = Blueprint('volunteer_task', __name__)


@router.route('/tasks', methods=['GET'])
@login_required
def list_volunteer_tasks():
    """获取可认领的志愿者任务（救助记录）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.get_all_rescues(page=page, page_size=page_size)
        filtered_result = {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": {
                "total": result.get("data", {}).get("total", 0),
                "page": page,
                "page_size": page_size,
                "records": [
                    r for r in result.get("data", {}).get("records", [])
                    if r.get("status") == 0
                ]
            }
        }
        return jsonify(filtered_result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/tasks/<task_id>/claim', methods=['POST'])
@login_required
def claim_volunteer_task(task_id):
    """认领志愿者任务"""
    user_id = g.current_user_id

    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.assign_helper(task_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/tasks/<task_id>/complete', methods=['POST'])
@login_required
def complete_volunteer_task(task_id):
    """完成任务"""
    user_id = g.current_user_id
    req = request.get_json()

    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.complete_rescue(
            record_id=task_id,
            helper_id=user_id,
            outcome=req.get('outcome'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my-tasks', methods=['GET'])
@login_required
def get_my_volunteer_tasks():
    """获取我认领的任务"""
    user_id = g.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.get_helper_rescues(helper_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/tasks/<task_id>/progress', methods=['PUT'])
@login_required
def update_task_progress(task_id):
    """更新任务进度"""
    user_id = g.current_user_id
    req = request.get_json()

    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.update_rescue_record(
            record_id=task_id,
            user_id=user_id,
            progress=req.get('progress'),
            description=req.get('description'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})
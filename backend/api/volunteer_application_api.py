from flask import Blueprint, request, jsonify, g

from backend.libs.volunteer_application_library import VolunteerApplicationLibrary
from backend.dependencies.auth import login_required

router = Blueprint('volunteer_application', __name__)


@router.route('/apply', methods=['POST'])
@login_required
def submit_application():
    user_id = g.current_user_id
    req = request.get_json()
    print(f"志愿者申请请求: user_id={user_id}, req={req}")
    try:
        volunteer_lib = VolunteerApplicationLibrary()
        apply_content = req.get('apply_content')
        print(f"接收到的申请理由: {apply_content}")
        result = volunteer_lib.submit_volunteer_application(
            user_id=user_id,
            apply_content=apply_content,
        )
        print(f"提交结果: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"志愿者申请异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<application_id>', methods=['GET'])
def get_application(application_id):
    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.get_application_by_id(application_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/user/<user_id>', methods=['GET'])
def get_user_applications(user_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.get_user_applications(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<application_id>/approve', methods=['POST'])
@login_required
def approve_application(application_id):
    req = request.get_json()
    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.approve_application(
            application_id=int(application_id),
            admin_id=g.current_user_id,
            review_comment=req.get('review_comment'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<application_id>/reject', methods=['POST'])
@login_required
def reject_application(application_id):
    req = request.get_json()
    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.reject_application(
            application_id=int(application_id),
            admin_id=g.current_user_id,
            reason=req.get('reason'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

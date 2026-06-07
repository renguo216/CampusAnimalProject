from flask import Blueprint, request, jsonify

from backend.libs.donation_project_library import DonationProjectLibrary
from backend.dependencies.auth import login_required

router = Blueprint('donation_project', __name__)


@router.route('/projects', methods=['GET'])
def list_projects():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        project_lib = DonationProjectLibrary()
        result = project_lib.get_all_projects(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    try:
        project_lib = DonationProjectLibrary()
        result = project_lib.get_project_by_id(project_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('', methods=['POST'])
@login_required
def create_project():
    req = request.get_json()
    try:
        project_lib = DonationProjectLibrary()
        result = project_lib.create_project(
            title=req.get('title'),
            description=req.get('description'),
            target_amount=req.get('target_amount'),
            deadline=req.get('deadline'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

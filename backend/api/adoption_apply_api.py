from flask import Blueprint, request, jsonify, g

from backend.libs.adoption_apply_library import AdoptionApplyLibrary
from backend.dependencies.auth import login_required

router = Blueprint('adoption_apply', __name__)


@router.route('/apply', methods=['POST'])
@login_required
def submit_application():
    user_id = g.current_user_id
    req = request.get_json()
    try:
        adoption_lib = AdoptionApplyLibrary()
        result = adoption_lib.submit_adoption_application(
            user_id=user_id,
            pet_id=req.get('pet_id'),
            content=req.get('content'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<apply_id>', methods=['GET'])
def get_application(apply_id):
    try:
        adoption_lib = AdoptionApplyLibrary()
        result = adoption_lib.get_application_by_id(apply_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/animal/<pet_id>', methods=['GET'])
def get_animal_applications(pet_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        adoption_lib = AdoptionApplyLibrary()
        result = adoption_lib.get_animal_applications(pet_id=pet_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my-records', methods=['GET'])
def get_my_adoption_records():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "缺少user_id", "data": None})
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        adoption_lib = AdoptionApplyLibrary()
        result = adoption_lib.get_user_applications(user_id=user_id, page=page, page_size=page_size)
        # 转换数据格式
        data_list = []
        if result.get('success') and result.get('data') and result.get('data').get('applications'):
            data_list = result.get('data').get('applications')
        return jsonify({"success": True, "message": "成功", "data": data_list})
    except Exception as e:
        print(f'获取我的领养记录异常: {str(e)}')
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<apply_id>/approve', methods=['POST'])
def approve_application(apply_id):
    req = request.get_json()
    try:
        adoption_lib = AdoptionApplyLibrary()
        result = adoption_lib.approve_application(
            apply_id=apply_id,
            reviewer_id='admin',
            review_comment=req.get('review_comment'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<apply_id>', methods=['PUT'])
def update_application(apply_id):
    """编辑领养申请"""
    req = request.get_json()
    try:
        from backend.utils.db_manager import DatabaseManager
        from datetime import datetime
        
        db = DatabaseManager()
        if not db.open_database():
            return jsonify({"success": False, "message": "数据库连接失败", "data": None})
        
        status = req.get('status')
        review_comment = req.get('review_comment', '')
        
        if status not in [0, 1, 2]:
            db.close_database()
            return jsonify({"success": False, "message": "状态值无效", "data": None})
        
        update_data = {
            "status": status,
            "review_comment": review_comment
        }
        
        success = db.update("t_adoptionapply", "apply_id", apply_id, update_data)
        db.close_database()
        
        if success:
            return jsonify({
                "success": True,
                "message": "修改成功",
                "data": {"apply_id": apply_id, "status": status}
            })
        else:
            return jsonify({"success": False, "message": "修改失败", "data": None})
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<apply_id>/reject', methods=['POST'])
def reject_application(apply_id):
    req = request.get_json()
    try:
        adoption_lib = AdoptionApplyLibrary()
        result = adoption_lib.reject_application(
            apply_id=apply_id,
            review_comment=req.get('review_comment'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})
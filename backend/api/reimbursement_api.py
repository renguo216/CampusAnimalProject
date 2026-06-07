from flask import Blueprint, request, jsonify, g

from backend.libs.reimbursement_library import ReimbursementLibrary
from backend.dependencies.auth import login_required

router = Blueprint('reimbursement', __name__)


@router.route('/apply', methods=['POST'])
@login_required
def create_reimbursement():
    user_id = g.current_user_id
    req = request.get_json()
    try:
        reimbursement_lib = ReimbursementLibrary()
        result = reimbursement_lib.submit_reimbursement(
            user_id=user_id,
            amount=req.get('amount'),
            type_=req.get('type'),
            description=req.get('description'),
            receipt_urls=req.get('receipt_urls'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('', methods=['GET'])
def list_reimbursements():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        reimbursement_lib = ReimbursementLibrary()
        result = reimbursement_lib.get_all_reimbursements(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/user/<user_id>', methods=['GET'])
def get_user_reimbursements(user_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        reimbursement_lib = ReimbursementLibrary()
        result = reimbursement_lib.get_user_reimbursements(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<reimbursement_id>/approve', methods=['POST'])
@login_required
def approve_reimbursement(reimbursement_id):
    req = request.get_json()
    try:
        reimbursement_lib = ReimbursementLibrary()
        result = reimbursement_lib.approve_reimbursement(
            reimb_id=reimbursement_id,
            admin_id=g.current_user_id,
            review_comment=req.get('review_comment'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<reimbursement_id>/reject', methods=['POST'])
@login_required
def reject_reimbursement(reimbursement_id):
    req = request.get_json()
    try:
        reimbursement_lib = ReimbursementLibrary()
        result = reimbursement_lib.reject_reimbursement(
            reimb_id=reimbursement_id,
            admin_id=g.current_user_id,
            reason=req.get('reason'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

from flask import Blueprint, request, jsonify, g

from backend.libs.donation_library import DonationLibrary
from backend.dependencies.auth import login_required

router = Blueprint('donation', __name__)


@router.route('/pay', methods=['POST'])
def create_donation():
    req = request.get_json()
    user_id = req.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "缺少用户ID", "data": None})
    try:
        donation_lib = DonationLibrary()
        result = donation_lib.submit_donation(
            user_id=user_id,
            project_id=req.get('project_id'),
            amount=req.get('amount'),
        )
        return jsonify(result)
    except Exception as e:
        print('创建捐赠记录异常:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('', methods=['GET'])
def list_donations():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        donation_lib = DonationLibrary()
        result = donation_lib.get_all_donations(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/user/<user_id>', methods=['GET'])
def get_user_donations(user_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        donation_lib = DonationLibrary()
        result = donation_lib.get_user_donations(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/history', methods=['GET'])
def get_my_donation_history():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "缺少user_id", "data": None})
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        donation_lib = DonationLibrary()
        result = donation_lib.get_user_donations(user_id=user_id, page=page, page_size=page_size)
        
        total_amount = 0
        data_list = []
        if result.get('success') and result.get('data') and result.get('data').get('donations'):
            data_list = result.get('data').get('donations')
            # 计算总金额
            for item in data_list:
                total_amount += float(item.get('amount', 0))
        
        return jsonify({
            "success": True, 
            "message": "成功", 
            "data": data_list,
            "totalAmount": round(total_amount, 2)
        })
    except Exception as e:
        print(f'获取捐赠历史异常: {str(e)}')
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

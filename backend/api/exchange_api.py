from flask import Blueprint, request, jsonify, g

from backend.libs.exchange_library import ExchangeLibrary
from backend.dependencies.auth import login_required

router = Blueprint('exchange', __name__)


@router.route('/my-points', methods=['GET'])
def get_my_points():
    user_id = request.args.get('user_id')
    try:
        exchange_lib = ExchangeLibrary()
        result = exchange_lib.check_user_points(user_id=user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/exchange', methods=['POST'])
def create_exchange():
    req = request.get_json()
    user_id = req.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "缺少用户ID", "data": None})
    try:
        exchange_lib = ExchangeLibrary()
        result = exchange_lib.submit_exchange(
            user_id=user_id,
            product_id=req.get('product_id'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/exchange-records', methods=['GET'])
def get_user_exchanges():
    user_id = request.args.get('user_id')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        exchange_lib = ExchangeLibrary()
        result = exchange_lib.get_user_exchanges(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('', methods=['GET'])
def list_exchanges():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        exchange_lib = ExchangeLibrary()
        result = exchange_lib.get_all_exchanges(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

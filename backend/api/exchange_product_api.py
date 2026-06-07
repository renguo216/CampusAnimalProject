from flask import Blueprint, request, jsonify

from backend.libs.exchange_product_library import ExchangeProductLibrary
from backend.dependencies.auth import login_required

router = Blueprint('exchange_product', __name__)


@router.route('/products', methods=['GET'])
def list_products():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        product_lib = ExchangeProductLibrary()
        result = product_lib.get_exchange_items(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product_lib = ExchangeProductLibrary()
        result = product_lib.get_exchange_item_by_id(product_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('', methods=['POST'])
def create_product():
    req = request.get_json()
    try:
        product_lib = ExchangeProductLibrary()
        result = product_lib.create_exchange_product({
            'name': req.get('name'),
            'points_required': req.get('points_required'),
            'stock': req.get('stock', 0),
            'description': req.get('description'),
            'image_url': req.get('image_url'),
            'status': req.get('status', 1)
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<product_id>', methods=['PUT'])
def update_product(product_id):
    req = request.get_json()
    try:
        product_lib = ExchangeProductLibrary()
        result = product_lib.update_exchange_product(product_id, {
            'name': req.get('name'),
            'points_required': req.get('points_required'),
            'stock': req.get('stock'),
            'description': req.get('description'),
            'image_url': req.get('image_url'),
            'status': req.get('status')
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<product_id>/status', methods=['PUT'])
def update_product_status(product_id):
    req = request.get_json()
    try:
        product_lib = ExchangeProductLibrary()
        result = product_lib.toggle_product_status(product_id, req.get('status'))
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<product_id>/stock', methods=['PUT'])
def update_product_stock(product_id):
    req = request.get_json()
    try:
        product_lib = ExchangeProductLibrary()
        result = product_lib.update_product_stock(product_id, req.get('stock'))
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product_lib = ExchangeProductLibrary()
        result = product_lib.delete_exchange_product(product_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/products/all', methods=['GET'])
def list_all_products():
    """获取所有商品（包括下架的，用于管理）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        product_lib = ExchangeProductLibrary()
        if not product_lib.db.open_database():
            return jsonify({"success": False, "message": "数据库连接失败", "data": None})
        
        result = product_lib.db.get_paginated(
            't_exchange_product',
            page=page,
            page_size=page_size,
            where_clause="1=1",
            params=None,
            order_by="created_at DESC"
        )
        
        product_lib.db.close_database()
        
        if result is None:
            return jsonify({"success": False, "message": "查询失败", "data": None})
        
        items = []
        data_list = result.get('data', [])
        for item in data_list:
            image_url = item.get('image_url', '')
            if image_url and image_url.startswith('/'):
                image_url = f"http://192.168.86.73:5000{image_url}"
            items.append({
                'product_id': item.get('product_id'),
                'name': item.get('name'),
                'description': item.get('description', ''),
                'image_url': image_url,
                'points_required': int(item.get('points_required', 0)),
                'stock': int(item.get('stock', 0)),
                'status': item.get('status', 1),
                'created_at': item.get('created_at') and item.get('created_at').strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return jsonify({
            "success": True,
            "message": "成功",
            "data": {
                "total": result.get('total', 0),
                "page": page,
                "page_size": page_size,
                "products": items
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})
from flask import Blueprint, request, jsonify, g

from backend.libs.rescue_record_library import RescueRecordLibrary
from backend.dependencies.auth import login_required

router = Blueprint('rescue_record', __name__)


@router.route('/records', methods=['GET'])
def list_rescue_records():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.get_all_rescues(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my-records', methods=['GET'])
def get_my_rescue_records():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "缺少user_id", "data": None})
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        rescue_lib = RescueRecordLibrary()
        # 既返回上报的，也返回参与救助的
        user_result = rescue_lib.get_user_rescues(user_id=user_id, page=page, page_size=page_size)
        helper_result = rescue_lib.get_helper_rescues(helper_id=user_id, page=page, page_size=page_size)
        
        # 合并结果并去重（按 record_id）
        record_map = {}
        
        if user_result.get('success') and user_result.get('data') and user_result.get('data').get('records'):
            for record in user_result.get('data').get('records'):
                record_map[record['record_id']] = record
        
        if helper_result.get('success') and helper_result.get('data') and helper_result.get('data').get('records'):
            for record in helper_result.get('data').get('records'):
                if record['record_id'] not in record_map:
                    record_map[record['record_id']] = record
        
        # 转换为列表并按时间排序
        all_records = sorted(record_map.values(), key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({"success": True, "message": "成功", "data": all_records})
    except Exception as e:
        print(f'获取我的救助记录异常: {str(e)}')
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<record_id>', methods=['GET'])
def get_rescue_record(record_id):
    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.get_rescue_record_by_id(record_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/records', methods=['POST'])
@login_required
def create_rescue_record():
    user_id = g.current_user_id
    req = request.get_json()
    try:
        rescue_lib = RescueRecordLibrary()
        print('创建救助记录请求:', req)
        result = rescue_lib.create_rescue_record(
            user_id=user_id,
            title=req.get('title'),
            description=req.get('description'),
            location=req.get('location'),
            found_location_text=req.get('found_location_text'),
            need_type=req.get('need_type'),
            photo_urls=req.get('photo_urls'),
            animal_name=req.get('animal_name'),
            pet_id=req.get('pet_id'),
            priority=req.get('priority', 0),
        )
        print('创建救助记录结果:', result)
        return jsonify(result)
    except Exception as e:
        print('创建救助记录异常:', str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<record_id>', methods=['PUT'])
@login_required
def update_rescue_record(record_id):
    user_id = g.current_user_id
    req = request.get_json()
    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.update_rescue_record(
            record_id=record_id,
            user_id=user_id,
            title=req.get('title'),
            description=req.get('description'),
            location=req.get('location'),
            photo_urls=req.get('photo_urls'),
            animal_name=req.get('animal_name'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<record_id>/claim', methods=['POST'])
@login_required
def claim_rescue(record_id):
    user_id = g.current_user_id
    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.claim_rescue(record_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<record_id>/complete', methods=['POST'])
@login_required
def complete_rescue(record_id):
    user_id = g.current_user_id
    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.complete_rescue(record_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<record_id>/confirm', methods=['POST'])
@login_required
def confirm_rescue(record_id):
    user_id = g.current_user_id
    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.confirm_rescue(record_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<record_id>/close', methods=['POST'])
@login_required
def close_rescue(record_id):
    user_id = g.current_user_id
    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.close_rescue(record_id, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

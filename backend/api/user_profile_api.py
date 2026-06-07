from flask import Blueprint, request, jsonify, g

from backend.libs.volunteer_application_library import VolunteerApplicationLibrary
from backend.libs.rescue_record_library import RescueRecordLibrary
from backend.libs.adoption_apply_library import AdoptionApplyLibrary
from backend.libs.exchange_library import ExchangeLibrary
from backend.libs.donation_library import DonationLibrary
from backend.libs.post_library import PostLibrary
from backend.dependencies.auth import login_required

router = Blueprint('user_profile', __name__)


@router.route('/profile/<user_id>', methods=['GET'])
@login_required
def get_user_profile(user_id):
    """获取用户个人资料（需登录，只能查看自己的）"""
    if g.current_user_id != user_id:
        return jsonify({"success": False, "message": "只能查看自己的资料", "data": None}), 403

    try:
        from backend.libs.user_library import UserLibrary
        user_lib = UserLibrary()
        result = user_lib.get_user_profile(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/rescues', methods=['GET'])
@login_required
def get_my_rescues():
    """获取我的救助记录"""
    user_id = g.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.get_user_rescues(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/adoptions', methods=['GET'])
@login_required
def get_my_adoptions():
    """获取我的领养申请"""
    user_id = g.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        adoption_lib = AdoptionApplyLibrary()
        result = adoption_lib.get_user_applications(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/points', methods=['GET'])
@login_required
def get_my_points():
    """获取我的积分信息"""
    user_id = g.current_user_id

    try:
        from backend.libs.user_library import UserLibrary
        user_lib = UserLibrary()
        user_result = user_lib.get_user_profile(user_id)
        if not user_result.get("success"):
            return jsonify(user_result)

        user_data = user_result.get("data", {})
        return jsonify({
            "success": True,
            "message": "成功",
            "data": {
                "points": user_data.get("points", 0),
                "level": user_data.get("level", 0),
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/exchanges', methods=['GET'])
@login_required
def get_my_exchanges():
    """获取我的积分兑换记录"""
    user_id = g.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        exchange_lib = ExchangeLibrary()
        result = exchange_lib.get_user_exchanges(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/donations', methods=['GET'])
@login_required
def get_my_donations():
    """获取我的捐款记录"""
    user_id = g.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        donation_lib = DonationLibrary()
        result = donation_lib.get_user_donations(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/posts', methods=['GET'])
@login_required
def get_my_posts():
    """获取我的帖子"""
    user_id = g.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        post_lib = PostLibrary()
        result = post_lib.get_posts_by_user(user_id=user_id, page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/volunteer', methods=['GET'])
@login_required
def get_my_volunteer_info():
    """获取我的志愿者信息"""
    user_id = g.current_user_id

    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.get_volunteer_info(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/my/volunteer/stats', methods=['GET'])
@login_required
def get_my_volunteer_stats():
    """获取我的志愿者统计"""
    user_id = g.current_user_id

    try:
        volunteer_lib = VolunteerApplicationLibrary()
        info_result = volunteer_lib.get_volunteer_info(user_id)

        from backend.libs.rescue_record_library import RescueRecordLibrary
        rescue_lib = RescueRecordLibrary()
        rescues_result = rescue_lib.get_user_rescues(user_id=user_id, page=1, page_size=100)

        rescue_count = 0
        if rescues_result.get("success"):
            rescue_count = len(rescues_result.get("data", {}).get("records", []))

        data = info_result.get("data", {}) if info_result.get("success") else {}
        data["rescue_count"] = rescue_count

        return jsonify({
            "success": True,
            "message": "成功",
            "data": data
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})
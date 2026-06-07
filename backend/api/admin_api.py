from flask import Blueprint, request, jsonify, g

from backend.libs.volunteer_application_library import VolunteerApplicationLibrary
from backend.libs.adoption_apply_library import AdoptionApplyLibrary
from backend.libs.donation_library import DonationLibrary
from backend.libs.donation_project_library import DonationProjectLibrary
from backend.libs.exchange_library import ExchangeLibrary
from backend.libs.rescue_record_library import RescueRecordLibrary
from backend.libs.animal_library import AnimalLibrary
from backend.libs.user_library import UserLibrary
from backend.dependencies.auth import login_required

router = Blueprint('admin', __name__)


def require_admin(user_id: str) -> bool:
    """检查用户是否为管理员"""
    try:
        user_lib = UserLibrary()
        result = user_lib.get_user_profile(user_id)
        if result.get("success"):
            return result.get("data", {}).get("role") == 3
    except:
        pass
    return False


@router.route('/stats', methods=['GET'])
def get_admin_stats():
    """获取管理后台统计"""
    try:
        from backend.libs.post_library import PostLibrary
        from backend.libs.adoption_apply_library import AdoptionApplyLibrary
        from backend.libs.rescue_record_library import RescueRecordLibrary
        from backend.libs.exchange_product_library import ExchangeProductLibrary

        post_lib = PostLibrary()
        posts_result = post_lib.get_all_posts(page=1, page_size=1)

        animal_lib = AnimalLibrary()
        animals_result = animal_lib.get_all_animals(page=1, page_size=1)

        donation_lib = DonationLibrary()
        donations_result = donation_lib.get_all_donations(page=1, page_size=1)

        volunteer_lib = VolunteerApplicationLibrary()
        volunteers_result = volunteer_lib.get_all_applications(page=1, page_size=1)

        adoption_lib = AdoptionApplyLibrary()
        adoptions_result = adoption_lib.get_all_applications(page=1, page_size=1)

        rescue_lib = RescueRecordLibrary()
        rescues_result = rescue_lib.get_all_rescues(page=1, page_size=1)

        product_lib = ExchangeProductLibrary()
        products_result = product_lib.get_exchange_items(page=1, page_size=1)

        user_lib = UserLibrary()
        users_result = user_lib.get_all_users(page=1, page_size=1)

        return jsonify({
            "success": True,
            "message": "成功",
            "data": {
                "posts_count": posts_result.get("data", {}).get("total", 0),
                "animals_count": animals_result.get("data", {}).get("total", 0),
                "donations_count": donations_result.get("data", {}).get("total", 0),
                "volunteers_count": volunteers_result.get("data", {}).get("total", 0),
                "adoptions_count": adoptions_result.get("data", {}).get("total", 0),
                "rescues_count": rescues_result.get("data", {}).get("total", 0),
                "products_count": len(products_result.get("data", [])),
                "users_count": users_result.get("data", {}).get("total", 0),
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/users', methods=['GET'])
def list_all_users():
    """获取所有用户列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        user_lib = UserLibrary()
        result = user_lib.get_all_users(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/users/<user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    """修改用户角色"""
    req = request.get_json()
    try:
        user_lib = UserLibrary()
        result = user_lib.update_role(
            user_id=user_id,
            new_role=req.get('role'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    try:
        user_lib = UserLibrary()
        result = user_lib.delete_user(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/animals/all', methods=['GET'])
def list_all_animals():
    """获取所有动物（管理）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        animal_lib = AnimalLibrary()
        result = animal_lib.get_all_animals(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/donations/all', methods=['GET'])
def list_all_donations():
    """获取所有捐款记录（管理）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        donation_lib = DonationLibrary()
        result = donation_lib.get_all_donations(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/donations/<donation_id>/approve', methods=['POST'])
def approve_donation(donation_id):
    """审核通过捐款"""
    try:
        donation_lib = DonationLibrary()
        result = donation_lib.approve_donation(
            donation_id=donation_id,
            admin_id='admin'
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/donations/<donation_id>/reject', methods=['POST'])
def reject_donation(donation_id):
    """驳回捐款"""
    req = request.get_json()
    try:
        donation_lib = DonationLibrary()
        result = donation_lib.reject_donation(
            donation_id=donation_id,
            admin_id='admin',
            reason=req.get('reason', '')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/volunteers/all', methods=['GET'])
def list_all_volunteers():
    """获取所有志愿者申请（管理）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.get_all_applications(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/volunteers/<application_id>/approve', methods=['POST'])
def admin_approve_volunteer(application_id):
    """管理员批准志愿者申请"""
    req = request.get_json()
    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.approve_application(
            application_id=int(application_id),
            admin_id='admin',
            review_comment=req.get('review_comment')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/volunteers/<application_id>/reject', methods=['POST'])
def admin_reject_volunteer(application_id):
    """管理员拒绝志愿者申请"""
    req = request.get_json()
    try:
        volunteer_lib = VolunteerApplicationLibrary()
        result = volunteer_lib.reject_application(
            application_id=int(application_id),
            admin_id='admin',
            reason=req.get('reason', '')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/adoptions/all', methods=['GET'])
def list_all_adoptions():
    """获取所有领养申请（管理）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        adoption_lib = AdoptionApplyLibrary()
        pet_id = request.args.get('pet_id')
        if pet_id:
            result = adoption_lib.get_animal_applications(
                pet_id=int(pet_id),
                page=page,
                page_size=page_size
            )
        else:
            result = adoption_lib.get_all_applications(
                page=page,
                page_size=page_size
            )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/rescues/all', methods=['GET'])
def list_all_rescues():
    """获取所有救助记录（管理）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        rescue_lib = RescueRecordLibrary()
        result = rescue_lib.get_all_rescues(page=page, page_size=page_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})
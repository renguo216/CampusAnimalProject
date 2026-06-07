from flask import Blueprint, request, jsonify, g
import hashlib

from backend.libs.user_library import UserLibrary
from backend.dependencies.auth import login_required

router = Blueprint('user', __name__)


@router.route('/login', methods=['POST'])
def login():
    req = request.get_json()
    try:
        user_lib = UserLibrary()
        userInfo = req.get('userInfo', {})
        
        # 生成稳定的 user_id：基于用户昵称和头像的哈希
        nickname = userInfo.get('nickName') or userInfo.get('nickname') or '微信用户'
        avatar_url = userInfo.get('avatarUrl') or userInfo.get('avatar_url') or ''
        
        # 使用用户信息生成稳定的 user_id
        user_identifier = f"{nickname}_{avatar_url}"
        user_id = hashlib.md5(user_identifier.encode('utf-8')).hexdigest()

        existing_user = user_lib.get_user_by_account(user_id)
        if existing_user.get('success'):
            return jsonify(existing_user)

        result = user_lib.register_user(
            user_id=user_id,
            nickname=nickname,
            avatar_url=avatar_url,
            role=1,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/update', methods=['POST'])
@login_required
def update_user():
    user_id = g.current_user_id
    req = request.get_json()
    try:
        user_lib = UserLibrary()
        result = user_lib.update_user_info(user_id, req)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user_lib = UserLibrary()
        result = user_lib.get_user_by_account(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/register', methods=['POST'])
def register():
    req = request.get_json()
    try:
        user_lib = UserLibrary()
        result = user_lib.register_user(
            user_id=req.get('user_id'),
            nickname=req.get('nickname'),
            avatar_url=req.get('avatar_url'),
            role=req.get('role', 1),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/validate', methods=['GET'])
def validate_user():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "缺少user_id参数", "data": None})
    try:
        user_lib = UserLibrary()
        result = user_lib.verify_user_validity(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

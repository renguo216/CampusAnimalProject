from functools import wraps
from flask import request, jsonify, g
from typing import Optional


def get_current_user_id():
    authorization = request.headers.get('Authorization')
    if not authorization:
        return None
    # 兼容 "Bearer token" 和直接发送 token 两种格式
    if authorization.startswith('Bearer '):
        return authorization[7:]
    return authorization


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "message": "未提供认证信息", "data": None}), 401
        g.current_user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


def get_optional_user_id():
    return get_current_user_id()


def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "message": "未提供认证信息", "data": None}), 401
        g.current_user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


def require_volunteer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "message": "未提供认证信息", "data": None}), 401
        g.current_user_id = user_id
        return f(*args, **kwargs)
    return decorated_function

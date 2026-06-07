
from flask import Blueprint, request, jsonify

from backend.libs.hospital_library import HospitalLibrary

router = Blueprint('hospital', __name__)


@router.route('/', methods=['GET'])
def list_hospitals():
    try:
        hospital_lib = HospitalLibrary()
        result = hospital_lib.get_all_hospitals()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<int:hospital_id>', methods=['GET'])
def get_hospital(hospital_id):
    try:
        hospital_lib = HospitalLibrary()
        result = hospital_lib.get_hospital_by_id(hospital_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


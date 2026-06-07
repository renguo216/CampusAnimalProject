from flask import Blueprint, request, jsonify, g

from backend.libs.animal_library import AnimalLibrary
from backend.dependencies.auth import login_required

router = Blueprint('animal', __name__)


@router.route('/search', methods=['GET'])
def list_animals():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    try:
        animal_lib = AnimalLibrary()
        result = animal_lib.get_all_animals(page=page, page_size=page_size)
        print(f"=== 动物列表API ===")
        print(f"请求参数: page={page}, page_size={page_size}")
        print(f"返回结果: {result}")
        if result.get('data') and result.get('data').get('animals'):
            for animal in result['data']['animals']:
                print(f"动物ID: {animal['pet_id']}, 名字: {animal['name']}, photo_urls: {animal['photo_urls']}, 状态: {animal['status']}")
        return jsonify(result)
    except Exception as e:
        print(f"动物列表API异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<animal_id>', methods=['GET'])
def get_animal(animal_id):
    try:
        animal_lib = AnimalLibrary()
        result = animal_lib.get_animal_by_id(animal_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('', methods=['POST'])
@login_required
def create_animal():
    req = request.get_json()
    try:
        animal_lib = AnimalLibrary()
        result = animal_lib.add_animal(
            name=req.get('name'),
            breed=req.get('breed', '未知'),
            status=req.get('status', 0),
            color=req.get('color'),
            age=req.get('age', 0),
            gender=req.get('gender', 0),
            is_neutered=req.get('is_neutered', 0),
            is_vaccinated=req.get('is_vaccinated', 0),
            personality=req.get('personality'),
            description=req.get('description'),
            photo_urls=req.get('photo_urls'),
            found_location=req.get('found_location'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})


@router.route('/<animal_id>/status', methods=['PUT'])
@login_required
def update_animal_status(animal_id):
    req = request.get_json()
    try:
        animal_lib = AnimalLibrary()
        result = animal_lib.update_animal_status(
            pet_id=animal_id,
            new_status=req.get('status'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器异常：{str(e)}", "data": None})

from flask import Blueprint, request, jsonify
import os
import uuid
from datetime import datetime

router = Blueprint('upload', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@router.route('/image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "没有上传文件", "data": None})
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "文件名不能为空", "data": None})
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_name = f"{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_name)
        
        file.save(file_path)
        
        # 返回相对路径，让前端根据当前协议自动选择http或https
        url = f"/{UPLOAD_FOLDER}/{unique_name}"
        
        return jsonify({
            "success": True,
            "message": "上传成功",
            "data": {"url": url, "filename": unique_name}
        })
    else:
        return jsonify({"success": False, "message": "不支持的文件格式", "data": None})

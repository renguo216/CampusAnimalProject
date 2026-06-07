from flask import Blueprint, request, jsonify
import requests
import tempfile
import os
import subprocess
import json
import sys

router = Blueprint('ai', __name__)

# 获取 test.py 的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_PY_PATH = os.path.join(BASE_DIR, 'backend', 'ai_module', 'test.py')

# 创建uploads目录用于保存上传的图片
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.route('/detect-species', methods=['POST'])
def detect_species():
    """识别动物种类和品种"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "没有上传文件"}), 400

    file = request.files['file']
    try:
        files = {'file': (file.filename, file.read(), file.content_type)}
        response = requests.post('http://192.168.143.128:8001/detect-species', files=files, timeout=30)
        return jsonify(response.json())
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "AI服务未启动", "data": None}), 503
    except Exception as e:
        return jsonify({"success": False, "message": f"AI识别失败：{str(e)}", "data": None}), 500


@router.route('/recognize', methods=['POST'])
def recognize():
    """AI识别动物（通过执行test.py文件实现）"""
    if 'photo' not in request.files:
        return jsonify({"success": False, "message": "没有上传文件"}), 400

    file = request.files['photo']
    try:
        # 1. 保存上传的图片到uploads目录
        import uuid
        file_extension = os.path.splitext(file.filename)[1] or '.jpg'
        filename = f"ai_recognize_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        file.save(file_path)
        
        print(f"[AI识别] 图片已保存: {file_path}")
        
        # 2. 执行test.py文件并传入图片路径
        python_exe = sys.executable
        cmd = [python_exe, TEST_PY_PATH, file_path]
        
        print(f"[AI识别] 执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=60
        )
        
        # 处理stdout，使用gbk编码（Windows默认编码）并忽略错误
        stdout_str = ""
        stderr_str = ""
        try:
            stdout_str = result.stdout.decode('gbk', errors='replace')
        except:
            try:
                stdout_str = result.stdout.decode('utf-8', errors='replace')
            except:
                stdout_str = str(result.stdout)
        
        try:
            stderr_str = result.stderr.decode('gbk', errors='replace')
        except:
            try:
                stderr_str = result.stderr.decode('utf-8', errors='replace')
            except:
                stderr_str = str(result.stderr)
        
        print(f"[AI识别] test.py stdout: {stdout_str}")
        print(f"[AI识别] test.py stderr: {stderr_str}")
        
        # 3. 解析test.py的输出
        ai_result = None
        if stdout_str and stdout_str.strip():
            try:
                ai_result = json.loads(stdout_str.strip())
            except json.JSONDecodeError as e:
                print(f"[AI识别] JSON解析失败: {e}")
                ai_result = {
                    "success": False,
                    "message": f"AI识别结果解析失败: {str(e)}",
                    "raw_output": stdout_str[:500]
                }
        else:
            ai_result = {
                "success": False,
                "message": "AI识别无输出，可能test.py执行失败",
                "stderr": stderr_str[:500]
            }
        
        # 4. 清理临时文件（可选，也可以保留用于调试）
        # try:
        #     if os.path.exists(file_path):
        #         os.remove(file_path)
        #         print(f"[AI识别] 临时文件已删除: {file_path}")
        # except Exception as e:
        #     print(f"[AI识别] 删除临时文件失败: {e}")
        
        # 5. 适配前端期望的数据格式
        if ai_result.get('success', True):
            return jsonify({
                "success": True,
                "message": "识别成功",
                "data": {
                    "species": ai_result.get('species', ai_result.get('data', {}).get('species', '未知')),
                    "breed": ai_result.get('breed_name', ai_result.get('data', {}).get('breed', '未知')),
                    "confidence": ai_result.get('confidence', ai_result.get('data', {}).get('confidence', 0)),
                    "suggestion": ai_result.get('suggestion', ai_result.get('data', {}).get('suggestion', ''))
                }
            })
        return jsonify(ai_result)
        
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "AI识别超时，请重试", "data": None}), 504
    except FileNotFoundError:
        return jsonify({"success": False, "message": f"test.py文件不存在: {TEST_PY_PATH}", "data": None}), 500
    except Exception as e:
        print(f"[AI识别] 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"AI识别失败：{str(e)}", "data": None}), 500


@router.route('/identify', methods=['POST'])
def identify_animal():
    """识别动物个体"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "没有上传文件"}), 400

    file = request.files['file']
    try:
        files = {'file': (file.filename, file.read(), file.content_type)}
        response = requests.post('http://192.168.175.128:8001/identify', files=files, timeout=30)
        return jsonify(response.json())
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "AI服务未启动", "data": None}), 503
    except Exception as e:
        return jsonify({"success": False, "message": f"AI识别失败：{str(e)}", "data": None}), 500


@router.route('/extract-features', methods=['POST'])
def extract_features():
    """提取图片特征向量"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "没有上传文件"}), 400

    file = request.files['file']
    try:
        files = {'file': (file.filename, file.read(), file.content_type)}
        response = requests.post('http://192.168.175.128:8001/extract-features', files=files, timeout=30)
        return jsonify(response.json())
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "AI服务未启动", "data": None}), 503
    except Exception as e:
        return jsonify({"success": False, "message": f"特征提取失败：{str(e)}", "data": None}), 500


@router.route('/stats', methods=['GET'])
def ai_stats():
    """AI服务状态"""
    try:
        response = requests.get('http://192.168.175.128:8001/stats', timeout=5)
        return jsonify(response.json())
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "AI服务未启动", "data": None}), 503
    except Exception as e:
        return jsonify({"success": False, "message": f"获取状态失败：{str(e)}", "data": None}), 500
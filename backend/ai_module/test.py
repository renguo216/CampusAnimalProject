import requests
import sys
import os

def detect_animal(image_path):
    """识别动物种类和品种"""
    try:
        with open(image_path, 'rb') as f:
            response = requests.post('http://192.168.143.128:8001/detect-species', files={'file': f})
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('{"success": false, "message": "请提供图片路径"}')
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f'{{"success": false, "message": "图片文件不存在: {image_path}"}}')
        sys.exit(1)
    
    result = detect_animal(image_path)
    import json
    print(json.dumps(result, ensure_ascii=False))
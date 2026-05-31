# test_ai_request.py
#python test_ai_request.py
import requests
try:
    with open('test.jpg', 'rb') as f:
        r = requests.post('http://localhost:8001/detect-species', files={'file': f})
    print(r.json())
except Exception as e:
    print(f"请求出错: {e}")
# TAGO API 서울시 도시코드 조회
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config import Config

# 도시코드 목록 조회
url = 'http://apis.data.go.kr/1613000/ArvlInfoInqireService/getCtyCodeList'
params = {
    'serviceKey': Config.API_KEY,  # 통일된 API_KEY 사용
    '_type': 'json'  # JSON으로 받기 (XML보다 파싱 쉬움)
}

response = requests.get(url, params=params)
print("응답 상태코드:", response.status_code)
print("응답 내용:")
print(response.content.decode('utf-8'))
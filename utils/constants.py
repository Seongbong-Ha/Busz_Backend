TAGO_API_CONFIG = {
    'TIMEOUT': 10,
    'MAX_RETRIES': 3,
    'DEFAULT_RADIUS': 500,  # 기본 검색 반경 (미터)
    'CACHE_TTL': 60,  # 캐시 유지 시간 (초)
}

# 버스 노선 유형 코드
BUS_ROUTE_TYPES = {
    '1': '일반버스',
    '2': '좌석버스', 
    '3': '마을버스',
    '4': '급행버스',
    '5': '간선버스',
    '6': '지선버스',
    '7': '순환버스',
    '8': '광역버스',
    '9': '인천버스',
    '10': '경기버스',
    '11': '공항버스',
    '12': '심야버스'
}

# 앱 상수
APP_VERSION = 'v1.0.0'

# API 정보
API_FLOWS = {
    'flow1': {
        'name': 'WebSocket 실시간 모니터링',
        'protocol': 'WebSocket',
        'events': ['start_bus_monitoring', 'stop_bus_monitoring', 'get_session_status']
    },
    'flow2': {
        'name': 'REST API 전체 버스 정보',
        'protocol': 'HTTP/JSON',
        'endpoints': ['/api/station/buses']
    }
}

# 사용 가능한 엔드포인트
AVAILABLE_ENDPOINTS = {
    'websocket_test': '/test',
    'station_buses': '/api/station/buses (POST)',
    'api_info': '/api'
}

# WebSocket 이벤트 정의
WEBSOCKET_EVENTS = {
    'start_bus_monitoring': {
        'description': '실시간 모니터링 시작',
        'parameters': {
            'lat': 'float - 위도',
            'lng': 'float - 경도', 
            'bus_number': 'string - 버스 번호',
            'interval': 'int - 업데이트 간격(초)'
        }
    }
}
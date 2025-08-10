from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import json
from config import Config
from websocket import init_websocket_handlers

# 🆕 플로우 2 라우트 임포트
from routes import register_routes

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY or 'dev-secret-key-change-in-production'

# 🆕 모바일 앱 JSON 통신 설정
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # JSON 응답 포맷팅
app.config['JSON_AS_ASCII'] = False  # 한글 지원
app.config['JSON_SORT_KEYS'] = False  # 키 정렬 비활성화

# 🆕 CORS 설정 (모바일 앱에서 API 호출 허용)
CORS(app, 
     origins=["*"],  # 개발용, 실제로는 앱 도메인만 허용
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Session-ID"],
     supports_credentials=True)

# SocketIO 초기화 (플로우 1 유지)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",  # 모바일 앱 WebSocket 연결 허용
                   json=json)  # JSON 엔코딩 설정

# WebSocket 핸들러 등록 (플로우 1 유지)
init_websocket_handlers(socketio)

# 🆕 플로우 2 REST API 라우트 등록
register_routes(app)

# ===================== JSON 응답 커스터마이징 =====================

@app.after_request
def after_request(response):
    """모든 응답에 모바일 앱 친화적 헤더 추가"""
    # JSON 응답 타입 명시
    if response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    
    # 모바일 앱 캐싱 제어
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # CORS 헤더 (중복 방지)
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response

@app.errorhandler(404)
def not_found(error):
    """404 에러를 JSON으로 응답"""
    return jsonify({
        'success': False,
        'error': '요청한 엔드포인트를 찾을 수 없습니다',
        'error_code': 'NOT_FOUND',
        'available_endpoints': {
            'websocket_test': '/test',
            'station_buses': '/api/station/buses (POST)',
            'api_info': '/api'
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 에러를 JSON으로 응답"""
    return jsonify({
        'success': False,
        'error': '서버 내부 오류가 발생했습니다',
        'error_code': 'INTERNAL_SERVER_ERROR'
    }), 500

@app.errorhandler(400)
def bad_request(error):
    """400 에러를 JSON으로 응답"""
    return jsonify({
        'success': False,
        'error': '잘못된 요청입니다',
        'error_code': 'BAD_REQUEST'
    }), 400

# ===================== 기본 라우트들 (JSON 응답) =====================

@app.route('/')
def home():
    """홈 - 서버 상태 확인 (JSON 응답)"""
    return jsonify({
        'success': True,
        'message': 'Busz Backend API 서버',
        'status': 'running',
        'version': 'v1.0.0',
        'flows': {
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
        },
        'mobile_app_ready': True
    })

@app.route('/test')
def test_page():
    """WebSocket 테스트 페이지 (개발용)"""
    return render_template('websocket_test.html')

@app.route('/api')
def api_info():
    """API 정보 (모바일 앱용)"""
    return jsonify({
        'success': True,
        'api_version': 'v1.0.0',
        'flows': {
            'flow1': {
                'type': 'WebSocket',
                'description': '특정 버스 실시간 모니터링',
                'url': f'ws://{Config.HOST}:{Config.PORT}',
                'events': {
                    'start_bus_monitoring': {
                        'description': '실시간 모니터링 시작',
                        'parameters': {
                            'lat': 'float - 위도',
                            'lng': 'float - 경도', 
                            'bus_number': 'string - 버스 번호',
                            'interval': 'int - 업데이트 간격(초)'
                        }
                    },
                    'bus_update': {
                        'description': '실시간 버스 정보 수신'
                    },
                    'stop_bus_monitoring': {
                        'description': '모니터링 중단'
                    }
                }
            },
            'flow2': {
                'type': 'REST API',
                'description': '전체 버스 정보 조회 (세션 기반)',
                'endpoints': {
                    'station_buses': {
                        'url': '/api/station/buses',
                        'method': 'POST',
                        'request_body': '{}',
                        'description': '현재 정류소의 전체 버스 정보',
                        'prerequisites': 'flow1이 먼저 실행되어야 함'
                    }
                }
            }
        },
        'usage_flow': [
            '1. WebSocket 연결',
            '2. start_bus_monitoring 이벤트로 플로우 1 시작',
            '3. POST /api/station/buses로 플로우 2 호출',
            '4. 받은 버스 정보로 앱에서 처리'
        ]
    })

# ===================== 메인 실행 =====================

if __name__ == '__main__':
    # Config 검증
    try:
        Config.validate()
    except ValueError as e:
        print(f"설정 오류: {e}")
        exit(1)
    
    print("🚌 Busz 백엔드 서버 시작 (모바일 앱 JSON 통신 지원)")
    print(f"서버 주소: http://{Config.HOST}:{Config.PORT}")
    print(f"WebSocket: ws://{Config.HOST}:{Config.PORT}")
    print(f"테스트 페이지: http://{Config.HOST}:{Config.PORT}/test")
    print(f"API 정보: http://{Config.HOST}:{Config.PORT}/api")
    print("=" * 60)
    print("플로우 1: WebSocket 실시간 모니터링")
    print("플로우 2: REST API 전체 버스 정보 조회")
    print("=" * 60)
    print("🔗 API 엔드포인트:")
    print(f"  - WebSocket: ws://{Config.HOST}:{Config.PORT}")
    print(f"  - POST /api/station/buses (플로우 2)")
    print("=" * 60)
    
    # SocketIO로 실행
    socketio.run(
        app,
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
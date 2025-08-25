from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
import json

from config import Config
from websocket import init_websocket_handlers
from routes import register_routes
from utils.constants import APP_VERSION, API_FLOWS, WEBSOCKET_EVENTS
from utils.middleware import handle_before_request, handle_after_request, register_error_handlers

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY or 'dev-secret-key-change-in-production'

# JSON 설정
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

# CORS 설정 강화
CORS(app, 
     origins=["*"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Session-ID", "ngrok-skip-browser-warning"],
     supports_credentials=True)

# SocketIO 초기화 (로그 활성화)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   cors_credentials=True,
                   logger=True,  # Socket.IO 로그 활성화
                   engineio_logger=True,  # Engine.IO 로그 활성화
                   json=json)

# WebSocket 핸들러 등록
init_websocket_handlers(socketio)

# REST API 라우트 등록
register_routes(app)

# 미들웨어 등록
app.before_request(handle_before_request)
app.after_request(handle_after_request)

# 에러 핸들러 등록
register_error_handlers(app)

# ===================== 기본 라우트들 =====================

@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def home():
    """홈 - 서버 상태 확인 (모든 메서드 허용)"""
    return jsonify({
        'success': True,
        'message': 'Busz Backend API 서버',
        'status': 'running',
        'version': APP_VERSION,
        'request_method': request.method,
        'request_path': request.path,
        'flows': API_FLOWS,
        'mobile_app_ready': True
    })

@app.route('/test')
def test_page():
    """WebSocket 테스트 페이지"""
    return render_template('websocket_test.html')

@app.route('/api')
def api_info():
    """API 정보"""
    return jsonify({
        'success': True,
        'api_version': APP_VERSION,
        'socket_io_path': '/socket.io/',
        'flows': {
            'flow1': {
                'type': 'WebSocket',
                'description': '특정 버스 실시간 모니터링',
                'url': f'ws://{Config.HOST}:{Config.PORT}',
                'events': WEBSOCKET_EVENTS
            }
        }
    })

# ===================== 메인 실행 =====================

if __name__ == '__main__':
    # Config 검증
    try:
        Config.validate()
    except ValueError as e:
        print(f"설정 오류: {e}")
        exit(1)
    
    print("🚌 Busz 백엔드 서버 시작 (Socket.IO 400 에러 수정 버전)")
    print(f"서버 주소: http://{Config.HOST}:{Config.PORT}")
    print(f"WebSocket: ws://{Config.HOST}:{Config.PORT}")
    print(f"Socket.IO 경로: /socket.io/")
    print("=" * 60)
    
    # SocketIO로 실행 (디버그 로그 활성화)
    socketio.run(
        app,
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT,
        log_output=True  # 상세 로그 출력
    )
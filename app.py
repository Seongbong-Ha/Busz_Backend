from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
from config import Config
from websocket import init_websocket_handlers

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY or 'dev-secret-key-change-in-production'

# SocketIO 초기화
socketio = SocketIO(app, cors_allowed_origins="*")

# WebSocket 핸들러 등록
init_websocket_handlers(socketio)

# ===================== 라우트 =====================

@app.route('/')
def home():
    """홈 - 서버 상태 확인"""
    return jsonify({
        'message': 'BUS API 서버가 실행 중입니다 (WebSocket 지원)',
        'status': 'running',
        'test_page': '/test'
    })

@app.route('/test')
def test_page():
    """WebSocket 실시간 버스 모니터링 테스트 페이지"""
    return render_template('websocket_test.html')

if __name__ == '__main__':
    # Config 검증
    try:
        Config.validate()
    except ValueError as e:
        print(f"설정 오류: {e}")
        exit(1)
    
    print("🚌 Busz 백엔드 서버 시작")
    print(f"WebSocket 서버: http://{Config.HOST}:{Config.PORT}")
    print(f"테스트 페이지: http://{Config.HOST}:{Config.PORT}/test")
    
    # SocketIO로 실행
    socketio.run(
        app,
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
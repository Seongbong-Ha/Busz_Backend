from flask import Flask, jsonify, request
from config import Config
from services.bis_service import BISService

# Flask 앱 초기화
app = Flask(__name__)
app.config.from_object(Config)

# 서비스 초기화
bis_service = BISService()

@app.route('/')
def home():
    """홈 - 서버 상태 확인"""
    return jsonify({
        'message': 'BUS API 서버가 실행 중입니다',
        'status': 'running'
    })
    
@app.route('/api/test-bis')
def test_bis_connection():
    """BIS API 테스트"""
    result = bis_service.test_connection()
    return jsonify(result)
    
if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
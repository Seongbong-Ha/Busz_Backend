from flask import Flask, jsonify, request
from config import Config

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
    
    
if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
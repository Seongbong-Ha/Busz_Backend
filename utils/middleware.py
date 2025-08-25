from flask import request, jsonify
from werkzeug.exceptions import BadRequest


def handle_before_request():
    """모든 요청 전처리"""
    print(f"📥 {request.method} {request.path}")
    print(f"Host: {request.headers.get('host', 'Unknown')}")
    print(f"User-Agent: {request.headers.get('user-agent', 'Unknown')}")
    
    print("✅ 모든 요청 허용")
    return None


def handle_after_request(response):
    """모든 응답에 헤더 추가"""
    if response.content_type and response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    
    if request.path.startswith('/socket.io/'):
        return response
    
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


def register_error_handlers(app):
    """에러 핸들러 등록"""
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/socket.io/'):
            return None
            
        from utils.constants import AVAILABLE_ENDPOINTS
        return jsonify({
            'success': False,
            'error': '요청한 엔드포인트를 찾을 수 없습니다',
            'error_code': 'NOT_FOUND',
            'path': request.path,
            'available_endpoints': AVAILABLE_ENDPOINTS
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': '서버 내부 오류가 발생했습니다',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        print(f"🔧 Werkzeug 400 에러 우회: {request.path}")
        print(f"User-Agent: {request.headers.get('user-agent', 'Unknown')}")
        
        return jsonify({
            'success': True,
            'message': 'Busz Backend API 서버 (400 우회)',
            'status': 'running',
            'path': request.path,
            'bypassed': True
        }), 200

    @app.errorhandler(400)
    def bad_request(error):
        print(f"🔧 일반 400 에러 우회: {request.path}")
        return jsonify({
            'success': True,
            'message': 'Busz Backend API 서버',
            'status': 'running'
        }), 200
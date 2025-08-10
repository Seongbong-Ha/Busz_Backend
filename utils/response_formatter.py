from datetime import datetime
from flask import jsonify

def success_response(data, message=None):
    """성공 응답 표준화"""
    response = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }
    
    # data가 dict이면 직접 병합, 아니면 data 키에 저장
    if isinstance(data, dict):
        response.update(data)
    else:
        response['data'] = data
        
    if message:
        response['message'] = message
    
    return jsonify(response)

def error_response(message, error_code=None, data=None):
    """에러 응답 표준화"""
    response = {
        'success': False,
        'error': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if error_code:
        response['error_code'] = error_code
        
    if data:
        response.update(data)
    
    return jsonify(response)
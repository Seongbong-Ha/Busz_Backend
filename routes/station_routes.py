from flask import Blueprint, request
from services.station_services import StationService
from utils.response_formatter import success_response, error_response
from utils.exceptions import TAGOAPIError
from websocket.manager import session_manager

station_bp = Blueprint('station', __name__)
station_service = StationService()

@station_bp.route('/station/buses', methods=['POST'])
def get_station_all_buses():
    """
    플로우 2: 전체 버스 정보 조회 (세션 기반)
    
    Request: 빈 POST 요청
    Response: 세션 정보 기반 전체 버스 정보
    """
    try:
        # WebSocket 세션 ID 확인 (여러 방법 중 선택 가능)
        session_id = request.headers.get('X-Session-ID')
        
        # 임시: request.sid 사용 (실제로는 앱에서 세션 ID 전달 필요)
        if not session_id:
            session_id = getattr(request, 'sid', None)
        
        # 활성 세션 확인
        if not session_manager.is_session_valid_for_flow2(session_id):
            return error_response(
                '활성 모니터링 세션이 없습니다. 플로우 1을 먼저 시작해주세요.',
                'NO_ACTIVE_SESSION'
            ), 401
        
        # 세션에서 정류소 정보 가져오기
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            return error_response(
                '세션 정보를 찾을 수 없습니다.',
                'SESSION_NOT_FOUND'
            ), 401
        
        # 전체 버스 정보 조회 (세션 정보 활용)
        result = station_service.get_all_buses_from_session(session_info)
        
        return success_response(result)
        
    except TAGOAPIError as e:
        return error_response(
            f'버스 정보 조회 실패: {str(e)}',
            'TAGO_API_ERROR'
        ), 503
        
    except Exception as e:
        print(f"Error in get_station_all_buses: {e}")
        return error_response(
            '서버 내부 오류가 발생했습니다',
            'INTERNAL_SERVER_ERROR'
        ), 500
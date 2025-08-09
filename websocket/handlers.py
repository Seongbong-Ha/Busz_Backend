from flask import request
from flask_socketio import emit
from .manager import session_manager

def init_websocket_handlers(socketio):
    """WebSocket 이벤트 핸들러 등록"""
    
    @socketio.on('connect')
    def handle_connect():
        print(f'클라이언트 연결됨: {request.sid}')
        emit('connected', {
            'message': '서버에 연결되었습니다',
            'session_id': request.sid
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'클라이언트 연결 해제됨: {request.sid}')
        session_manager.stop_session(request.sid)

    @socketio.on('start_bus_monitoring')
    def handle_start_monitoring(data):
        """
        버스 실시간 모니터링 시작
        
        data = {
            "lat": 37.497928,
            "lng": 127.027583,
            "bus_number": "9201",
            "interval": 30
        }
        """
        try:
            session_id = request.sid
            lat = data.get('lat')
            lng = data.get('lng')
            bus_number = data.get('bus_number')
            interval = data.get('interval', 30)
            
            # 입력값 검증
            if not all([lat, lng, bus_number]):
                emit('error', {'message': '위도, 경도, 버스번호가 모두 필요합니다'})
                return
            
            if not isinstance(interval, int) or interval < 10:
                interval = 30  # 최소 10초, 기본 30초
            
            # 세션 생성
            if session_manager.create_session(session_id, lat, lng, bus_number, interval):
                # 모니터링 시작
                if session_manager.start_monitoring(session_id, socketio):
                    emit('monitoring_started', {
                        'message': f'{bus_number}번 버스 실시간 모니터링을 시작합니다',
                        'bus_number': bus_number,
                        'interval': interval,
                        'session_id': session_id
                    })
                else:
                    emit('error', {'message': '모니터링 시작에 실패했습니다'})
            else:
                emit('error', {'message': '세션 생성에 실패했습니다'})
                
        except Exception as e:
            emit('error', {'message': f'모니터링 시작 실패: {str(e)}'})

    @socketio.on('stop_bus_monitoring')
    def handle_stop_monitoring():
        """버스 모니터링 중단"""
        session_id = request.sid
        
        if session_manager.stop_session(session_id):
            emit('monitoring_stopped', {
                'message': '버스 모니터링이 중단되었습니다',
                'session_id': session_id
            })
        else:
            emit('error', {'message': '활성 모니터링이 없습니다'})

    @socketio.on('get_session_status')
    def handle_get_status():
        """현재 세션 상태 조회"""
        session_id = request.sid
        session_info = session_manager.get_session_info(session_id)
        
        if session_info:
            emit('session_status', {
                'active': True,
                'bus_number': session_info['bus_number'],
                'interval': session_info['interval'],
                'session_id': session_id
            })
        else:
            emit('session_status', {
                'active': False,
                'session_id': session_id
            })

    @socketio.on('get_server_stats')
    def handle_get_stats():
        """서버 통계 조회 (관리자용)"""
        emit('server_stats', {
            'active_sessions': session_manager.get_active_sessions_count(),
            'timestamp': str(datetime.now())
        })

    print("WebSocket 핸들러 등록 완료")
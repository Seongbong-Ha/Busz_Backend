import threading
from typing import Dict, Optional
from .workers import BusMonitoringWorker

class SessionManager:
    """WebSocket 세션 및 모니터링 워커 관리"""
    
    def __init__(self):
        self.active_sessions: Dict[str, dict] = {}
        self.monitoring_workers: Dict[str, BusMonitoringWorker] = {}
        self._lock = threading.Lock()
    
    def create_session(self, session_id: str, lat: float, lng: float, 
                      bus_number: str, interval: int = 30) -> bool:
        """새 모니터링 세션 생성"""
        with self._lock:
            # 기존 세션이 있다면 중단
            if session_id in self.active_sessions:
                self.stop_session(session_id)
            
            # 세션 정보 저장
            self.active_sessions[session_id] = {
                'lat': lat,
                'lng': lng,
                'bus_number': bus_number,
                'interval': interval,
                'active': True
            }
            
            return True
    
    def start_monitoring(self, session_id: str, socketio) -> bool:
        """모니터링 워커 시작"""
        if session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        
        # 워커 생성 및 시작
        worker = BusMonitoringWorker(
            session_id=session_id,
            lat=session_data['lat'],
            lng=session_data['lng'],
            bus_number=session_data['bus_number'],
            interval=session_data['interval'],
            socketio=socketio,
            session_manager=self
        )
        
        self.monitoring_workers[session_id] = worker
        worker.start()
        
        return True
    
    def stop_session(self, session_id: str) -> bool:
        """세션 중단"""
        with self._lock:
            stopped = False
            
            # 워커 중단
            if session_id in self.monitoring_workers:
                worker = self.monitoring_workers[session_id]
                worker.stop()
                del self.monitoring_workers[session_id]
                stopped = True
            
            # 세션 정보 삭제
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                stopped = True
            
            return stopped
    
    def is_session_active(self, session_id: str) -> bool:
        """세션 활성 상태 확인"""
        return (session_id in self.active_sessions and 
                self.active_sessions[session_id].get('active', False))
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """세션 정보 조회"""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions_count(self) -> int:
        """활성 세션 수 조회"""
        return len(self.active_sessions)
    
    def is_session_valid_for_flow2(self, session_id):
        """플로우 2 호출 가능한 세션인지 확인"""
        if not session_id:
            return False
            
        return (session_id in self.active_sessions and 
                self.active_sessions[session_id].get('active', False))
    
    def get_session_station_info(self, session_id):
        """세션의 정류소 정보 반환"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].get('station_info')
        return None
    
    def update_session_station_info(self, session_id, station_info):
        """세션에 정류소 정보 저장 """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['station_info'] = station_info

# 글로벌 세션 매니저 인스턴스
session_manager = SessionManager()
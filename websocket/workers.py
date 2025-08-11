import threading
import time
from datetime import datetime
from typing import Optional
from config import Config
from apis.tago_api import TAGOAPIClient

class BusMonitoringWorker:
    """백그라운드 버스 모니터링 워커"""
    
    def __init__(self, session_id: str, lat: float, lng: float, 
                 bus_number: str, interval: int, socketio, session_manager):
        self.session_id = session_id
        self.lat = lat
        self.lng = lng
        self.bus_number = bus_number
        self.interval = interval
        self.socketio = socketio
        self.session_manager = session_manager
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # API 클라이언트 초기화
        self.client = TAGOAPIClient(
            api_key=Config.TAGO_API_KEY,
            base_url=Config.TAGO_BASE_URL
        )
    
    def start(self):
        """워커 시작"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop)
        self.thread.daemon = True
        self.thread.start()
        print(f'모니터링 워커 시작: {self.session_id} - {self.bus_number}번')
    
    def stop(self):
        """워커 중단"""
        self.running = False
        print(f'모니터링 워커 중단: {self.session_id} - {self.bus_number}번')
    
    def _worker_loop(self):
        """메인 워커 루프"""
        while self.running and self.session_manager.is_session_active(self.session_id):
            try:
                # 버스 정보 조회 및 업데이트 전송
                update_data = self._get_bus_update()
                
                if update_data:
                    self.socketio.emit('bus_update', update_data, room=self.session_id)
                
                # 다음 업데이트까지 대기
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                print(f'워커 에러 ({self.session_id}): {e}')
                self.socketio.emit('error', {
                    'message': f'모니터링 오류: {str(e)}'
                }, room=self.session_id)
                break
        
        print(f'모니터링 워커 종료: {self.session_id}')
    
    def _get_bus_update(self) -> Optional[dict]:
        """버스 정보 업데이트 데이터 생성"""
        try:
            # 1. 현재 정류소 찾기
            stations = self.client.get_stations_by_location(lng=self.lng, lat=self.lat)
            if not stations:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'error': '주변에 정류소가 없습니다'
                }
            
            current_station, _ = self.client.find_current_station(self.lat, self.lng, stations)
            if not current_station:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'error': '현재 정류소를 찾을 수 없습니다'
                }
            
            # 2. 특정 버스 정보 조회
            specific_buses = self.client.get_specific_bus_arrival(
                station_id=current_station['station_id'],
                city_code=current_station['city_code'],
                target_bus_number=self.bus_number
            )
            
            # 3. 업데이트 데이터 구성
            timestamp = datetime.now().isoformat()
            
            if specific_buses:
                fastest_bus = self.client.find_fastest_bus(specific_buses)
                
                if fastest_bus:
                    formatted_time = self.client.format_arrival_time(fastest_bus['arrival_time'])
                    
                    return {
                        'timestamp': timestamp,
                        'bus_found': True,
                        'station_name': current_station['station_name'],
                        'station_id': current_station['station_id'],
                        'bus_number': self.bus_number,
                        'arrival_time': fastest_bus['arrival_time'],
                        'arrival_time_formatted': formatted_time,
                        'remaining_stations': fastest_bus['remaining_stations'],
                        'vehicle_type': fastest_bus['vehicle_type'],
                        'route_type': fastest_bus['route_type'],
                        'total_buses': len(specific_buses)
                    }
            
            # 버스를 찾지 못한 경우
            return {
                'timestamp': timestamp,
                'bus_found': False,
                'station_name': current_station['station_name'],
                'station_id': current_station['station_id'],
                'bus_number': self.bus_number,
                'message': f'{self.bus_number}번 버스를 찾을 수 없습니다'
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': f'버스 정보 조회 실패: {str(e)}'
            }
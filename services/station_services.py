from apis.tago_api import TAGOAPIClient
from config import Config
from datetime import datetime

class StationService:
    """정류소 관련 비즈니스 로직 (플로우 2용)"""
    
    def __init__(self):
        self.client = TAGOAPIClient(
            api_key=Config.TAGO_API_KEY,
            base_url=Config.TAGO_BASE_URL
        )
    
    def get_all_buses_from_session(self, session_info):
        """
        세션 정보를 활용한 전체 버스 정보 조회 (플로우 2 메인)
        
        Args:
            session_info (dict): WebSocket 세션 정보
            
        Returns:
            dict: 전체 버스 정보
        """
        # 세션에서 위치 정보 추출
        lat = session_info.get('lat')
        lng = session_info.get('lng')
        
        if not lat or not lng:
            raise Exception('세션에 위치 정보가 없습니다')
        
        # 1. 현재 정류소 찾기 (세션 정보 재활용 가능하면 재활용)
        if 'station_info' in session_info:
            # 세션에 정류소 정보가 이미 있으면 재사용
            current_station = session_info['station_info']
        else:
            # 없으면 새로 조회
            stations = self.client.get_stations_by_location(lng=lng, lat=lat)
            if not stations:
                raise Exception('주변에 정류소가 없습니다')
                
            current_station, _ = self.client.find_current_station(lat, lng, stations)
            if not current_station:
                raise Exception('현재 정류소를 찾을 수 없습니다')
        
        # 2. 전체 버스 정보 조회 (route_id=None → 전체 버스)
        all_buses = self.client.get_bus_arrival_info(
            station_id=current_station['station_id'],
            city_code=current_station['city_code']
        )
        
        # 3. 간소화 데이터 가공 (버스 번호 + 도착시간만)
        processed_buses = self._process_buses_simple(all_buses)
        
        # 4. 응답 데이터 구성
        return {
            'timestamp': datetime.now().isoformat(),
            'station': self._format_station_info(current_station, lat, lng),
            'buses': processed_buses,
            'total_count': len(processed_buses)
        }
    
    def _process_buses_simple(self, buses):
        """버스 데이터 간소화 (번호 + 도착시간만)"""
        processed = []
        for bus in buses:
            processed_bus = {
                'route_name': bus['route_name'],    # 버스 번호
                'arrival_time': bus['arrival_time'] # 도착 시간(초)
            }
            processed.append(processed_bus)
        
        # 도착 시간순 정렬
        processed.sort(key=lambda x: x['arrival_time'] if x['arrival_time'] > 0 else float('inf'))
        return processed
    
    def _format_station_info(self, station, user_lat, user_lng):
        """정류소 정보 포맷팅"""
        return {
            'station_name': station['station_name'],
            'latitude': station['latitude'],
            'longitude': station['longitude'],
            'distance_from_user': round(self.client.calculate_distance(
                user_lat, user_lng, station['latitude'], station['longitude']
            ))
        }
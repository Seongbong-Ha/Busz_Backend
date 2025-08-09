# apis/tago_api.py

import requests
import json
import math
from typing import List, Dict, Optional, Tuple
from utils.exceptions import TAGOAPIError
from utils.constants import TAGO_API_CONFIG


class TAGOAPIClient:
    """TAGO API 클라이언트"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or "http://apis.data.go.kr/1613000"
        self.session = requests.Session()
        
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """API 요청 실행"""
        # 공통 파라미터 추가
        params.update({
            'serviceKey': self.api_key,
            '_type': 'json'
        })
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # TAGO API 응답 구조 확인
            if 'response' not in data:
                raise TAGOAPIError("Invalid API response structure")
                
            if data['response']['header']['resultCode'] != '00':
                error_msg = data['response']['header']['resultMsg']
                raise TAGOAPIError(f"API Error: {error_msg}")
                
            return data['response']['body']
            
        except requests.RequestException as e:
            raise TAGOAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise TAGOAPIError(f"JSON decode error: {str(e)}")
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """두 GPS 좌표 간 거리 계산 (미터)"""
        R = 6371000  # 지구 반지름 (미터)
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def find_current_station(self, user_lat: float, user_lng: float, stations: List[Dict]) -> Tuple[Optional[Dict], str]:
        """현재 위치에서 가장 가까운 정류소 찾기"""
        if not stations:
            return None, "주변에 정류소가 없습니다"
        
        # 가장 가까운 정류소 찾기
        closest_station = min(stations, 
            key=lambda s: self.calculate_distance(user_lat, user_lng, s['latitude'], s['longitude']))
        
        distance = self.calculate_distance(user_lat, user_lng, closest_station['latitude'], closest_station['longitude'])
        
        # 거리 검증
        if distance > 50:  # 50m 이상이면 경고
            return closest_station, f"가장 가까운 정류소가 {distance:.0f}m 떨어져 있습니다. 정류소로 이동해주세요."
        else:
            return closest_station, f"현재 위치: {closest_station['station_name']} ({distance:.0f}m)"
    
    def get_stations_by_location(self, lng: float, lat: float) -> List[Dict]:
        """
        GPS 좌표 기반 주변 정류소 검색
        
        Args:
            lng (float): 경도 (longitude) - gpsLong
            lat (float): 위도 (latitude) - gpsLati
            
        Returns:
            List[Dict]: 정류소 정보 리스트
        """
        endpoint = "/BusSttnInfoInqireService/getCrdntPrxmtSttnList"
        
        params = {
            'gpsLati': lat,    # GPS Y좌표 (위도) - 필수
            'gpsLong': lng,    # GPS X좌표 (경도) - 필수  
            'pageNo': 1,       # 페이지 번호 - 옵션 (기본 1)
            'numOfRows': 10    # 한 페이지 결과 수 - 옵션 (기본 10)
        }
        
        try:
            result = self._make_request(endpoint, params)
            
            # items가 없을 경우 빈 리스트 반환
            if 'items' not in result or not result['items']:
                return []
                
            stations = result['items']['item']
            
            # 단일 항목인 경우 리스트로 변환
            if isinstance(stations, dict):
                stations = [stations]
                
            return [self._format_station_info(station) for station in stations]
            
        except TAGOAPIError:
            raise
        except Exception as e:
            raise TAGOAPIError(f"Unexpected error in get_stations_by_location: {str(e)}")
    
    def get_station_by_name(self, station_name: str, city_code: str = None) -> List[Dict]:
        """
        정류소명으로 정류소 검색
        
        Args:
            station_name (str): 정류소명
            city_code (str): 도시코드 (선택사항)
            
        Returns:
            List[Dict]: 정류소 정보 리스트
        """
        endpoint = "/BusSttnInfoInqireService/getSttnInfoBySttnNm"
        
        params = {
            'sttnNm': station_name
        }
        
        if city_code:
            params['cityCode'] = city_code
            
        try:
            result = self._make_request(endpoint, params)
            
            if 'items' not in result or not result['items']:
                return []
                
            stations = result['items']['item']
            
            if isinstance(stations, dict):
                stations = [stations]
                
            return [self._format_station_info(station) for station in stations]
            
        except TAGOAPIError:
            raise
        except Exception as e:
            raise TAGOAPIError(f"Unexpected error in get_station_by_name: {str(e)}")
    
    def get_bus_arrival_info(self, station_id: str, city_code: str, route_id: str = None) -> List[Dict]:
        """
        정류소별 버스 도착 정보 조회
        
        Args:
            station_id (str): 정류소 ID
            city_code (str): 도시코드 (필수)
            route_id (str): 노선 ID (선택사항)
            
        Returns:
            List[Dict]: 버스 도착 정보 리스트
        """
        endpoint = "/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList"
        
        params = {
            'cityCode': city_code,  # 도시코드 필수
            'nodeId': station_id    # 정류소ID (nodeId로 변경)
        }
        
        if route_id:
            params['routeId'] = route_id
            
        try:
            result = self._make_request(endpoint, params)
            
            if 'items' not in result or not result['items']:
                return []
                
            arrivals = result['items']['item']
            
            if isinstance(arrivals, dict):
                arrivals = [arrivals]
                
            return [self._format_arrival_info(arrival) for arrival in arrivals]
            
        except TAGOAPIError:
            raise
        except Exception as e:
            raise TAGOAPIError(f"Unexpected error in get_bus_arrival_info: {str(e)}")
    
    def get_specific_bus_arrival(self, station_id: str, city_code: str, target_bus_number: str) -> List[Dict]:
        """
        특정 버스 번호의 도착 정보만 조회
        
        Args:
            station_id (str): 정류소 ID
            city_code (str): 도시코드
            target_bus_number (str): 찾고자 하는 버스 번호 (예: "9200", "146")
            
        Returns:
            List[Dict]: 해당 버스 번호의 도착 정보 리스트
        """
        try:
            # 전체 버스 도착 정보 조회
            all_arrivals = self.get_bus_arrival_info(station_id, city_code)
            
            # 특정 버스 번호만 필터링 (문자열로 변환해서 비교)
            filtered_buses = [
                bus for bus in all_arrivals 
                if str(bus['route_name']).strip() == str(target_bus_number).strip()
            ]
            
            return filtered_buses
            
        except Exception as e:
            raise TAGOAPIError(f"Specific bus arrival query failed: {str(e)}")
    
    def find_fastest_bus(self, arrivals: List[Dict]) -> Optional[Dict]:
        """
        도착 정보 리스트에서 가장 빨리 오는 버스 찾기
        
        Args:
            arrivals (List[Dict]): 버스 도착 정보 리스트
            
        Returns:
            Optional[Dict]: 가장 빨리 오는 버스 정보 (없으면 None)
        """
        if not arrivals:
            return None
        
        # arrival_time이 유효한 버스들만 필터링 (0보다 큰 값)
        valid_arrivals = [bus for bus in arrivals if bus.get('arrival_time', 0) > 0]
        
        if not valid_arrivals:
            return None
            
        return min(valid_arrivals, key=lambda bus: bus['arrival_time'])
    
    def format_arrival_time(self, seconds: int) -> str:
        """
        초 단위 시간을 읽기 쉬운 형태로 변환
        
        Args:
            seconds (int): 초 단위 시간
            
        Returns:
            str: "3분 31초" 형태의 문자열
        """
        # 안전하게 정수로 변환
        try:
            seconds = int(seconds)
        except (ValueError, TypeError):
            return "정보 없음"
            
        if seconds <= 0:
            return "정보 없음"
            
        if seconds < 60:
            return f"{seconds}초"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if remaining_seconds == 0:
            return f"{minutes}분"
        else:
            return f"{minutes}분 {remaining_seconds}초"
    
    def get_route_info_by_route_id(self, route_id: str) -> Dict:
        """
        노선 ID로 노선 정보 조회
        
        Args:
            route_id (str): 노선 ID
            
        Returns:
            Dict: 노선 정보
        """
        endpoint = "/BusRouteInfoInqireService/getRouteInfoIiem"
        
        params = {
            'routeId': route_id
        }
        
        try:
            result = self._make_request(endpoint, params)
            
            if 'items' not in result or not result['items']:
                return {}
                
            route_info = result['items']['item']
            
            if isinstance(route_info, list):
                route_info = route_info[0] if route_info else {}
                
            return self._format_route_info(route_info)
            
        except TAGOAPIError:
            raise
        except Exception as e:
            raise TAGOAPIError(f"Unexpected error in get_route_info_by_route_id: {str(e)}")
    
    def _format_station_info(self, station: Dict) -> Dict:
        """정류소 정보 포맷팅 - TAGO API 응답 필드 기준"""
        return {
            'station_id': station.get('nodeid', ''),      # 정류소ID
            'station_name': station.get('nodenm', ''),    # 정류소명  
            'city_code': station.get('citycode', ''),     # 도시코드
            'latitude': float(station.get('gpslati', 0)), # 정류소 Y좌표 (위도)
            'longitude': float(station.get('gpslong', 0)) # 정류소 X좌표 (경도)
        }
    
    def _format_arrival_info(self, arrival: Dict) -> Dict:
        """버스 도착 정보 포맷팅"""
        # arrival_time을 안전하게 정수로 변환
        try:
            arrival_time = int(arrival.get('arrtime', 0))
        except (ValueError, TypeError):
            arrival_time = 0
            
        # remaining_stations도 안전하게 정수로 변환
        try:
            remaining_stations = int(arrival.get('arrprevstationcnt', 0))
        except (ValueError, TypeError):
            remaining_stations = 0
            
        return {
            'station_id': arrival.get('nodeid', ''),        # 정류소ID
            'station_name': arrival.get('nodenm', ''),      # 정류소명
            'route_id': arrival.get('routeid', ''),         # 노선ID
            'route_name': arrival.get('routeno', ''),       # 노선번호
            'route_type': arrival.get('routetp', ''),       # 노선유형
            'remaining_stations': remaining_stations,       # 남은 정류장 수
            'vehicle_type': arrival.get('vehicletp', ''),   # 차량유형
            'arrival_time': arrival_time,                   # 도착예상시간(초)
        }
    
    def _format_route_info(self, route: Dict) -> Dict:
        """노선 정보 포맷팅"""
        return {
            'route_id': route.get('routeid', ''),
            'route_name': route.get('routeno', ''),
            'route_type': route.get('routetp', ''),
            'start_station': route.get('startstationname', ''),
            'end_station': route.get('endstationname', ''),
            'up_first_time': route.get('upfirsttime', ''),
            'up_last_time': route.get('uplasttime', ''),
            'down_first_time': route.get('downfirsttime', ''),
            'down_last_time': route.get('downlasttime', ''),
            'peek_alloc': route.get('peekalloc', ''),  # 평시 배차간격
            'npeek_alloc': route.get('npeekalloc', ''),  # 비평시 배차간격
        }

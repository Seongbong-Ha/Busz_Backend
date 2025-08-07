import requests
import xml.etree.ElementTree as ET
from config import Config

class BISService:
    """서울시 BIS API 서비스"""
    
    def __init__(self):
        self.api_key = Config.BIS_API_KEY
        self.base_url = Config.BIS_BASE_URL
        print(f"초기화 완료")
    
    def get_station_by_uid(self, ars_id):
        """정류소 도착 정보 조회"""
        pass
    
    def get_station_by_position(self, lat, lon, radius=500):
        """좌표 기반 근처 정류소 조회"""
        pass
    
    def get_route_by_station(self, ars_id):
        """정류소 경유 노선 조회"""
        pass
    
    def get_station_by_route(self, bus_route_id):
        """노선별 경유 정류소 조회"""
        pass
    
    def test_connection(self):
        """API 연결 테스트 - 간단한 정류소 조회"""
        try:
            # 테스트용 정류소 ID (서울역 버스환승센터)
            test_ars_id = "02189"
            
            url = f"{self.base_url}/stationinfo/getStationByUid"
            params = {
                'serviceKey': self.api_key,
                'arsId': test_ars_id
            }
            
            response = requests.get(url, params=params)
            
            return {
                'status_code': response.status_code,
                'api_key_preview': self.api_key[:10] + "...",
                'url': url,
                'test_station_id': test_ars_id,
                'response_preview': response.text[:300],
                'success': response.status_code == 200
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
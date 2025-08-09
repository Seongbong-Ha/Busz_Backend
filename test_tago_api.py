# test_tago_api.py
import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apis.tago_api import TAGOAPIClient  # app. 제거
from config import Config

def test_stations_by_location():
    """GPS 좌표 기반 정류소 검색 및 현재 정류소 찾기 테스트"""
    print("=== TAGO API 테스트 시작 ===")
    
    try:
        # API 키 확인
        if not Config.TAGO_API_KEY:
            raise ValueError("TAGO_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        # API 클라이언트 초기화
        client = TAGOAPIClient(
            api_key=Config.TAGO_API_KEY,
            base_url=Config.TAGO_BASE_URL
        )
        
        # 서울 강남역 근처 좌표 (예시)
        lng = 127.027583  # 경도
        lat = 37.497928   # 위도
        
        print(f"현재 위치: 경도={lng}, 위도={lat}")
        print("주변 정류소 검색 중...")
        
        # API 호출 - 주변 정류소 검색
        stations = client.get_stations_by_location(lng=lng, lat=lat)
        
        print(f"\n검색 결과: {len(stations)}개 정류소 발견")
        print("-" * 50)
        
        # 모든 정류소 목록 출력
        for i, station in enumerate(stations, 1):
            distance = client.calculate_distance(lat, lng, station['latitude'], station['longitude'])
            print(f"{i}. {station['station_name']} ({distance:.0f}m)")
            print(f"   ID: {station['station_id']}")
            print(f"   도시코드: {station['city_code']}")
            print(f"   좌표: ({station['longitude']}, {station['latitude']})")
            print()
        
        # 현재 정류소 찾기
        print("=" * 50)
        print("현재 정류소 찾기...")
        
        current_station, message = client.find_current_station(lat, lng, stations)
        
        print(f"결과: {message}")
        
        if current_station:
            print(f"선택된 정류소: {current_station['station_name']}")
            print(f"정류소 ID: {current_station['station_id']}")
            
            # 버스 도착 정보 조회
            print("\n" + "=" * 50)
            print("버스 도착 정보 조회 중...")
            
            try:
                arrival_info = client.get_bus_arrival_info(
                    station_id=current_station['station_id'],
                    city_code=current_station['city_code']  # 도시코드 추가
                )
                
                if arrival_info:
                    print(f"\n{current_station['station_name']} 정류소 버스 도착 정보:")
                    print("-" * 50)
                    
                    for i, bus in enumerate(arrival_info, 1):
                        print(f"{i}. {bus['route_name']}번 버스")
                        print(f"   노선 ID: {bus['route_id']}")
                        print(f"   노선 유형: {bus['route_type']}")
                        print(f"   남은 정류장: {bus['remaining_stations']}개")
                        print(f"   도착 예상 시간: {bus['arrival_time']}초 ({bus['arrival_time']//60}분 {bus['arrival_time']%60}초)")
                        print(f"   차량 유형: {bus['vehicle_type']}")
                        print()
                else:
                    print("현재 운행 중인 버스가 없습니다.")
                
                # 특정 버스 검색 테스트
                print("\n" + "=" * 50)
                print("특정 버스 검색 테스트...")
                
                target_bus = "9201"  # 실제 존재하는 버스로 변경
                print(f"{target_bus}번 버스 도착 정보 검색 중...")
                
                # 디버깅: 현재 있는 버스 번호들 출력
                print("현재 정류소에 있는 모든 버스 번호들:")
                for bus in arrival_info:
                    print(f"   '{bus['route_name']}' (타입: {type(bus['route_name'])})")
                print()
                
                specific_buses = client.get_specific_bus_arrival(
                    station_id=current_station['station_id'],
                    city_code=current_station['city_code'],
                    target_bus_number=target_bus
                )
                
                if specific_buses:
                    print(f"\n{target_bus}번 버스 도착 정보:")
                    print("-" * 30)
                    
                    for i, bus in enumerate(specific_buses, 1):
                        formatted_time = client.format_arrival_time(bus['arrival_time'])
                        print(f"{i}번째 {bus['route_name']}번 버스:")
                        print(f"   도착 시간: {formatted_time}")
                        print(f"   남은 정류장: {bus['remaining_stations']}개")
                        print(f"   차량 유형: {bus['vehicle_type']}")
                        print()
                    
                    # 가장 빨리 오는 버스 찾기
                    fastest_bus = client.find_fastest_bus(specific_buses)
                    if fastest_bus:
                        fastest_time = client.format_arrival_time(fastest_bus['arrival_time'])
                        print(f"🚌 가장 빨리 오는 {target_bus}번 버스: {fastest_time} 후 도착")
                        
                        # 시각장애인 음성 안내 형태
                        if fastest_bus['arrival_time'] < 300:  # 5분 이내
                            urgency = "곧"
                        elif fastest_bus['arrival_time'] < 600:  # 10분 이내  
                            urgency = "조금 기다리시면"
                        else:
                            urgency = "시간이 좀 걸리지만"
                            
                        voice_message = f"{urgency} {target_bus}번 버스가 {fastest_time} 후에 도착합니다."
                        print(f"🔊 음성 안내: \"{voice_message}\"")
                else:
                    print(f"{target_bus}번 버스는 현재 이 정류소로 오지 않습니다.")
                    
                    # 다른 버스 추천
                    if arrival_info:
                        print("\n대신 이용 가능한 버스들:")
                        available_buses = set([str(bus['route_name']).strip() for bus in arrival_info])
                        for bus_name in sorted(available_buses, key=lambda x: (len(x), x)):  # 길이순, 알파벳순 정렬
                            print(f"   - {bus_name}번")
                    
            except Exception as e:
                print(f"버스 도착 정보 조회 실패: {e}")
        else:
            print("정류소를 찾을 수 없어서 버스 정보를 조회할 수 없습니다.")
        
    except Exception as e:
        print(f"에러 발생: {e}")
        return False
        
    print("\n=== 테스트 완료 ===")
    return True

if __name__ == "__main__":
    test_stations_by_location()
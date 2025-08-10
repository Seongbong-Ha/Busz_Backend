# 🚌 Busz Backend

시각장애인 버스 탑승 지원 시스템의 백엔드 서버 (데이터 허브)

## 📋 개요

Busz Backend은 실시간 버스 정보를 수집하고 가공하여 모바일 앱에 제공하는 **데이터 허브** 역할을 담당합니다.

### 🏗️ 아키텍처
```
📱 모바일 앱              🖥️ 백엔드 서버              🚌 공공 API
    ↓                       ↓                       ↓
┌─────────────┐      ┌─────────────────┐      ┌──────────────┐
│ 사용자 경험  │ ←→   │   데이터 허브    │ ←→   │ TAGO API     │
│ • CV 처리   │      │ • 실시간 수집   │      │ • BIS API    │
│ • 음성처리  │      │ • 데이터 가공   │      │ • 교통정보   │
│ • 센서활용  │      │ • 세션 관리     │      │              │
│ • 햅틱제어  │      │ • 상태 추적     │      │              │
└─────────────┘      └─────────────────┘      └──────────────┘
```

## 📱 프론트엔드 개발자용 API 문서

### 🌐 서버 정보
- **Base URL**: `http://localhost:8000` (개발환경)
- **Protocol**: HTTP/HTTPS + WebSocket
- **Data Format**: JSON
- **CORS**: 모든 Origin 허용 (개발환경)

### 🔄 통신 플로우

#### **전체 사용 흐름**
```
1. WebSocket 연결
2. 플로우 1: start_bus_monitoring (실시간 모니터링 시작)
3. 플로우 2: POST /api/station/buses (전체 버스 정보 조회)
4. 사용자가 원하는 시점에 stop_bus_monitoring
```

---

## 🔌 WebSocket API (플로우 1: 실시간 모니터링)

### 연결
```javascript
const socket = io('http://localhost:8000');
```

### 📤 클라이언트 → 서버 이벤트

#### `start_bus_monitoring` - 실시간 모니터링 시작
```javascript
socket.emit('start_bus_monitoring', {
    "lat": 37.497928,        // 위도 (필수)
    "lng": 127.027583,       // 경도 (필수)  
    "bus_number": "9201",    // 모니터링할 버스 번호 (필수)
    "interval": 30           // 업데이트 간격(초), 기본 30초
});
```

#### `stop_bus_monitoring` - 모니터링 중단
```javascript
socket.emit('stop_bus_monitoring');
```

#### `get_session_status` - 현재 상태 확인
```javascript
socket.emit('get_session_status');
```

### 📥 서버 → 클라이언트 이벤트

#### `connected` - 연결 완료
```javascript
socket.on('connected', (data) => {
    console.log(data.message);     // "서버에 연결되었습니다"
    console.log(data.session_id);  // WebSocket 세션 ID
});
```

#### `monitoring_started` - 모니터링 시작됨
```javascript
socket.on('monitoring_started', (data) => {
    console.log(data.message);      // "9201번 버스 실시간 모니터링을 시작합니다"
    console.log(data.bus_number);   // "9201"
    console.log(data.interval);     // 30
    console.log(data.session_id);   // 세션 ID (플로우 2에서 사용)
});
```

#### `bus_update` - 실시간 버스 정보 (핵심!)
```javascript
socket.on('bus_update', (data) => {
    if (data.bus_found) {
        // 버스 발견됨
        console.log(data.bus_number);              // "9201"
        console.log(data.arrival_time);            // 180 (초)
        console.log(data.arrival_time_formatted);  // "3분"
        console.log(data.remaining_stations);      // 2
        console.log(data.urgency);                 // "moderate"
        console.log(data.voice_message);           // "조금 기다리시면 9201번 버스가 3분 후에 도착합니다."
        
        // TTS로 음성 안내
        speak(data.voice_message);
        
    } else if (data.error) {
        // 에러 발생
        console.error(data.error);
        
    } else {
        // 버스를 찾지 못함
        console.log(data.message);  // "9201번 버스를 찾을 수 없습니다"
    }
});
```

#### `monitoring_stopped` - 모니터링 중단됨
```javascript
socket.on('monitoring_stopped', (data) => {
    console.log(data.message);  // "버스 모니터링이 중단되었습니다"
});
```

#### `session_status` - 세션 상태 응답
```javascript
socket.on('session_status', (data) => {
    console.log(data.active);      // true/false
    console.log(data.bus_number);  // "9201" (활성 시)
    console.log(data.interval);    // 30 (활성 시)
});
```

#### `error` - 에러 발생
```javascript
socket.on('error', (data) => {
    console.error(data.message);  // 에러 메시지
});
```

---

## 🌐 REST API (플로우 2: 전체 버스 정보)

### POST `/api/station/buses` - 전체 버스 정보 조회

**⚠️ 중요**: 플로우 1이 먼저 실행되어야 합니다!

#### Request
```http
POST /api/station/buses
Content-Type: application/json
X-Session-ID: <WebSocket 세션 ID>

{}
```

#### Success Response (200)
```json
{
    "success": true,
    "timestamp": "2025-01-10T15:30:45.123456",
    "station": {
        "station_name": "강남역",
        "latitude": 37.497928,
        "longitude": 127.027583,
        "distance_from_user": 25
    },
    "buses": [
        {
            "route_name": "9201",
            "arrival_time": 180
        },
        {
            "route_name": "146",
            "arrival_time": 420
        }
    ],
    "total_count": 2
}
```

#### Error Response (401) - 세션 없음
```json
{
    "success": false,
    "error": "활성 모니터링 세션이 없습니다. 플로우 1을 먼저 시작해주세요.",
    "error_code": "NO_ACTIVE_SESSION",
    "timestamp": "2025-01-10T15:30:45.123456"
}
```

#### Error Response (503) - API 오류
```json
{
    "success": false,
    "error": "버스 정보 조회 실패: TAGO API 오류",
    "error_code": "TAGO_API_ERROR",
    "timestamp": "2025-01-10T15:30:45.123456"
}
```

---

## 📋 기타 엔드포인트

### GET `/` - 서버 상태 확인
```json
{
    "success": true,
    "message": "Busz Backend API 서버",
    "status": "running",
    "version": "v1.0.0",
    "mobile_app_ready": true
}
```

### GET `/api` - API 정보
전체 API 구조와 사용법에 대한 상세 정보를 제공합니다.


## 📱 안드로이드 앱에서 받는 실제 데이터

### 🔌 **WebSocket 연결 시 받는 이벤트 순서**

#### **1. 연결 직후 (자동 발생)**
```json
// 'connected' 이벤트
{
    "message": "서버에 연결되었습니다",
    "session_id": "abc123def456"  // ⚠️ 중요: REST API에서 사용
}
```

#### **2. 모니터링 시작 요청 후**
```javascript
// 안드로이드에서 전송
socket.emit('start_bus_monitoring', {
    "lat": 37.497928,
    "lng": 127.027583,
    "bus_number": "9201", 
    "interval": 30
});
```

**즉시 받는 응답:**
```json
// 'monitoring_started' 이벤트
{
    "message": "9201번 버스 실시간 모니터링을 시작합니다",
    "bus_number": "9201",
    "interval": 30,
    "session_id": "abc123def456"
}
```

#### **3. 실시간 업데이트 (30초마다)**

**버스 발견된 경우:**
```json
// 'bus_update' 이벤트
{
    "timestamp": "2025-01-10T15:30:45.123456",
    "bus_found": true,
    "station_name": "강남역",
    "station_id": "station123",
    "bus_number": "9201",
    "arrival_time": 180,                    // 초 단위
    "arrival_time_formatted": "3분",
    "remaining_stations": 2,
    "vehicle_type": "일반버스",
    "route_type": "간선버스", 
    "urgency": "moderate",                  // "urgent", "moderate", "normal"
    "voice_message": "조금 기다리시면 9201번 버스가 3분 후에 도착합니다.",
    "total_buses": 1
}
```

**버스 못 찾은 경우:**
```json
// 'bus_update' 이벤트
{
    "timestamp": "2025-01-10T15:30:45.123456",
    "bus_found": false,
    "station_name": "강남역", 
    "station_id": "station123",
    "bus_number": "9201",
    "message": "9201번 버스를 찾을 수 없습니다"
}
```

**에러 발생한 경우:**
```json
// 'bus_update' 이벤트  
{
    "timestamp": "2025-01-10T15:30:45.123456",
    "error": "버스 정보 조회 실패: TAGO API 오류"
}
```

#### **4. 에러 상황**
```json
// 'error' 이벤트
{
    "message": "위도, 경도, 버스번호가 모두 필요합니다"
}
```

### 📋 **안드로이드 앱 데이터 처리 가이드**

#### **연결 흐름**
```
1. 소켓 연결 성공
   ↓
2. 'connected' 이벤트 수신 → session_id 저장 ⚠️
   ↓  
3. start_bus_monitoring 전송
   ↓
4. 'monitoring_started' 이벤트 수신 → 모니터링 시작 확인
   ↓
5. 30초마다 'bus_update' 이벤트 수신 (지속적)
   ↓
6. 필요시 REST API 호출 (session_id 사용)
```

#### **데이터 활용 방법**
- **session_id**: 반드시 저장하여 REST API 헤더에 사용
- **voice_message**: 바로 TTS로 음성 안내
- **urgency**: 
  - `"urgent"` (5분 이내) → 강한 알림
  - `"moderate"` (5-10분) → 보통 알림  
  - `"normal"` (10분 이상) → 약한 알림
- **arrival_time**: 초 단위이므로 분 변환 시 `arrival_time / 60`
- **bus_found**: false면 다른 버스 추천 로직 실행

---

## 🔧 개발 환경

### 의존성
- **Python**: 3.8+
- **Flask**: 3.1.1
- **Flask-SocketIO**: WebSocket 지원
- **Flask-CORS**: 모바일 앱 연동
- **requests**: HTTP API 호출

### 사용 중인 외부 API
- **TAGO API**: 전국 버스 정보 (서울 제외)

### 현재 제한사항
- 서울 지역 서비스 제외 (BIS API 이슈)
- TAGO API 키 필요 (공공데이터포털에서 발급)

---
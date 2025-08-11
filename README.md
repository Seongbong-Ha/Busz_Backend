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
│ • UI/UX     │      │ • 실시간 수집   │      │ • BIS API    │
│ • 음성처리  │      │ • 데이터 가공   │      │ • 교통정보   │
│ • 센서활용  │      │ • 세션 관리     │      │              │
│ • 햅틱제어  │      │ • 상태 추적     │      │              │
└─────────────┘      └─────────────────┘      └──────────────┘
```

## 🚀 API 명세서

### 🌐 서버 정보
- **Base URL**: `http://localhost:8000` (개발환경)
- **Protocol**: HTTP/HTTPS + WebSocket
- **Data Format**: JSON
- **CORS**: 모든 Origin 허용 (개발환경)

### 🔄 통신 플로우

#### **전체 사용 흐름**
```
1. WebSocket 연결 → 자동으로 connected 이벤트 수신
2. 플로우 1: start_bus_monitoring 전송 → 실시간 모니터링 시작
3. 플로우 2: POST /api/station/buses → 전체 버스 정보 조회
4. 사용자가 원하는 시점에 stop_bus_monitoring 전송
```

---

## 🔌 WebSocket API (플로우 1: 실시간 모니터링)

### 연결 정보
- **URL**: `ws://localhost:8000`
- **Protocol**: Socket.IO

### 🔄 **이벤트 플로우**

#### **1단계: 연결 (자동)**
```kotlin
// 안드로이드에서 연결만 하면
socket = IO.socket("https://your-server-url")
socket.connect()
```

#### **2단계: 연결 확인 (자동 수신)**
```json
// 서버가 자동으로 전송하는 이벤트
{
    "message": "서버에 연결되었습니다",
    "session_id": "abc123def456"  // ⚠️ 중요: 플로우 2에서 사용
}
```

#### **3단계: 모니터링 시작 (수동 전송)**
```json
// 앱에서 직접 전송해야 하는 이벤트
{
    "lat": 37.497928,        // 위도 (필수)
    "lng": 127.027583,       // 경도 (필수)  
    "bus_number": "9201",    // 모니터링할 버스 번호 (필수)
    "interval": 30           // 업데이트 간격(초), 기본 30초
}
```

#### **4단계: 모니터링 시작 확인 (자동 응답)**
```json
// 서버가 자동으로 응답하는 이벤트
{
    "message": "9201번 버스 실시간 모니터링을 시작합니다",
    "bus_number": "9201",
    "interval": 30,
    "session_id": "abc123def456"
}
```

#### **5단계: 실시간 버스 정보 (자동, 주기적)**
30초마다 자동으로 전송되는 이벤트:

**버스 발견된 경우:**
```json
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
    "route_type": "간선버스"
}
```

**버스 못 찾은 경우:**
```json
{
    "timestamp": "2025-01-10T15:30:45.123456",
    "bus_found": false,
    "station_name": "강남역",
    "bus_number": "9201", 
    "message": "9201번 버스를 찾을 수 없습니다"
}
```

### 📤 **앱에서 전송하는 이벤트들**

| 이벤트명 | 타이밍 | 매개변수 | 설명 |
|---------|--------|----------|------|
| `start_bus_monitoring` | 수동 | lat, lng, bus_number, interval | 실시간 모니터링 시작 |
| `stop_bus_monitoring` | 수동 | 없음 | 모니터링 중단 |
| `get_session_status` | 수동 | 없음 | 현재 상태 확인 |

### 📥 **서버에서 전송하는 이벤트들**

| 이벤트명 | 타이밍 | 설명 |
|---------|--------|------|
| `connected` | 연결 시 자동 | 연결 완료 + session_id 제공 |
| `monitoring_started` | start_bus_monitoring 응답 | 모니터링 시작 확인 |
| `bus_update` | 30초마다 자동 | 실시간 버스 정보 |
| `monitoring_stopped` | stop_bus_monitoring 응답 | 모니터링 중단 확인 |
| `session_status` | get_session_status 응답 | 현재 세션 상태 |
| `error` | 에러 발생 시 | 에러 메시지 |

---

## 🌐 REST API (플로우 2: 전체 버스 정보)

### POST `/api/station/buses` - 전체 버스 정보 조회

**⚠️ 중요 전제조건**: 
1. WebSocket이 연결되어 있어야 함
2. 플로우 1이 실행 중이어야 함 (`start_bus_monitoring` 이벤트 전송 완료)

#### 📤 앱 → 서버 요청 형식
```http
POST /api/station/buses
Content-Type: application/json
X-Session-ID: abc123def456  ← WebSocket connected 이벤트에서 받은 session_id

{}  ← 빈 JSON 객체 전송
```

#### 📥 서버 → 앱 응답 형식

**성공 응답 (200):**
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
            "arrival_time": 180      // 초 단위
        },
        {
            "route_name": "146", 
            "arrival_time": 420
        }
    ],
    "total_count": 2
}
```

**에러 응답 (401) - 세션 없음:**
```json
{
    "success": false,
    "error": "활성 모니터링 세션이 없습니다. 플로우 1을 먼저 시작해주세요.",
    "error_code": "NO_ACTIVE_SESSION"
}
```

---

## 💡 실제 사용 예시

### 🔄 **안드로이드 구현 예시**

```kotlin
class BusService {
    private lateinit var socket: Socket
    private var sessionId: String? = null
    
    // 1. WebSocket 연결
    fun connectWebSocket() {
        socket = IO.socket("https://your-server-url")
        
        // 자동으로 수신되는 이벤트들
        socket.on("connected") { args ->
            val data = args[0] as Map<String, Any>
            sessionId = data["session_id"] as String
            Log.d("Socket", "✅ 연결 완료, 세션 ID: $sessionId")
        }
        
        socket.on("monitoring_started") { args ->
            Log.d("Socket", "✅ 모니터링 시작됨")
        }
        
        socket.on("bus_update") { args ->
            val data = args[0] as Map<String, Any>
            processBusUpdate(data)
        }
        
        socket.connect()
    }
    
    // 2. 플로우 1: 실시간 모니터링 시작
    fun startMonitoring(lat: Double, lng: Double, busNumber: String) {
        val data = mapOf(
            "lat" to lat,
            "lng" to lng,
            "bus_number" to busNumber,
            "interval" to 30
        )
        
        socket.emit("start_bus_monitoring", data)
    }
    
    // 3. 플로우 2: 전체 버스 정보 조회
    suspend fun getAllBuses(): List<Bus> {
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("https://your-server-url/api/station/buses")
            .post("{}".toRequestBody("application/json".toMediaType()))
            .addHeader("X-Session-ID", sessionId ?: "")
            .build()
            
        val response = client.newCall(request).execute()
        // JSON 파싱 후 버스 목록 반환
    }
}
```

### 📱 **추천 사용 패턴**

1. **앱 시작 시**: WebSocket 연결 → `session_id` 저장
2. **음성 인식 후**: `start_bus_monitoring` 전송
3. **필요 시**: REST API로 전체 버스 목록 조회
4. **앱 종료 시**: `stop_bus_monitoring` 전송

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

## ❓ 자주 묻는 질문

**Q: WebSocket 연결만 하면 자동으로 데이터가 오나요?**
A: 아니요. 연결 시 `connected` 이벤트만 자동으로 오고, 실제 버스 정보를 받으려면 `start_bus_monitoring` 이벤트를 전송해야 합니다.

**Q: 플로우 2를 사용하려면 반드시 플로우 1이 실행 중이어야 하나요?**
A: 네, 플로우 2는 플로우 1에서 생성된 세션 정보를 활용합니다.

**Q: session_id는 언제 받을 수 있나요?**
A: WebSocket 연결 직후 `connected` 이벤트에서 자동으로 받을 수 있습니다.
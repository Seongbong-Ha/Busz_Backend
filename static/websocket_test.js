// 기존 WebSocket 코드 + 플로우 2 기능 추가

// ===================== 전역 변수 =====================
let socket = null;
let isFlow1Active = false;
let sessionId = null;

// Socket.IO 안전 초기화
function initSocket() {
    if (typeof io !== 'undefined') {
        socket = io();
        setupSocketEvents();
        addUpdate('info', '🔌 Socket.IO 초기화 완료');
    } else {
        addUpdate('error', '❌ Socket.IO 로드 실패, 3초 후 재시도...');
        setTimeout(initSocket, 3000);
    }
}

// ===================== WebSocket 이벤트 설정 =====================
function setupSocketEvents() {
    socket.on('connect', () => {
        sessionId = socket.id;
        updateConnectionStatus(true);
        setFlow1Status('connected', '✅ WebSocket 연결 완료');
        addUpdate('success', `✅ WebSocket 연결 완료 (세션: ${sessionId})`);
    });

    socket.on('disconnect', () => {
        updateConnectionStatus(false);
        setFlow1Status('error', '❌ WebSocket 연결 끊어짐');
        addUpdate('error', '❌ WebSocket 연결 끊어짐');
        isFlow1Active = false;
        updateFlow1Buttons();
    });

    socket.on('monitoring_started', (data) => {
        isFlow1Active = true;
        updateFlow1Buttons();
        setFlow1Status('active', '🔄 ' + data.message);
        addUpdate('success', `🔄 플로우 1 시작: ${data.bus_number}번 버스 (${data.interval}초 간격)`);
    });

    socket.on('bus_update', (data) => {
        if (data.bus_found) {
            const urgencyEmoji = getUrgencyEmoji(data.urgency);
            const msg = `${urgencyEmoji} ${data.bus_number}번: ${data.arrival_time_formatted} (${data.remaining_stations}개 정류장)`;
            setFlow1Status('active', msg);
            addUpdate('success', `${msg} - ${data.voice_message}`);
        } else if (data.error) {
            setFlow1Status('error', '❌ ' + data.error);
            addUpdate('error', '❌ ' + data.error);
        } else {
            setFlow1Status('error', '❌ ' + data.message);
            addUpdate('error', '❌ ' + data.message);
        }
    });

    socket.on('monitoring_stopped', (data) => {
        isFlow1Active = false;
        updateFlow1Buttons();
        setFlow1Status('stopped', '⏹️ ' + data.message);
        addUpdate('info', '⏹️ 플로우 1 중단됨');
    });

    socket.on('session_status', (data) => {
        if (data.active) {
            addUpdate('info', `📊 플로우 1 활성: ${data.bus_number}번 버스 (${data.interval}초 간격)`);
            isFlow1Active = true;
        } else {
            addUpdate('info', '📊 플로우 1 비활성');
            isFlow1Active = false;
        }
        updateFlow1Buttons();
    });

    socket.on('reconnect', () => {
        setFlow1Status('connected', '✅ 서버에 재연결되었습니다');
        addUpdate('success', '✅ 서버 재연결 완료');
    });

    socket.on('error', (data) => {
        setFlow1Status('error', '❌ ' + data.message);
        addUpdate('error', '❌ 에러: ' + data.message);
        isFlow1Active = false;
        updateFlow1Buttons();
    });
}

// ===================== 플로우 1 함수들 (기존) =====================
function startFlow1() {
    if (!socket) {
        alert('Socket.IO가 아직 로드되지 않았습니다. 잠시 후 다시 시도해주세요.');
        return;
    }
    
    const lat = parseFloat(document.getElementById('lat').value);
    const lng = parseFloat(document.getElementById('lng').value);
    const busNumber = document.getElementById('busNumber').value.trim();
    const interval = parseInt(document.getElementById('interval').value);
    
    // 입력값 검증
    if (!lat || !lng || !busNumber) {
        alert('모든 필드를 입력해주세요');
        return;
    }
    
    if (isNaN(lat) || isNaN(lng)) {
        alert('위도와 경도는 숫자여야 합니다');
        return;
    }
    
    if (lat < -90 || lat > 90) {
        alert('위도는 -90도에서 90도 사이여야 합니다');
        return;
    }
    
    if (lng < -180 || lng > 180) {
        alert('경도는 -180도에서 180도 사이여야 합니다');
        return;
    }
    
    if (interval < 10 || interval > 300) {
        alert('업데이트 간격은 10초에서 300초 사이여야 합니다');
        return;
    }
    
    // 모니터링 시작 요청
    socket.emit('start_bus_monitoring', {
        lat: lat,
        lng: lng,
        bus_number: busNumber,
        interval: interval
    });
    
    addUpdate('info', `🚀 플로우 1 시작 요청: ${busNumber}번 버스 모니터링`);
}

function stopFlow1() {
    if (!socket) {
        alert('Socket.IO 연결이 없습니다.');
        return;
    }
    
    socket.emit('stop_bus_monitoring');
    addUpdate('info', '⏹️ 플로우 1 중단 요청...');
}

function getFlow1Status() {
    if (!socket) {
        alert('Socket.IO 연결이 없습니다.');
        return;
    }
    
    socket.emit('get_session_status');
    addUpdate('info', '📊 플로우 1 상태 요청...');
}

// ===================== 플로우 2 함수들 (신규) =====================
async function callFlow2() {
    if (!isFlow1Active) {
        alert('플로우 1을 먼저 시작해주세요!');
        setFlow2Status('error', '❌ 플로우 1이 활성화되지 않음');
        return;
    }

    if (!sessionId) {
        alert('세션 ID가 없습니다. WebSocket 연결을 확인해주세요.');
        setFlow2Status('error', '❌ 세션 ID 없음');
        return;
    }

    try {
        setFlow2Status('active', '🔄 플로우 2 호출 중...');
        addUpdate('flow2', '📋 플로우 2 API 호출 시작...');

        const response = await fetch('/api/station/buses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId  // 세션 ID 전달
            },
            body: '{}'  // 빈 POST 요청
        });

        const data = await response.json();
        
        if (response.ok && data.success) {
            setFlow2Status('connected', '✅ 플로우 2 성공');
            addUpdate('flow2', `✅ 플로우 2 성공: ${data.total_count}개 버스 정보 수신`);
            
            // 버스 정보 로그 출력
            if (data.buses && data.buses.length > 0) {
                const busInfo = data.buses.map(bus => `${bus.route_name}번(${bus.arrival_time}초)`).join(', ');
                addUpdate('flow2', `🚌 수신된 버스: ${busInfo}`);
            }
            
            displayFlow2Result(data);
        } else {
            setFlow2Status('error', `❌ ${data.error || '플로우 2 실패'}`);
            addUpdate('error', `❌ 플로우 2 실패: ${data.error_code} - ${data.error}`);
            displayFlow2Result(data);
        }

    } catch (error) {
        setFlow2Status('error', '❌ 네트워크 오류');
        addUpdate('error', `❌ 플로우 2 네트워크 오류: ${error.message}`);
        console.error('Flow 2 Error:', error);
    }
}

async function testFlow2Direct() {
    try {
        setFlow2Status('active', '🧪 직접 테스트 중...');
        addUpdate('flow2', '🧪 플로우 2 직접 테스트 (세션 없이)...');

        const response = await fetch('/api/station/buses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: '{}'
        });

        const data = await response.json();
        
        if (data.success) {
            setFlow2Status('connected', '✅ 직접 테스트 성공');
            addUpdate('flow2', '✅ 직접 테스트 성공 (예상치 못한 성공)');
        } else {
            setFlow2Status('error', `❌ ${data.error || '직접 테스트 실패'}`);
            addUpdate('flow2', `❌ 직접 테스트 실패 (예상된 결과): ${data.error_code}`);
        }
        
        displayFlow2Result(data);

    } catch (error) {
        setFlow2Status('error', '❌ 직접 테스트 오류');
        addUpdate('error', `❌ 직접 테스트 오류: ${error.message}`);
    }
}

function displayFlow2Result(data) {
    const resultDiv = document.getElementById('flow2Result');
    const jsonDiv = document.getElementById('flow2Json');
    
    if (resultDiv && jsonDiv) {
        jsonDiv.textContent = JSON.stringify(data, null, 2);
        resultDiv.style.display = 'block';
    }
}

// ===================== UI 업데이트 함수들 =====================
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connectionIndicator');
    if (indicator) {
        indicator.className = `connection-indicator ${connected ? 'connected' : 'disconnected'}`;
    }
}

function setFlow1Status(type, message) {
    const statusDiv = document.getElementById('flow1Status');
    if (statusDiv) {
        statusDiv.className = `status ${type}`;
        statusDiv.textContent = message;
    }
}

function setFlow2Status(type, message) {
    const statusDiv = document.getElementById('flow2Status');
    if (statusDiv) {
        statusDiv.className = `status ${type}`;
        statusDiv.textContent = message;
    }
}

function updateFlow1Buttons() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    if (startBtn && stopBtn) {
        startBtn.disabled = isFlow1Active;
        stopBtn.disabled = !isFlow1Active;
        
        if (isFlow1Active) {
            startBtn.textContent = '🔄 플로우 1 실행 중...';
            stopBtn.textContent = '⏹️ 플로우 1 중단';
        } else {
            startBtn.textContent = '🚀 플로우 1 시작';
            stopBtn.textContent = '⏹️ 플로우 1 중단';
        }
    }
}

function addUpdate(type, message) {
    const updates = document.getElementById('updates');
    if (!updates) return;
    
    const time = new Date().toLocaleTimeString('ko-KR');
    const date = new Date().toLocaleDateString('ko-KR');
    
    const updateItem = document.createElement('div');
    updateItem.className = `update-item ${type}`;
    updateItem.innerHTML = `<strong>[${date} ${time}]</strong> ${message}`;
    
    updates.appendChild(updateItem);
    updates.scrollTop = updates.scrollHeight;
    
    // 최대 200개 로그만 유지
    const items = updates.children;
    if (items.length > 200) {
        updates.removeChild(items[0]);
    }
}

function clearUpdates() {
    const updates = document.getElementById('updates');
    if (updates) {
        updates.innerHTML = '';
        addUpdate('info', '🗑️ 로그가 지워졌습니다');
    }
}

function exportLogs() {
    const updates = document.getElementById('updates');
    if (!updates) {
        alert('로그가 없습니다.');
        return;
    }
    
    const logs = Array.from(updates.children).map(item => item.textContent).join('\n');
    
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `busz_test_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addUpdate('info', '💾 로그 파일이 다운로드되었습니다');
}

function getUrgencyEmoji(urgency) {
    switch(urgency) {
        case 'urgent': return '🚨';
        case 'moderate': return '⚠️';
        case 'normal': return '⏰';
        default: return '🚌';
    }
}

// ===================== 초기화 =====================
document.addEventListener('DOMContentLoaded', function() {
    addUpdate('info', '🚌 Busz 백엔드 통합 테스트 페이지 로드 완료');
    addUpdate('info', '📋 사용법: 플로우 1 → 플로우 2 순서로 테스트하세요');
    updateFlow1Buttons();
    updateConnectionStatus(false);
    
    // Socket.IO 초기화
    initSocket();
});

// 페이지 언로드시 정리
window.addEventListener('beforeunload', function() {
    if (socket && isFlow1Active) {
        socket.emit('stop_bus_monitoring');
    }
});

// Enter 키로 플로우 1 시작
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !isFlow1Active) {
        startFlow1();
    }
});
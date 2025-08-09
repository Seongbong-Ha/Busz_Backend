const socket = io();
let isMonitoring = false;

// SocketIO 이벤트 리스너들
socket.on('connected', (data) => {
    setStatus('connected', '✅ ' + data.message);
    addUpdate('success', '✅ 서버 연결 완료');
});

socket.on('monitoring_started', (data) => {
    isMonitoring = true;
    updateButtons();
    setStatus('active', '🔄 ' + data.message);
    addUpdate('info', `🔄 ${data.bus_number}번 버스 모니터링 시작 (${data.interval}초 간격)`);
});

socket.on('bus_update', (data) => {
    if (data.bus_found) {
        const urgencyEmoji = getUrgencyEmoji(data.urgency);
        const msg = `${urgencyEmoji} ${data.bus_number}번: ${data.arrival_time_formatted} (${data.remaining_stations}개 정류장)`;
        setStatus('active', msg);
        addUpdate('success', `${msg} - ${data.voice_message}`);
    } else if (data.error) {
        setStatus('error', '❌ ' + data.error);
        addUpdate('error', '❌ ' + data.error);
    } else {
        setStatus('error', '❌ ' + data.message);
        addUpdate('error', '❌ ' + data.message);
    }
});

socket.on('monitoring_stopped', (data) => {
    isMonitoring = false;
    updateButtons();
    setStatus('stopped', '⏹️ ' + data.message);
    addUpdate('info', '⏹️ 모니터링 중단됨');
});

socket.on('session_status', (data) => {
    if (data.active) {
        addUpdate('info', `📊 세션 활성: ${data.bus_number}번 버스 (${data.interval}초 간격)`);
        isMonitoring = true;
    } else {
        addUpdate('info', '📊 세션 비활성');
        isMonitoring = false;
    }
    updateButtons();
});

socket.on('error', (data) => {
    setStatus('error', '❌ ' + data.message);
    addUpdate('error', '❌ 에러: ' + data.message);
    isMonitoring = false;
    updateButtons();
});

socket.on('disconnect', () => {
    setStatus('error', '❌ 서버 연결이 끊어졌습니다');
    addUpdate('error', '❌ 서버 연결 끊어짐');
    isMonitoring = false;
    updateButtons();
});

socket.on('reconnect', () => {
    setStatus('connected', '✅ 서버에 재연결되었습니다');
    addUpdate('success', '✅ 서버 재연결 완료');
});

// 메인 함수들
function startMonitoring() {
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
    
    addUpdate('info', `🚀 ${busNumber}번 버스 모니터링 요청 전송...`);
}

function stopMonitoring() {
    socket.emit('stop_bus_monitoring');
    addUpdate('info', '⏹️ 모니터링 중단 요청 전송...');
}

function getStatus() {
    socket.emit('get_session_status');
    addUpdate('info', '📊 세션 상태 요청...');
}

function clearUpdates() {
    document.getElementById('updates').innerHTML = '';
    addUpdate('info', '🗑️ 로그가 지워졌습니다');
}

// 유틸리티 함수들
function setStatus(type, message) {
    const statusDiv = document.getElementById('status');
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
}

function addUpdate(type, message) {
    const updates = document.getElementById('updates');
    const time = new Date().toLocaleTimeString('ko-KR');
    const date = new Date().toLocaleDateString('ko-KR');
    
    const updateItem = document.createElement('div');
    updateItem.className = `update-item ${type}`;
    updateItem.innerHTML = `<strong>[${date} ${time}]</strong> ${message}`;
    
    updates.appendChild(updateItem);
    updates.scrollTop = updates.scrollHeight;
    
    // 최대 100개 로그만 유지
    const items = updates.children;
    if (items.length > 100) {
        updates.removeChild(items[0]);
    }
}

function updateButtons() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    startBtn.disabled = isMonitoring;
    stopBtn.disabled = !isMonitoring;
    
    if (isMonitoring) {
        startBtn.textContent = '🔄 모니터링 중...';
        stopBtn.textContent = '⏹️ 모니터링 중단';
    } else {
        startBtn.textContent = '🚀 모니터링 시작';
        stopBtn.textContent = '⏹️ 모니터링 중단';
    }
}

function getUrgencyEmoji(urgency) {
    switch(urgency) {
        case 'urgent': return '🚨';
        case 'moderate': return '⚠️';
        case 'normal': return '⏰';
        default: return '🚌';
    }
}

// 페이지 로드시 초기화
document.addEventListener('DOMContentLoaded', function() {
    addUpdate('info', '페이지가 로드되었습니다. 서버 연결을 시도하는 중...');
    updateButtons();
    
    // Enter 키로 모니터링 시작
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !isMonitoring) {
            startMonitoring();
        }
    });
});

// 페이지 언로드시 모니터링 정리
window.addEventListener('beforeunload', function() {
    if (isMonitoring) {
        socket.emit('stop_bus_monitoring');
    }
});
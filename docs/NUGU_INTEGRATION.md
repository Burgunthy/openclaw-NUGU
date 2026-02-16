# NUGU 연동 가이드

이 문서는 NUGU 스피커("아리아")를 OpenClaw와 연동하는 방법을 설명합니다.

## 연동 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  NUGU 스피커  │ ──▶ │ SmartThings  │ ──▶ │ MQTT Broker │ ──▶ │ Home Assistant │
│   (아리아)    │     │   (허브)      │     │             │     │   → 웹훅서버   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

## 연동 방식 선택

### 방식 1: SmartThings + MQTT (권장)

NUGU는 SmartThings와 공식 연동되어 있으므로, SmartThings → MQTT → Home Assistant 경로를 사용합니다.

#### 장점
- NUGU 공식 연동 지원
- 안정적인 통신
- 응답 생성 가능

#### 설정 방법

1. **SmartThings 설정**
   - SmartThings 앱에서 NUGU 디바이스 추가
   - 자동화 규칙 생성

2. **MQTT 브로커 설정**
   - Home Assistant에 MQTT 통합 구성
   - 토픽: `nugu/command`

3. **Home Assistant 자동화**
   - `automations.yaml`에 MQTT 트리거 추가 (아래 참조)

### 방식 2: NUGU Developer Kit (DIY)

NUGU Play Kit을 사용하여 직접 웹훅 서버와 연동합니다.

#### 장점
- 완전한 커스터마이징
- 직접 응답 제어

#### 단점
- 개발 복잡도 높음
- NUGU 개발자 계정 필요

---

## MQTT 자동화 설정

### Home Assistant MQTT 통합

`configuration.yaml`:

```yaml
mqtt:
  broker: core-mosquitto
  port: 1883
```

### MQTT 트리거 자동화

`automations.yaml`에 추가:

```yaml
automation:
  # MQTT로 NUGU 명령 수신
  - alias: "MQTT NUGU 명령 수신"
    description: "MQTT를 통해 수신된 NUGU 명령을 웹훅 서버로 전달"
    trigger:
      - platform: mqtt
        topic: "nugu/command"
    condition: []
    action:
      - service: rest_command.nugu_webhook
        data:
          command: "{{ trigger.payload }}"
    mode: queued
    max: 10
```

### REST Command 설정

`configuration.yaml`:

```yaml
rest_command:
  nugu_webhook:
    url: "http://127.0.0.1:5000/nugu/command/cli"
    method: POST
    payload: '{"command": "{{ command }}"}'
    content_type: "application/json"
```

---

## SmartThings 연동

### 1. SmartThings 디바이스 설정

1. SmartThings 앱 실행
2. **디바이스 추가** → **NUGU** 검색
3. NUGU 스피커 추가

### 2. 자동화 규칙 생성

SmartThings 앱에서:

1. **자동화** → **새로 만들기**
2. 트리거: 음성 명령 "날씨"
3. 동작: MQTT 메시지 발행

### 3. SmartThings Edge Driver (고급)

SmartThings Edge Driver를 사용하면 MQTT 직접 발행 가능:

```lua
-- driver.lua
local driver = require("st.driver")
local mqtt = require("st.mqtt")

local function handle_voice_command(driver, device, command)
    mqtt.publish("nugu/command", command.args.text)
end

driver:register_handler("voiceCommand", handle_voice_command)
driver:run()
```

---

## 테스트 방법

### 1. MQTT 테스트

```bash
# MQTT 메시지 발행 (테스트)
mosquitto_pub -h localhost -t "nugu/command" -m "오늘 날씨 알려줘"

# MQTT 메시지 구독 (모니터링)
mosquitto_sub -h localhost -t "nugu/response" -v
```

### 2. 직접 API 테스트

```bash
# 웹훅 서버 직접 호출
curl -X POST http://192.168.0.25:5000/nugu/command/cli \
  -H "Content-Type: application/json" \
  -d '{"command": "오늘 날씨 알려줘"}'
```

### 3. NUGU 실제 테스트

1. "아리아, 오늘 날씨 알려줘" 발화
2. Home Assistant 로그 확인
3. 웹훅 서버 응답 확인

---

## 응답 처리

### NUGU 응답 포맷

NUGU는 TTS(Text-to-Speech)로 응답을 재생합니다. 웹훅 서버에서 JSON 응답을 반환하면 이를 NUGU가 음성으로 변환합니다.

```json
{
  "status": "success",
  "result": {
    "text_output": "오늘 서울의 날씨는 맑음이며, 기온은 22도입니다."
  }
}
```

### 응답 시간 제한

NUGU는 8초 내에 응답해야 합니다. 긴 작업의 경우:

1. **비동기 처리**: 즉시 "처리 중입니다" 응답
2. **나중에 알림**: 작업 완료 시 NUGU 알림

---

## 문제 해결

### MQTT 연결 실패

```bash
# MQTT 브로커 상태 확인
docker logs core-mosquitto

# 포트 확인
netstat -tlnp | grep 1883
```

### 응답 없음

1. 웹훅 서버 로그 확인
2. OpenClaw 실행 상태 확인
3. 네트워크 연결 확인

### NUGU가 명령을 인식하지 못함

1. NUGU 웨이크워드("아리아") 확인
2. SmartThings 연결 상태 확인
3. 마이크 감도 조정

---

## 참고 자료

- [NUGU 개발자 포털](https://developers-doc.nugu.co.kr/)
- [SmartThings 개발자 문서](https://developer.smartthings.com/)
- [Home Assistant MQTT 통합](https://www.home-assistant.io/integrations/mqtt/)

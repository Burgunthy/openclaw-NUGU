# NUGU Play Builder 설정 가이드

## 목표
NUGU 스피커("아리아")의 음성 명령으로 OpenClaw를 호출하여 날씨 정보를 얻고 응답받기

## Flow
```
"아리아, 오늘 날씨 알려줘"
    ↓
NUGU 스피커
    ↓
NUGU 서버 (Play Builder에서 설정한 Play 실행)
    ↓
Backend Proxy 호출: POST https://nugu-openclaw.loca.lt/{actionName}
    ↓
웹훅 서버 (Flask) → OpenClaw CLI
    ↓
응답: {"version": "2.0", "resultCode": "OK", "output": {...}}
    ↓
NUGU가 응답을 음성으로 재생
```

---

## Play Builder 설정 단계

### Step 1: 외부 서버 연결 정보 ✅ 완료
**메뉴**: `General` > `외부 서버 연결 정보`

| 항목 | 값 |
|-----|-----|
| Web URL | `https://nugu-openclaw.loca.lt` |
| 연결 실패 시 Prompt | `서버 연결에 실패했습니다.` |

---

### Step 2: Custom Action 생성 (진행 중)
**메뉴**: `Actions` > `Custom Actions`

#### Action 기본 설정
| 항목 | 값 |
|-----|-----|
| Action Name | `weatherAction` (예시) |
| Backend proxy 사용 여부 | **ON** |

#### Utterance Parameter (발화에서 추출)
| Parameter Name | Entity Mapping | 설명 |
|---------------|----------------|------|
| `location` | BID_LOCATION | 위치 (서울, 부산 등) |
| `date` | BID_DT_DAY | 날짜 (오늘, 내일 등) |

#### Backend Parameter (서버에서 받아올 값)
| Parameter Name | 설명 |
|---------------|------|
| `weatherResult` | 날씨 정보 결과 텍스트 |

#### Response (응답 Prompt)
```
{{weatherResult}}
```

---

### Step 3: Intent 생성
**메뉴**: `User Utterance Model` > `Intents`

#### Intent 설정
| 항목 | 값 |
|-----|-----|
| Intent Name | `WeatherIntent` |
| Type | Custom Intent |

#### 예상 발화 (User Utterances)
```
오늘 날씨 알려줘
{location} 날씨 어때
{date} {location} 날씨
내일 서울 날씨
지금 비 와?
```

---

## 서버 측 구현 (완료)

### 엔드포인트
- **Health Check**: `GET /health`
- **Action Handler**: `POST /{action_name}` (동적 라우팅)

### Request/Response 형식

**Request (NUGU → 서버)**:
```json
{
  "version": "2.0",
  "action": {
    "actionName": "weatherAction",
    "parameters": {
      "location": {"type": "BID_LOCATION", "value": "서울"},
      "date": {"type": "BID_DT_DAY", "value": "오늘"}
    }
  },
  "context": {...}
}
```

**Response (서버 → NUGU)**:
```json
{
  "version": "2.0",
  "resultCode": "OK",
  "output": {
    "weatherResult": "서울의 현재 날씨는 맑고, 기온은 -3°C입니다."
  }
}
```

---

## 테스트 방법

### 1. 서버 헬스체크
```bash
curl https://nugu-openclaw.loca.lt/health
```

### 2. Action 엔드포인트 테스트
```bash
curl -X POST https://nugu-openclaw.loca.lt/weatherAction \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "action": {
      "actionName": "weatherAction",
      "parameters": {
        "location": {"type": "BID_LOCATION", "value": "서울"},
        "date": {"type": "BID_DT_DAY", "value": "오늘"}
      }
    }
  }'
```

### 3. NUGU Play Builder 테스트
- Play Builder 하단 `테스트` 탭
- "오늘 날씨 알려줘" 입력

### 4. 실제 NUGU 스피커 테스트
- "아리아, 오늘 날씨 알려줘" 발화

---

## 파일 위치

| 파일 | 용도 |
|------|------|
| `webhook-server/app.py` | Flask 웹훅 서버 (NUGU API 호환) |
| `webhook-server/openclaw_cli.py` | OpenClaw CLI 래퍼 |
| `docker-compose.yml` | Docker 구성 |

---

## 상태

| 항목 | 상태 |
|-----|------|
| 웹훅 서버 | ✅ 실행 중 |
| Localtunnel | ✅ 실행 중 |
| Web URL 설정 | ✅ 완료 |
| Custom Action 생성 | ✅ 완료 |
| Intent 생성 | ✅ 완료 |
| Action-Intent 연결 | 🔄 진행 중 |
| 빌드 및 테스트 | ⏳ 대기 |

---

## 다음 단계

### 1. Action의 Trigger를 WeatherIntent로 변경
- `weatherAction` → Trigger → `WeatherIntent` 선택

### 2. Play 빌드
- `Play 구조` 또는 `빌드 / History` 메뉴에서 빌드

### 3. 테스트
- Play Builder 하단 테스트 탭에서 "오늘 날씨 알려줘" 입력

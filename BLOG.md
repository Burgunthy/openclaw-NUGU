# [프로젝트] NUGU(아리아)로 OpenClaw 제어하기 - 음성 AI 자동화 구축기

## 시작하며

국내 스마트 스피커 NUGU의 음성 인식 기능과 오픈소스 AI 에이전트 OpenClaw를 연동하여, 음성 명령으로 복잡한 AI 작업을 자동화하는 프로젝트를 진행했습니다.

### 왜 이 프로젝트를 시작했는가?

1. **NUGU의 장점:** 국내 음성 인식 정확도가 높음
2. **OpenClaw의 강력함:** 웹 검색, 파일 관리, 캘린더 연동 등 다양한 기능
3. **Home Assistant의 안정성:** 스마트 홈 중계 서버

---

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NUGU 스피커    │ ──▶ │  SmartThings    │ ──▶ │  MQTT Broker    │ ──▶ │ Home Assistant  │
│   (아리아)       │     │    (허브)       │     │                 │     │   웹훅 서버     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                                          │
                                                                          ▼
                                                                  ┌─────────────────┐
                                                                  │   OpenClaw      │
                                                                  │   (AI 에이전트)  │
                                                                  └─────────────────┘
```

---

## 개발 과정

### Phase 1: 기본 구조 설계 (완료)

#### 1.1 웹훅 서버 구현
Flask 기반 웹훅 서버를 구현했습니다.

**주요 엔드포인트:**
| 엔드포인트 | 메서드 | 용도 |
|-----------|--------|------|
| `/health` | GET | 헬스체크 |
| `/nugu/command` | POST | NUGU 명령 수신 |
| `/nugu/command/cli` | POST | OpenClaw CLI 직접 실행 |
| `/nugu/openclaw` | POST | OpenClaw API 호출 |

**명령 분석 로직:**
- 날씨 관련 키워드 → `get_weather()`
- 검색 관련 키워드 → `search_web()`
- 일정 관련 키워드 → `get_schedule()`

#### 1.2 OpenClaw CLI 래퍼
subprocess 방식으로 OpenClaw CLI를 실행하는 래퍼를 구현했습니다.

```python
# 실행 예시
cmd = ["openclaw", "agent", "--local", "--message", command, "--json", "--timeout", "60"]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=70)
```

### Phase 2: NUGU 연동 (진행 중)

#### 2.1 연동 방식 선택
NUGU는 직접 HTTP 웹훅을 지원하지 않아 SmartThings + MQTT 경로를 선택했습니다.

**선택 이유:**
- NUGU와 SmartThings는 공식 연동됨
- MQTT는 가볍고 안정적
- Home Assistant와 쉽게 통합

#### 2.2 MQTT 자동화 구현
Home Assistant의 MQTT 트리거를 사용하여 웹훅 서버를 호출합니다.

```yaml
automation:
  - alias: "MQTT NUGU 명령 처리"
    trigger:
      - platform: mqtt
        topic: "nugu/command"
    action:
      - service: rest_command.nugu_webhook
        data:
          command: "{{ trigger.payload }}"
```

### Phase 3: 서버 배포 (예정)

#### 3.1 배포 환경
- **서버**: 192.168.0.25
- **Docker Compose**: Home Assistant + 웹훅 서버 + Caddy
- **OpenClaw**: 서버에 직접 설치

#### 3.2 배포 스크립트
자동화된 배포 스크립트(`scripts/deploy.sh`)를 작성했습니다.

```bash
# 실행
./scripts/deploy.sh
```

### Phase 4: 테스트 및 검증 (예정)

#### 4.1 테스트 코드
pytest를 사용한 API 테스트 코드를 작성했습니다.

```bash
# 테스트 실행
cd webhook-server && pytest tests/
```

#### 4.2 E2E 테스트 시나리오
1. 웹훅 서버 헬스체크
2. 날씨 명령 테스트
3. NUGU 실제 음성 테스트

---

## 구현된 파일 구조

```
nugu-openclaw-ha/
├── webhook-server/
│   ├── app.py              # Flask 웹훅 서버 (359줄)
│   ├── openclaw_cli.py     # OpenClaw CLI 래퍼 (191줄)
│   ├── config.yml          # 서버 설정
│   ├── requirements.txt    # Python 의존성
│   └── tests/
│       ├── test_app.py     # API 테스트
│       └── test_openclaw_cli.py  # CLI 테스트
├── home-assistant/
│   ├── automations.yaml    # MQTT 자동화 규칙
│   ├── scripts.yaml        # HA 스크립트
│   └── configuration.yaml  # HA 설정
├── scripts/
│   ├── deploy.sh           # 배포 자동화
│   └── setup.sh            # 초기 설정
├── docs/
│   ├── NUGU_INTEGRATION.md # NUGU 연동 가이드
│   ├── SETUP.md            # 상세 설정 가이드
│   └── TROUBLESHOOTING.md  # 문제 해결
├── docker-compose.yml      # Docker 구성
├── .env.example            # 환경 변수 예시
└── README.md               # 프로젝트 개요
```

---

## 트러블슈팅 기록

### 이슈 1: NUGU 직접 연동 불가
- **문제**: NUGU Play Kit이 개발자에게 제한적으로 제공됨
- **해결**: SmartThings + MQTT 경유 방식으로 우회

### 이슈 2: 응답 시간 제한
- **문제**: NUGU는 8초 내에 응답해야 함
- **해결**: 비동기 처리 + 캐싱 전략 도입 예정

### 이슈 3: OpenClaw 경로 문제
- **문제**: Docker 컨테이너에서 호스트의 OpenClaw 실행
- **해결**: 볼륨 마운트로 OpenClaw 바이너리 공유

---

## 마치며

### 가능한 활용 방안

1. **"아리아, 오늘 날씨 알려줘"** → OpenClaw 웹 검색 → 날씨 응답
2. **"아리아, 내일 일정 뭐야?"** → 캘린더 조회 → 일정 응답
3. **"아리아, 스팸 메일 정리해줘"** → 이메일 필터링 (향후 구현)

### 다음 단계

1. 서버 배포 및 실행
2. E2E 테스트 수행
3. GitHub 공개
4. 추가 기능 구현 (이메일, 파일 관리)

---

## 참고 자료

- [OpenClaw 공식 문서](https://openclaw.ai/)
- [Home Assistant MQTT 통합](https://www.home-assistant.io/integrations/mqtt/)
- [NUGU 개발자 포털](https://developers-doc.nugu.co.kr/)
- [SmartThings 개발자 문서](https://developer.smartthings.com/)

---

*최종 업데이트: 2026년 2월 16일*

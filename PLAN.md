# NUGU(아리아) + OpenClaw + Home Assistant 연동 개발 계획

## 프로젝트 개요
NUGU 스마트 스피커("아리아" 웨이크워드)와 오픈소스 AI 에이전트인 OpenClaw를 Home Assistant를 통해 연동하여 음성으로 AI 자동화를 제어하는 시스템 구축

---

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NUGU 스피커    │ ──▶ │  웹훅 서버      │ ──▶ │ Home Assistant  │ ──▶ │   OpenClaw      │
│   (아리아)       │     │  (Python/Flask) │     │  (중계 서버)    │     │  (별도 PC)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
   음성 명령              HTTP POST 요청         API 호출               AI 작업 수행
```

**네트워크 구성:**
- **Home Assistant**: 메인 서버 (예: `192.168.1.100:8123`)
- **OpenClaw PC**: 별도 로컬 PC (예: `192.168.1.200:8080`)
- **웹훅 서버**: Home Assistant와 같은 서버 또는 별도 컨테이너

---

## 📁 프로젝트 파일 구조

```
nugu-openclaw-ha/
├── README.md              # 프로젝트 개요
├── PLAN.md                # 이 개발 계획서
├── GUIDE.md               # 아리아 음성 명령 가이드
├── BLOG.md                # 블로그 포스트
├── LICENSE                # MIT 라이선스
├── CONTRIBUTING.md        # 기여 가이드
├── Makefile               # 빌드 스크립트
├── docker-compose.yml     # Docker Compose 설정
├── docs/
│   ├── SETUP.md           # 상세 설정 가이드
│   └── TROUBLESHOOTING.md # 문제 해결 가이드
├── webhook-server/        # NUGU → HA 웹훅 서버
│   ├── app.py             # Flask 애플리케이션
│   ├── requirements.txt   # Python 의존성
│   ├── config.yml         # 설정 파일
│   ├── Dockerfile         # Docker 이미지
│   └── tests/             # 테스트 파일
├── home-assistant/        # HA 설정 파일
│   ├── configuration.yaml # HA 설정
│   ├── scripts.yaml       # HA 스크립트
│   └── automations.yaml   # HA 자동화
├── openclaw/              # OpenClaw 설정
│   └── config.yml         # OpenClaw 설정
├── caddy/                 # Caddy 역방향 프록시
│   └── Caddyfile          # Caddy 설정
└── scripts/               # 유틸리티 스크립트
    └── setup.sh           # 설치 스크립트
```

---

## 🚀 개발 단계

### 1단계: 환경 준비

#### 1.1 사전 요구사항 확인
- [ ] NUGU 스피커 (NUGU/NUGU Mini/NUGU Candle)
- [ ] Home Assistant 설치된 서버 (또는 Raspberry Pi)
- [ ] OpenClaw 설치할 별도 PC (macOS/Linux)
- [ ] 동일 로컬 네트워크 (LAN)

#### 1.2 네트워크 IP 고정
| 장비 | 예시 IP | 비고 |
|------|--------|------|
| Home Assistant | `192.168.1.100` | HA 설정에서 고정 |
| OpenClaw PC | `192.168.1.200` | OS 네트워크 설정에서 고정 |
| NUGU 스피커 | DHCP | 변경 불가능하므로 확인만 |

---

### 2단계: OpenClaw 원격 접속 설정

**목표**: 별도 PC에 설치된 OpenClaw를 다른 PC에서 IP로 접근 가능하게 설정

#### 2.1 OpenClaw 설치
```bash
curl -fsSL https://get.openclaw.ai | sh
```

#### 2.2 원격 접속 설정
```yaml
# ~/.openclaw/config.yml
server:
  host: "0.0.0.0"
  port: 8080
```

#### 2.3 접속 테스트
```bash
curl http://192.168.1.200:8080/api/status
```

---

### 3단계: Home Assistant 설정

#### 3.1 웹훅 활성화
Home Assistant에서 웹훅 URL 확인

#### 3.2 스크립트 작성
`scripts.yaml`에 OpenClaw 명령 전송 스크립트 추가

#### 3.3 자동화 작성
`automations.yaml`에 웹훅 트리거 자동화 추가

---

### 4단계: 웹훅 서버 구축

Flask로 NUGU 명령을 수신하여 OpenClaw로 전달하는 중계 서버 구축

---

### 5단계: 서비스로 배포

Docker Compose로 간편하게 배포

---

### 6단계: NUGU 연동 방법

#### 방법 A: NUGU Developers SDK 활용
NUGU 개발자 포털에서 External Service 추가

#### 방법 B: MQTT 활용
NUGU → SmartThings → MQTT → Home Assistant → OpenClaw

---

### 7단계: 테스트 및 검증

```bash
# 전체 경로 테스트
curl -X POST http://192.168.1.100:5000/nugu/command \
  -H "Content-Type: application/json" \
  -d '{"command": "테스트"}'
```

---

## 🎯 프로젝트 완료 기준

- [ ] OpenClaw가 IP로 원격 접속 가능
- [ ] Home Assistant에서 OpenClaw 명령 실행 가능
- [ ] 웹훅 서버가 정상적으로 중계 동작
- [ ] NUGU에서 명령 → OpenClaw 실행까지 전체 경로 작동
- [ ] BLOG.md 작성 완료
- [ ] GUIDE.md 작성 완료
- [ ] README.md 작성 완료

---

## 📞 참고 자료

- [OpenClaw 공식 문서](https://openclaw.ai/)
- [Home Assistant 웹훅 문서](https://www.home-assistant.io/integrations/webhook/)
- [NUGU 개발자 포털](https://developers-doc.nugu.co.kr/)

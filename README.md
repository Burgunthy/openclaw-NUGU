# NUGU + OpenClaw + Home Assistant Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)

NUGU 스마트 스피커("아리아" 웨이크워드)와 오픈소스 AI 에이전트인 OpenClaw를 Home Assistant를 통해 연동하여 음성으로 AI 자동화를 제어하는 통합 시스템입니다.

## 프로젝트 개요

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NUGU 스피커    │ ──▶ │  웹훅 서버      │ ──▶ │ Home Assistant  │ ──▶ │   OpenClaw      │
│   (아리아)       │     │  (Python/Flask) │     │  (중계 서버)    │     │  (별도 PC)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
   음성 명령              HTTP POST 요청         API 호출               AI 작업 수행
```

## 주요 기능

- **음성 명령 실행**: NUGU 스피커로 OpenClaw 제어
- **이메일 관리**: "아리아, 스팸 메일 정리해줘"
- **캘린더 연동**: "아리아, 내일 일정 뭐야?"
- **파일 정리**: "아리아, 다운로드 폴더 정리해줘"
- **정보 검색**: "아리아, 오늘 날씨 알려줘"

## 사전 요구사항

| 장비 | 최소 사양 | 권장 사양 |
|------|-----------|-----------|
| NUGU 스피커 | NUGU mini | NUGU Candle |
| Home Assistant | Raspberry Pi 4 (2GB) | Intel NUC / VM (2코어 4GB) |
| OpenClaw PC | macOS / Linux (4GB RAM) | macOS / Linux (8GB RAM) |

## 빠른 시작

### 1. 클론 및 설치

```bash
git clone https://github.com/yourusername/nugu-openclaw-ha.git
cd nugu-openclaw-ha
make install
```

### 2. 설정

```bash
# 설정 스크립트 실행
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. OpenClaw 설정

```bash
# OpenClaw PC에서
cp openclaw/config.yml ~/.openclaw/config.yml
openclaw start
```

### 4. Home Assistant 설정

`home-assistant/` 디렉토리의 YAML 파일을 Home Assistant에 복사하고 재시작합니다.

### 5. 실행

```bash
# 직접 실행
make run

# 또는 Docker 사용
docker-compose up -d
```

## 프로젝트 구조

```
nugu-openclaw-ha/
├── README.md              # 프로젝트 개요
├── PLAN.md                # 개발 계획서
├── GUIDE.md               # 음성 명령 가이드
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

## 사용 예시

```bash
# 웹훅 서버 테스트
curl http://localhost:5000/health

# 명령 전송
curl -X POST http://localhost:5000/nugu/command \
  -H "Content-Type: application/json" \
  -d '{"command": "오늘 날씨 알려줘", "action": "openclaw"}'
```

## 음성 명령 가이드

상세 가이드는 [GUIDE.md](GUIDE.md)를 참조하세요.

| 음성 명령 | 동작 |
|-----------|------|
| "아리아, 이메일 정리해줘" | OpenClaw 이메일 정리 |
| "아리아, 내일 일정 뭐야?" | 캘린더 일정 조회 |
| "아리아, 스팸 메일 삭제해줘" | 스팸 필터링 후 삭제 |
| "아리아, 오늘 날씨 알려줘" | 날씨 정보 검색 |

## 설정 가이드

- [상세 설정 가이드](docs/SETUP.md)
- [문제 해결 가이드](docs/TROUBLESHOOTING.md)

## 테스트

```bash
make test
```

## 기여

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참조하세요.

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

## 참고 자료

- [OpenClaw 공식 문서](https://openclaw.ai/)
- [Home Assistant 웹훅 문서](https://www.home-assistant.io/integrations/webhook/)
- [NUGU 개발자 포털](https://developers-doc.nugu.co.kr/)

## 저자

- GitHub [@yourusername](https://github.com/yourusername)

## 감사의 인사

- [OpenClaw](https://openclaw.ai/) 팀
- [Home Assistant](https://www.home-assistant.io/) 커뮤니티
- [NUGU](https://www.nugu.co.kr/) 개발자 팀

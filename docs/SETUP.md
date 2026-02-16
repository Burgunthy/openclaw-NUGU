# NUGU + OpenClaw + Home Assistant 상세 설정 가이드

이 가이드에서는 NUGU 스마트 스피커와 OpenClaw AI 에이전트, Home Assistant를 연동하는 전체 과정을 단계별로 설명합니다.

---

## 목차

1. [아키텍처 개요](#1-아키텍처-개요)
2. [사전 준비](#2-사전-준비)
3. [OpenClaw 설치 및 설정](#3-openclaw-설치-및-설정)
4. [Home Assistant 설치](#4-home-assistant-설치)
5. [웹훅 서버 설정](#5-웹훅-서버-설정)
6. [Docker로 일괄 배포](#6-docker로-일괄-배포)
7. [Home Assistant 설정 추가](#7-home-assistant-설정-추가)
8. [NUGU 연동](#8-nugu-연동)
9. [테스트 및 검증](#9-테스트-및-검증)

---

## 1. 아키텍처 개요

### 단일 PC 구성 (권장)

```
┌─────────────────────────────────────────────────────────┐
│           Linux PC (192.168.0.25)                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ OpenClaw    │  │ Home Asst.  │  │ 웹훅 서버   │    │
│  │ :8080       │  │ :8123       │  │ :5000       │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                         ↑
                   NUGU 스피커
```

### 다중 PC 구성

```
NUGU → 웹훅 서버(5000) → Home Assistant(8123) → OpenClaw(8080)
        192.168.0.100         192.168.0.100            192.168.0.25
```

---

## 2. 사전 준비

### 2.1 필요한 장비

| 장비 | 최소 사양 | 권장 사양 |
|------|-----------|-----------|
| 메인 PC (Linux) | 4코어 8GB RAM | 4코어 16GB RAM |
| NUGU 스피커 | NUGU mini | NUGU Candle |

### 2.2 필요한 소프트웨어

| 소프트웨어 | 버전 | 설치 확인 |
|-----------|------|-----------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |
| Python | 3.9+ | `python3 --version` |
| OpenCL | (可选) | - |

### 2.3 네트워크 구성

```
네트워크: 192.168.0.0/24
├── 192.168.0.1   (라우터)
├── 192.168.0.25  (메인 서버 - 모든 서비스 실행)
└── 192.168.0.xxx (NUGU 스피커 - DHCP)
```

---

## 3. OpenClaw 설치 및 설정

### 3.1 OpenClaw 설치

```bash
# OpenClaw 설치 스크립트 실행
curl -fsSL https://get.openclaw.ai | sh

# 설치 확인
openclaw --version
```

### 3.2 보안 토큰 생성

```bash
# 랜덤 토큰 생성
openssl rand -hex 32

# 출력 예시: a1b2c3d4e5f6... (이 토큰을 안전하게 저장)
```

### 3.3 OpenClaw 설정

```bash
# 설정 디렉토리 생성
mkdir -p ~/.openclaw

# 설정 파일 생성
nano ~/.openclaw/config.yml
```

다음 내용을 붙여넣으세요:

```yaml
server:
  host: "0.0.0.0"  # 모든 인터페이스에서 접속 허용
  port: 8080

api:
  enabled: true
  authentication:
    type: "token"
    token: "생성한_토큰_여기에_입력"

cors:
  enabled: true
  origins:
    - "http://localhost:8123"
    - "http://127.0.0.1:8123"
    - "http://localhost:5000"
    - "http://127.0.0.1:5000"
    - "http://192.168.0.25:8123"
    - "http://192.168.0.25:5000"

logging:
  level: "INFO"
  file: "logs/openclaw.log"

skills:
  enabled:
    - email
    - calendar
    - web_search
    - file_management
    - system

execution:
  timeout: 300
  max_concurrent_tasks: 3
```

### 3.4 OpenClaw 시작

```bash
# OpenClaw 시작
openclaw start

# 백그라운드 실행
openclaw start --daemon

# 상태 확인
openclaw status

# 로그 확인
openclaw logs
```

### 3.5 접속 테스트

```bash
# 로컬 테스트
curl http://localhost:8080/api/status

# 토큰 인증 테스트
curl http://localhost:8080/api/status \
  -H "Authorization: Bearer 생성한_토큰"
```

---

## 4. Home Assistant 설치

### 4.1 Docker로 Home Assistant 설치

```bash
# HA 설정 디렉토리 생성
mkdir -p ~/homeassistant/config

# Docker 컨테이너 실행 (테스트)
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Asia/Seoul \
  -v ~/homeassistant/config:/config \
  --network=host \
  homeassistant/home-assistant:latest
```

### 4.2 Home Assistant 초기화

1. 브라우저에서 `http://192.168.0.25:8123` 접속
2. 초기 설정 완료 (계정 생성, 위치 설정 등)
3. 대시보드 접속 확인

---

## 5. 웹훅 서버 설정

### 5.1 프로젝트 복사

```bash
# 프로젝트를 서버로 복사 (Mac에서)
rsync -avz /path/to/nugu-openclaw-ha/ user@192.168.0.25:~/nugu-openclaw-ha/

# 또는 git clone
git clone <repository-url> ~/nugu-openclaw-ha
cd ~/nugu-openclaw-ha
```

### 5.2 설정 파일 업데이트

```bash
cd ~/nugu-openclaw-ha

# 웹훅 서버 설정
nano webhook-server/config.yml
```

```yaml
server:
  host: "0.0.0.0"
  port: 5000
  debug: false

openclaw:
  url: "http://127.0.0.1:8080"
  token: "OpenClaw_토큰"
  timeout: 300

homeassistant:
  url: "http://127.0.0.1:8123"
  token: "HA_토큰_아직_없음"
  webhook_id: "nugu_to_openclaw"

logging:
  level: "INFO"
```

---

## 6. Docker로 일괄 배포

### 6.1 Docker Compose 실행

```bash
cd ~/nugu-openclaw-ha

# 설정 디렉토리 생성
mkdir -p home-assistant/ha-config
mkdir -p webhook-server/logs

# Docker Compose 시작
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f homeassistant
```

### 6.2 서비스 상태 확인

| 서비스 | URL | 상태 |
|--------|-----|------|
| Home Assistant | http://192.168.0.25:8123 | 정상 |
| 웹훅 서버 | http://192.168.0.25:5000/health | 정상 |
| OpenClaw | http://192.168.0.25:8080/api/status | 정상 |

---

## 7. Home Assistant 설정 추가

### 7.1 Long-Lived Access Token 생성

1. Home Assistant 대시보드 접속
2. **좌측 메뉴** → **설정** (하단 스크롤)
3. **프로필** → **Long-Lived Access Tokens**
4. **Create Token** 클릭
5. 이름: `nugu-openclaw`
6. 생성된 토큰 복사 (다시는 볼 수 없습니다!)

### 7.2 웹훅 서버 설정 업데이트

```bash
# HA 토큰으로 설정 업데이트
nano webhook-server/config.yml

# homeassistant.token에 생성한 토큰 입력

# Docker 재시작
docker-compose restart nugu-webhook
```

### 7.3 HA 설정 파일 추가

**방법 A: UI에서 추가**

1. **설정** → **장치 및 서비스** → **추가**
2. **RESTful Command** 검색 후 추가
3. YAML 모드로 전환하여 `home-assistant/configuration.yaml` 내용 붙여넣기

**방법 B: 파일 편집기로 추가**

1. **설정** → **서버 관리** → **파일 편집기**
2. `configuration.yaml`에 내용 추가
3. Home Assistant 재시작

---

## 8. NUGU 연동

### 8.1 NUGU Developers 포털 가입

1. [NUGU 개발자 포털](https://developers.nugu.co.kr) 접속
2. NAVER 계정으로 로그인
3. 개발자 등록

### 8.2 새 프로젝트 생성

1. **내 앱** → **새 프로젝트**
2. 프로젝트 정보 입력
3. **Bidirectional External Service** 추가

### 8.3 웹훅 URL 등록

```
웹훅 URL: http://192.168.0.25:5000/nugu/command
```

### 8.4 NUGU Play 빌더

1. **NUGU Play 빌더** 접속
2. 새 Play 생성
3. Custom Action 설정
4. 테스트 및 배포

---

## 9. 테스트 및 검증

### 9.1 개별 서비스 테스트

```bash
# 1. OpenClaw 테스트
curl http://192.168.0.25:8080/api/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 웹훅 서버 헬스 체크
curl http://192.168.0.25:5000/health

# 3. Home Assistant 접속
curl http://192.168.0.25:8123
```

### 9.2 전체 경로 테스트

```bash
# 웹훅 → OpenClaw
curl -X POST http://192.168.0.25:5000/nugu/command \
  -H "Content-Type: application/json" \
  -d '{"command": "안녕", "action": "openclaw"}'
```

### 9.3 NUGU 음성 명령 테스트

```
"아리아, 테스트해줘"
"아리아, 오늘 날씨 알려줘"
```

---

## 문제 해결

설정 중 문제가 발생하면 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참조하세요.

---

## 다음 단계

- [GUIDE.md](../GUIDE.md): 음성 명령 가이드
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): 문제 해결
- [README.md](../README.md): 프로젝트 개요

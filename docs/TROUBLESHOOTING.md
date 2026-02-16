# 문제 해결 가이드

NUGU + OpenClaw + Home Assistant 연동 중 발생할 수 있는 문제와 해결 방법을 정리했습니다.

---

## 목차

1. [연결 문제](#1-연결-문제)
2. [OpenClaw 문제](#2-openclaw-문제)
3. [Home Assistant 문제](#3-home-assistant-문제)
4. [웹훅 서버 문제](#4-웹훅-서버-문제)
5. [NUGU 관련 문제](#5-nugu-관련-문제)
6. [Docker 관련 문제](#6-docker-관련-문제)
7. [로그 확인 방법](#7-로그-확인-방법)

---

## 1. 연결 문제

### 1.1 OpenClaw에 연결할 수 없음

**증상:**
```
Error: Cannot connect to OpenClaw
Connection refused
```

**원인 분석:**
```bash
# 1. OpenClaw 실행 상태 확인
openclaw status

# 2. 포트 listening 확인
sudo netstat -tulpn | grep 8080
# 또는
sudo ss -tulpn | grep 8080
```

**해결 방법:**

1. **OpenClaw 시작**
```bash
openclaw start
# 또는 백그라운드로
openclaw start --daemon
```

2. **설정 파일 확인**
```bash
# ~/.openclaw/config.yml 확인
cat ~/.openclaw/config.yml | grep host
# host: "0.0.0.0" 이어야 함 (localhost가 아님)
```

3. **방화벽 확인**
```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8080/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# macOS (시스템 설정 → 보안 및 개인정보 보호 → 방화벽)
```

4. **테스트**
```bash
# 로컬 테스트
curl http://localhost:8080/api/status

# 원격 테스트
curl http://192.168.0.25:8080/api/status
```

### 1.2 Home Assistant에서 웹훅 서버 연결 불가

**증상:**
```
Webhook connection timeout
```

**해결 방법:**

1. **웹훅 서버 상태 확인**
```bash
# 헬스 체크
curl http://localhost:5000/health

# 예상 응답
{"status": "ok", "service": "nugu-webhook-server", ...}
```

2. **Docker 컨테이너 확인**
```bash
docker ps | grep nugu-webhook
docker logs nugu-webhook
```

3. **포트 충돌 확인**
```bash
sudo lsof -i :5000
# 또는
sudo netstat -tulpn | grep 5000
```

---

## 2. OpenClaw 문제

### 2.1 인증 토큰 오류

**증상:**
```
401 Unauthorized
Invalid token
```

**해결 방법:**

1. **토큰 일치 확인**
```bash
# OpenClaw 설정
cat ~/.openclaw/config.yml | grep token

# 웹훅 서버 설정
cat ~/nugu-openclaw-ha/webhook-server/config.yml | grep token

# HA 설정
cat ~/homeassistant/config/configuration.yaml | grep Authorization
```

2. **새 토큰 생성 및 동기화**
```bash
# 새 토큰 생성
NEW_TOKEN=$(openssl rand -hex 32)
echo $NEW_TOKEN

# OpenClaw 설정 업데이트
sed -i "s/token: .*/token: \"$NEW_TOKEN\"/" ~/.openclaw/config.yml

# 웹훅 서버 설정 업데이트
sed -i "s/YOUR_OPENCLAW_TOKEN/$NEW_TOKEN/" ~/nugu-openclaw-ha/webhook-server/config.yml

# OpenClaw 재시작
openclaw restart
```

### 2.2 OpenClaw 명령 응답 없음

**증상:**
```
Request timeout
No response from OpenClaw
```

**해결 방법:**

1. **타임아웃 설정 확인**
```yaml
# webhook-server/config.yml
openclaw:
  timeout: 600  # 10분으로 증가
```

2. **OpenClaw 로그 확인**
```bash
openclaw logs
tail -f ~/.openclaw/logs/openclaw.log
```

3. **OpenClaw 재시작**
```bash
openclaw restart
```

### 2.3 CORS 오류

**증상:**
```
CORS policy error
Access-Control-Allow-Origin missing
```

**해결 방법:**

1. **CORS 설정 확인**
```bash
cat ~/.openclaw/config.yml | grep -A 5 cors
```

2. **CORS 설정 업데이트**
```yaml
# ~/.openclaw/config.yml
cors:
  enabled: true
  origins:
    - "http://localhost:8123"
    - "http://127.0.0.1:8123"
    - "http://192.168.0.25:8123"
    - "*"
```

---

## 3. Home Assistant 문제

### 3.1 자동화가 실행되지 않음

**증상:**
```
Automation not triggered
```

**해결 방법:**

1. **자동화 활성화 확인**
- HA 대시보드 → 설정 → 자동화
- 해당 자동화가 "켜기" 상태인지 확인

2. **웹훅 ID 확인**
```yaml
# automations.yaml
webhook_id: "nugu_to_openclaw"
```

```yaml
# webhook-server/config.yml
homeassistant:
  webhook_id: "nugu_to_openclaw"
```

3. **자동화 로그 확인**
- HA 대시보드 → 설정 → 자동화 → 해당 자동화 → 실행 로그

4. **YAML 문법 검증**
```bash
# HA 설정 재시작
docker restart homeassistant
# 또는
docker-compose restart homeassistant
```

### 3.2 스크립트 실행 실패

**증상:**
```
Script failed: KeyError 'command'
```

**해결 방법:**

1. **필수 파라미터 확인**
```yaml
# scripts.yaml
script:
  openclaw_send_command:
    fields:
      command:
        required: true
```

2. **UI에서 테스트**
- HA 대시보드 → 개발자 도구 → 서비스
- `script.openclaw_send_command` 선택
- command 파라미터 입력 후 실행

### 3.3 Long-Lived Token 만료

**증상:**
```
401 Unauthorized: Invalid token
```

**해결 방법:**

1. **새 토큰 생성**
- HA 대시보드 → 설정 → 프로필
- Long-Lived Access Tokens → Create Token

2. **설정 파일 업데이트**
```bash
# webhook-server/config.yml
nano ~/nugu-openclaw-ha/webhook-server/config.yml
# homeassistant.token에 새 토큰 입력

# 웹훅 서버 재시작
docker-compose restart nugu-webhook
```

---

## 4. 웹훅 서버 문제

### 4.1 Flask 서버 시작 실패

**증상:**
```
Address already in use
Port 5000 already in use
```

**해결 방법:**

1. **포트 사용 확인**
```bash
sudo lsof -i :5000
```

2. **프로세스 종료**
```bash
kill -9 $(lsof -t -i:5000)
```

3. **포트 변경**
```yaml
# webhook-server/config.yml
server:
  port: 5001
```

### 4.2 의존성 설치 실패

**증상:**
```
ModuleNotFoundError: No module named 'flask'
```

**해결 방법:**

1. **Python 버전 확인**
```bash
python3 --version  # 3.9+ 필요
```

2. **의존성 재설치**
```bash
cd ~/nugu-openclaw-ha/webhook-server
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. NUGU 관련 문제

### 5.1 NUGU 응답 시간 초과

**증상:**
```
NUGU가 응답하지 않습니다
요청 시간 초과
```

**원인:**
- NUGU 응답 제한시간: 약 8초
- OpenClaw 작업이 더 오래 걸리면 타임아웃

**해결 방법:**

1. **비동기 처리 구현**
```python
# app.py 수정 (즉시 응답 후 백그라운드 처리)
@app.route('/nugu/command', methods=['POST'])
def receive_nugu_command():
    # 즉시 응답
    response = {"status": "accepted", "message": "명령을 전송했습니다"}
    # 백그라운드에서 OpenClaw 실행
    threading.Thread(target=send_to_openclaw_async, args=(command,)).start()
    return jsonify(response)
```

2. **NUGU 응답 분리**
- NUGU: "명령을 전송했습니다"
- OpenClaw: 결과를 HA 알림으로 전송

### 5.2 NUGU 개발자 포털 연동 어려움

**대안:**

1. **MQTT 활용**
   - NUGU → SmartThings → MQTT → HA → OpenClaw

2. **IFTTT 사용**
   - NUGU 앱에서 IFTTT 앱플레이스 실행
   - IFTTT → Webhook → 웹훅 서버

3. **수동 테스트로 구현**
```bash
curl 명령으로 직접 테스트
```

---

## 6. Docker 관련 문제

### 6.1 컨테이너 시작 실패

**증상:**
```
Container failed to start
Exit code 1
```

**해결 방법:**

1. **로그 확인**
```bash
docker logs nugu-webhook
docker logs homeassistant
```

2. **설정 마운트 확인**
```bash
docker volume ls
docker volume inspect nugu-openclaw-ha_caddy-data
```

3. **권한 문제 해결**
```bash
sudo chown -R $USER:$USER ~/nugu-openclaw-ha
```

### 6.2 network_mode host 문제

**증상:**
```
Error: network mode host not supported
```

**해결 방법:**

1. **Docker Desktop에서는 호스트 네트워크 미지원**
```yaml
# docker-compose.yml에서 bridge 네트워크로 변경
services:
  nugu-webhook:
    ports:
      - "5000:5000"
    # network_mode: host  # 제거
```

---

## 7. 로그 확인 방법

### 각 서비스 로그 위치

| 서비스 | 로그 위치 | 확인 명령어 |
|--------|-----------|-------------|
| OpenClaw | `~/.openclaw/logs/` | `openclaw logs` |
| 웹훅 서버 | `./webhook-server/logs/webhook.log` | `tail -f logs/webhook.log` |
| Home Assistant | HA UI | UI에서 확인 |
| Docker | `docker logs` | `docker logs -f <container>` |

### 실시간 로그 모니터링

```bash
# 모든 컨테이너 로그
docker-compose logs -f

# 특정 컨테이너
docker logs -f nugu-webhook
docker logs -f homeassistant

# OpenClaw
openclaw logs -f
```

---

## 추가 지원

문제가 해결되지 않으면:

1. **로그 수집**
```bash
# 로그 압축
tar -czf debug-logs.tar.gz \
  ~/.openclaw/logs/* \
  ~/nugu-openclaw-ha/webhook-server/logs/* \
  <(docker logs nugu-webhook --tail 100) \
  <(docker logs homeassistant --tail 100)
```

2. **GitHub Issue 생성**
   - 환경 정보 포함
   - 에러 메시지 포함
   - 로그 첨부

3. **커뮤니티 질문**
   - [Home Assistant 커뮤니티](https://community.home-assistant.io/)
   - [OpenClaw Discord](https://discord.gg/openclaw)

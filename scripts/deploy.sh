#!/bin/bash
# NUGU + OpenClaw + HA 배포 스크립트
# 서버: jth@192.168.0.25

set -e

# ============================================
# 설정 변수
# ============================================
SERVER_USER="jth"
SERVER_HOST="192.168.0.25"
SERVER_PW="1"  # 보안을 위해 실제 사용 시 환경 변수로 관리 권장
PROJECT_DIR="/home/jth/nugu-openclaw-ha"
REPO_URL="${REPO_URL:-https://github.com/USERNAME/nugu-openclaw-ha.git}"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# 유틸리티 함수
# ============================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# 원격 명령 실행 함수
# ============================================
remote_exec() {
    ssh "${SERVER_USER}@${SERVER_HOST}" "$1"
}

# ============================================
# 배포 단계
# ============================================

echo "=========================================="
echo "  NUGU + OpenClaw + HA 배포 스크립트"
echo "=========================================="
echo ""

# 1. SSH 연결 테스트
log_info "1. SSH 연결 테스트..."
if remote_exec "echo 'SSH 연결 성공'" > /dev/null 2>&1; then
    log_success "SSH 연결 확인 완료"
else
    log_error "SSH 연결 실패. sshpass를 사용하거나 SSH 키를 설정하세요."
    log_info "sshpass 설치: brew install sshpass (macOS)"
    exit 1
fi

# 2. 기존 프로젝트 확인 및 백업
log_info "2. 기존 프로젝트 확인..."
if remote_exec "[ -d ${PROJECT_DIR} ]"; then
    log_warning "기존 프로젝트가 존재합니다. 백업 후 업데이트합니다."
    BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    remote_exec "mv ${PROJECT_DIR} ${BACKUP_DIR}" || true
    log_success "백업 완료: ${BACKUP_DIR}"
fi

# 3. 프로젝트 클론
log_info "3. 프로젝트 클론..."
remote_exec "git clone ${REPO_URL} ${PROJECT_DIR}" || {
    log_error "Git 클론 실패. REPO_URL을 확인하세요: ${REPO_URL}"
    exit 1
}
log_success "프로젝트 클론 완료"

# 4. OpenClaw 설치 확인
log_info "4. OpenClaw 설치 확인..."
if remote_exec "command -v openclaw" > /dev/null 2>&1; then
    OPENCLAW_VERSION=$(remote_exec "openclaw --version" 2>/dev/null || echo "unknown")
    log_success "OpenClaw 이미 설치됨: ${OPENCLAW_VERSION}"
else
    log_warning "OpenClaw가 설치되지 않았습니다. 설치를 시도합니다..."

    # Node.js 확인
    if ! remote_exec "command -v node" > /dev/null 2>&1; then
        log_info "Node.js 설치 중..."
        remote_exec "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs"
    fi

    # OpenClaw 설치
    log_info "OpenClaw 설치 중..."
    remote_exec "npm install -g @anthropic-ai/openclaw" || {
        log_warning "npm 설치 실패. curl 설치 시도..."
        remote_exec "curl -fsSL https://get.openclaw.ai | sh" || {
            log_error "OpenClaw 설치 실패. 수동 설치가 필요합니다."
            log_info "설치 가이드: https://openclaw.ai/docs/installation"
        }
    }

    if remote_exec "command -v openclaw" > /dev/null 2>&1; then
        log_success "OpenClaw 설치 완료"
    fi
fi

# 5. OpenClaw 경로 확인
log_info "5. OpenClaw 경로 확인..."
OPENCLAW_PATH=$(remote_exec "which openclaw" 2>/dev/null || echo "")
if [ -n "$OPENCLAW_PATH" ]; then
    log_success "OpenClaw 경로: ${OPENCLAW_PATH}"
else
    log_warning "OpenClaw 경로를 찾을 수 없습니다."
    # 일반적인 경로들 확인
    for path in "/usr/local/bin/openclaw" "/usr/bin/openclaw" "$HOME/.npm-global/bin/openclaw"; do
        if remote_exec "[ -f ${path} ]"; then
            OPENCLAW_PATH=$path
            log_info "발견된 경로: ${OPENCLAW_PATH}"
            break
        fi
    done
fi

# 6. Docker Compose 파일 업데이트 (OpenClaw 경로)
log_info "6. Docker Compose 설정..."
if [ -n "$OPENCLAW_PATH" ]; then
    # OpenClaw 경로로 docker-compose.yml 업데이트
    remote_exec "cd ${PROJECT_DIR} && sed -i 's|/home/jth/.nvm/versions/node/v24.13.1/bin/openclaw|${OPENCLAW_PATH}|g' docker-compose.yml"
fi

# 7. 설정 파일 생성
log_info "7. 설정 파일 확인..."
remote_exec "cd ${PROJECT_DIR} && [ -f webhook-server/config.yml ] || cp webhook-server/config.yml.example webhook-server/config.yml 2>/dev/null || echo '기본 config.yml 사용'"

# 8. Docker 실행
log_info "8. Docker 컨테이너 실행..."
remote_exec "cd ${PROJECT_DIR} && docker-compose pull && docker-compose up -d --build" || {
    log_error "Docker 실행 실패"
    exit 1
}
log_success "Docker 컨테이너 시작 완료"

# 9. 헬스체크
log_info "9. 헬스체크..."
sleep 5  # 컨테이너 시작 대기

HEALTH_CHECK_URL="http://${SERVER_HOST}:5000/health"
for i in {1..10}; do
    if curl -s "${HEALTH_CHECK_URL}" | grep -q '"status": "ok"'; then
        log_success "웹훅 서버 정상 작동!"
        break
    fi
    if [ $i -eq 10 ]; then
        log_error "헬스체크 실패. 로그를 확인하세요."
        remote_exec "docker logs nugu-webhook --tail 50"
        exit 1
    fi
    log_info "헬스체크 재시도... ($i/10)"
    sleep 3
done

# 10. 배포 완료 요약
echo ""
echo "=========================================="
log_success "배포 완료!"
echo "=========================================="
echo ""
echo "서버 정보:"
echo "  - 웹훅 서버: http://${SERVER_HOST}:5000"
echo "  - Home Assistant: http://${SERVER_HOST}:8123"
echo ""
echo "테스트 명령어:"
echo "  curl http://${SERVER_HOST}:5000/health"
echo "  curl -X POST http://${SERVER_HOST}:5000/nugu/command/cli -H 'Content-Type: application/json' -d '{\"command\": \"오늘 날씨 알려줘\"}'"
echo ""
echo "로그 확인:"
echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'docker logs nugu-webhook -f'"
echo ""

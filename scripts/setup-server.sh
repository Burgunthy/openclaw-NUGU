#!/bin/bash
# ============================================
# NUGU + OpenClaw + HA Setup Script
# Target: jth-server@192.168.0.25
# ============================================

set -e

echo "=========================================="
echo "NUGU + OpenClaw + HA 설치 스크립트"
echo "=========================================="
echo ""

echo "=== 1단계: 프로젝트 디렉토리 확인 ==="
cd ~/nugu-openclaw-ha || exit 1
echo "현재 디렉토리: $(pwd)"
echo ""

echo "=== 2단계: Docker 설치 확인 ==="
if ! command -v docker &> /dev/null; then
    echo "Docker가 설치되어 있지 않습니다. 설치를 진행합니다..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Docker 설치 완료. 재로그인이 필요할 수 있습니다."
else
    echo "✓ Docker 버전: $(docker --version)"
fi
echo ""

echo "=== 3단계: Docker Compose 설치 확인 ==="
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose 설치 중..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "✓ Docker Compose 설치됨"
fi
echo ""

echo "=== 4단계: Home Assistant 설정 디렉토리 생성 ==="
mkdir -p home-assistant/ha-config
mkdir -p webhook-server/logs
echo "✓ 디렉토리 생성 완료"
echo ""

echo "=== 5단계: OpenClaw 설정 파일 복사 ==="
if [ -f ~/.openclaw/config.yml ]; then
    echo "기존 OpenClaw 설정 백업"
    cp ~/.openclaw/config.yml ~/.openclaw/config.yml.backup.$(date +%Y%m%d_%H%M%S)
fi
mkdir -p ~/.openclaw
cp openclaw/config.yml ~/.openclaw/config.yml
echo "✓ OpenClaw 설정 파일 복사 완료"
echo ""

echo "=== 6단계: 보안 토큰 생성 (이미 생성된 경우 건너뜀) ==="
if grep -q "YOUR_SECURE_TOKEN_HERE" ~/.openclaw/config.yml 2>/dev/null; then
    echo "새로운 보안 토큰 생성 중..."
    NEW_TOKEN=$(openssl rand -hex 32)
    sed -i "s/YOUR_SECURE_TOKEN_HERE/$NEW_TOKEN/g" ~/.openclaw/config.yml
    sed -i "s/YOUR_OPENCLAW_TOKEN/$NEW_TOKEN/g" webhook-server/config.yml
    sed -i "s/YOUR_OPENCLAW_TOKEN/$NEW_TOKEN/g" home-assistant/configuration.yaml
    echo "✓ 토큰 생성 완료"
    echo "토큰: $NEW_TOKEN"
else
    echo "토큰이 이미 설정되어 있습니다."
fi
echo ""

echo "=== 7단계: HA Long-Lived Token 생성 안내 ==="
echo "Home Assistant 시작 후 다음 단계를 수행하세요:"
echo "1. http://192.168.0.25:8123 접속"
echo "2. 설정 → 프로필 → Long-Lived Access Tokens → Create Token"
echo "3. 생성된 토큰으로 webhook-server/config.yml 업데이트"
echo ""

echo "=========================================="
echo "준비 완료!"
echo "=========================================="
echo ""
echo "다음 명령으로 서비스 시작:"
echo "  docker-compose up -d"
echo ""
echo "상태 확인:"
echo "  docker-compose ps"
echo "  docker-compose logs -f"

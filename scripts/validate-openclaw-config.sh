#!/bin/bash
# OpenClaw 설정 파일 유효성 검사 스크립트
# 사용법: ./validate-openclaw-config.sh

CONFIG_FILE="$HOME/.openclaw/openclaw.json"
BACKUP_DIR="$HOME/.openclaw/backups"

# 설정 파일 존재 확인
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ OpenClaw config file not found: $CONFIG_FILE"
    exit 1
fi

# JSON 문법 검사
if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
    echo "❌ Invalid JSON syntax in $CONFIG_FILE"
    exit 1
fi

# 중복 키 검사 (compaction 등)
DUPLICATE_KEYS=$(cat "$CONFIG_FILE" | grep -o '"[a-zA-Z_]*"[[:space:]]*:' | sort | uniq -d)
if [ -n "$DUPLICATE_KEYS" ]; then
    echo "⚠️  Potential duplicate keys found in same object:"
    echo "$DUPLICATE_KEYS"
fi

# 알려진 잘못된 키 검사
INVALID_KEYS=("targetTokens" "triggerTokens" "runTimeoutSeconds")
FOUND_INVALID=""

for key in "${INVALID_KEYS[@]}"; do
    if grep -q "\"$key\"" "$CONFIG_FILE"; then
        FOUND_INVALID="$FOUND_INVALID $key"
    fi
done

if [ -n "$FOUND_INVALID" ]; then
    echo "❌ Invalid keys found in config:$FOUND_INVALID"
    echo "   These keys are not recognized by OpenClaw and will cause errors."
    echo ""
    echo "Run: openclaw doctor --fix"
    echo "Or manually remove these keys from $CONFIG_FILE"
    exit 1
fi

# OpenClaw로 검증
echo "Running OpenClaw config validation..."
if ! openclaw doctor 2>&1 | grep -q "Config valid"; then
    echo "⚠️  OpenClaw doctor found issues. Run: openclaw doctor --fix"
    exit 1
fi

echo "✅ OpenClaw config is valid"

# 백업 생성
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/openclaw.json.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "📁 Backup created: $BACKUP_FILE"

# 오래된 백업 정리 (7개일 이상)
find "$BACKUP_DIR" -name "openclaw.json.*" -mtime +7 -delete 2>/dev/null

exit 0

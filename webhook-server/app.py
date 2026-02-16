"""
NUGU Webhook Server
NUGU 스피커로부터 받은 명령을 Home Assistant 또는 OpenClaw로 전달하는 중계 서버
"""

from flask import Flask, request, jsonify
import requests
import yaml
import os
import logging
from datetime import datetime
from pathlib import Path
from openclaw_cli import get_openclaw_cli

app = Flask(__name__)

# 설정 로드
CONFIG_PATH = Path(__file__).parent / 'config.yml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 로깅 설정
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'webhook.log'

logging.basicConfig(
    level=getattr(logging, config.get('logging', {}).get('level', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "ok",
        "service": "nugu-webhook-server",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/nugu/command', methods=['POST'])
def receive_nugu_command():
    """
    NUGU로부터 명령 수신
    NUGU 스피커 또는 NUGU 앱에서 전송된 명령을 처리합니다.
    """
    try:
        data = request.json
        if not data:
            logger.warning("Received empty JSON payload")
            return jsonify({"error": "empty payload"}), 400

        # 명령 파싱
        command = data.get('command', '')
        action = data.get('action', 'openclaw')

        if not command:
            logger.warning("Received request without command")
            return jsonify({"error": "command is required"}), 400

        # 로깅
        logger.info(f"Received command: '{command}', action: {action}")

        if action == 'openclaw':
            # OpenClaw로 직접 전송 (REST API 경로)
            response = send_to_openclaw(command, data.get('context', {}))
        elif action == 'cli':
            # OpenClaw CLI로 직접 실행
            openclaw_cli = get_openclaw_cli()
            parsed = parse_command_type(command)

            if parsed['type'] == 'weather':
                response = openclaw_cli.get_weather(parsed.get('location', '서울'))
            elif parsed['type'] == 'web_search':
                response = openclaw_cli.search_web(parsed.get('query', command))
            elif parsed['type'] == 'schedule':
                response = openclaw_cli.get_schedule(parsed.get('when', '오늘'))
            else:
                response = openclaw_cli.execute_command(command, data.get('context', {}))
        elif action == 'ha':
            # Home Assistant로 전송
            response = send_to_ha(command, data.get('context', {}))
        else:
            logger.warning(f"Unknown action: {action}")
            return jsonify({"error": f"Unknown action: {action}"}), 400

        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "result": response
        })

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/nugu/openclaw', methods=['POST'])
def send_to_openclaw_direct():
    """
    OpenClaw로 직접 명령 전송하는 엔드포인트
    Home Assistant 자동화에서 호출할 수 있습니다.
    """
    try:
        data = request.json
        command = data.get('command', '')

        if not command:
            return jsonify({"error": "command is required"}), 400

        logger.info(f"Sending to OpenClaw: '{command}'")
        response = send_to_openclaw(command, data.get('context', {}))

        return jsonify({
            "status": "success",
            "result": response
        })

    except Exception as e:
        logger.error(f"Error sending to OpenClaw: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/nugu/command/cli', methods=['POST'])
def execute_openclaw_cli():
    """
    OpenClaw CLI로 직접 명령 실행하는 엔드포인트
    날씨, 검색 등 다양한 명령을 처리합니다.

    Use Case 예시:
    - "날씨 알려줘" → OpenClaw 날씨 검색
    - "서울 날씨 어때" → OpenClaw 날씨 검색
    - "오늘 뉴스 검색해줘" → OpenClaw 웹 검색
    """
    try:
        data = request.json
        if not data:
            logger.warning("Received empty JSON payload")
            return jsonify({"error": "empty payload"}), 400

        command = data.get('command', '')
        if not command:
            logger.warning("Received request without command")
            return jsonify({"error": "command is required"}), 400

        logger.info(f"CLI endpoint received command: '{command}'")

        # OpenClaw CLI 인스턴스 가져오기
        openclaw_cli = get_openclaw_cli()

        # 명령 타입 판별 및 실행
        parsed = parse_command_type(command)

        if parsed['type'] == 'weather':
            # 날씨 관련 명령
            location = parsed.get('location', '서울')
            logger.info(f"Weather query detected for location: {location}")
            result = openclaw_cli.get_weather(location)

        elif parsed['type'] == 'web_search':
            # 웹 검색 명령
            query = parsed.get('query', command)
            logger.info(f"Web search query detected: {query}")
            result = openclaw_cli.search_web(query)

        elif parsed['type'] == 'schedule':
            # 일정 조회 명령
            when = parsed.get('when', '오늘')
            logger.info(f"Schedule query detected for: {when}")
            result = openclaw_cli.get_schedule(when)

        else:
            # 일반 명령 처리
            logger.info(f"Generic command execution: {command}")
            result = openclaw_cli.execute_command(
                command,
                context=data.get('context', {'source': 'nugu'})
            )

        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "command_type": parsed['type'],
            "result": result
        })

    except Exception as e:
        logger.error(f"Error executing CLI command: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def parse_command_type(command: str) -> dict:
    """
    명령 타입을 판별하고 관련 정보를 추출합니다.

    Args:
        command: 사용자 명령 텍스트

    Returns:
        {'type': command_type, ...additional_params}
    """
    command_lower = command.lower()

    # 날씨 관련 키워드 체크
    weather_keywords = ['날씨', 'weather', '기온', 'temperature', '비', '눈', '바람']
    if any(keyword in command_lower for keyword in weather_keywords):
        # 위치 추출 (간단 구현)
        locations = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '수원', '강남', '홍대']
        location = '서울'  # 기본값
        for loc in locations:
            if loc in command:
                location = loc
                break
        return {'type': 'weather', 'location': location}

    # 검색 관련 키워드 체크
    search_keywords = ['검색', 'search', '찾아줘', '알려줘', '조사']
    if any(keyword in command_lower for keyword in search_keywords):
        # 검색어 추출
        query = command
        for keyword in ['검색해줘', '검색', '찾아줘']:
            if keyword in command:
                query = command.replace(keyword, '').strip()
                break
        return {'type': 'web_search', 'query': query}

    # 일정 관련 키워드 체크
    schedule_keywords = ['일정', 'schedule', '약속', '회의', '미팅', '캘린더', 'calendar']
    time_keywords = {
        '오늘': '오늘',
        '내일': '내일',
        '다음주': '다음주',
        '이번주': '이번주',
        'tomorrow': '내일',
        'today': '오늘'
    }
    if any(keyword in command_lower for keyword in schedule_keywords):
        when = '오늘'  # 기본값
        for time_kw, time_val in time_keywords.items():
            if time_kw in command_lower:
                when = time_val
                break
        return {'type': 'schedule', 'when': when}

    # 기본 명령
    return {'type': 'general'}


def send_to_openclaw(command: str, context: dict = None) -> dict:
    """
    OpenClaw PC로 명령 전송

    Args:
        command: 실행할 명령 텍스트
        context: 추가 컨텍스트 정보

    Returns:
        OpenClaw 응답
    """
    url = f"{config['openclaw']['url']}/api/execute"
    headers = {
        "Authorization": f"Bearer {config['openclaw']['token']}",
        "Content-Type": "application/json"
    }

    payload = {
        "command": command,
        "source": "nugu",
        "context": context or {}
    }

    try:
        logger.info(f"POST {url} - {payload}")
        resp = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=config.get('openclaw', {}).get('timeout', 300)
        )
        resp.raise_for_status()

        result = resp.json()
        logger.info(f"OpenClaw response: {result}")
        return result

    except requests.exceptions.Timeout:
        error_msg = "OpenClaw request timeout"
        logger.error(error_msg)
        return {"error": error_msg}
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to OpenClaw"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        logger.error(f"OpenClaw error: {e}")
        return {"error": str(e)}


def send_to_ha(command: str, context: dict = None) -> dict:
    """
    Home Assistant 웹훅으로 전송

    Args:
        command: 실행할 명령 텍스트
        context: 추가 컨텍스트 정보

    Returns:
        HA 응답
    """
    url = f"{config['homeassistant']['url']}/api/webhook/{config['homeassistant']['webhook_id']}"
    headers = {
        "Authorization": f"Bearer {config['homeassistant']['token']}",
        "Content-Type": "application/json"
    }

    payload = {
        "command": command,
        "context": context or {}
    }

    try:
        logger.info(f"POST {url} - {payload}")
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()

        result = resp.json() if resp.content else {"status": "accepted"}
        logger.info(f"HA response: {result}")
        return result

    except Exception as e:
        logger.error(f"HA error: {e}")
        return {"error": str(e)}


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "internal server error"}), 500


if __name__ == '__main__':
    server_config = config.get('server', {})
    app.run(
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 5000),
        debug=server_config.get('debug', False)
    )

"""
Pytest Fixtures for NUGU Webhook Server Tests
Provides common fixtures and test utilities
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'server': {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': False
        },
        'logging': {
            'level': 'DEBUG'
        },
        'openclaw': {
            'url': 'http://localhost:8000',
            'token': 'test_openclaw_token',
            'timeout': 300
        },
        'homeassistant': {
            'url': 'http://localhost:8123',
            'token': 'test_ha_token',
            'webhook_id': 'test_webhook_id'
        }
    }


@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as f:
        yaml.dump(sample_config, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def mock_openclaw_cli():
    """Mock OpenClaw CLI instance"""
    mock = MagicMock()
    mock.execute_command.return_value = {
        'status': 'success',
        'output': {'text': 'Command executed successfully'}
    }
    mock.get_weather.return_value = {
        'status': 'success',
        'output': {'temperature': '20°C', 'condition': 'sunny'}
    }
    mock.search_web.return_value = {
        'status': 'success',
        'output': {'results': ['result1', 'result2']}
    }
    mock.get_schedule.return_value = {
        'status': 'success',
        'output': {'events': ['meeting at 10am']}
    }
    return mock


@pytest.fixture
def app_with_mock_config(temp_config_file, mock_openclaw_cli):
    """Create Flask app with mocked config and dependencies"""
    # Patch config file path
    with patch('app.CONFIG_PATH', Path(temp_config_file)):
        with patch('app.get_openclaw_cli', return_value=mock_openclaw_cli):
            # Import app after patching
            import app
            app.app.config['TESTING'] = True
            app.app.config['WTF_CSRF_ENABLED'] = False

            yield app.app


@pytest.fixture
def client(app_with_mock_config):
    """Flask test client"""
    return app_with_mock_config.test_client()


@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch('app.requests') as mock:
        mock.post.return_value = Mock(
            status_code=200,
            json=lambda: {'result': 'success'},
            raise_for_status=lambda: None
        )
        yield mock


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for OpenClaw CLI testing"""
    with patch('openclaw_cli.subprocess') as mock:
        mock.run.return_value = Mock(
            returncode=0,
            stdout='{"result": "success"}',
            stderr=''
        )
        yield mock


@pytest.fixture
def sample_nugu_payload():
    """Sample NUGU webhook payload"""
    return {
        'command': '서울 날씨 알려줘',
        'action': 'cli',
        'context': {
            'user_id': 'test_user',
            'device': 'nugu_speaker'
        }
    }


@pytest.fixture
def weather_payloads():
    """Various weather command payloads"""
    return [
        {'command': '날씨 알려줘', 'action': 'cli'},
        {'command': '서울 날씨 어때', 'action': 'cli'},
        {'command': '부산 날씨 검색해줘', 'action': 'cli'},
        {'command': 'weather today', 'action': 'cli'}
    ]


@pytest.fixture
def search_payloads():
    """Various search command payloads"""
    return [
        {'command': '오늘 뉴스 검색해줘', 'action': 'cli'},
        {'command': '파이썬에 대해 찾아줘', 'action': 'cli'},
        {'command': '최신 IT 기사 조사해줘', 'action': 'cli'}
    ]


@pytest.fixture
def schedule_payloads():
    """Various schedule command payloads"""
    return [
        {'command': '오늘 일정 뭐야', 'action': 'cli'},
        {'command': '내일 약속 있어', 'action': 'cli'},
        {'command': '다음주 회의 일정 확인', 'action': 'cli'}
    ]


@pytest.fixture
def mock_log_dir():
    """Create a temporary log directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / 'logs'
        log_path.mkdir()
        yield log_path

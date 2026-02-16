"""
Webhook Server Tests
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """헬스 체크 엔드포인트 테스트"""
    rv = client.get('/health')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'nugu-webhook-server'


def test_receive_nugu_command_missing_command(client):
    """명령 없이 요청 시 400 에러 반환"""
    rv = client.post('/nugu/command', json={})
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'error' in data


def test_receive_nugu_command_with_command(client, mocker):
    """명령과 함께 요청 시 성공 반환 (mock 사용)"""
    # OpenClaw 호출을 mock
    mock_post = mocker.patch('app.requests.post')
    mock_post.return_value.json.return_value = {'status': 'success'}
    mock_post.return_value.raise_for_status = lambda: None

    rv = client.post('/nugu/command', json={
        'command': '테스트 명령',
        'action': 'openclaw'
    })
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'success'


def test_send_to_openclaw_direct_missing_command(client):
    """OpenClaw 직접 전송 엔드포인트 테스트 - 명령 없음"""
    rv = client.post('/nugu/openclaw', json={})
    assert rv.status_code == 400


def test_404_handler(client):
    """존재하지 않는 엔드포인트 테스트"""
    rv = client.get('/nonexistent')
    assert rv.status_code == 404

"""
OpenClaw CLI Wrapper Tests
"""

import pytest
from unittest.mock import patch, MagicMock
from openclaw_cli import OpenClawCLI, get_openclaw_cli


class TestOpenClawCLI:
    """OpenClaw CLI 래퍼 테스트"""

    def test_init(self):
        """초기화 테스트"""
        cli = OpenClawCLI()
        assert cli.openclaw_path == "openclaw"

    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """명령 실행 성공 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"status": "success", "message": "테스트 완료"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        cli = OpenClawCLI()
        result = cli.execute_command("테스트 명령")

        assert result["status"] == "success"
        assert result["command"] == "테스트 명령"
        assert result["return_code"] == 0
        assert "output" in result

    @patch('subprocess.run')
    def test_execute_command_non_json_output(self, mock_run):
        """JSON이 아닌 출력 처리 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "일반 텍스트 출력"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        cli = OpenClawCLI()
        result = cli.execute_command("테스트")

        assert result["status"] == "success"
        assert result["output"]["text_output"] == "일반 텍스트 출력"

    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """타임아웃 테스트"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="openclaw", timeout=70)

        cli = OpenClawCLI()
        result = cli.execute_command("긴 명령")

        assert result["status"] == "error"
        assert result["error_type"] == "timeout"

    @patch('subprocess.run')
    def test_execute_command_not_found(self, mock_run):
        """OpenClaw 미설치 테스트"""
        mock_run.side_effect = FileNotFoundError()

        cli = OpenClawCLI()
        result = cli.execute_command("명령")

        assert result["status"] == "error"
        assert result["error_type"] == "not_found"

    @patch('subprocess.run')
    def test_execute_command_general_error(self, mock_run):
        """일반 오류 테스트"""
        mock_run.side_effect = Exception("알 수 없는 오류")

        cli = OpenClawCLI()
        result = cli.execute_command("명령")

        assert result["status"] == "error"
        assert result["error_type"] == "unknown"

    @patch('subprocess.run')
    def test_search_web(self, mock_run):
        """웹 검색 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"results": ["결과1", "결과2"]}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        cli = OpenClawCLI()
        result = cli.search_web("날씨")

        assert result["status"] == "success"
        # 검색어가 포맷되어 전달되는지 확인
        call_args = mock_run.call_args
        assert "검색해줘: 날씨" in call_args[0][0]

    @patch('subprocess.run')
    def test_get_weather(self, mock_run):
        """날씨 조회 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"weather": "맑음", "temp": 22}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        cli = OpenClawCLI()
        result = cli.get_weather("서울")

        assert result["status"] == "success"
        call_args = mock_run.call_args
        assert "서울 날씨 알려줘" in call_args[0][0]

    @patch('subprocess.run')
    def test_get_weather_default_location(self, mock_run):
        """기본 위치 날씨 조회 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"weather": "맑음"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        cli = OpenClawCLI()
        result = cli.get_weather()  # 위치 지정 안 함

        assert result["status"] == "success"
        call_args = mock_run.call_args
        assert "서울 날씨 알려줘" in call_args[0][0]

    @patch('subprocess.run')
    def test_get_schedule(self, mock_run):
        """일정 조회 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"events": ["회의", "점심"]}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        cli = OpenClawCLI()
        result = cli.get_schedule("내일")

        assert result["status"] == "success"
        call_args = mock_run.call_args
        assert "내일 일정 뭐야?" in call_args[0][0]

    @patch('subprocess.run')
    def test_get_schedule_default_time(self, mock_run):
        """기본 시간 일정 조회 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"events": []}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        cli = OpenClawCLI()
        result = cli.get_schedule()  # 시간 지정 안 함

        assert result["status"] == "success"
        call_args = mock_run.call_args
        assert "오늘 일정 뭐야?" in call_args[0][0]


class TestGetOpenClawCLI:
    """싱글톤 함수 테스트"""

    def test_singleton(self):
        """싱글톤 패턴 테스트"""
        cli1 = get_openclaw_cli()
        cli2 = get_openclaw_cli()

        assert cli1 is cli2

    def test_instance_type(self):
        """반환 타입 테스트"""
        cli = get_openclaw_cli()
        assert isinstance(cli, OpenClawCLI)


class TestEnvWithConcontext:
    """환경 변수 테스트"""

    def test_get_env_with_context(self):
        """컨텍스트 환경 변수 변환 테스트"""
        import os

        cli = OpenClawCLI()
        env = cli._get_env_with_context({"source": "nugu", "user": "test"})

        assert env["OPENCLAW_CONTEXT_SOURCE"] == "nugu"
        assert env["OPENCLAW_CONTEXT_USER"] == "test"

    def test_get_env_without_context(self):
        """컨텍스트 없이 환경 변수 테스트"""
        import os

        cli = OpenClawCLI()
        env = cli._get_env_with_context(None)

        # 기존 환경 변수가 유지되는지 확인
        assert "PATH" in env

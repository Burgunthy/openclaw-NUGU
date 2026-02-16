"""
OpenClaw CLI Wrapper
OpenClaw CLI를 통해 OpenClaw 기능을 실행하는 래퍼
"""

import subprocess
import json
import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OpenClawCLI:
    """OpenClaw CLI 실행"""

    def __init__(self):
        self.openclaw_path = "openclaw"

    def execute_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        OpenClaw CLI로 명령 실행

        Args:
            command: 실행할 명령 텍스트
            context: 추가 컨텍스트

        Returns:
            OpenClaw 실행 결과
        """
        try:
            # OpenClaw 로그 확인
            logger.info(f"Executing OpenClaw command: {command}")

            # OpenClaw CLI를 통해 로컬 에이전트 실행
            # openclaw agent --local --message "{command}" --json --timeout 60
            cmd = [
                self.openclaw_path,
                "agent",
                "--local",
                "--message", command,
                "--json",
                "--timeout", "60"
            ]

            logger.info(f"Running command: {' '.join(cmd)}")

            # OpenClaw 실행을 위한 작업 디렉토리
            openclaw_cwd = "/usr/local/lib/node_modules/openclaw"

            # subprocess 실행
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=70,  # 명령 타임아웃보다 10초 여유
                cwd=openclaw_cwd,  # OpenClaw 모듈 디렉토리에서 실행
                env=self._get_env_with_context(context)
            )

            # 출력 로깅
            if result.stdout:
                logger.info(f"OpenClaw stdout: {result.stdout[:500]}")  # 처음 500자만
            if result.stderr:
                logger.warning(f"OpenClaw stderr: {result.stderr[:500]}")

            # JSON 파싱 시도
            try:
                output_data = json.loads(result.stdout) if result.stdout else {}
            except json.JSONDecodeError:
                # JSON이 아닌 경우 텍스트 응답 처리
                output_data = {
                    "text_output": result.stdout,
                    "stderr": result.stderr
                }

            return {
                "status": "success",
                "command": command,
                "source": "nugu",
                "context": context or {},
                "return_code": result.returncode,
                "output": output_data,
                "raw_output": result.stdout
            }

        except subprocess.TimeoutExpired:
            error_msg = "OpenClaw command timeout (70s)"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "error_type": "timeout",
                "command": command
            }
        except FileNotFoundError:
            error_msg = "OpenClaw CLI not found. Please install OpenClaw."
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "error_type": "not_found",
                "command": command
            }
        except Exception as e:
            logger.error(f"OpenClaw CLI error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": "unknown",
                "command": command
            }

    def _get_env_with_context(self, context: Dict[str, Any] = None) -> Dict[str, str]:
        """컨텍스트를 환경 변수로 변환"""
        import os
        env = os.environ.copy()

        if context:
            # 컨텍스트 정보를 환경 변수에 추가
            for key, value in context.items():
                env_key = f"OPENCLAW_CONTEXT_{key.upper()}"
                env[env_key] = str(value)

        return env

    async def execute_async(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        OpenClaw 비동기 명령 실행
        긴 작업의 경우 백그라운드에서 실행
        """
        try:
            # TODO: 비동기 실행 구현
            return await asyncio.to_thread(
                self.execute_command,
                command,
                context
            )
        except Exception as e:
            logger.error(f"Async OpenClaw error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def search_web(self, query: str) -> Dict[str, Any]:
        """
        웹 검색 실행

        Args:
            query: 검색어

        Returns:
            검색 결과
        """
        command = f"검색해줘: {query}"
        return self.execute_command(command, {"type": "web_search"})

    def get_weather(self, location: str = "서울") -> Dict[str, Any]:
        """
        날씨 정보 조회

        Args:
            location: 위치 (기본값: 서울)

        Returns:
            날씨 정보
        """
        command = f"{location} 날씨 알려줘"
        return self.execute_command(command, {"type": "weather"})

    def get_schedule(self, when: str = "오늘") -> Dict[str, Any]:
        """
        일정 조회

        Args:
            when: 시간 (기본값: 오늘)

        Returns:
            일정 정보
        """
        command = f"{when} 일정 뭐야?"
        return self.execute_command(command, {"type": "calendar"})


# 싱글톤 클래스
_openclaw_cli_instance: Optional[OpenClawCLI] = None

def get_openclaw_cli() -> OpenClawCLI:
    """OpenClaw CLI 싱글톤 인스턴스 반환"""
    global _openclaw_cli_instance
    if _openclaw_cli_instance is None:
        _openclaw_cli_instance = OpenClawCLI()
    return _openclaw_cli_instance

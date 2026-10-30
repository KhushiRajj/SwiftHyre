from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

MAX_CODE_BYTES = 100_000
MAX_INPUT_BYTES = 100_000
MAX_TIMEOUT_SECONDS = 30
SUPPORTED_LANGUAGES = {
    'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'c++',
    'csharp', 'go', 'rust', 'php', 'ruby',
}

ExecutionStatus = Literal['completed', 'timeout', 'unavailable', 'invalid']


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    stdout: str
    stderr: str
    duration_ms: int | None = None
    exit_code: int | None = None


class RunnerProvider(Protocol):
    def run(self, source: str, language: str, stdin: str, timeout_seconds: int) -> ExecutionResult:
        ...


class CodeRunner:
    def __init__(
        self,
        provider: RunnerProvider | None = None,
        api_key: str | None = None,
    ) -> None:
        if provider is None:
            from .onlinecompiler import OnlineCompilerProvider

            provider = OnlineCompilerProvider(api_key=api_key)
        self._provider = provider

    def run(
        self,
        source: str,
        language: str,
        stdin: str,
        timeout_seconds: int,
    ) -> ExecutionResult:
        if not isinstance(source, str) or not isinstance(stdin, str):
            return ExecutionResult('invalid', '', 'Code and input must be text.')

        try:
            source_bytes = source.encode('utf-8')
            input_bytes = stdin.encode('utf-8')
        except UnicodeEncodeError:
            return ExecutionResult('invalid', '', 'Code and input must be valid UTF-8.')

        if '\x00' in source or '\x00' in stdin:
            return ExecutionResult('invalid', '', 'Code and input cannot contain NUL characters.')
        if len(source_bytes) > MAX_CODE_BYTES:
            return ExecutionResult('invalid', '', 'Code exceeds the 100 KB limit.')
        if len(input_bytes) > MAX_INPUT_BYTES:
            return ExecutionResult('invalid', '', 'Input exceeds the 100 KB limit.')
        if type(timeout_seconds) is not int or not 0 < timeout_seconds <= MAX_TIMEOUT_SECONDS:
            return ExecutionResult('invalid', '', 'Timeout must be between 0 and 30 seconds.')
        if not isinstance(language, str) or language.strip().lower() not in SUPPORTED_LANGUAGES:
            return ExecutionResult('unavailable', '', 'The requested language is unavailable.')

        return self._provider.run(
            source,
            language.strip().lower(),
            stdin,
            timeout_seconds,
        )

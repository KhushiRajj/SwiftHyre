from __future__ import annotations

import json
import logging
import os
import urllib.request
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request

from .runner import ExecutionResult

LOGGER = logging.getLogger(__name__)
API_URL = 'https://api.onlinecompiler.io/api/run-code-sync/'
COMPILER_IDS = {
    'python': 'python-3.14',
    'javascript': 'nodejs-24',
    'typescript': 'typescript-deno',
    'java': 'openjdk-25',
    'c': 'gcc-15',
    'cpp': 'g++-15',
    'c++': 'g++-15',
    'csharp': 'dotnet-csharp-10',
    'go': 'go-1.26',
    'rust': 'rust-1.93',
    'php': 'php-8.5',
    'ruby': 'ruby-4.0',
}


class OnlineCompilerProvider:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get('ONLINECOMPILER_API_KEY')

    def run(self, source: str, language: str, stdin: str, timeout_seconds: int) -> ExecutionResult:
        compiler = COMPILER_IDS.get(language.strip().lower())
        if compiler is None:
            return ExecutionResult('unavailable', '', 'The requested language is unavailable.')
        if not self._api_key:
            return ExecutionResult('unavailable', '', 'Code execution provider is not configured.')

        payload = json.dumps({
            'compiler': compiler,
            'code': source,
            'input': stdin,
            'time_limit': timeout_seconds,
        }).encode('utf-8')
        request = Request(
            API_URL,
            data=payload,
            headers={
                'Authorization': self._api_key,
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        started = perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds + 10) as response:
                body = json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            LOGGER.warning('OnlineCompiler request failed with HTTP %s', exc.code)
            if exc.code in {401, 403}:
                return ExecutionResult(
                    'unavailable',
                    '',
                    'Code execution provider authentication failed. Retry after provider configuration is corrected.',
                )
            return ExecutionResult('unavailable', '', 'Code execution provider is temporarily unavailable.')
        except (URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            LOGGER.warning('OnlineCompiler request failed: %s', type(exc).__name__)
            return ExecutionResult('unavailable', '', 'Code execution provider is temporarily unavailable.')

        if not isinstance(body, dict):
            return ExecutionResult('unavailable', '', 'Code execution provider returned an invalid response.')

        exit_code = body.get('exit_code')
        stdout = body.get('output')
        stderr = body.get('error')
        if not isinstance(exit_code, int) or not isinstance(stdout, str) or not isinstance(stderr, str):
            return ExecutionResult('unavailable', '', 'Code execution provider returned an invalid response.')

        duration_value = body.get('total')
        if not isinstance(duration_value, (int, float)):
            duration_value = perf_counter() - started
        duration_ms = max(0, int(duration_value * 1000))

        if exit_code == 124:
            return ExecutionResult('timeout', '', 'Execution exceeded the configured time limit.', duration_ms, exit_code)

        return ExecutionResult('completed', stdout, stderr, duration_ms, exit_code)

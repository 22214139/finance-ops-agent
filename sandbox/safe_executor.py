"""Runs a callable under a timeout, catching any exception so one failing
tool/agent step never takes down the whole pipeline.
"""
import concurrent.futures
from dataclasses import dataclass
from typing import Any, Callable, Optional

DEFAULT_TIMEOUT_SECONDS = 10

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


@dataclass
class ExecutionResult:
    success: bool
    output: Any
    error: Optional[str]


def safe_execute(fn: Callable, *args, timeout: float = DEFAULT_TIMEOUT_SECONDS, **kwargs) -> ExecutionResult:
    future = _executor.submit(fn, *args, **kwargs)
    try:
        result = future.result(timeout=timeout)
        return ExecutionResult(success=True, output=result, error=None)
    except concurrent.futures.TimeoutError:
        future.cancel()
        return ExecutionResult(success=False, output=None, error=f"Timed out after {timeout}s")
    except Exception as e:
        return ExecutionResult(success=False, output=None, error=f"{type(e).__name__}: {e}")

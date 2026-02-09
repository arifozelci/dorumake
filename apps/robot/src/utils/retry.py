"""
KolayRobot Retry Utilities
Exponential backoff retry mechanism with configurable policies
"""

import asyncio
from functools import wraps
from typing import Callable, List, Optional, Type, Union
from loguru import logger


class RetryError(Exception):
    """Raised when all retry attempts are exhausted"""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    wait_seconds: Union[List[int], int] = [5, 15, 30],
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
    operation_name: str = "operation"
):
    """
    Retry an async function with exponential backoff

    Args:
        func: Async function to retry (should be a coroutine or callable returning coroutine)
        max_attempts: Maximum number of attempts
        wait_seconds: List of wait times or single int for all retries
        exceptions: Tuple of exception types to catch
        on_retry: Callback called on each retry (attempt, exception)
        on_failure: Callback called when all retries exhausted
        operation_name: Name for logging purposes

    Returns:
        Result of the function if successful

    Raises:
        RetryError: When all attempts are exhausted
    """

    # Normalize wait_seconds to a list
    if isinstance(wait_seconds, int):
        wait_seconds = [wait_seconds] * max_attempts

    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(f"[{operation_name}] Attempt {attempt}/{max_attempts}")

            # Call the function
            if asyncio.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()
                if asyncio.iscoroutine(result):
                    result = await result

            logger.debug(f"[{operation_name}] Success on attempt {attempt}")
            return result

        except exceptions as e:
            last_exception = e
            logger.warning(
                f"[{operation_name}] Attempt {attempt}/{max_attempts} failed: {type(e).__name__}: {str(e)}"
            )

            # Call retry callback if provided
            if on_retry:
                try:
                    if asyncio.iscoroutinefunction(on_retry):
                        await on_retry(attempt, e)
                    else:
                        on_retry(attempt, e)
                except Exception as callback_error:
                    logger.error(f"[{operation_name}] Retry callback error: {callback_error}")

            # If not the last attempt, wait before retrying
            if attempt < max_attempts:
                wait_time = wait_seconds[min(attempt - 1, len(wait_seconds) - 1)]
                logger.info(f"[{operation_name}] Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

    # All attempts exhausted
    error_msg = f"[{operation_name}] All {max_attempts} attempts failed"
    logger.error(error_msg)

    # Call failure callback if provided
    if on_failure:
        try:
            if asyncio.iscoroutinefunction(on_failure):
                await on_failure(last_exception)
            else:
                on_failure(last_exception)
        except Exception as callback_error:
            logger.error(f"[{operation_name}] Failure callback error: {callback_error}")

    raise RetryError(error_msg, last_exception)


def with_retry(
    max_attempts: int = 3,
    wait_seconds: Union[List[int], int] = [5, 15, 30],
    exceptions: tuple = (Exception,),
    operation_name: Optional[str] = None
):
    """
    Decorator for retry functionality

    Usage:
        @with_retry(max_attempts=3, wait_seconds=[5, 10, 20])
        async def my_function():
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            name = operation_name or func.__name__

            async def call_func():
                return await func(*args, **kwargs)

            return await retry_async(
                call_func,
                max_attempts=max_attempts,
                wait_seconds=wait_seconds,
                exceptions=exceptions,
                operation_name=name
            )

        return wrapper

    return decorator


class RetryContext:
    """
    Context manager for retry operations

    Usage:
        async with RetryContext(max_attempts=3) as ctx:
            result = await ctx.execute(my_async_function)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        wait_seconds: Union[List[int], int] = [5, 15, 30],
        exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.exceptions = exceptions
        self.attempts = 0
        self.last_error = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def execute(
        self,
        func: Callable,
        operation_name: str = "operation",
        on_retry: Optional[Callable] = None,
        on_failure: Optional[Callable] = None
    ):
        return await retry_async(
            func,
            max_attempts=self.max_attempts,
            wait_seconds=self.wait_seconds,
            exceptions=self.exceptions,
            on_retry=on_retry,
            on_failure=on_failure,
            operation_name=operation_name
        )

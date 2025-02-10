from functools import wraps
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep
)
import aiohttp
import asyncio

def before_sleep_log(retry_state):
    """Log information about this retry call before sleeping."""
    if retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        logger.warning(
            f"Retrying {retry_state.fn.__name__} in {retry_state.next_action.sleep} seconds "
            f"after {retry_state.attempt_number} attempts. "
            f"Error: {str(exception)}"
        )

def with_retry(max_attempts=3, min_wait=1, max_wait=10):
    """
    Decorator that adds retry capability to async functions making API calls.
    
    Args:
        max_attempts (int): Maximum number of retry attempts
        min_wait (int): Minimum wait time between retries in seconds
        max_wait (int): Maximum wait time between retries in seconds
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ConnectionError
        )),
        before_sleep=before_sleep_log,
        reraise=True
    )
"""Retry mechanism with exponential backoff for API calls."""
import time
import functools
from typing import Callable, Any, Type
from src.utils.logger import logger


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on

    Returns:
        Decorated function

    Example:
        @retry_with_backoff(max_retries=3)
        def fetch_data():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )

            # If we get here, all retries failed
            raise last_exception

        return wrapper
    return decorator


def retry_on_rate_limit(max_retries: int = 5, initial_delay: float = 60.0) -> Callable:
    """
    Decorator specifically for handling API rate limits.
    Uses longer delays suitable for rate limit errors.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (default 60s for rate limits)

    Returns:
        Decorated function
    """
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=1.5,
        exceptions=(Exception,)  # Catch all exceptions, check for rate limit in message
    )

"""Rate limiting for API calls."""
import time
from collections import deque
from threading import Lock
from typing import Optional
from src.utils.logger import logger


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Ensures no more than `max_calls` happen within `period` seconds.

    Example:
        limiter = RateLimiter(max_calls=50, period=60)

        for item in items:
            with limiter:
                api_call(item)
    """

    def __init__(self, max_calls: int, period: float):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = Lock()

    def __enter__(self):
        """Context manager entry - wait if rate limit reached."""
        self.wait_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False

    def wait_if_needed(self):
        """Wait if rate limit has been reached."""
        with self.lock:
            now = time.time()

            # Remove calls outside the time window
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            # If we've hit the limit, wait
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    # Clean up old calls after sleeping
                    now = time.time()
                    while self.calls and self.calls[0] < now - self.period:
                        self.calls.popleft()

            # Record this call
            self.calls.append(time.time())

    def get_wait_time(self) -> float:
        """
        Get the time in seconds until next call is allowed.

        Returns:
            Wait time in seconds (0 if call is immediately allowed)
        """
        with self.lock:
            now = time.time()

            # Remove calls outside the time window
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            # Calculate wait time
            if len(self.calls) >= self.max_calls:
                return max(0, self.period - (now - self.calls[0]))
            return 0.0


class MultiRateLimiter:
    """
    Manages multiple rate limiters for different services.

    Example:
        limiters = MultiRateLimiter()
        limiters.add('claude', max_calls=50, period=60)
        limiters.add('wikipedia', max_calls=100, period=60)

        with limiters.get('claude'):
            claude_api_call()
    """

    def __init__(self):
        """Initialize multi-rate limiter."""
        self.limiters: dict[str, RateLimiter] = {}

    def add(self, name: str, max_calls: int, period: float):
        """
        Add a rate limiter for a service.

        Args:
            name: Service name
            max_calls: Maximum calls allowed
            period: Time period in seconds
        """
        self.limiters[name] = RateLimiter(max_calls, period)
        logger.info(f"Added rate limiter '{name}': {max_calls} calls per {period}s")

    def get(self, name: str) -> Optional[RateLimiter]:
        """
        Get a rate limiter by name.

        Args:
            name: Service name

        Returns:
            RateLimiter instance or None if not found
        """
        return self.limiters.get(name)

    def wait(self, name: str):
        """
        Wait if needed for a specific service.

        Args:
            name: Service name
        """
        limiter = self.get(name)
        if limiter:
            limiter.wait_if_needed()

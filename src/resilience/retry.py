"""Retry logic with exponential backoff and jitter."""

import time
import random
from functools import wraps
from typing import Callable, TypeVar, Any

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable[[F], F]:
    """
    Decorator for retrying with exponential backoff and optional jitter.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Whether to add random jitter (default: True)

    Returns:
        Decorator function

    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def call_api():
            # May raise exceptions, will retry up to 3 times
            pass
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt >= max_attempts:
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay,
                    )

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay *= 0.5 + random.random()

                    time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator

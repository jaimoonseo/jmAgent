"""Circuit breaker pattern implementation for API protection."""

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, TypeVar, Any
from functools import wraps

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for API protection.

    Protects against cascading failures by monitoring failure rates
    and temporarily rejecting requests when failures exceed threshold.

    States:
        CLOSED: Normal operation, requests pass through
        OPEN: Too many failures, requests are rejected immediately
        HALF_OPEN: Timeout expired, testing if service recovered

    Example:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        def call_api():
            return breaker.call(some_function)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening (default: 5)
            recovery_timeout: Seconds before attempting recovery (default: 60)
            expected_exception: Exception type to catch (default: Exception)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Result from function call

        Raises:
            Exception: Circuit breaker is OPEN or function raises expected exception
        """

        # Check if we should transition to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has passed."""
        if not self.last_failure_time:
            return False

        elapsed = datetime.now() - self.last_failure_time
        return elapsed >= timedelta(seconds=self.recovery_timeout)

    def __call__(self, func: F) -> F:
        """
        Decorator form of circuit breaker.

        Example:
            @breaker
            def call_api():
                pass
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

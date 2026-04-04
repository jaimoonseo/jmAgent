"""Tests for resilience patterns: retry logic and circuit breaker."""

import pytest
import time
from src.resilience.retry import retry_with_backoff
from src.resilience.circuit_breaker import CircuitBreaker, CircuitState


# ============================================================================
# Retry with Backoff Tests
# ============================================================================


def test_retry_success_on_second_attempt():
    """Test retry succeeds after initial failure."""
    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.01)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary failure")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count == 2


def test_retry_max_attempts_exceeded():
    """Test retry gives up after max attempts."""

    @retry_with_backoff(max_attempts=2, initial_delay=0.01)
    def always_fails():
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_fails()


def test_retry_success_first_try():
    """Test function that succeeds on first try."""

    @retry_with_backoff(max_attempts=3, initial_delay=0.01)
    def succeeds_immediately():
        return "success"

    result = succeeds_immediately()
    assert result == "success"


def test_retry_exponential_backoff():
    """Test exponential backoff calculation."""
    call_times = []

    @retry_with_backoff(max_attempts=3, initial_delay=0.02, exponential_base=2.0, jitter=False)
    def track_calls():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise Exception("Retry")
        return "ok"

    result = track_calls()
    assert result == "ok"
    assert len(call_times) == 3

    # Delays should be approximately: 0.02, 0.04
    delay1 = call_times[1] - call_times[0]
    delay2 = call_times[2] - call_times[1]
    assert delay1 >= 0.015  # Allow some variance
    assert delay2 >= 0.035


def test_retry_with_jitter():
    """Test that jitter is applied when enabled."""
    call_times = []

    @retry_with_backoff(max_attempts=3, initial_delay=0.02, jitter=True)
    def track_calls():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise Exception("Retry")
        return "ok"

    result = track_calls()
    assert result == "ok"
    assert len(call_times) == 3


def test_retry_max_delay_capped():
    """Test that backoff delay is capped at max_delay."""
    call_times = []

    @retry_with_backoff(
        max_attempts=4,
        initial_delay=10.0,
        max_delay=0.05,
        exponential_base=10.0,
        jitter=False
    )
    def track_calls():
        call_times.append(time.time())
        if len(call_times) < 4:
            raise Exception("Retry")
        return "ok"

    result = track_calls()
    assert result == "ok"

    # Check that delays don't exceed max_delay
    for i in range(1, len(call_times)):
        delay = call_times[i] - call_times[i - 1]
        assert delay <= 0.07  # Allow some variance


def test_retry_preserves_return_value():
    """Test that retry preserves the return value."""

    @retry_with_backoff(max_attempts=2, initial_delay=0.01)
    def returns_dict():
        return {"key": "value", "number": 42}

    result = returns_dict()
    assert result == {"key": "value", "number": 42}


def test_retry_with_args_and_kwargs():
    """Test retry with function arguments."""

    @retry_with_backoff(max_attempts=2, initial_delay=0.01)
    def add_numbers(a, b, multiplier=1):
        return (a + b) * multiplier

    result = add_numbers(2, 3, multiplier=10)
    assert result == 50


def test_retry_different_exception_types():
    """Test retry with different exception types."""
    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.01)
    def raises_different_errors():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First error")
        elif call_count == 2:
            raise TypeError("Second error")
        return "success"

    result = raises_different_errors()
    assert result == "success"
    assert call_count == 3


# ============================================================================
# Circuit Breaker Tests
# ============================================================================


def test_circuit_breaker_closed_state():
    """Test circuit breaker in closed state (normal)."""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    assert breaker.state == CircuitState.CLOSED

    def success_func():
        return "ok"

    result = breaker.call(success_func)
    assert result == "ok"


def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    def always_fails():
        raise Exception("Always fails")

    # First failure
    with pytest.raises(Exception):
        breaker.call(always_fails)
    assert breaker.state == CircuitState.CLOSED

    # Second failure - should open
    with pytest.raises(Exception):
        breaker.call(always_fails)
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_rejects_when_open():
    """Test circuit breaker rejects calls when open."""
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60)

    # Open the circuit manually
    breaker.failure_count = 1
    breaker.state = CircuitState.OPEN

    def any_func():
        return "ok"

    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        breaker.call(any_func)


def test_circuit_breaker_resets_on_success():
    """Test circuit breaker resets on success."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0)

    def sometimes_fails():
        if breaker.failure_count < 2:
            raise Exception("Fail")
        return "ok"

    # Fail twice
    with pytest.raises(Exception):
        breaker.call(sometimes_fails)
    with pytest.raises(Exception):
        breaker.call(sometimes_fails)

    assert breaker.state == CircuitState.OPEN

    # Wait for recovery timeout (set to 0, so minimal wait needed)
    time.sleep(0.01)

    # Success should reset the circuit
    result = breaker.call(sometimes_fails)
    assert result == "ok"
    assert breaker.failure_count == 0
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_half_open_to_closed():
    """Test circuit breaker transitions from OPEN to HALF_OPEN to CLOSED."""
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

    def always_fails():
        raise Exception("Always fails")

    # First failure opens the circuit
    with pytest.raises(Exception):
        breaker.call(always_fails)
    assert breaker.state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.01)

    # Next call should transition to HALF_OPEN (timeout expired)
    def succeeds():
        return "ok"

    result = breaker.call(succeeds)
    assert result == "ok"
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_half_open_to_open():
    """Test circuit breaker transitions from HALF_OPEN back to OPEN on failure."""
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

    def always_fails():
        raise Exception("Always fails")

    # Open the circuit
    with pytest.raises(Exception):
        breaker.call(always_fails)
    assert breaker.state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.01)

    # Attempt recovery but fail again
    with pytest.raises(Exception):
        breaker.call(always_fails)
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_as_decorator():
    """Test circuit breaker used as a decorator."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    @breaker
    def decorated_function():
        return "success"

    result = decorated_function()
    assert result == "success"


def test_circuit_breaker_with_expected_exception():
    """Test circuit breaker only counts expected exceptions."""
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=60,
        expected_exception=ValueError
    )

    def raises_type_error():
        raise TypeError("Wrong type")

    # TypeError should not be caught by circuit breaker
    with pytest.raises(TypeError):
        breaker.call(raises_type_error)
    assert breaker.failure_count == 0


def test_circuit_breaker_state_enum():
    """Test CircuitState enum values."""
    assert CircuitState.CLOSED.value == "closed"
    assert CircuitState.OPEN.value == "open"
    assert CircuitState.HALF_OPEN.value == "half_open"


def test_circuit_breaker_failure_count_increments():
    """Test that failure count increments correctly."""
    breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    def always_fails():
        raise Exception("Fail")

    for i in range(1, 5):
        with pytest.raises(Exception):
            breaker.call(always_fails)
        assert breaker.failure_count == i

    # Fifth failure should open the circuit
    with pytest.raises(Exception):
        breaker.call(always_fails)
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_multiple_functions():
    """Test circuit breaker with multiple different functions."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    def func1():
        return "func1"

    def func2():
        return "func2"

    # Both should work in CLOSED state
    assert breaker.call(func1) == "func1"
    assert breaker.call(func2) == "func2"

    # Open the circuit
    def always_fails():
        raise Exception("Fail")

    with pytest.raises(Exception):
        breaker.call(always_fails)
    with pytest.raises(Exception):
        breaker.call(always_fails)

    assert breaker.state == CircuitState.OPEN

    # Both functions should be rejected now
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        breaker.call(func1)
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        breaker.call(func2)

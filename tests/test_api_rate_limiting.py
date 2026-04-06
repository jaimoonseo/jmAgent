"""Tests for rate limiting functionality."""

import pytest
import time
from src.api.security.rate_limiter import RateLimiter
from src.api.exceptions import RateLimitError


@pytest.fixture
def rate_limiter():
    """Create a rate limiter instance."""
    return RateLimiter()


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_rate_limiter_default_values(self):
        """Test RateLimiter has correct default values."""
        limiter = RateLimiter()
        assert limiter.default_limit == 100
        assert limiter.default_window == 60

    def test_rate_limiter_custom_values(self):
        """Test RateLimiter accepts custom values."""
        limiter = RateLimiter(default_limit=50, default_window=120)
        assert limiter.default_limit == 50
        assert limiter.default_window == 120

    def test_rate_limiter_storage_initialized(self):
        """Test RateLimiter initializes empty storage."""
        limiter = RateLimiter()
        assert isinstance(limiter._requests, dict)
        assert len(limiter._requests) == 0


class TestRateLimiterCheckLimit:
    """Tests for check_rate_limit method."""

    def test_check_rate_limit_first_request_succeeds(self, rate_limiter):
        """Test first request always succeeds."""
        result = rate_limiter.check_rate_limit("user1", limit=10, window=60)
        assert result is True

    def test_check_rate_limit_multiple_requests_succeed(self, rate_limiter):
        """Test multiple requests within limit succeed."""
        for i in range(5):
            result = rate_limiter.check_rate_limit("user1", limit=10, window=60)
            assert result is True

    def test_check_rate_limit_exceeds_limit(self, rate_limiter):
        """Test requests exceeding limit fail."""
        limit = 3
        # First 3 should succeed
        for i in range(limit):
            result = rate_limiter.check_rate_limit(
                "user1", limit=limit, window=60
            )
            assert result is True

        # 4th should fail
        result = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
        assert result is False

    def test_check_rate_limit_different_users_independent(self, rate_limiter):
        """Test rate limits are per-user."""
        limit = 2

        # User1 uses up their limit
        rate_limiter.check_rate_limit("user1", limit=limit, window=60)
        rate_limiter.check_rate_limit("user1", limit=limit, window=60)

        # User1 exceeds limit
        result1 = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
        assert result1 is False

        # User2 should still be able to make requests
        result2 = rate_limiter.check_rate_limit("user2", limit=limit, window=60)
        assert result2 is True

    def test_check_rate_limit_different_ips_independent(self, rate_limiter):
        """Test rate limits are per-IP."""
        limit = 2

        # IP1 uses up their limit
        rate_limiter.check_rate_limit("ip:192.168.1.1", limit=limit, window=60)
        rate_limiter.check_rate_limit("ip:192.168.1.1", limit=limit, window=60)

        # IP1 exceeds limit
        result1 = rate_limiter.check_rate_limit(
            "ip:192.168.1.1", limit=limit, window=60
        )
        assert result1 is False

        # IP2 should be able to make requests
        result2 = rate_limiter.check_rate_limit(
            "ip:192.168.1.2", limit=limit, window=60
        )
        assert result2 is True

    def test_check_rate_limit_sliding_window(self, rate_limiter):
        """Test sliding window algorithm works correctly."""
        limit = 2
        window = 2  # 2 second window

        # Make 2 requests at time 0
        result1 = rate_limiter.check_rate_limit("user1", limit=limit, window=window)
        assert result1 is True

        result2 = rate_limiter.check_rate_limit("user1", limit=limit, window=window)
        assert result2 is True

        # 3rd request should fail
        result3 = rate_limiter.check_rate_limit("user1", limit=limit, window=window)
        assert result3 is False

        # Wait for window to expire
        time.sleep(window + 0.1)

        # Now request should succeed (old requests expired)
        result4 = rate_limiter.check_rate_limit("user1", limit=limit, window=window)
        assert result4 is True

    def test_check_rate_limit_default_values(self, rate_limiter):
        """Test check_rate_limit uses defaults when not specified."""
        # Use default limit (100) and window (60)
        # All should succeed since limit is high
        for i in range(10):
            result = rate_limiter.check_rate_limit("user1")
            assert result is True

    def test_check_rate_limit_per_minute_default(self, rate_limiter):
        """Test default is per-minute (100 requests/minute)."""
        # Make 100 requests rapidly
        for i in range(100):
            result = rate_limiter.check_rate_limit("user1")
            assert result is True

        # 101st should fail
        result = rate_limiter.check_rate_limit("user1")
        assert result is False

    def test_check_rate_limit_cleanup_old_entries(self, rate_limiter):
        """Test old timestamp entries are cleaned up."""
        window = 1  # 1 second window

        # Make requests
        rate_limiter.check_rate_limit("user1", limit=1, window=window)

        # Wait for window to expire
        time.sleep(window + 0.1)

        # Make another request (should clean up old entries)
        rate_limiter.check_rate_limit("user1", limit=1, window=window)

        # Verify storage is cleaned
        timestamps = rate_limiter._requests.get("user1", [])
        assert len(timestamps) == 1  # Only the latest request

    def test_check_rate_limit_zero_limit(self, rate_limiter):
        """Test zero limit denies all requests."""
        result = rate_limiter.check_rate_limit("user1", limit=0, window=60)
        assert result is False

    def test_check_rate_limit_negative_limit(self, rate_limiter):
        """Test negative limit allows unlimited requests."""
        # Typically negative limit means unlimited
        for i in range(1000):
            result = rate_limiter.check_rate_limit("user1", limit=-1, window=60)
            assert result is True


class TestRateLimiterReset:
    """Tests for reset functionality."""

    def test_reset_clears_all_limits(self, rate_limiter):
        """Test reset clears all stored limits."""
        # Use up limit for multiple users
        rate_limiter.check_rate_limit("user1", limit=1, window=60)
        rate_limiter.check_rate_limit("user2", limit=1, window=60)

        # Verify limits are exceeded
        assert rate_limiter.check_rate_limit("user1", limit=1, window=60) is False
        assert rate_limiter.check_rate_limit("user2", limit=1, window=60) is False

        # Reset
        rate_limiter.reset()

        # Limits should be restored
        assert rate_limiter.check_rate_limit("user1", limit=1, window=60) is True
        assert rate_limiter.check_rate_limit("user2", limit=1, window=60) is True

    def test_reset_for_specific_user(self, rate_limiter):
        """Test reset for a specific user."""
        # Use up limits
        rate_limiter.check_rate_limit("user1", limit=1, window=60)
        rate_limiter.check_rate_limit("user2", limit=1, window=60)

        # Reset only user1
        rate_limiter.reset_user("user1")

        # User1 should have reset, user2 should not
        assert rate_limiter.check_rate_limit("user1", limit=1, window=60) is True
        assert rate_limiter.check_rate_limit("user2", limit=1, window=60) is False


class TestRateLimiterPercentageThreshold:
    """Tests for rate limiter near-limit scenarios."""

    def test_rate_limit_at_threshold(self, rate_limiter):
        """Test behavior exactly at the limit threshold."""
        limit = 5

        # Use exactly the limit
        for i in range(limit):
            result = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
            assert result is True

        # Next request should fail
        result = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
        assert result is False

    def test_rate_limit_almost_at_threshold(self, rate_limiter):
        """Test behavior just below the limit threshold."""
        limit = 5

        # Use limit - 1 requests
        for i in range(limit - 1):
            result = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
            assert result is True

        # Next request should succeed
        result = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
        assert result is True

        # Now we're at the limit, next should fail
        result = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
        assert result is False


class TestRateLimiterEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_rate_limiter_rapid_requests(self, rate_limiter):
        """Test rapid requests in a loop."""
        limit = 100
        count = 0

        # Make 100 rapid requests
        for i in range(limit):
            if rate_limiter.check_rate_limit("user1", limit=limit, window=60):
                count += 1

        assert count == limit

    def test_rate_limiter_concurrent_users(self, rate_limiter):
        """Test multiple concurrent users don't interfere."""
        limit = 2

        # Track requests per user
        user_counts = {0: 0, 1: 0, 2: 0}

        # Alternate between users
        for i in range(10):
            user_idx = i % 3
            user = f"user{user_idx}"  # 3 different users
            result = rate_limiter.check_rate_limit(user, limit=limit, window=60)

            # Each user should get 2 requests before failing
            if user_counts[user_idx] < limit:
                assert result is True
                user_counts[user_idx] += 1
            else:
                assert result is False

    def test_rate_limiter_very_large_limit(self, rate_limiter):
        """Test with very large limit."""
        limit = 1000000

        # Should handle large numbers
        for i in range(10):
            result = rate_limiter.check_rate_limit("user1", limit=limit, window=60)
            assert result is True

    def test_rate_limiter_very_small_window(self, rate_limiter):
        """Test with very small time window."""
        limit = 1
        window = 0.1  # 100ms

        result1 = rate_limiter.check_rate_limit("user1", limit=limit, window=window)
        assert result1 is True

        result2 = rate_limiter.check_rate_limit("user1", limit=limit, window=window)
        assert result2 is False

        # Wait for window
        time.sleep(window + 0.05)

        result3 = rate_limiter.check_rate_limit("user1", limit=limit, window=window)
        assert result3 is True

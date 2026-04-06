"""Rate limiting for jmAgent API."""

import time
from typing import Dict, List
from src.logging.logger import StructuredLogger

logger = StructuredLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    Tracks request timestamps per identifier (IP, user, etc.) and enforces
    request limits within a time window.
    """

    def __init__(self, default_limit: int = 100, default_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            default_limit: Default request limit per window (default: 100/minute)
            default_window: Default time window in seconds (default: 60)
        """
        self.default_limit = default_limit
        self.default_window = default_window
        self._requests: Dict[str, List[float]] = {}

    def check_rate_limit(
        self,
        identifier: str,
        limit: int = None,
        window: int = None,
    ) -> bool:
        """
        Check if a request is within the rate limit.

        Uses a sliding window algorithm to track request timestamps.
        Old timestamps outside the window are automatically cleaned up.

        Args:
            identifier: Unique identifier for rate limiting (e.g., user_id, ip)
            limit: Request limit per window (uses default if None)
            window: Time window in seconds (uses default if None)

        Returns:
            True if request is allowed, False if limit exceeded

        Examples:
            >>> limiter = RateLimiter()
            >>> limiter.check_rate_limit("user123", limit=10, window=60)
            True
        """
        if limit is None:
            limit = self.default_limit
        if window is None:
            window = self.default_window

        # Handle special cases
        if limit < 0:  # Negative limit = unlimited
            return True

        current_time = time.time()
        window_start = current_time - window

        # Get or initialize timestamps for this identifier
        timestamps = self._requests.get(identifier, [])

        # Clean up old timestamps outside the window
        timestamps = [ts for ts in timestamps if ts > window_start]

        # Check if limit is exceeded
        if len(timestamps) >= limit:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "identifier": identifier,
                    "limit": limit,
                    "window": window,
                    "requests": len(timestamps),
                },
            )
            # Update storage with cleaned timestamps
            self._requests[identifier] = timestamps
            return False

        # Add current timestamp
        timestamps.append(current_time)
        self._requests[identifier] = timestamps

        logger.debug(
            "Rate limit check passed",
            extra={
                "identifier": identifier,
                "requests_count": len(timestamps),
                "limit": limit,
            },
        )

        return True

    def reset(self) -> None:
        """
        Reset all stored rate limits.

        Clears all request tracking data for all identifiers.
        """
        self._requests.clear()
        logger.info("Rate limiter reset")

    def reset_user(self, identifier: str) -> None:
        """
        Reset rate limit for a specific identifier.

        Args:
            identifier: The identifier to reset
        """
        if identifier in self._requests:
            del self._requests[identifier]
            logger.info("Rate limit reset for identifier", extra={"identifier": identifier})

    def get_status(self, identifier: str) -> Dict[str, any]:
        """
        Get current rate limit status for an identifier.

        Args:
            identifier: The identifier to check

        Returns:
            Dictionary with current request count and timestamp info

        Examples:
            >>> limiter = RateLimiter()
            >>> limiter.check_rate_limit("user123")
            >>> status = limiter.get_status("user123")
            >>> status['request_count']
            1
        """
        current_time = time.time()
        timestamps = self._requests.get(identifier, [])

        return {
            "identifier": identifier,
            "request_count": len(timestamps),
            "last_request": timestamps[-1] if timestamps else None,
            "oldest_request": timestamps[0] if timestamps else None,
            "current_time": current_time,
        }

    def cleanup(self, window: int = None) -> int:
        """
        Clean up expired entries from storage.

        Args:
            window: Time window in seconds (uses default if None)

        Returns:
            Number of identifiers cleaned up

        Examples:
            >>> limiter = RateLimiter()
            >>> cleaned = limiter.cleanup(window=60)
        """
        if window is None:
            window = self.default_window

        current_time = time.time()
        window_start = current_time - window
        cleaned_count = 0

        identifiers_to_remove = []

        for identifier, timestamps in self._requests.items():
            # Clean old timestamps
            valid_timestamps = [ts for ts in timestamps if ts > window_start]

            if not valid_timestamps:
                # Remove identifier if no valid timestamps
                identifiers_to_remove.append(identifier)
                cleaned_count += 1
            else:
                # Update with cleaned timestamps
                self._requests[identifier] = valid_timestamps

        # Remove empty entries
        for identifier in identifiers_to_remove:
            del self._requests[identifier]

        if cleaned_count > 0:
            logger.debug(
                "Rate limiter cleanup completed",
                extra={"identifiers_cleaned": cleaned_count},
            )

        return cleaned_count

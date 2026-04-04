import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class CacheEntry:
    """Represents a cached entry with TTL-based expiry."""

    def __init__(self, content: str, ttl_minutes: int = 60):
        """
        Initialize a cache entry.

        Args:
            content: The cached content
            ttl_minutes: Time-to-live in minutes (default: 60)
        """
        self.content = content
        self.ttl_minutes = ttl_minutes
        self.created_at = datetime.now()

    def is_expired(self) -> bool:
        """
        Check if the cache entry has expired.

        Returns:
            True if expired, False otherwise
        """
        expiry_time = self.created_at + timedelta(minutes=self.ttl_minutes)
        return datetime.now() > expiry_time

    def get_content(self) -> Optional[str]:
        """
        Get the cached content if not expired.

        Returns:
            The cached content if valid, None if expired
        """
        if self.is_expired():
            return None
        return self.content


class CacheManager:
    """Manages cache entries with SHA-256 keys and TTL-based expiry."""

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize the cache manager.

        Args:
            ttl_minutes: Default time-to-live in minutes (default: 60)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.ttl_minutes = ttl_minutes

    def get_cache_key(self, context: str) -> str:
        """
        Generate SHA-256 cache key for the given context.

        Args:
            context: The context string to hash

        Returns:
            64-character SHA-256 hash in hexadecimal
        """
        return hashlib.sha256(context.encode()).hexdigest()

    def set(self, context: str, value: str) -> str:
        """
        Set a value in the cache.

        Args:
            context: The context string
            value: The value to cache

        Returns:
            The cache key (SHA-256 hash)
        """
        key = self.get_cache_key(context)
        self.cache[key] = CacheEntry(value, ttl_minutes=self.ttl_minutes)
        return key

    def get(self, context: str) -> Optional[str]:
        """
        Get a value from the cache.

        Args:
            context: The context string

        Returns:
            The cached value if found and not expired, None otherwise
        """
        key = self.get_cache_key(context)

        if key not in self.cache:
            self.cache_misses += 1
            return None

        entry = self.cache[key]
        content = entry.get_content()

        if content is None:
            self.cache_misses += 1
            return None

        self.cache_hits += 1
        return content

    def has_valid_cache(self, context: str) -> bool:
        """
        Check if valid cache exists for the given context.

        Args:
            context: The context string

        Returns:
            True if valid cache exists, False otherwise
        """
        key = self.get_cache_key(context)

        if key not in self.cache:
            return False

        entry = self.cache[key]
        return entry.get_content() is not None

    def clear_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with keys: hits, misses, entries, hit_rate
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (
            self.cache_hits / total_requests
            if total_requests > 0
            else 0.0
        )

        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "entries": len(self.cache),
            "hit_rate": hit_rate
        }

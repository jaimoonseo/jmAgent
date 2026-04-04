import pytest
import time
from datetime import datetime, timedelta
from src.cache.cache_manager import CacheEntry, CacheManager


class TestCacheEntry:
    """Test CacheEntry class."""

    def test_cache_entry_initialization(self):
        """Test CacheEntry initialization with default TTL."""
        content = "test content"
        entry = CacheEntry(content)
        assert entry.content == content
        assert entry.created_at is not None
        assert entry.ttl_minutes == 60

    def test_cache_entry_initialization_custom_ttl(self):
        """Test CacheEntry initialization with custom TTL."""
        content = "test content"
        entry = CacheEntry(content, ttl_minutes=30)
        assert entry.content == content
        assert entry.ttl_minutes == 30

    def test_cache_entry_not_expired_within_ttl(self):
        """Test CacheEntry.is_expired() returns False within TTL."""
        content = "test content"
        entry = CacheEntry(content, ttl_minutes=60)
        assert not entry.is_expired()

    def test_cache_entry_expired_after_ttl(self):
        """Test CacheEntry.is_expired() returns True after TTL expires."""
        content = "test content"
        entry = CacheEntry(content, ttl_minutes=1)
        # Manually set created_at to 2 minutes ago
        entry.created_at = datetime.now() - timedelta(minutes=2)
        assert entry.is_expired()

    def test_cache_entry_get_content_valid(self):
        """Test CacheEntry.get_content() returns content when not expired."""
        content = "test content"
        entry = CacheEntry(content, ttl_minutes=60)
        assert entry.get_content() == content

    def test_cache_entry_get_content_expired(self):
        """Test CacheEntry.get_content() returns None when expired."""
        content = "test content"
        entry = CacheEntry(content, ttl_minutes=1)
        entry.created_at = datetime.now() - timedelta(minutes=2)
        assert entry.get_content() is None


class TestCacheManager:
    """Test CacheManager class."""

    def test_cache_manager_initialization(self):
        """Test CacheManager initialization."""
        manager = CacheManager()
        assert manager.cache == {}
        assert manager.cache_hits == 0
        assert manager.cache_misses == 0
        assert manager.ttl_minutes == 60

    def test_cache_manager_initialization_custom_ttl(self):
        """Test CacheManager initialization with custom TTL."""
        manager = CacheManager(ttl_minutes=30)
        assert manager.ttl_minutes == 30

    def test_get_cache_key_returns_sha256(self):
        """Test get_cache_key returns SHA-256 hash."""
        manager = CacheManager()
        context = "test context"
        key = manager.get_cache_key(context)

        # SHA-256 hash should be 64 characters
        assert isinstance(key, str)
        assert len(key) == 64
        # Should be hexadecimal
        assert all(c in "0123456789abcdef" for c in key)

    def test_get_cache_key_consistent(self):
        """Test get_cache_key returns same key for same input."""
        manager = CacheManager()
        context = "test context"
        key1 = manager.get_cache_key(context)
        key2 = manager.get_cache_key(context)
        assert key1 == key2

    def test_get_cache_key_different_for_different_input(self):
        """Test get_cache_key returns different keys for different inputs."""
        manager = CacheManager()
        key1 = manager.get_cache_key("context1")
        key2 = manager.get_cache_key("context2")
        assert key1 != key2

    def test_set_cache_stores_value(self):
        """Test set() stores value and returns key."""
        manager = CacheManager()
        context = "test context"
        value = "test value"
        key = manager.set(context, value)

        assert isinstance(key, str)
        assert len(key) == 64  # SHA-256 hash
        assert key in manager.cache
        assert manager.cache[key].content == value

    def test_set_cache_with_custom_ttl(self):
        """Test set() respects manager's TTL setting."""
        manager = CacheManager(ttl_minutes=30)
        context = "test context"
        value = "test value"
        key = manager.set(context, value)

        assert manager.cache[key].ttl_minutes == 30

    def test_get_cache_hit(self):
        """Test get() returns cached value on hit."""
        manager = CacheManager()
        context = "test context"
        value = "test value"
        manager.set(context, value)

        result = manager.get(context)
        assert result == value
        assert manager.cache_hits == 1
        assert manager.cache_misses == 0

    def test_get_cache_miss_not_set(self):
        """Test get() returns None on miss (not set)."""
        manager = CacheManager()
        context = "test context"

        result = manager.get(context)
        assert result is None
        assert manager.cache_hits == 0
        assert manager.cache_misses == 1

    def test_get_cache_miss_expired(self):
        """Test get() returns None on miss (expired)."""
        manager = CacheManager(ttl_minutes=1)
        context = "test context"
        value = "test value"
        manager.set(context, value)

        # Manually expire the cache entry
        key = manager.get_cache_key(context)
        manager.cache[key].created_at = datetime.now() - timedelta(minutes=2)

        result = manager.get(context)
        assert result is None
        assert manager.cache_hits == 0
        assert manager.cache_misses == 1

    def test_has_valid_cache_true(self):
        """Test has_valid_cache() returns True for valid cache."""
        manager = CacheManager()
        context = "test context"
        value = "test value"
        manager.set(context, value)

        assert manager.has_valid_cache(context) is True

    def test_has_valid_cache_false_not_set(self):
        """Test has_valid_cache() returns False when not set."""
        manager = CacheManager()
        context = "test context"

        assert manager.has_valid_cache(context) is False

    def test_has_valid_cache_false_expired(self):
        """Test has_valid_cache() returns False when expired."""
        manager = CacheManager(ttl_minutes=1)
        context = "test context"
        value = "test value"
        manager.set(context, value)

        # Manually expire the cache entry
        key = manager.get_cache_key(context)
        manager.cache[key].created_at = datetime.now() - timedelta(minutes=2)

        assert manager.has_valid_cache(context) is False

    def test_clear_expired_removes_expired_entries(self):
        """Test clear_expired() removes expired entries."""
        manager = CacheManager(ttl_minutes=1)

        # Add two entries
        manager.set("context1", "value1")
        manager.set("context2", "value2")

        assert len(manager.cache) == 2

        # Expire the first entry
        key1 = manager.get_cache_key("context1")
        manager.cache[key1].created_at = datetime.now() - timedelta(minutes=2)

        # Clear expired
        count = manager.clear_expired()
        assert count == 1
        assert len(manager.cache) == 1

    def test_clear_expired_returns_zero_when_no_expired(self):
        """Test clear_expired() returns 0 when no expired entries."""
        manager = CacheManager(ttl_minutes=60)
        manager.set("context1", "value1")

        count = manager.clear_expired()
        assert count == 0
        assert len(manager.cache) == 1

    def test_get_stats_initial(self):
        """Test get_stats() returns correct initial stats."""
        manager = CacheManager()
        stats = manager.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["entries"] == 0
        assert stats["hit_rate"] == 0.0

    def test_get_stats_with_activity(self):
        """Test get_stats() calculates hit rate correctly."""
        manager = CacheManager()

        # Set a value
        manager.set("context1", "value1")

        # Hit twice
        manager.get("context1")
        manager.get("context1")

        # Miss once
        manager.get("context2")

        stats = manager.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["entries"] == 1
        assert stats["hit_rate"] == 2/3  # 2 hits out of 3 requests

    def test_get_stats_hit_rate_100_percent(self):
        """Test get_stats() hit_rate is 1.0 with only hits."""
        manager = CacheManager()
        manager.set("context1", "value1")
        manager.get("context1")
        manager.get("context1")
        manager.get("context1")

        stats = manager.get_stats()
        assert stats["hit_rate"] == 1.0

    def test_get_stats_hit_rate_zero_with_only_misses(self):
        """Test get_stats() hit_rate is 0.0 with only misses."""
        manager = CacheManager()
        manager.get("context1")
        manager.get("context2")

        stats = manager.get_stats()
        assert stats["hit_rate"] == 0.0

    def test_multiple_set_same_context_overwrites(self):
        """Test setting same context overwrites previous value."""
        manager = CacheManager()
        context = "test context"

        key1 = manager.set(context, "value1")
        key2 = manager.set(context, "value2")

        # Same context should generate same key
        assert key1 == key2
        assert manager.cache[key1].content == "value2"

    def test_cache_isolation_between_contexts(self):
        """Test different contexts maintain separate cache entries."""
        manager = CacheManager()

        manager.set("context1", "value1")
        manager.set("context2", "value2")

        assert manager.get("context1") == "value1"
        assert manager.get("context2") == "value2"
        assert len(manager.cache) == 2

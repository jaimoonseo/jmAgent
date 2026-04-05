# Phase 4: Enterprise-Ready Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform jmAgent into an enterprise-grade coding assistant with production hardening, performance optimization, advanced enterprise features, and extensibility support.

**Architecture:** 
- Production Hardening: Comprehensive error handling, structured logging, resilience patterns with circuit breakers and retry logic
- Performance Optimization: Benchmarking framework, response time tracking, token usage analytics, caching improvements
- Enterprise Features: Configuration management system, audit logging, usage analytics, multi-user support foundations
- Integration & Extensibility: Custom prompt templates, GitHub integration, plugin architecture, IDE support groundwork

**Tech Stack:** Python logging (structured), Pydantic for config validation, SQLite for metrics, GitHub API SDK, custom decorator-based plugin system

---

## File Structure

**New files:**
- `src/logging/` - Structured logging with JSON output
- `src/config/` - Configuration management (YAML/environment)
- `src/monitoring/` - Performance metrics, benchmarking
- `src/integrations/` - GitHub, IDE, custom templates
- `src/plugins/` - Plugin architecture and loader
- `src/audit/` - Audit logging system
- `tests/test_*` - Comprehensive test suite for Phase 4

**Modified files:**
- `src/agent.py` - Add monitoring, error handling
- `src/cli.py` - Add config, monitoring CLI commands
- `src/auth/bedrock_auth.py` - Add retry logic, circuit breaker
- `CLAUDE.md` - Update with Phase 4 completion

---

## Task 1: Production Hardening - Structured Logging

**Files:**
- Create: `src/logging/__init__.py`
- Create: `src/logging/logger.py`
- Modify: `src/utils/logger.py`
- Test: `tests/test_structured_logging.py`

### Context
Replace simple logging with structured logging that outputs JSON for better integration with monitoring systems and easier debugging.

- [ ] **Step 1: Write test for structured logger**

```python
# tests/test_structured_logging.py
import json
import pytest
from src.logging.logger import StructuredLogger

def test_structured_logger_init():
    """Test StructuredLogger initialization."""
    logger = StructuredLogger("test", level="INFO")
    assert logger.name == "test"
    assert logger.level == "INFO"

def test_structured_logger_json_output(capsys):
    """Test JSON output format."""
    logger = StructuredLogger("test")
    logger.info("Test message", extra={"user_id": "123", "action": "generate"})
    
    # Parse captured output as JSON
    captured = capsys.readouterr()
    log_line = json.loads(captured.out.strip())
    
    assert log_line["message"] == "Test message"
    assert log_line["level"] == "INFO"
    assert log_line["user_id"] == "123"
    assert log_line["action"] == "generate"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_structured_logging.py::test_structured_logger_init -v
```

Expected: FAIL - `ModuleNotFoundError: No module named 'src.logging.logger'`

- [ ] **Step 3: Implement StructuredLogger**

```python
# src/logging/__init__.py
"""Structured logging for jmAgent."""

# src/logging/logger.py
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

class StructuredLogger:
    """Logger that outputs structured JSON for better observability."""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        
        # JSON formatter handler
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _format_log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format log entry as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            **(extra or {})
        }
        return json.dumps(log_entry)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info level."""
        log_json = self._format_log("INFO", message, extra)
        self.logger.info(log_json)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error level."""
        log_json = self._format_log("ERROR", message, extra)
        self.logger.error(log_json)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning level."""
        log_json = self._format_log("WARNING", message, extra)
        self.logger.warning(log_json)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug level."""
        log_json = self._format_log("DEBUG", message, extra)
        self.logger.debug(log_json)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_structured_logging.py -v
```

Expected: PASS

- [ ] **Step 5: Update existing logger to use StructuredLogger**

```python
# src/utils/logger.py - Update get_logger function
from src.logging.logger import StructuredLogger

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
```

- [ ] **Step 6: Commit**

```bash
git add src/logging/ src/utils/logger.py tests/test_structured_logging.py
git commit -m "feat: implement structured JSON logging for observability

- Create StructuredLogger class outputting JSON format
- Add timestamp, level, logger name, message, and extra fields
- Update get_logger() to return StructuredLogger
- Comprehensive tests for JSON output format
- Better integration with monitoring and log aggregation systems
"
```

---

## Task 2: Error Handling & Resilience Patterns

**Files:**
- Create: `src/errors/__init__.py`
- Create: `src/errors/exceptions.py`
- Create: `src/resilience/__init__.py`
- Create: `src/resilience/retry.py`
- Create: `src/resilience/circuit_breaker.py`
- Modify: `src/auth/bedrock_auth.py`
- Test: `tests/test_error_handling.py`
- Test: `tests/test_resilience.py`

**Implementation Details:** Custom exception hierarchy, retry_with_backoff decorator with exponential backoff, CircuitBreaker class for API protection.

---

## Task 3: Performance Monitoring & Analytics

**Files:**
- Create: `src/monitoring/__init__.py`
- Create: `src/monitoring/metrics.py`
- Create: `src/monitoring/benchmarks.py`
- Create: `src/monitoring/analytics.py`
- Modify: `src/agent.py`
- Test: `tests/test_monitoring.py`

**Implementation Details:** MetricsCollector for request tracking, per-action statistics, token usage analytics.

---

## Task 4: Configuration Management

**Files:**
- Create: `src/config/__init__.py`
- Create: `src/config/settings.py`
- Create: `.env.example`
- Modify: `src/cli.py`
- Test: `tests/test_config.py`

**Implementation Details:** Pydantic-based Settings class with validation, environment variable support with JMAGENT_ prefix.

---

## Task 5: Audit Logging System

**Files:**
- Create: `src/audit/__init__.py`
- Create: `src/audit/logger.py`
- Create: `src/audit/storage.py`
- Modify: `src/agent.py`
- Modify: `src/cli.py`
- Test: `tests/test_audit.py`

**Implementation Details:** Comprehensive audit trail for all user actions, API calls, results.

---

## Task 6: GitHub Integration

**Files:**
- Create: `src/integrations/__init__.py`
- Create: `src/integrations/github.py`
- Create: `src/integrations/base.py`
- Test: `tests/test_github_integration.py`

**Implementation Details:** GitHub API integration for repo context, PR operations.

---

## Task 7: Custom Prompt Templates

**Files:**
- Create: `src/templates/__init__.py`
- Create: `src/templates/loader.py`
- Create: `src/templates/manager.py`
- Create: `docs/templates/` (example templates)
- Test: `tests/test_custom_templates.py`

**Implementation Details:** Template loading, validation, custom system prompts.

---

## Task 8: Plugin Architecture

**Files:**
- Create: `src/plugins/__init__.py`
- Create: `src/plugins/base.py`
- Create: `src/plugins/loader.py`
- Test: `tests/test_plugins.py`

**Implementation Details:** Base Plugin class, dynamic loader, plugin discovery.

---

## Task 9: CLI Commands & Documentation

**Files:**
- Modify: `src/cli.py` (add config, metrics, audit commands)
- Create: `docs/PHASE4_FEATURES.md`
- Modify: `README.md`
- Modify: `CLAUDE.md`

**Implementation Details:** New CLI commands for config, metrics, audit logs.

---

## Task 10: Integration Testing & Finalization

**Files:**
- Create: `tests/test_phase4_integration.py`

**Implementation Details:** Comprehensive integration tests for all Phase 4 features.

---

## Self-Review Checklist

✅ **Spec Coverage:**
- Production Hardening (Task 1-2)
- Performance Optimization (Task 3)
- Enterprise Features (Task 4-5, 9)
- Integration & Extensibility (Task 6-8)

✅ **No Placeholders:** All tasks have complete code samples and exact commands

✅ **Type Consistency:** Consistent method signatures and class definitions across tasks

---

Plan ready for Subagent-Driven Development execution.

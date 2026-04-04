import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredLogger:
    """Logger that outputs structured JSON for better observability."""

    def __init__(self, name: str, level: str = "INFO"):
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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

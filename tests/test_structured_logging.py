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


def test_structured_logger_different_levels():
    """Test different log levels."""
    logger = StructuredLogger("test")

    # Should not raise
    logger.info("info message")
    logger.error("error message")
    logger.warning("warning message")
    logger.debug("debug message")


def test_structured_logger_without_extra():
    """Test logging without extra fields."""
    logger = StructuredLogger("test")
    logger.info("Simple message")
    # Should not raise


def test_structured_logger_with_nested_extra():
    """Test logging with nested extra data."""
    logger = StructuredLogger("test")
    logger.info("Nested message", extra={
        "user": {"id": "123", "name": "test"},
        "action": "generate"
    })
    # Should properly serialize nested dict


def test_structured_logger_json_has_timestamp(capsys):
    """Test that JSON output includes timestamp."""
    logger = StructuredLogger("test")
    logger.info("Test message")

    captured = capsys.readouterr()
    log_line = json.loads(captured.out.strip())

    assert "timestamp" in log_line
    assert log_line["timestamp"]  # Should have a value


def test_structured_logger_json_has_logger_name(capsys):
    """Test that JSON output includes logger name."""
    logger = StructuredLogger("my_test_logger")
    logger.info("Test message")

    captured = capsys.readouterr()
    log_line = json.loads(captured.out.strip())

    assert log_line["logger"] == "my_test_logger"


def test_structured_logger_error_level(capsys):
    """Test ERROR level output."""
    logger = StructuredLogger("test")
    logger.error("Error occurred", extra={"error_code": "500"})

    captured = capsys.readouterr()
    log_line = json.loads(captured.out.strip())

    assert log_line["level"] == "ERROR"
    assert log_line["message"] == "Error occurred"
    assert log_line["error_code"] == "500"


def test_structured_logger_warning_level(capsys):
    """Test WARNING level output."""
    logger = StructuredLogger("test")
    logger.warning("Warning issued", extra={"warning_type": "deprecation"})

    captured = capsys.readouterr()
    log_line = json.loads(captured.out.strip())

    assert log_line["level"] == "WARNING"


def test_structured_logger_debug_level(capsys):
    """Test DEBUG level output."""
    logger = StructuredLogger("test", level="DEBUG")
    logger.debug("Debug info", extra={"debug_flag": True})

    captured = capsys.readouterr()
    log_line = json.loads(captured.out.strip())

    assert log_line["level"] == "DEBUG"


def test_structured_logger_complex_extra(capsys):
    """Test logging with complex extra data."""
    logger = StructuredLogger("test")
    logger.info("Complex data", extra={
        "user": {"id": "123", "name": "test", "role": "admin"},
        "action": "generate",
        "tokens": 4096,
        "metadata": {
            "source": "cli",
            "version": "1.0"
        }
    })

    captured = capsys.readouterr()
    log_line = json.loads(captured.out.strip())

    assert log_line["user"]["id"] == "123"
    assert log_line["metadata"]["version"] == "1.0"
    assert log_line["tokens"] == 4096

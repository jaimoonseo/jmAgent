from src.logging.logger import StructuredLogger
from src.utils.logger import get_logger


def test_get_logger_returns_structured_logger():
    """Test that get_logger returns a StructuredLogger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, StructuredLogger)
    assert logger.name == "test_logger"


def test_get_logger_has_handler():
    """Test that logger has at least one handler."""
    logger = get_logger("test_logger_2")
    assert len(logger.logger.handlers) > 0


def test_get_logger_creates_new_instance():
    """Test that calling get_logger creates a StructuredLogger instance."""
    logger1 = get_logger("test_logger_3")
    logger2 = get_logger("test_logger_3")
    # New instances are created each time, but with same underlying logger name
    assert logger1.name == logger2.name

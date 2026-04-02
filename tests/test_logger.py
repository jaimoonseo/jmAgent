import logging
from src.utils.logger import get_logger

def test_get_logger_returns_logger():
    """Test that get_logger returns a Logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"

def test_get_logger_has_handler():
    """Test that logger has at least one handler."""
    logger = get_logger("test_logger_2")
    assert len(logger.handlers) > 0

def test_get_logger_same_instance():
    """Test that calling get_logger twice returns same instance."""
    logger1 = get_logger("test_logger_3")
    logger2 = get_logger("test_logger_3")
    assert logger1 is logger2

from src.logging.logger import StructuredLogger


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance for better observability."""
    return StructuredLogger(name)

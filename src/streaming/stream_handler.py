"""Stream event handler for processing Bedrock streaming responses."""

from typing import Optional, Dict
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StreamHandler:
    """
    Handles processing of Bedrock streaming events.
    Accumulates text chunks and provides statistics.
    """

    def __init__(self):
        """Initialize StreamHandler with empty buffer and counters."""
        self.buffer: str = ""
        self.token_count: int = 0
        self.events_processed: int = 0

    def process_event(self, event: Dict) -> Optional[str]:
        """
        Process a single Bedrock stream event.

        Args:
            event: Event dictionary from Bedrock streaming response

        Returns:
            Text chunk if this is a text_delta event, None otherwise
        """
        try:
            # Check if this is a content_block_delta event
            if event.get("type") != "content_block_delta":
                return None

            # Get the delta
            delta = event.get("delta", {})

            # Only process text_delta events
            if delta.get("type") != "text_delta":
                return None

            # Extract text
            text = delta.get("text", "")

            if text:
                # Accumulate text
                self.buffer += text
                # Count this as one token (simplified - actual token count would require tokenizer)
                self.token_count += 1
                self.events_processed += 1
                logger.debug(f"Processed text delta: {len(text)} chars, total: {len(self.buffer)} chars")
                return text

            return None

        except Exception as e:
            logger.error(f"Error processing stream event: {str(e)}")
            return None

    def get_buffer(self) -> str:
        """
        Get the current accumulated text buffer.

        Returns:
            Current buffer content
        """
        return self.buffer

    def clear_buffer(self) -> str:
        """
        Clear the buffer and return its previous content.

        Returns:
            Previous buffer content
        """
        result = self.buffer
        self.buffer = ""
        return result

    def get_stats(self) -> Dict[str, int]:
        """
        Get streaming statistics.

        Returns:
            Dictionary with token_count, events_processed, and buffer_length
        """
        return {
            "token_count": self.token_count,
            "events_processed": self.events_processed,
            "buffer_length": len(self.buffer)
        }


class StreamCollector:
    """
    Collects and accumulates streamed text from multiple events.
    Provides a convenient interface for consuming streaming responses.
    """

    def __init__(self):
        """Initialize StreamCollector with a handler."""
        self.handler: StreamHandler = StreamHandler()
        self.complete_text: str = ""

    def add_event(self, event: Dict) -> None:
        """
        Add a single stream event for processing.

        Args:
            event: Event dictionary from Bedrock streaming response
        """
        self.handler.process_event(event)

    def finalize(self) -> str:
        """
        Finalize streaming and return complete accumulated text.

        Returns:
            Complete accumulated text from all events
        """
        self.complete_text = self.handler.get_buffer()
        logger.info(f"Stream finalized: {len(self.complete_text)} total chars")
        return self.complete_text

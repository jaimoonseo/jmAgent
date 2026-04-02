from dataclasses import dataclass
from typing import Optional

@dataclass
class BedrockResponse:
    """Response from Bedrock API."""
    content: str
    stop_reason: str
    usage: dict  # {"input_tokens": int, "output_tokens": int}

@dataclass
class GenerateResponse:
    """Response from generate action."""
    code: str
    language: Optional[str]
    tokens_used: dict  # {"input_tokens": int, "output_tokens": int}

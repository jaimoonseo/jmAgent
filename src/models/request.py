from dataclasses import dataclass
from typing import Optional, List, Any

@dataclass
class BedrockRequest:
    """Request to Bedrock API."""
    model_id: str
    max_tokens: int
    system_prompt: str
    user_message: str
    messages: Optional[List[dict]] = None  # Conversation history
    use_cache: bool = False
    cache_control: Optional[dict] = None

    def to_body(self) -> dict:
        """Convert to Bedrock request body."""
        messages = self.messages or []
        if self.user_message:
            messages.append({"role": "user", "content": self.user_message})

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages
        }

        # Add cache control if enabled
        if self.use_cache and self.cache_control:
            body["system"] = [
                {"type": "text", "text": self.system_prompt},
                {"type": "text", "text": self.cache_control.get("context", ""), "cache_control": {"type": "ephemeral"}}
            ]

        return body

@dataclass
class GenerateRequest:
    """Request to generate code."""
    prompt: str
    language: Optional[str] = None
    context_files: Optional[List[str]] = None
    temperature: float = 0.2
    max_tokens: int = 4096

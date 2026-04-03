from dataclasses import dataclass
from typing import Optional, List

@dataclass
class BedrockRequest:
    """Request to Bedrock API."""
    model_id: str
    max_tokens: int
    system_prompt: str
    user_message: str
    messages: Optional[List[dict]] = None  # Conversation history

    def to_body(self) -> dict:
        """Convert to Bedrock request body."""
        messages = self.messages or []
        if self.user_message:
            messages.append({"role": "user", "content": self.user_message})

        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages
        }

@dataclass
class GenerateRequest:
    """Request to generate code."""
    prompt: str
    language: Optional[str] = None
    context_files: Optional[List[str]] = None
    temperature: float = 0.2
    max_tokens: int = 4096

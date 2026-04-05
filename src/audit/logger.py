"""Audit logger for recording user actions and API calls."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
import json


@dataclass
class AuditRecord:
    """
    Represents a single audit log entry.

    Attributes:
        action_type: Type of action ('generate', 'refactor', 'test', 'explain', 'fix', 'chat')
        user: Username or 'anonymous'
        timestamp: ISO 8601 timestamp
        input_data: Input parameters for the action
        output_data: Generated output from the action
        status: Status of the action ('success', 'failure', 'partial')
        error_message: Error details if status is 'failure'
        duration: Execution time in seconds
        tokens_used: Dictionary with 'input_tokens' and 'output_tokens'
        metadata: Additional custom fields (model, temperature, etc.)
    """

    action_type: str
    user: str
    timestamp: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    status: str
    error_message: Optional[str] = None
    duration: Optional[float] = None
    tokens_used: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert AuditRecord to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditRecord":
        """Create AuditRecord from dictionary."""
        return cls(**data)


class AuditLogger:
    """
    Logger for recording user actions, API calls, and results.

    This logger captures comprehensive audit trails for compliance and debugging,
    including action type, user, timestamp, inputs, outputs, and execution metrics.
    """

    def __init__(self, user: str = "anonymous"):
        """
        Initialize AuditLogger.

        Args:
            user: Username for audit logs (default: 'anonymous')
        """
        self.user = user

    def log_action(
        self,
        action_type: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        duration: Optional[float] = None,
        tokens_used: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditRecord:
        """
        Log a user action or API call.

        Args:
            action_type: Type of action ('generate', 'refactor', 'test', 'explain', 'fix', 'chat')
            input_data: Input parameters for the action
            output_data: Generated output from the action
            status: Status of the action ('success', 'failure', 'partial')
            error_message: Error details if status is 'failure'
            duration: Execution time in seconds
            tokens_used: Dictionary with token counts
            metadata: Additional custom fields

        Returns:
            AuditRecord: The created audit record
        """
        # Generate ISO 8601 timestamp
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Create audit record
        record = AuditRecord(
            action_type=action_type,
            user=self.user,
            timestamp=timestamp,
            input_data=input_data,
            output_data=output_data,
            status=status,
            error_message=error_message,
            duration=duration,
            tokens_used=tokens_used or {},
            metadata=metadata or {}
        )

        return record

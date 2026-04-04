"""Metrics collection for performance monitoring."""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class ActionMetric:
    """Represents a single action metric."""
    action_type: str
    response_time: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "action_type": self.action_type,
            "response_time": self.response_time,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsCollector:
    """Collects and aggregates metrics for all actions."""

    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics: List[ActionMetric] = []

    def record_metric(
        self,
        action_type: str,
        response_time: float,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Record a metric for an action.

        Args:
            action_type: Type of action (generate, refactor, test, explain, fix, chat)
            response_time: Time taken to complete the action in seconds
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            success: Whether the action succeeded
            error: Error message if action failed (optional)
        """
        total_tokens = input_tokens + output_tokens
        metric = ActionMetric(
            action_type=action_type,
            response_time=response_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            success=success,
            error=error,
            timestamp=datetime.now(),
        )
        self.metrics.append(metric)

    def get_action_stats(self, action_type: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific action type.

        Args:
            action_type: Type of action

        Returns:
            Dictionary with statistics or None if no metrics found
        """
        action_metrics = [m for m in self.metrics if m.action_type == action_type]
        if not action_metrics:
            return None

        response_times = [m.response_time for m in action_metrics]
        success_count = sum(1 for m in action_metrics if m.success)
        failure_count = len(action_metrics) - success_count

        return {
            "action_type": action_type,
            "count": len(action_metrics),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / len(action_metrics),
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "total_tokens": sum(m.total_tokens for m in action_metrics),
            "total_input_tokens": sum(m.input_tokens for m in action_metrics),
            "total_output_tokens": sum(m.output_tokens for m in action_metrics),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all action types.

        Returns:
            Dictionary mapping action_type -> stats
        """
        action_types = set(m.action_type for m in self.metrics)
        stats = {}
        for action_type in action_types:
            action_stats = self.get_action_stats(action_type)
            if action_stats:
                stats[action_type] = action_stats
        return stats

    def clear(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()

    def to_json(self) -> str:
        """Convert metrics to JSON string."""
        metrics_dicts = [m.to_dict() for m in self.metrics]
        return json.dumps(metrics_dicts)

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert metrics to list of dictionaries."""
        return [m.to_dict() for m in self.metrics]

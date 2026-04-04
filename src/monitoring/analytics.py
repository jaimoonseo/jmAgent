"""Analytics engine for performance metrics."""

import json
import statistics
from typing import Dict, Any, Optional
from src.monitoring.metrics import MetricsCollector


# Pricing constants for Claude Haiku (as of 2025)
# Using example pricing - actual prices may vary
PRICING = {
    "input_tokens_per_1m": 0.80,      # $0.80 per 1M input tokens
    "output_tokens_per_1m": 4.00,     # $4.00 per 1M output tokens
}


class AnalyticsEngine:
    """Provides analytics and reporting on collected metrics."""

    def __init__(self, collector: MetricsCollector):
        """
        Initialize the analytics engine.

        Args:
            collector: MetricsCollector instance
        """
        self.collector = collector

    def get_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of all metrics.

        Returns:
            Dictionary with summary statistics
        """
        all_stats = self.collector.get_all_stats()
        metrics = self.collector.metrics

        total_requests = len(metrics)
        total_success = sum(1 for m in metrics if m.success)
        overall_success_rate = (
            total_success / total_requests if total_requests > 0 else 0
        )

        return {
            "total_requests": total_requests,
            "total_success": total_success,
            "total_failures": total_requests - total_success,
            "overall_success_rate": overall_success_rate,
            "actions": all_stats,
        }

    def get_token_usage_breakdown(self) -> Dict[str, Any]:
        """
        Get breakdown of token usage by action type.

        Returns:
            Dictionary with token usage breakdown
        """
        all_stats = self.collector.get_all_stats()
        breakdown = {"total_tokens": 0}

        for action_type, stats in all_stats.items():
            breakdown[action_type] = {
                "total": stats["total_tokens"],
                "input": stats["total_input_tokens"],
                "output": stats["total_output_tokens"],
                "requests": stats["count"],
            }
            breakdown["total_tokens"] += stats["total_tokens"]

        return breakdown

    def estimate_cost(self) -> float:
        """
        Estimate total cost based on token usage.

        Returns:
            Estimated cost in USD
        """
        total_input = sum(m.input_tokens for m in self.collector.metrics)
        total_output = sum(m.output_tokens for m in self.collector.metrics)

        input_cost = (total_input / 1_000_000) * PRICING["input_tokens_per_1m"]
        output_cost = (total_output / 1_000_000) * PRICING["output_tokens_per_1m"]

        return round(input_cost + output_cost, 6)

    def estimate_cost_by_action(self) -> Dict[str, float]:
        """
        Estimate cost broken down by action type.

        Returns:
            Dictionary mapping action_type -> estimated_cost
        """
        all_stats = self.collector.get_all_stats()
        cost_by_action = {}

        for action_type, stats in all_stats.items():
            input_cost = (
                (stats["total_input_tokens"] / 1_000_000)
                * PRICING["input_tokens_per_1m"]
            )
            output_cost = (
                (stats["total_output_tokens"] / 1_000_000)
                * PRICING["output_tokens_per_1m"]
            )
            cost_by_action[action_type] = round(input_cost + output_cost, 6)

        return cost_by_action

    def get_response_time_distribution(self) -> Dict[str, float]:
        """
        Get response time statistics.

        Returns:
            Dictionary with response time distribution
        """
        if not self.collector.metrics:
            return {
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "stddev": 0,
            }

        response_times = [m.response_time for m in self.collector.metrics]

        return {
            "min": min(response_times),
            "max": max(response_times),
            "mean": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "stddev": statistics.stdev(response_times)
            if len(response_times) > 1
            else 0,
        }

    def get_success_rate(self) -> float:
        """
        Get overall success rate.

        Returns:
            Success rate as decimal (0.0-1.0)
        """
        if not self.collector.metrics:
            return 0.0

        total = len(self.collector.metrics)
        success = sum(1 for m in self.collector.metrics if m.success)
        return success / total

    def get_success_rate_by_action(self) -> Dict[str, float]:
        """
        Get success rate broken down by action type.

        Returns:
            Dictionary mapping action_type -> success_rate
        """
        all_stats = self.collector.get_all_stats()
        return {action_type: stats["success_rate"] for action_type, stats in all_stats.items()}

    def get_report_as_json(self) -> str:
        """
        Get full report as JSON string.

        Returns:
            JSON string containing full analytics report
        """
        report = {
            "summary": self.get_summary_report(),
            "token_breakdown": self.get_token_usage_breakdown(),
            "cost": {
                "total": self.estimate_cost(),
                "by_action": self.estimate_cost_by_action(),
            },
            "response_times": self.get_response_time_distribution(),
            "success_rates": {
                "overall": self.get_success_rate(),
                "by_action": self.get_success_rate_by_action(),
            },
        }
        return json.dumps(report, indent=2)

    def get_report_as_dict(self) -> Dict[str, Any]:
        """
        Get full report as dictionary.

        Returns:
            Dictionary containing full analytics report
        """
        return {
            "summary": self.get_summary_report(),
            "token_breakdown": self.get_token_usage_breakdown(),
            "cost": {
                "total": self.estimate_cost(),
                "by_action": self.estimate_cost_by_action(),
            },
            "response_times": self.get_response_time_distribution(),
            "success_rates": {
                "overall": self.get_success_rate(),
                "by_action": self.get_success_rate_by_action(),
            },
        }

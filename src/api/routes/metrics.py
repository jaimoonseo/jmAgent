"""Metrics management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
from datetime import datetime, timezone

from src.api.models import APIResponse
from src.api.security.auth import get_current_user
from src.api.schemas.management import (
    MetricsSummary,
    ActionMetrics,
    MetricsbyActionResponse,
    MetricsCostResponse,
    ActionCost,
    MetricsHistoryResponse,
    MetricsHistoryEntry,
    ResetMetricsResponse,
)
from src.monitoring.metrics import MetricsCollector
from src.logging.logger import StructuredLogger

router = APIRouter(tags=["metrics"])
logger = StructuredLogger(__name__)

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Pricing per 1M tokens (for Haiku model)
PRICING_HAIKU = {
    "input": 0.08,  # $0.08 per 1M input tokens
    "output": 0.24,  # $0.24 per 1M output tokens
}

# Pricing for other models
PRICING_SONNET = {
    "input": 3.0,  # $3.00 per 1M input tokens
    "output": 15.0,  # $15.00 per 1M output tokens
}

PRICING_OPUS = {
    "input": 15.0,  # $15.00 per 1M input tokens
    "output": 75.0,  # $75.00 per 1M output tokens
}


def calculate_cost(input_tokens: int, output_tokens: int, model: str = "haiku") -> float:
    """
    Calculate the cost for token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (haiku, sonnet, opus)

    Returns:
        Cost in USD
    """
    pricing = PRICING_HAIKU
    if model == "sonnet":
        pricing = PRICING_SONNET
    elif model == "opus":
        pricing = PRICING_OPUS

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


@router.get(
    "/metrics/summary",
    response_model=APIResponse,
    summary="Get Overall Metrics Summary",
    tags=["Metrics"],
)
async def get_metrics_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve overall metrics summary.

    Returns aggregated statistics including total requests, average response time,
    total tokens used, and success rate.
    """
    try:
        all_stats = metrics_collector.get_all_stats()

        # Calculate overall metrics
        total_requests = sum(stats["count"] for stats in all_stats.values())
        total_tokens = sum(stats["total_tokens"] for stats in all_stats.values())

        if total_requests == 0:
            summary = MetricsSummary(
                total_requests=0,
                avg_response_time=0.0,
                total_tokens_used=0,
                success_rate=0.0,
                last_updated=datetime.now(timezone.utc).isoformat(),
            )
        else:
            # Calculate weighted average response time
            total_response_time = sum(
                stats["count"] * stats["avg_response_time"]
                for stats in all_stats.values()
            )
            avg_response_time = total_response_time / total_requests

            # Calculate overall success rate
            total_successes = sum(stats["success_count"] for stats in all_stats.values())
            success_rate = total_successes / total_requests

            summary = MetricsSummary(
                total_requests=total_requests,
                avg_response_time=avg_response_time,
                total_tokens_used=total_tokens,
                success_rate=success_rate,
                last_updated=datetime.now(timezone.utc).isoformat(),
            )

        logger.info(
            "Metrics summary retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "total_requests": total_requests,
                "total_tokens": total_tokens,
            },
        )

        return APIResponse(success=True, data=summary)
    except Exception as e:
        logger.error(
            "Error retrieving metrics summary",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics summary")


@router.get(
    "/metrics/by-action",
    response_model=APIResponse,
    summary="Get Per-Action Metrics",
    tags=["Metrics"],
)
async def get_metrics_by_action(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve metrics broken down by action type.

    Returns individual statistics for each action type (generate, refactor, test, etc.).
    """
    try:
        all_stats = metrics_collector.get_all_stats()

        # Convert to ActionMetrics objects
        actions_data = {}
        for action_type, stats in all_stats.items():
            actions_data[action_type] = ActionMetrics(
                count=stats["count"],
                success_count=stats["success_count"],
                failure_count=stats["failure_count"],
                success_rate=stats["success_rate"],
                avg_response_time=stats["avg_response_time"],
                min_response_time=stats["min_response_time"],
                max_response_time=stats["max_response_time"],
                total_tokens=stats["total_tokens"],
                total_input_tokens=stats["total_input_tokens"],
                total_output_tokens=stats["total_output_tokens"],
            )

        response_data = MetricsbyActionResponse(actions=actions_data)

        logger.info(
            "Per-action metrics retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "action_count": len(actions_data),
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error retrieving per-action metrics",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve action metrics")


@router.get(
    "/metrics/cost",
    response_model=APIResponse,
    summary="Get Cost Estimation",
    tags=["Metrics"],
)
async def get_metrics_cost(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve cost estimation based on token usage.

    Returns estimated costs broken down by action type using Haiku pricing.
    """
    try:
        all_stats = metrics_collector.get_all_stats()

        # Calculate costs by action
        by_action = {}
        total_cost = 0.0

        for action_type, stats in all_stats.items():
            action_cost = calculate_cost(
                stats["total_input_tokens"],
                stats["total_output_tokens"],
                model="haiku",
            )
            by_action[action_type] = ActionCost(
                requests=stats["count"],
                cost=round(action_cost, 4),
            )
            total_cost += action_cost

        response_data = MetricsCostResponse(
            total_cost=round(total_cost, 4),
            by_action=by_action,
        )

        logger.info(
            "Cost estimation retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "total_cost": total_cost,
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error retrieving cost estimation",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve cost estimation")


@router.get(
    "/metrics/history",
    response_model=APIResponse,
    summary="Get Metrics History",
    tags=["Metrics"],
)
async def get_metrics_history(
    limit: int = Query(20, ge=1, le=100, description="Number of metrics to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve historical metrics with pagination.

    Returns a paginated list of individual metric records.
    """
    try:
        # Get all metrics as list of dicts
        all_metrics = metrics_collector.to_dict()

        # Apply pagination (reverse order - most recent first)
        total = len(all_metrics)
        start = max(0, total - offset - limit)
        end = max(0, total - offset)
        paginated_metrics = all_metrics[start:end]

        # Convert to MetricsHistoryEntry objects
        history_entries = []
        for metric in paginated_metrics:
            entry = MetricsHistoryEntry(
                timestamp=metric["timestamp"],
                action_type=metric["action_type"],
                response_time=metric["response_time"],
                input_tokens=metric["input_tokens"],
                output_tokens=metric["output_tokens"],
                total_tokens=metric["total_tokens"],
                success=metric["success"],
                error=metric["error"],
            )
            history_entries.append(entry)

        response_data = MetricsHistoryResponse(
            metrics=history_entries,
            total=total,
            limit=limit,
            offset=offset,
        )

        logger.info(
            "Metrics history retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "limit": limit,
                "offset": offset,
                "total": total,
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error retrieving metrics history",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics history")


@router.get(
    "/metrics/by-model",
    response_model=APIResponse,
    summary="Get Metrics by Model",
    tags=["Metrics"],
)
async def get_metrics_by_model(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve metrics broken down by model type.

    Returns individual statistics for each model (haiku, sonnet, opus).
    """
    try:
        all_stats = metrics_collector.get_all_stats()

        # Group metrics by model - extract from action names or metadata
        # For now, we'll create model breakdown from all stats
        # In real implementation, metrics would track model separately
        by_model = {
            "haiku": ActionMetrics(
                count=0,
                success_count=0,
                failure_count=0,
                success_rate=0.0,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                total_tokens=0,
                total_input_tokens=0,
                total_output_tokens=0,
            ),
            "sonnet": ActionMetrics(
                count=0,
                success_count=0,
                failure_count=0,
                success_rate=0.0,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                total_tokens=0,
                total_input_tokens=0,
                total_output_tokens=0,
            ),
            "opus": ActionMetrics(
                count=0,
                success_count=0,
                failure_count=0,
                success_rate=0.0,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                total_tokens=0,
                total_input_tokens=0,
                total_output_tokens=0,
            ),
        }

        # For now, assume all metrics are haiku (default model)
        # In production, metrics would track model type separately
        if all_stats:
            for action_type, stats in all_stats.items():
                by_model["haiku"] = ActionMetrics(
                    count=stats["count"],
                    success_count=stats["success_count"],
                    failure_count=stats["failure_count"],
                    success_rate=stats["success_rate"],
                    avg_response_time=stats["avg_response_time"],
                    min_response_time=stats["min_response_time"],
                    max_response_time=stats["max_response_time"],
                    total_tokens=stats["total_tokens"],
                    total_input_tokens=stats["total_input_tokens"],
                    total_output_tokens=stats["total_output_tokens"],
                )
                break

        response_data = {
            "by_model": by_model,
        }

        logger.info(
            "Per-model metrics retrieved",
            extra={
                "user_id": current_user.get("user_id"),
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error retrieving per-model metrics",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve model metrics")


@router.delete(
    "/metrics",
    response_model=APIResponse,
    summary="Delete All Metrics",
    tags=["Metrics"],
)
async def delete_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete all recorded metrics.

    Removes all metrics data and resets counters.
    """
    try:
        count = len(metrics_collector.metrics)
        metrics_collector.clear()

        logger.info(
            "Metrics deleted",
            extra={
                "user_id": current_user.get("user_id"),
                "deleted_count": count,
            },
        )

        return APIResponse(
            success=True,
            data=ResetMetricsResponse(
                reset=True,
                cleared_count=count,
            ),
        )
    except Exception as e:
        logger.error(
            "Error deleting metrics",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to delete metrics")

"""Request and response models for management endpoints."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, List
from datetime import datetime
from enum import Enum


# Configuration Models
class UpdateConfigRequest(BaseModel):
    """Request to update a single configuration setting."""

    key: str = Field(..., description="Setting key")
    value: Any = Field(..., description="Setting value")


class UpdateAllConfigRequest(BaseModel):
    """Request to replace all configuration settings."""

    model_config = ConfigDict(extra="allow")


class ConfigResponse(BaseModel):
    """Response with configuration data."""

    all_settings: Dict[str, Any] = Field(..., description="All current settings")


class UpdatedConfigResponse(BaseModel):
    """Response after updating a configuration setting."""

    updated: bool = Field(..., description="Whether update was successful")
    key: str = Field(..., description="Updated setting key")
    value: Any = Field(..., description="New setting value")


class ReplacedConfigResponse(BaseModel):
    """Response after replacing all settings."""

    replaced: bool = Field(..., description="Whether replacement was successful")
    count: int = Field(..., description="Number of settings replaced")


class DeletedConfigResponse(BaseModel):
    """Response after deleting a setting."""

    deleted: bool = Field(..., description="Whether deletion was successful")
    key: str = Field(..., description="Deleted setting key")
    default_value: Any = Field(..., description="Default value for the setting")


class ResetConfigResponse(BaseModel):
    """Response after resetting all settings to defaults."""

    reset: bool = Field(..., description="Whether reset was successful")
    defaults_count: int = Field(..., description="Number of settings reset")


# Metrics Models
class MetricsSummary(BaseModel):
    """Summary of overall metrics."""

    total_requests: int = Field(..., description="Total number of requests")
    avg_response_time: float = Field(..., description="Average response time in seconds")
    total_tokens_used: int = Field(..., description="Total tokens used")
    success_rate: float = Field(..., description="Success rate (0-1)")
    last_updated: str = Field(..., description="Timestamp of last update")


class ActionMetrics(BaseModel):
    """Metrics for a single action type."""

    count: int = Field(..., description="Number of executions")
    success_count: int = Field(..., description="Number of successful executions")
    failure_count: int = Field(..., description="Number of failed executions")
    success_rate: float = Field(..., description="Success rate (0-1)")
    avg_response_time: float = Field(..., description="Average response time in seconds")
    min_response_time: float = Field(..., description="Minimum response time in seconds")
    max_response_time: float = Field(..., description="Maximum response time in seconds")
    total_tokens: int = Field(..., description="Total tokens used")
    total_input_tokens: int = Field(..., description="Total input tokens")
    total_output_tokens: int = Field(..., description="Total output tokens")


class MetricsbyActionResponse(BaseModel):
    """Response with per-action metrics."""

    actions: Dict[str, ActionMetrics] = Field(..., description="Metrics by action type")


class ActionCost(BaseModel):
    """Cost information for an action type."""

    requests: int = Field(..., description="Number of requests")
    cost: float = Field(..., description="Estimated cost in USD")


class MetricsCostResponse(BaseModel):
    """Response with cost estimation."""

    total_cost: float = Field(..., description="Total estimated cost in USD")
    by_action: Dict[str, ActionCost] = Field(..., description="Cost by action type")


class MetricsHistoryEntry(BaseModel):
    """Single entry in metrics history."""

    timestamp: str = Field(..., description="Timestamp of the metric")
    action_type: str = Field(..., description="Type of action")
    response_time: float = Field(..., description="Response time in seconds")
    input_tokens: int = Field(..., description="Input tokens used")
    output_tokens: int = Field(..., description="Output tokens generated")
    total_tokens: int = Field(..., description="Total tokens used")
    success: bool = Field(..., description="Whether the action succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class MetricsHistoryResponse(BaseModel):
    """Response with paginated metrics history."""

    metrics: List[MetricsHistoryEntry] = Field(..., description="Metrics entries")
    total: int = Field(..., description="Total number of metrics")
    limit: int = Field(..., description="Limit used in query")
    offset: int = Field(..., description="Offset used in query")


class ResetMetricsResponse(BaseModel):
    """Response after resetting metrics."""

    reset: bool = Field(..., description="Whether reset was successful")
    cleared_count: int = Field(..., description="Number of metrics cleared")


# Audit Models
class AuditLogEntry(BaseModel):
    """Single audit log entry."""

    id: int = Field(..., description="Audit log ID")
    timestamp: str = Field(..., description="Timestamp of the action")
    user_id: str = Field(..., description="User ID who performed the action")
    action: str = Field(..., description="Action type")
    status: str = Field(..., description="Action status (success/failure)")
    details: Dict[str, Any] = Field(..., description="Additional details")


class AuditLogsResponse(BaseModel):
    """Response with paginated audit logs."""

    logs: List[AuditLogEntry] = Field(..., description="Audit log entries")
    total: int = Field(..., description="Total number of logs")
    limit: int = Field(..., description="Limit used in query")
    offset: int = Field(..., description="Offset used in query")


class AuditSearchRequest(BaseModel):
    """Request to search audit logs."""

    action: Optional[str] = Field(None, description="Filter by action type")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by status")
    start_date: Optional[str] = Field(None, description="Filter by start date (ISO format)")
    end_date: Optional[str] = Field(None, description="Filter by end date (ISO format)")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class ClearAuditRequest(BaseModel):
    """Request to clear audit logs."""

    confirm: bool = Field(..., description="Must be true to confirm clearing all logs")


class ClearedAuditResponse(BaseModel):
    """Response after clearing audit logs."""

    cleared: bool = Field(..., description="Whether clearing was successful")
    count: int = Field(..., description="Number of logs cleared")


# Plugin Models
class PluginInfo(BaseModel):
    """Information about a single plugin."""

    name: str = Field(..., description="Plugin name")
    enabled: bool = Field(..., description="Whether plugin is enabled")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")


class PluginsListResponse(BaseModel):
    """Response with list of plugins."""

    plugins: List[PluginInfo] = Field(..., description="List of plugins")


class PluginDetailResponse(BaseModel):
    """Detailed information about a plugin."""

    name: str = Field(..., description="Plugin name")
    enabled: bool = Field(..., description="Whether plugin is enabled")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    config_schema: Dict[str, Any] = Field(..., description="Plugin configuration schema")


class PluginStateResponse(BaseModel):
    """Response after changing plugin state."""

    name: str = Field(..., description="Plugin name")
    enabled: bool = Field(..., description="New enabled state")


class PluginConfigRequest(BaseModel):
    """Request to update plugin configuration."""

    config: Dict[str, Any] = Field(..., description="Plugin configuration")


class PluginConfigResponse(BaseModel):
    """Response with plugin configuration."""

    name: str = Field(..., description="Plugin name")
    config: Dict[str, Any] = Field(..., description="Plugin configuration")


class UpdatedPluginConfigResponse(BaseModel):
    """Response after updating plugin configuration."""

    name: str = Field(..., description="Plugin name")
    config: Dict[str, Any] = Field(..., description="Updated configuration")
    updated: bool = Field(..., description="Whether update was successful")


# Template Models
class TemplateInfo(BaseModel):
    """Information about a single template."""

    name: str = Field(..., description="Template name")
    action: str = Field(..., description="Action type (generate, refactor, test, etc.)")
    description: str = Field(..., description="Template description")
    variables: List[str] = Field(..., description="List of template variables")


class TemplatesListResponse(BaseModel):
    """Response with list of templates."""

    templates: List[TemplateInfo] = Field(..., description="List of templates")


class TemplateDetailResponse(BaseModel):
    """Detailed information about a template."""

    name: str = Field(..., description="Template name")
    action: str = Field(..., description="Action type")
    content: str = Field(..., description="Template content")
    variables: List[str] = Field(..., description="List of template variables")


class CreateTemplateRequest(BaseModel):
    """Request to create a custom template."""

    name: str = Field(..., description="Template name")
    action: str = Field(..., description="Action type")
    content: str = Field(..., description="Template content")
    description: str = Field(..., description="Template description")


class CreatedTemplateResponse(BaseModel):
    """Response after creating a template."""

    name: str = Field(..., description="Template name")
    created: bool = Field(..., description="Whether creation was successful")


class UpdateTemplateRequest(BaseModel):
    """Request to update a template."""

    content: str = Field(..., description="Updated template content")
    description: str = Field(..., description="Updated description")


class UpdatedTemplateResponse(BaseModel):
    """Response after updating a template."""

    name: str = Field(..., description="Template name")
    updated: bool = Field(..., description="Whether update was successful")


class DeletedTemplateResponse(BaseModel):
    """Response after deleting a template."""

    name: str = Field(..., description="Template name")
    deleted: bool = Field(..., description="Whether deletion was successful")


class TemplatePreviewRequest(BaseModel):
    """Request to preview a template with variables."""

    variables: Dict[str, Any] = Field(..., description="Variables for template rendering")


class TemplatePreviewResponse(BaseModel):
    """Response with rendered template."""

    name: str = Field(..., description="Template name")
    rendered: str = Field(..., description="Rendered template content")

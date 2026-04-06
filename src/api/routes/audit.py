"""Audit log management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import csv
import json
import io

from src.api.models import APIResponse
from src.api.security.auth import get_current_user
from src.api.schemas.management import (
    AuditLogsResponse,
    AuditLogEntry,
    AuditSearchRequest,
    ClearAuditRequest,
    ClearedAuditResponse,
)
from src.audit.storage import AuditStorage
from src.logging.logger import StructuredLogger

router = APIRouter(tags=["audit"])
logger = StructuredLogger(__name__)

# Global audit storage instance
audit_storage = AuditStorage(db_path="audit.db")


def is_admin(user: Dict[str, Any]) -> bool:
    """Check if user has admin privileges."""
    # Check for admin marker in JWT claims
    return user.get("admin", False) or user.get("user_id") == "admin_user"


def _get_all_logs():
    """Get all audit logs from storage."""
    try:
        return audit_storage.get_all()
    except Exception as e:
        logger.error("Error retrieving logs from storage", extra={"error": str(e)})
        return []


def _filter_logs(
    logs,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Filter logs based on criteria."""
    filtered = logs

    if action:
        filtered = [log for log in filtered if log.action_type == action]

    if user_id:
        filtered = [log for log in filtered if log.user == user_id]

    if status:
        filtered = [log for log in filtered if log.status == status]

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            filtered = [
                log
                for log in filtered
                if datetime.fromisoformat(log.timestamp) >= start_dt
            ]
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            filtered = [
                log
                for log in filtered
                if datetime.fromisoformat(log.timestamp) <= end_dt
            ]
        except ValueError:
            pass

    return filtered


def _audit_record_to_entry(record, idx: int) -> AuditLogEntry:
    """Convert AuditRecord to AuditLogEntry."""
    return AuditLogEntry(
        id=idx,
        timestamp=record.timestamp,
        user_id=record.user,
        action=record.action_type,
        status=record.status,
        details={
            "error": record.error_message,
            "duration": record.duration,
            "tokens_used": record.tokens_used,
            "metadata": record.metadata,
        },
    )


@router.get(
    "/audit/logs",
    response_model=APIResponse,
    summary="Get Recent Audit Logs",
    tags=["Audit"],
)
async def get_audit_logs(
    limit: int = Query(20, ge=1, le=100, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve recent audit logs with pagination.

    Returns a paginated list of audit log entries showing actions performed in the system.
    """
    try:
        # Get all logs
        all_logs = _get_all_logs()

        # Apply pagination (reverse order - most recent first)
        total = len(all_logs)
        start = max(0, total - offset - limit)
        end = max(0, total - offset)
        paginated_logs = all_logs[start:end]

        # Convert to AuditLogEntry objects
        log_entries = [
            _audit_record_to_entry(log, idx)
            for idx, log in enumerate(paginated_logs, start=offset)
        ]

        response_data = AuditLogsResponse(
            logs=log_entries,
            total=total,
            limit=limit,
            offset=offset,
        )

        logger.info(
            "Audit logs retrieved",
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
            "Error retrieving audit logs",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get(
    "/audit/search",
    response_model=APIResponse,
    summary="Search Audit Logs",
    tags=["Audit"],
)
async def search_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Search audit logs with filters.

    Supports filtering by action type, user ID, status, and date range.
    """
    try:
        # Get all logs
        all_logs = _get_all_logs()

        # Apply filters
        filtered_logs = _filter_logs(
            all_logs,
            action=action,
            user_id=user_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        # Apply pagination
        total = len(filtered_logs)
        start = max(0, total - offset - limit)
        end = max(0, total - offset)
        paginated_logs = filtered_logs[start:end]

        # Convert to AuditLogEntry objects
        log_entries = [
            _audit_record_to_entry(log, idx)
            for idx, log in enumerate(paginated_logs, start=offset)
        ]

        response_data = AuditLogsResponse(
            logs=log_entries,
            total=total,
            limit=limit,
            offset=offset,
        )

        logger.info(
            "Audit logs searched",
            extra={
                "user_id": current_user.get("user_id"),
                "action": action,
                "user_id_filter": user_id,
                "status": status,
                "total": total,
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error searching audit logs",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to search audit logs")


@router.get(
    "/audit/export",
    summary="Export Audit Logs",
    tags=["Audit"],
)
async def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    start_date: Optional[str] = Query(None, description="Filter by start date"),
    end_date: Optional[str] = Query(None, description="Filter by end date"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Export audit logs in CSV or JSON format.

    Supports date range filtering. Returns proper Content-Type headers for the format.
    """
    try:
        # Get all logs
        all_logs = _get_all_logs()

        # Apply date filtering if specified
        filtered_logs = _filter_logs(
            all_logs,
            start_date=start_date,
            end_date=end_date,
        )

        if format == "json":
            # JSON export
            export_data = [
                {
                    "timestamp": log.timestamp,
                    "user_id": log.user,
                    "action": log.action_type,
                    "status": log.status,
                    "error": log.error_message,
                    "duration": log.duration,
                    "tokens_used": log.tokens_used,
                    "metadata": log.metadata,
                }
                for log in filtered_logs
            ]

            json_str = json.dumps(export_data, indent=2)

            logger.info(
                "Audit logs exported as JSON",
                extra={
                    "user_id": current_user.get("user_id"),
                    "count": len(export_data),
                },
            )

            return StreamingResponse(
                io.BytesIO(json_str.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now(timezone.utc).date()}.json"
                },
            )

        else:
            # CSV export
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                "timestamp",
                "user_id",
                "action",
                "status",
                "error",
                "duration",
                "tokens_used",
            ])

            # Write rows
            for log in filtered_logs:
                writer.writerow([
                    log.timestamp,
                    log.user,
                    log.action_type,
                    log.status,
                    log.error_message or "",
                    log.duration or "",
                    json.dumps(log.tokens_used) if log.tokens_used else "",
                ])

            csv_str = output.getvalue()

            logger.info(
                "Audit logs exported as CSV",
                extra={
                    "user_id": current_user.get("user_id"),
                    "count": len(filtered_logs),
                },
            )

            return StreamingResponse(
                io.BytesIO(csv_str.encode()),
                media_type="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now(timezone.utc).date()}.csv"
                },
            )
    except Exception as e:
        logger.error(
            "Error exporting audit logs",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to export audit logs")


@router.get(
    "/audit/summary",
    response_model=APIResponse,
    summary="Get Audit Summary Statistics",
    tags=["Audit"],
)
async def get_audit_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get summary statistics about audit logs.

    Returns total count, action breakdown, success rate, and error rate.
    """
    try:
        all_logs = _get_all_logs()
        total = len(all_logs)

        if total == 0:
            summary_data = {
                "total_logs": 0,
                "actions": {},
                "success_rate": 0.0,
                "error_rate": 0.0,
            }
        else:
            # Count by action
            actions = {}
            success_count = 0
            error_count = 0

            for log in all_logs:
                action = log.action_type
                if action not in actions:
                    actions[action] = 0
                actions[action] += 1

                if log.status == "success":
                    success_count += 1
                else:
                    error_count += 1

            summary_data = {
                "total_logs": total,
                "actions": actions,
                "success_rate": success_count / total,
                "error_rate": error_count / total,
            }

        logger.info(
            "Audit summary retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "total_logs": total,
            },
        )

        return APIResponse(success=True, data=summary_data)
    except Exception as e:
        logger.error(
            "Error retrieving audit summary",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve audit summary")


@router.delete(
    "/audit/logs",
    response_model=APIResponse,
    summary="Delete All Audit Logs",
    tags=["Audit"],
)
async def delete_audit_logs(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete all audit logs.

    This is an admin-only operation that removes all audit log entries.
    """
    try:
        # Check admin privilege
        if not is_admin(current_user):
            logger.warning(
                "Non-admin user attempted to delete audit logs",
                extra={"user_id": current_user.get("user_id")},
            )
            raise HTTPException(
                status_code=403,
                detail="Only administrators can delete audit logs",
            )

        # Get count before clearing
        all_logs = _get_all_logs()
        count = len(all_logs)

        # Clear logs
        audit_storage.clear()

        logger.warning(
            "All audit logs deleted",
            extra={
                "user_id": current_user.get("user_id"),
                "deleted_count": count,
            },
        )

        return APIResponse(
            success=True,
            data=ClearedAuditResponse(
                cleared=True,
                count=count,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting audit logs",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to delete audit logs")

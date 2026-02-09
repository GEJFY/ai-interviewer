"""Audit logging service for enterprise compliance.

Provides comprehensive audit trail for all system activities,
supporting regulatory compliance and security requirements.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class AuditAction(StrEnum):
    """Types of auditable actions."""

    # Authentication
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    PASSWORD_CHANGED = "auth.password_changed"
    MFA_ENABLED = "auth.mfa_enabled"
    MFA_DISABLED = "auth.mfa_disabled"

    # User Management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ROLE_CHANGED = "user.role_changed"

    # Project Management
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    PROJECT_ARCHIVED = "project.archived"

    # Interview Operations
    INTERVIEW_CREATED = "interview.created"
    INTERVIEW_STARTED = "interview.started"
    INTERVIEW_PAUSED = "interview.paused"
    INTERVIEW_RESUMED = "interview.resumed"
    INTERVIEW_COMPLETED = "interview.completed"
    INTERVIEW_CANCELLED = "interview.cancelled"
    TRANSCRIPT_EDITED = "interview.transcript_edited"

    # Report Operations
    REPORT_GENERATED = "report.generated"
    REPORT_EXPORTED = "report.exported"
    REPORT_APPROVED = "report.approved"
    REPORT_REJECTED = "report.rejected"

    # Knowledge Operations
    KNOWLEDGE_CREATED = "knowledge.created"
    KNOWLEDGE_UPDATED = "knowledge.updated"
    KNOWLEDGE_DELETED = "knowledge.deleted"
    KNOWLEDGE_SEARCHED = "knowledge.searched"

    # Template Operations
    TEMPLATE_CREATED = "template.created"
    TEMPLATE_UPDATED = "template.updated"
    TEMPLATE_DELETED = "template.deleted"
    TEMPLATE_PUBLISHED = "template.published"

    # Data Access
    DATA_EXPORTED = "data.exported"
    DATA_IMPORTED = "data.imported"
    SENSITIVE_DATA_ACCESSED = "data.sensitive_accessed"

    # System Operations
    SETTINGS_CHANGED = "system.settings_changed"
    API_KEY_CREATED = "system.api_key_created"
    API_KEY_REVOKED = "system.api_key_revoked"


class AuditSeverity(StrEnum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit log event."""

    event_id: UUID
    timestamp: datetime
    action: AuditAction
    user_id: UUID | None
    user_email: str | None
    resource_type: str | None
    resource_id: UUID | None
    details: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    session_id: str | None
    severity: AuditSeverity = AuditSeverity.INFO
    success: bool = True
    error_message: str | None = None
    organization_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditService:
    """Service for recording and querying audit logs.

    Features:
    - Structured audit logging
    - Real-time event streaming
    - Compliance reporting
    - Anomaly detection support
    """

    def __init__(self):
        """Initialize the audit service."""
        # In-memory store for demo (use database in production)
        self._events: list[AuditEvent] = []
        self._event_handlers: list[callable] = []

    async def log(
        self,
        action: AuditAction,
        user_id: UUID | None = None,
        user_email: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        error_message: str | None = None,
        organization_id: UUID | None = None,
    ) -> AuditEvent:
        """Record an audit event.

        Args:
            action: The type of action being logged
            user_id: ID of the user performing the action
            user_email: Email of the user
            resource_type: Type of resource being accessed/modified
            resource_id: ID of the resource
            details: Additional event details
            ip_address: Client IP address
            user_agent: Client user agent string
            session_id: Session identifier
            severity: Event severity level
            success: Whether the action succeeded
            error_message: Error message if action failed
            organization_id: Organization context

        Returns:
            The created AuditEvent
        """
        event = AuditEvent(
            event_id=uuid4(),
            timestamp=datetime.utcnow(),
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            severity=severity,
            success=success,
            error_message=error_message,
            organization_id=organization_id,
        )

        # Store event
        self._events.append(event)

        # Log to standard logger
        log_message = self._format_log_message(event)
        if severity == AuditSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Notify handlers
        for handler in self._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Audit handler error: {e}")

        return event

    def _format_log_message(self, event: AuditEvent) -> str:
        """Format event for logging."""
        parts = [
            f"[AUDIT] {event.action.value}",
            f"user={event.user_email or event.user_id or 'anonymous'}",
        ]

        if event.resource_type:
            parts.append(f"resource={event.resource_type}:{event.resource_id}")

        if not event.success:
            parts.append(f"FAILED: {event.error_message}")

        if event.ip_address:
            parts.append(f"ip={event.ip_address}")

        return " | ".join(parts)

    async def query(
        self,
        user_id: UUID | None = None,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        organization_id: UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        severity: AuditSeverity | None = None,
        success: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit events with filters.

        Args:
            user_id: Filter by user
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            organization_id: Filter by organization
            start_time: Filter events after this time
            end_time: Filter events before this time
            severity: Filter by severity
            success: Filter by success status
            limit: Maximum events to return
            offset: Pagination offset

        Returns:
            List of matching AuditEvents
        """
        results = []

        for event in reversed(self._events):
            # Apply filters
            if user_id and event.user_id != user_id:
                continue
            if action and event.action != action:
                continue
            if resource_type and event.resource_type != resource_type:
                continue
            if resource_id and event.resource_id != resource_id:
                continue
            if organization_id and event.organization_id != organization_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if severity and event.severity != severity:
                continue
            if success is not None and event.success != success:
                continue

            results.append(event)

        # Apply pagination
        return results[offset : offset + limit]

    async def get_user_activity(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get activity summary for a user.

        Args:
            user_id: The user ID
            days: Number of days to analyze

        Returns:
            Activity summary including action counts, last activity, etc.
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        events = await self.query(
            user_id=user_id,
            start_time=cutoff,
            limit=1000,
        )

        action_counts: dict[str, int] = {}
        failed_actions = 0
        resources_accessed: set[str] = set()

        for event in events:
            action_key = event.action.value
            action_counts[action_key] = action_counts.get(action_key, 0) + 1

            if not event.success:
                failed_actions += 1

            if event.resource_type and event.resource_id:
                resources_accessed.add(f"{event.resource_type}:{event.resource_id}")

        return {
            "user_id": str(user_id),
            "period_days": days,
            "total_actions": len(events),
            "action_breakdown": action_counts,
            "failed_actions": failed_actions,
            "unique_resources_accessed": len(resources_accessed),
            "last_activity": events[0].timestamp.isoformat() if events else None,
        }

    async def export_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        format: str = "json",
    ) -> bytes:
        """Export audit logs for compliance reporting.

        Args:
            start_time: Start of export period
            end_time: End of export period
            format: Export format (json, csv)

        Returns:
            Exported data as bytes
        """
        events = await self.query(
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )

        if format == "json":
            data = []
            for event in events:
                event_dict = asdict(event)
                event_dict["event_id"] = str(event_dict["event_id"])
                event_dict["user_id"] = str(event_dict["user_id"]) if event_dict["user_id"] else None
                event_dict["resource_id"] = str(event_dict["resource_id"]) if event_dict["resource_id"] else None
                event_dict["organization_id"] = str(event_dict["organization_id"]) if event_dict["organization_id"] else None
                event_dict["timestamp"] = event_dict["timestamp"].isoformat()
                event_dict["action"] = event_dict["action"].value
                event_dict["severity"] = event_dict["severity"].value
                data.append(event_dict)

            return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "timestamp", "action", "user_email", "resource_type",
                "resource_id", "success", "severity", "ip_address", "details"
            ])

            # Data
            for event in events:
                writer.writerow([
                    event.timestamp.isoformat(),
                    event.action.value,
                    event.user_email,
                    event.resource_type,
                    str(event.resource_id) if event.resource_id else "",
                    event.success,
                    event.severity.value,
                    event.ip_address,
                    json.dumps(event.details),
                ])

            return output.getvalue().encode("utf-8")

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def add_event_handler(self, handler: callable) -> None:
        """Add a handler for real-time event processing.

        Args:
            handler: Async function to call for each event
        """
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: callable) -> None:
        """Remove an event handler.

        Args:
            handler: Handler to remove
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)


# Singleton instance
_audit_service: AuditService | None = None


def get_audit_service() -> AuditService:
    """Get or create the audit service singleton."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service

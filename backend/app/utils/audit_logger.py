import json
from datetime import datetime
from flask import request


class AuditLogger:
    """Audit logging utility for compliance tracking"""

    @staticmethod
    def log(candidate_id, action, actor='system', details=None, ip_address=None):
        """
        Create an immutable audit log entry

        Args:
            candidate_id: UUID of the candidate
            action: Action performed (e.g., 'resume_uploaded', 'extraction_completed')
            actor: Who performed the action ('system', 'hr', 'candidate')
            details: Dict with action-specific details
            ip_address: IP address of the actor
        """
        from app.models import AuditLog, db

        # Get IP from request if not provided
        if ip_address is None:
            try:
                ip_address = request.remote_addr
            except RuntimeError:
                ip_address = None

        log_entry = AuditLog(
            candidate_id=candidate_id,
            action=action,
            actor=actor,
            actor_ip=ip_address,
            details=json.dumps(details) if details else None,
            created_at=datetime.utcnow()
        )

        db.session.add(log_entry)
        db.session.commit()

        return log_entry

    @staticmethod
    def get_logs(candidate_id, limit=50):
        """Get audit logs for a candidate"""
        from app.models import AuditLog

        logs = AuditLog.query.filter_by(candidate_id=candidate_id)\
            .order_by(AuditLog.created_at.desc())\
            .limit(limit)\
            .all()

        return [log.to_dict() for log in logs]


# Common action constants
class AuditActions:
    RESUME_UPLOADED = 'resume_uploaded'
    EXTRACTION_STARTED = 'extraction_started'
    EXTRACTION_COMPLETED = 'extraction_completed'
    EXTRACTION_FAILED = 'extraction_failed'
    DOCUMENT_REQUEST_SENT = 'document_request_sent'
    DOCUMENT_REQUEST_FAILED = 'document_request_failed'
    PORTAL_ACCESSED = 'portal_accessed'
    DOCUMENTS_SUBMITTED = 'documents_submitted'
    CANDIDATE_VIEWED = 'candidate_viewed'
    CANDIDATE_DELETED = 'candidate_deleted'

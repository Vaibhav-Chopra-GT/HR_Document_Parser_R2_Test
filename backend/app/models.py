from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import uuid
import secrets

db = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


def generate_token():
    return secrets.token_urlsafe(32)


class Candidate(db.Model):
    """Candidate model with extracted resume data"""
    __tablename__ = 'candidates'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Extracted Information
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(255))
    designation = db.Column(db.String(255))
    skills = db.Column(db.Text)  # JSON array stored as string
    raw_resume_text = db.Column(db.Text)

    # Confidence Scores (0.0 - 1.0)
    name_confidence = db.Column(db.Float)
    email_confidence = db.Column(db.Float)
    phone_confidence = db.Column(db.Float)
    company_confidence = db.Column(db.Float)
    designation_confidence = db.Column(db.Float)
    skills_confidence = db.Column(db.Float)
    overall_confidence = db.Column(db.Float)

    # File References
    resume_filename = db.Column(db.String(500))
    resume_original_name = db.Column(db.String(500))
    pan_filename = db.Column(db.String(500))
    pan_original_name = db.Column(db.String(500))
    aadhaar_filename = db.Column(db.String(500))
    aadhaar_original_name = db.Column(db.String(500))

    # Document Validation
    pan_validated = db.Column(db.Boolean, default=False)
    aadhaar_validated = db.Column(db.Boolean, default=False)

    # Status Tracking
    extraction_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    extraction_error = db.Column(db.Text)
    document_status = db.Column(db.String(50), default='pending')  # pending, requested, partial, completed

    # Secure Portal Access
    submission_token = db.Column(db.String(100), unique=True)
    token_expires_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    documents_requested_at = db.Column(db.DateTime)
    documents_submitted_at = db.Column(db.DateTime)

    # Relationships
    audit_logs = db.relationship('AuditLog', backref='candidate', lazy='dynamic')
    email_logs = db.relationship('EmailLog', backref='candidate', lazy='dynamic')

    def generate_submission_token(self, expiry_days=7):
        """Generate a new submission token"""
        self.submission_token = generate_token()
        self.token_expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        return self.submission_token

    def is_token_valid(self):
        """Check if submission token is still valid"""
        if not self.submission_token or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API response"""
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'designation': self.designation,
            'skills': self.skills,
            'confidence_scores': {
                'name': self.name_confidence,
                'email': self.email_confidence,
                'phone': self.phone_confidence,
                'company': self.company_confidence,
                'designation': self.designation_confidence,
                'skills': self.skills_confidence,
                'overall': self.overall_confidence
            },
            'extraction_status': self.extraction_status,
            'extraction_error': self.extraction_error,
            'document_status': self.document_status,
            'has_pan': bool(self.pan_filename),
            'has_aadhaar': bool(self.aadhaar_filename),
            'pan_validated': self.pan_validated,
            'aadhaar_validated': self.aadhaar_validated,
            'resume_original_name': self.resume_original_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'documents_requested_at': self.documents_requested_at.isoformat() if self.documents_requested_at else None,
            'documents_submitted_at': self.documents_submitted_at.isoformat() if self.documents_submitted_at else None
        }

        if include_sensitive:
            data['submission_token'] = self.submission_token
            data['token_expires_at'] = self.token_expires_at.isoformat() if self.token_expires_at else None

        return data

    def to_list_dict(self):
        """Simplified dict for list view"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'extraction_status': self.extraction_status,
            'document_status': self.document_status,
            'overall_confidence': self.overall_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(db.Model):
    """Immutable audit log for compliance"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'))
    action = db.Column(db.String(100), nullable=False)
    actor = db.Column(db.String(50))  # 'system', 'hr', 'candidate'
    actor_ip = db.Column(db.String(50))
    details = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'actor': self.actor,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EmailLog(db.Model):
    """Email tracking log"""
    __tablename__ = 'email_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # document_request, reminder, confirmation
    recipient_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500))
    body_preview = db.Column(db.String(500))
    status = db.Column(db.String(50), default='pending')  # pending, sent, delivered, failed, bounced
    resend_message_id = db.Column(db.String(100))
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'email_type': self.email_type,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message
        }

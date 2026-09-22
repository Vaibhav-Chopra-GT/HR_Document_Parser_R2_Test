"""
Email Service - Send emails via Resend
"""
from datetime import datetime
from app.config import Config


class EmailService:
    """Email service using Resend API"""

    def __init__(self):
        self.api_key = Config.RESEND_API_KEY
        self.from_email = Config.EMAIL_FROM
        self._client = None

    @property
    def client(self):
        """Lazy load Resend client"""
        if self._client is None:
            if not self.api_key:
                return None
            import resend
            resend.api_key = self.api_key
            self._client = resend
        return self._client

    def is_configured(self) -> bool:
        """Check if email service is configured"""
        return bool(self.api_key)

    def send_document_request(self, candidate, subject: str, body: str) -> dict:
        """
        Send document request email to candidate

        Args:
            candidate: Candidate model instance
            subject: Email subject
            body: Email body (plain text)

        Returns:
            dict with success status and message ID or error
        """
        from app.models import EmailLog, db

        if not self.is_configured():
            # Log but don't fail - useful for testing without email
            log = EmailLog(
                candidate_id=candidate.id,
                email_type='document_request',
                recipient_email=candidate.email,
                subject=subject,
                body_preview=body[:200] if body else None,
                status='skipped',
                error_message='Email service not configured (RESEND_API_KEY missing)'
            )
            db.session.add(log)
            db.session.commit()

            return {
                "success": True,
                "skipped": True,
                "message": "Email service not configured - email logged but not sent",
                "log_id": log.id
            }

        try:
            # Format body as HTML
            html_body = self._text_to_html(body)

            response = self.client.Emails.send({
                "from": self.from_email,
                "to": [candidate.email],
                "subject": subject,
                "html": html_body,
                "text": body,  # Plain text fallback
                "tags": [
                    {"name": "type", "value": "document_request"},
                    {"name": "candidate_id", "value": candidate.id}
                ]
            })

            # Log successful send
            log = EmailLog(
                candidate_id=candidate.id,
                email_type='document_request',
                recipient_email=candidate.email,
                subject=subject,
                body_preview=body[:200] if body else None,
                status='sent',
                resend_message_id=response.get('id'),
                sent_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()

            return {
                "success": True,
                "message_id": response.get('id'),
                "log_id": log.id
            }

        except Exception as e:
            # Log failed send
            log = EmailLog(
                candidate_id=candidate.id,
                email_type='document_request',
                recipient_email=candidate.email,
                subject=subject,
                body_preview=body[:200] if body else None,
                status='failed',
                error_message=str(e)
            )
            db.session.add(log)
            db.session.commit()

            return {
                "success": False,
                "error": str(e),
                "log_id": log.id
            }

    def send_confirmation(self, candidate) -> dict:
        """Send document submission confirmation to candidate"""
        from app.models import EmailLog, db

        subject = "Documents Received - TraqCheck Verification"
        body = f"""Dear {candidate.name or 'Candidate'},

Thank you for submitting your documents for verification.

We have successfully received:
{'✓ PAN Card' if candidate.pan_filename else ''}
{'✓ Aadhaar Card' if candidate.aadhaar_filename else ''}

Our team will review your documents and get back to you if needed.

Best regards,
TraqCheck Verification Team"""

        if not self.is_configured():
            log = EmailLog(
                candidate_id=candidate.id,
                email_type='confirmation',
                recipient_email=candidate.email,
                subject=subject,
                body_preview=body[:200],
                status='skipped',
                error_message='Email service not configured'
            )
            db.session.add(log)
            db.session.commit()
            return {"success": True, "skipped": True}

        try:
            response = self.client.Emails.send({
                "from": self.from_email,
                "to": [candidate.email],
                "subject": subject,
                "html": self._text_to_html(body),
                "text": body
            })

            log = EmailLog(
                candidate_id=candidate.id,
                email_type='confirmation',
                recipient_email=candidate.email,
                subject=subject,
                body_preview=body[:200],
                status='sent',
                resend_message_id=response.get('id'),
                sent_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()

            return {"success": True, "message_id": response.get('id')}

        except Exception as e:
            log = EmailLog(
                candidate_id=candidate.id,
                email_type='confirmation',
                recipient_email=candidate.email,
                subject=subject,
                status='failed',
                error_message=str(e)
            )
            db.session.add(log)
            db.session.commit()

            return {"success": False, "error": str(e)}

    def _text_to_html(self, text: str) -> str:
        """Convert plain text to basic HTML email"""
        # Escape HTML
        import html
        escaped = html.escape(text)

        # Convert line breaks to <br>
        html_body = escaped.replace('\n', '<br>\n')

        # Wrap in basic HTML template
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        a {{
            color: #2563eb;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

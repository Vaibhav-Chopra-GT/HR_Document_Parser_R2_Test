"""
Candidates API Routes - HR Dashboard endpoints
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from app.models import db, Candidate, AuditLog
from app.utils.file_handler import save_file, get_file_path, allowed_file
from app.utils.audit_logger import AuditLogger, AuditActions
from app.services.resume_parser import ResumeParser
from app.services.ai_service import get_ai_service
from app.services.email_service import get_email_service
from app.config import Config

candidates_bp = Blueprint('candidates', __name__)


def find_duplicate_candidate(email=None, phone=None):
    """
    Check if a candidate with same email or phone already exists.
    Returns (existing_candidate, match_field) or (None, None)
    """
    # Check by email (case-insensitive)
    if email:
        existing = Candidate.query.filter(
            db.func.lower(Candidate.email) == email.lower()
        ).first()
        if existing:
            return existing, 'email'

    # Check by phone (normalize to last 10 digits)
    if phone:
        normalized_phone = ''.join(filter(str.isdigit, str(phone)))
        if len(normalized_phone) >= 10:
            last_10 = normalized_phone[-10:]
            # Check against existing candidates
            candidates_with_phone = Candidate.query.filter(
                Candidate.phone.isnot(None)
            ).all()
            for candidate in candidates_with_phone:
                existing_normalized = ''.join(filter(str.isdigit, str(candidate.phone or '')))
                if len(existing_normalized) >= 10 and existing_normalized[-10:] == last_10:
                    return candidate, 'phone'

    return None, None


@candidates_bp.route('/upload', methods=['POST'])
def upload_resume():
    """
    Upload and parse a resume
    POST /api/candidates/upload

    Form data:
        - file: Resume file (PDF or DOCX)
        - force: "true" to create even if duplicate exists

    Returns:
        - If duplicate found (and force!=true): 409 with existing candidate info
        - If success: 201 with new candidate
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, 'resume'):
        return jsonify({"error": "Invalid file type. Only PDF and DOCX allowed"}), 400

    force_create = request.form.get('force', '').lower() == 'true'

    # Create candidate record
    candidate = Candidate(extraction_status='processing')
    db.session.add(candidate)
    db.session.commit()

    try:
        # Save file
        file_info = save_file(file, 'resume', candidate.id)
        candidate.resume_filename = file_info['filename']
        candidate.resume_original_name = file_info['original_name']
        db.session.commit()

        # Log upload
        AuditLogger.log(
            candidate.id,
            AuditActions.RESUME_UPLOADED,
            'hr',
            {"filename": file_info['original_name'], "size": file_info['size']}
        )

        # Parse resume
        parser = ResumeParser()
        result = parser.parse_resume(file_info['path'])

        if not result['success']:
            candidate.extraction_status = 'failed'
            candidate.extraction_error = result.get('error', 'Unknown error')
            candidate.raw_resume_text = result.get('raw_text')
            db.session.commit()

            AuditLogger.log(
                candidate.id,
                AuditActions.EXTRACTION_FAILED,
                'system',
                {"error": result.get('error')}
            )

            return jsonify({
                "id": candidate.id,
                "status": "failed",
                "error": result.get('error'),
                "message": "Resume uploaded but extraction failed"
            }), 200

        # Update candidate with extracted data
        extracted = result['extracted']
        confidence = result['confidence']

        # Check for duplicate BEFORE finalizing (unless force=true)
        if not force_create:
            existing, match_field = find_duplicate_candidate(
                email=extracted.get('email'),
                phone=extracted.get('phone')
            )
            if existing:
                # Delete the temporary candidate we created
                db.session.delete(candidate)
                db.session.commit()

                return jsonify({
                    "duplicate": True,
                    "match_field": match_field,
                    "message": f"A candidate with this {match_field} already exists",
                    "existing_candidate": existing.to_list_dict(),
                    "extracted_data": extracted,
                    "hint": "Send with force=true to create anyway, or view existing candidate"
                }), 409

        candidate.name = extracted.get('name')
        candidate.email = extracted.get('email')
        candidate.phone = extracted.get('phone')
        candidate.company = extracted.get('company')
        candidate.designation = extracted.get('designation')
        candidate.skills = json.dumps(extracted.get('skills', []))
        candidate.raw_resume_text = result.get('raw_text')

        candidate.name_confidence = confidence.get('name')
        candidate.email_confidence = confidence.get('email')
        candidate.phone_confidence = confidence.get('phone')
        candidate.company_confidence = confidence.get('company')
        candidate.designation_confidence = confidence.get('designation')
        candidate.skills_confidence = confidence.get('skills')
        candidate.overall_confidence = confidence.get('overall')

        candidate.extraction_status = 'completed'
        db.session.commit()

        AuditLogger.log(
            candidate.id,
            AuditActions.EXTRACTION_COMPLETED,
            'system',
            {"overall_confidence": confidence.get('overall')}
        )

        return jsonify({
            "id": candidate.id,
            "status": "completed",
            "candidate": candidate.to_dict(),
            "message": "Resume parsed successfully"
        }), 201

    except Exception as e:
        candidate.extraction_status = 'failed'
        candidate.extraction_error = str(e)
        db.session.commit()

        AuditLogger.log(
            candidate.id,
            AuditActions.EXTRACTION_FAILED,
            'system',
            {"error": str(e)}
        )

        return jsonify({
            "id": candidate.id,
            "status": "failed",
            "error": str(e)
        }), 500


@candidates_bp.route('', methods=['GET'])
def list_candidates():
    """
    List all candidates with optional filters
    GET /api/candidates

    Query params:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - status: Filter by extraction_status
        - doc_status: Filter by document_status
        - search: Search by name or email
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    doc_status = request.args.get('doc_status')
    search = request.args.get('search')

    query = Candidate.query

    if status:
        query = query.filter(Candidate.extraction_status == status)

    if doc_status:
        query = query.filter(Candidate.document_status == doc_status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Candidate.name.ilike(search_term),
                Candidate.email.ilike(search_term),
                Candidate.company.ilike(search_term)
            )
        )

    # Order by most recent first
    query = query.order_by(Candidate.created_at.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "candidates": [c.to_list_dict() for c in pagination.items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    })


@candidates_bp.route('/<candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    """
    Get candidate details
    GET /api/candidates/<id>
    """
    candidate = Candidate.query.get_or_404(candidate_id)

    # Parse skills JSON
    candidate_dict = candidate.to_dict()
    if candidate.skills:
        try:
            candidate_dict['skills'] = json.loads(candidate.skills)
        except:
            candidate_dict['skills'] = []

    # Log view
    AuditLogger.log(candidate.id, AuditActions.CANDIDATE_VIEWED, 'hr')

    return jsonify({"candidate": candidate_dict})


@candidates_bp.route('/<candidate_id>/request-documents', methods=['POST'])
def request_documents(candidate_id):
    """
    Generate and send document request email
    POST /api/candidates/<id>/request-documents
    """
    candidate = Candidate.query.get_or_404(candidate_id)

    if not candidate.email:
        return jsonify({"error": "Candidate has no email address"}), 400

    # Generate submission token
    token = candidate.generate_submission_token(Config.SUBMISSION_TOKEN_EXPIRY_DAYS)
    submission_link = f"{Config.FRONTEND_URL}/submit/{token}"

    # Generate personalized email using AI
    ai_service = get_ai_service()
    email_result = ai_service.generate_document_request({
        "name": candidate.name,
        "company": candidate.company,
        "designation": candidate.designation,
        "submission_link": submission_link
    })

    if not email_result.get('success'):
        return jsonify({
            "error": "Failed to generate email",
            "details": email_result.get('error')
        }), 500

    # Send email
    email_service = get_email_service()
    send_result = email_service.send_document_request(
        candidate,
        email_result['subject'],
        email_result['body']
    )

    if not send_result.get('success') and not send_result.get('skipped'):
        AuditLogger.log(
            candidate.id,
            AuditActions.DOCUMENT_REQUEST_FAILED,
            'hr',
            {"error": send_result.get('error')}
        )
        return jsonify({
            "error": "Failed to send email",
            "details": send_result.get('error')
        }), 500

    # Update candidate status
    candidate.document_status = 'requested'
    candidate.documents_requested_at = datetime.utcnow()
    db.session.commit()

    AuditLogger.log(
        candidate.id,
        AuditActions.DOCUMENT_REQUEST_SENT,
        'hr',
        {
            "email": candidate.email,
            "skipped": send_result.get('skipped', False)
        }
    )

    return jsonify({
        "success": True,
        "message": "Document request sent" if not send_result.get('skipped') else "Document request logged (email not configured)",
        "email_sent": not send_result.get('skipped', False),
        "submission_link": submission_link,
        "subject": email_result['subject'],
        "body": email_result['body']
    })


@candidates_bp.route('/<candidate_id>/audit-log', methods=['GET'])
def get_audit_log(candidate_id):
    """
    Get audit log for a candidate
    GET /api/candidates/<id>/audit-log
    """
    candidate = Candidate.query.get_or_404(candidate_id)

    limit = request.args.get('limit', 50, type=int)
    logs = AuditLogger.get_logs(candidate.id, limit)

    return jsonify({"logs": logs})


@candidates_bp.route('/<candidate_id>/resume', methods=['GET'])
def download_resume(candidate_id):
    """
    Download candidate's resume
    GET /api/candidates/<id>/resume
    """
    candidate = Candidate.query.get_or_404(candidate_id)

    if not candidate.resume_filename:
        return jsonify({"error": "No resume found"}), 404

    file_path = get_file_path(candidate.resume_filename, 'resume')

    return send_file(
        file_path,
        download_name=candidate.resume_original_name or candidate.resume_filename,
        as_attachment=True
    )


@candidates_bp.route('/<candidate_id>/documents/<doc_type>', methods=['GET'])
def download_document(candidate_id, doc_type):
    """
    Download candidate's submitted document
    GET /api/candidates/<id>/documents/pan
    GET /api/candidates/<id>/documents/aadhaar
    """
    candidate = Candidate.query.get_or_404(candidate_id)

    if doc_type == 'pan':
        filename = candidate.pan_filename
        original_name = candidate.pan_original_name
    elif doc_type == 'aadhaar':
        filename = candidate.aadhaar_filename
        original_name = candidate.aadhaar_original_name
    else:
        return jsonify({"error": "Invalid document type"}), 400

    if not filename:
        return jsonify({"error": f"No {doc_type} document found"}), 404

    file_path = get_file_path(filename, 'document')

    return send_file(
        file_path,
        download_name=original_name or filename,
        as_attachment=True
    )


@candidates_bp.route('/<candidate_id>/reprocess', methods=['POST'])
def reprocess_resume(candidate_id):
    """
    Re-run extraction on existing resume
    POST /api/candidates/<id>/reprocess
    """
    candidate = Candidate.query.get_or_404(candidate_id)

    if not candidate.resume_filename:
        return jsonify({"error": "No resume to process"}), 400

    candidate.extraction_status = 'processing'
    db.session.commit()

    try:
        file_path = get_file_path(candidate.resume_filename, 'resume')

        parser = ResumeParser()
        result = parser.parse_resume(file_path)

        if not result['success']:
            candidate.extraction_status = 'failed'
            candidate.extraction_error = result.get('error')
            db.session.commit()
            return jsonify({
                "status": "failed",
                "error": result.get('error')
            }), 200

        # Update with new extracted data
        extracted = result['extracted']
        confidence = result['confidence']

        candidate.name = extracted.get('name')
        candidate.email = extracted.get('email')
        candidate.phone = extracted.get('phone')
        candidate.company = extracted.get('company')
        candidate.designation = extracted.get('designation')
        candidate.skills = json.dumps(extracted.get('skills', []))

        candidate.name_confidence = confidence.get('name')
        candidate.email_confidence = confidence.get('email')
        candidate.phone_confidence = confidence.get('phone')
        candidate.company_confidence = confidence.get('company')
        candidate.designation_confidence = confidence.get('designation')
        candidate.skills_confidence = confidence.get('skills')
        candidate.overall_confidence = confidence.get('overall')

        candidate.extraction_status = 'completed'
        candidate.extraction_error = None
        db.session.commit()

        AuditLogger.log(
            candidate.id,
            AuditActions.EXTRACTION_COMPLETED,
            'hr',
            {"reprocess": True, "overall_confidence": confidence.get('overall')}
        )

        return jsonify({
            "status": "completed",
            "candidate": candidate.to_dict()
        })

    except Exception as e:
        candidate.extraction_status = 'failed'
        candidate.extraction_error = str(e)
        db.session.commit()

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


@candidates_bp.route('/<candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    """
    Soft delete a candidate (for GDPR compliance, we might want to keep audit logs)
    DELETE /api/candidates/<id>
    """
    candidate = Candidate.query.get_or_404(candidate_id)

    # Log deletion before removing
    AuditLogger.log(
        candidate.id,
        AuditActions.CANDIDATE_DELETED,
        'hr',
        {"name": candidate.name, "email": candidate.email}
    )

    # Delete the candidate
    db.session.delete(candidate)
    db.session.commit()

    return jsonify({"success": True, "message": "Candidate deleted"})

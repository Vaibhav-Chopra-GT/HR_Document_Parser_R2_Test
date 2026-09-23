"""
Candidates API Routes - HR Dashboard endpoints
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Candidate, AuditLog, User
from app.utils.file_handler import save_file, get_file_path, allowed_file, get_file_for_download
import os
from app.utils.audit_logger import AuditLogger, AuditActions
from app.services.resume_parser import ResumeParser
from app.services.ai_service import get_ai_service
from app.services.email_service import get_email_service
from app.config import Config

candidates_bp = Blueprint('candidates', __name__)


def get_current_user():
    """Get the current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)


def get_candidate_or_403(candidate_id, user_id):
    """Get candidate and verify ownership"""
    candidate = Candidate.query.get_or_404(candidate_id)
    if candidate.user_id != user_id:
        return None
    return candidate


def find_duplicate_candidate(user_id, email=None, phone=None):
    """
    Check if a candidate with same email or phone already exists FOR THIS USER.
    Returns (existing_candidate, match_field) or (None, None)
    """
    # Check by email (case-insensitive) - within user's candidates only
    if email:
        existing = Candidate.query.filter(
            Candidate.user_id == user_id,
            db.func.lower(Candidate.email) == email.lower()
        ).first()
        if existing:
            return existing, 'email'

    # Check by phone (normalize to last 10 digits) - within user's candidates only
    if phone:
        normalized_phone = ''.join(filter(str.isdigit, str(phone)))
        if len(normalized_phone) >= 10:
            last_10 = normalized_phone[-10:]
            # Check against user's candidates
            candidates_with_phone = Candidate.query.filter(
                Candidate.user_id == user_id,
                Candidate.phone.isnot(None)
            ).all()
            for candidate in candidates_with_phone:
                existing_normalized = ''.join(filter(str.isdigit, str(candidate.phone or '')))
                if len(existing_normalized) >= 10 and existing_normalized[-10:] == last_10:
                    return candidate, 'phone'

    return None, None


@candidates_bp.route('/upload', methods=['POST'])
@jwt_required()
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
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, 'resume'):
        return jsonify({"error": "Invalid file type. Only PDF and DOCX allowed"}), 400

    force_create = request.form.get('force', '').lower() == 'true'

    # Create candidate record linked to current user
    candidate = Candidate(extraction_status='processing', user_id=current_user.id)
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
                current_user.id,
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
@jwt_required()
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
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    doc_status = request.args.get('doc_status')
    search = request.args.get('search')

    # Filter by current user's candidates only
    query = Candidate.query.filter_by(user_id=current_user.id)

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
@jwt_required()
def get_candidate(candidate_id):
    """
    Get candidate details
    GET /api/candidates/<id>
    """
    current_user = get_current_user()
    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

    # Parse skills JSON
    candidate_dict = candidate.to_dict()
    if candidate.skills:
        try:
            candidate_dict['skills'] = json.loads(candidate.skills)
        except:
            candidate_dict['skills'] = []

    return jsonify({"candidate": candidate_dict})


@candidates_bp.route('/<candidate_id>/request-documents', methods=['POST'])
@jwt_required()
def request_documents(candidate_id):
    """
    Generate and send document request email
    POST /api/candidates/<id>/request-documents
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

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
        "submission_link": submission_link,
        "hr_name": current_user.name,
        "hr_email": current_user.email,
        "hr_company": current_user.company
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

    # Update candidate status regardless of email success
    candidate.document_status = 'requested'
    candidate.documents_requested_at = datetime.utcnow()
    db.session.commit()

    # Determine email status
    email_sent = send_result.get('success', False) and not send_result.get('skipped', False)
    email_skipped = send_result.get('skipped', False)
    email_failed = not send_result.get('success', False) and not email_skipped

    if email_failed:
        AuditLogger.log(
            candidate.id,
            AuditActions.DOCUMENT_REQUEST_FAILED,
            'hr',
            {"error": send_result.get('error')}
        )
        message = f"Email failed to send: {send_result.get('error', 'Unknown error')}. Portal link still generated."
    elif email_skipped:
        message = "Document request logged (email not configured)"
    else:
        message = "Document request sent successfully"

    AuditLogger.log(
        candidate.id,
        AuditActions.DOCUMENT_REQUEST_SENT,
        'hr',
        {
            "email": candidate.email,
            "skipped": email_skipped,
            "failed": email_failed
        }
    )

    return jsonify({
        "success": True,
        "message": message,
        "email_sent": email_sent,
        "email_failed": email_failed,
        "submission_link": submission_link,
        "subject": email_result['subject'],
        "body": email_result['body']
    })


@candidates_bp.route('/<candidate_id>/audit-log', methods=['GET'])
@jwt_required()
def get_audit_log(candidate_id):
    """
    Get audit log for a candidate
    GET /api/candidates/<id>/audit-log
    """
    current_user = get_current_user()
    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

    limit = request.args.get('limit', 50, type=int)
    logs = AuditLogger.get_logs(candidate.id, limit)

    return jsonify({"logs": logs})


@candidates_bp.route('/<candidate_id>/resume', methods=['GET'])
@jwt_required()
def download_resume(candidate_id):
    """
    Download candidate's resume
    GET /api/candidates/<id>/resume
    """
    current_user = get_current_user()
    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

    if not candidate.resume_filename:
        return jsonify({"error": "No resume found"}), 404

    try:
        file_path, is_temp = get_file_for_download(candidate.resume_filename, 'resume')
        response = send_file(
            file_path,
            download_name=candidate.resume_original_name or candidate.resume_filename,
            as_attachment=True
        )
        # Clean up temp file after sending (for cloud storage)
        if is_temp:
            @response.call_on_close
            def cleanup():
                try:
                    os.unlink(file_path)
                except:
                    pass
        return response
    except FileNotFoundError:
        return jsonify({"error": "Resume file not found"}), 404


@candidates_bp.route('/<candidate_id>/documents/<doc_type>', methods=['GET'])
@jwt_required()
def download_document(candidate_id, doc_type):
    """
    Download candidate's submitted document
    GET /api/candidates/<id>/documents/pan
    GET /api/candidates/<id>/documents/aadhaar
    """
    current_user = get_current_user()
    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

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

    try:
        file_path, is_temp = get_file_for_download(filename, 'document')
        response = send_file(
            file_path,
            download_name=original_name or filename,
            as_attachment=True
        )
        # Clean up temp file after sending (for cloud storage)
        if is_temp:
            @response.call_on_close
            def cleanup():
                try:
                    os.unlink(file_path)
                except:
                    pass
        return response
    except FileNotFoundError:
        return jsonify({"error": f"{doc_type} file not found"}), 404


@candidates_bp.route('/<candidate_id>/reprocess', methods=['POST'])
@jwt_required()
def reprocess_resume(candidate_id):
    """
    Re-run extraction on existing resume
    POST /api/candidates/<id>/reprocess
    """
    current_user = get_current_user()
    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

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


@candidates_bp.route('/<candidate_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_candidate(candidate_id):
    """
    Update candidate information (manual edit by HR)
    PUT/PATCH /api/candidates/<id>

    JSON body: { name, email, phone, company, designation, skills }
    """
    current_user = get_current_user()
    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Track what was changed
    changes = {}

    # Update allowed fields
    editable_fields = ['name', 'email', 'phone', 'company', 'designation', 'skills']

    for field in editable_fields:
        if field in data:
            old_value = getattr(candidate, field)
            new_value = data[field]

            # Handle skills (convert list to JSON string)
            if field == 'skills':
                if isinstance(new_value, list):
                    new_value = json.dumps(new_value)
                elif isinstance(new_value, str):
                    # Validate it's valid JSON if string
                    try:
                        json.loads(new_value)
                    except:
                        new_value = json.dumps([new_value])

            if old_value != new_value:
                setattr(candidate, field, new_value)
                changes[field] = {"old": old_value, "new": new_value}

    if changes:
        db.session.commit()

        # Log the edit
        AuditLogger.log(
            candidate.id,
            'candidate_edited',
            'hr',
            {"changes": {k: v['new'] for k, v in changes.items()}}
        )

    return jsonify({
        "success": True,
        "message": "Candidate updated" if changes else "No changes made",
        "changes": list(changes.keys()),
        "candidate": candidate.to_dict()
    })


@candidates_bp.route('/<candidate_id>', methods=['DELETE'])
@jwt_required()
def delete_candidate(candidate_id):
    """
    Soft delete a candidate (for GDPR compliance, we might want to keep audit logs)
    DELETE /api/candidates/<id>
    """
    current_user = get_current_user()
    candidate = get_candidate_or_403(candidate_id, current_user.id)
    if not candidate:
        return jsonify({"error": "Candidate not found or access denied"}), 403

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

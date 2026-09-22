"""
Portal API Routes - Candidate document submission endpoints
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.models import db, Candidate, User
from app.utils.file_handler import save_file, allowed_file
from app.utils.audit_logger import AuditLogger, AuditActions
from app.services.document_validator import PANValidator, AadhaarValidator, validate_document_image
from app.services.email_service import get_email_service

portal_bp = Blueprint('portal', __name__)


@portal_bp.route('/<token>', methods=['GET'])
def validate_token(token):
    """
    Validate submission token and return basic candidate info
    GET /api/portal/<token>

    Returns only name (for personalization) - no sensitive data
    """
    candidate = Candidate.query.filter_by(submission_token=token).first()

    if not candidate:
        return jsonify({"error": "Invalid or expired link"}), 404

    if not candidate.is_token_valid():
        return jsonify({"error": "This link has expired"}), 410

    # Log portal access
    AuditLogger.log(
        candidate.id,
        AuditActions.PORTAL_ACCESSED,
        'candidate'
    )

    # Check if already submitted (link already used)
    already_submitted = candidate.documents_submitted_at is not None

    # Get HR contact info
    hr_email = None
    hr_company = None
    if candidate.user_id:
        hr_user = User.query.get(candidate.user_id)
        if hr_user:
            hr_email = hr_user.email
            hr_company = hr_user.company

    return jsonify({
        "valid": True,
        "already_submitted": already_submitted,
        "name": candidate.name,  # Only return name for personalization
        "documents_submitted": {
            "pan": bool(candidate.pan_filename),
            "aadhaar": bool(candidate.aadhaar_filename)
        },
        "submitted_at": candidate.documents_submitted_at.isoformat() if candidate.documents_submitted_at else None,
        "hr_email": hr_email,
        "hr_company": hr_company
    })


@portal_bp.route('/<token>/submit', methods=['POST'])
def submit_documents(token):
    """
    Submit PAN and/or Aadhaar documents
    POST /api/portal/<token>/submit

    Form data:
        - pan: PAN card image (optional)
        - aadhaar: Aadhaar card image (optional)
        - pan_number: PAN number for validation (optional)
        - aadhaar_number: Aadhaar number for validation (optional)
    """
    candidate = Candidate.query.filter_by(submission_token=token).first()

    if not candidate:
        return jsonify({"error": "Invalid or expired link"}), 404

    if not candidate.is_token_valid():
        return jsonify({"error": "This link has expired"}), 410

    # Check if documents have already been submitted with this token
    if candidate.documents_submitted_at:
        return jsonify({
            "error": "Documents have already been submitted",
            "message": "This link has already been used. Please contact HR if you need to update your documents."
        }), 409

    # Check if at least one file is provided
    has_pan = 'pan' in request.files and request.files['pan'].filename
    has_aadhaar = 'aadhaar' in request.files and request.files['aadhaar'].filename

    if not has_pan and not has_aadhaar:
        return jsonify({"error": "Please upload at least one document"}), 400

    results = {
        "pan": None,
        "aadhaar": None,
        "errors": []
    }

    # Process PAN
    if has_pan:
        pan_file = request.files['pan']

        if not allowed_file(pan_file.filename, 'document'):
            results['errors'].append("PAN: Invalid file type. Use PDF, PNG, or JPG")
        else:
            try:
                file_info = save_file(pan_file, 'document', f"{candidate.id}_pan")

                # Validate image
                validation = validate_document_image(file_info['path'])
                if not validation['valid']:
                    results['errors'].append(f"PAN: {validation['error']}")
                else:
                    candidate.pan_filename = file_info['filename']
                    candidate.pan_original_name = file_info['original_name']
                    results['pan'] = {"uploaded": True, "filename": file_info['original_name']}

            except Exception as e:
                results['errors'].append(f"PAN: {str(e)}")

    # Validate PAN number if provided
    pan_number = request.form.get('pan_number')
    if pan_number:
        pan_validation = PANValidator.validate(pan_number)
        if pan_validation['valid']:
            candidate.pan_validated = True
            if results['pan']:
                results['pan']['validated'] = True
                results['pan']['holder_type'] = pan_validation['holder_type']
        else:
            results['errors'].append(f"PAN Number: {pan_validation['error']}")

    # Process Aadhaar
    if has_aadhaar:
        aadhaar_file = request.files['aadhaar']

        if not allowed_file(aadhaar_file.filename, 'document'):
            results['errors'].append("Aadhaar: Invalid file type. Use PDF, PNG, or JPG")
        else:
            try:
                file_info = save_file(aadhaar_file, 'document', f"{candidate.id}_aadhaar")

                # Validate image
                validation = validate_document_image(file_info['path'])
                if not validation['valid']:
                    results['errors'].append(f"Aadhaar: {validation['error']}")
                else:
                    candidate.aadhaar_filename = file_info['filename']
                    candidate.aadhaar_original_name = file_info['original_name']
                    results['aadhaar'] = {"uploaded": True, "filename": file_info['original_name']}

            except Exception as e:
                results['errors'].append(f"Aadhaar: {str(e)}")

    # Validate Aadhaar number if provided
    aadhaar_number = request.form.get('aadhaar_number')
    if aadhaar_number:
        aadhaar_validation = AadhaarValidator.validate(aadhaar_number)
        if aadhaar_validation['valid']:
            candidate.aadhaar_validated = True
            if results['aadhaar']:
                results['aadhaar']['validated'] = True
                results['aadhaar']['masked'] = aadhaar_validation['masked']
        else:
            results['errors'].append(f"Aadhaar Number: {aadhaar_validation['error']}")

    # Update document status
    if candidate.pan_filename and candidate.aadhaar_filename:
        candidate.document_status = 'completed'
    elif candidate.pan_filename or candidate.aadhaar_filename:
        candidate.document_status = 'partial'

    if candidate.pan_filename or candidate.aadhaar_filename:
        candidate.documents_submitted_at = datetime.utcnow()

    db.session.commit()

    # Log submission
    AuditLogger.log(
        candidate.id,
        AuditActions.DOCUMENTS_SUBMITTED,
        'candidate',
        {
            "pan": bool(candidate.pan_filename),
            "aadhaar": bool(candidate.aadhaar_filename),
            "pan_validated": candidate.pan_validated,
            "aadhaar_validated": candidate.aadhaar_validated
        }
    )

    # Send confirmation email if both documents submitted
    if candidate.document_status == 'completed':
        email_service = get_email_service()
        email_service.send_confirmation(candidate)

    # Determine overall success
    success = bool(results['pan'] or results['aadhaar'])

    return jsonify({
        "success": success,
        "results": results,
        "document_status": candidate.document_status,
        "message": "Documents submitted successfully" if success else "No documents were uploaded"
    }), 200 if success else 400


@portal_bp.route('/<token>/status', methods=['GET'])
def get_submission_status(token):
    """
    Get current submission status
    GET /api/portal/<token>/status
    """
    candidate = Candidate.query.filter_by(submission_token=token).first()

    if not candidate:
        return jsonify({"error": "Invalid link"}), 404

    return jsonify({
        "document_status": candidate.document_status,
        "documents_submitted": {
            "pan": {
                "uploaded": bool(candidate.pan_filename),
                "validated": candidate.pan_validated,
                "filename": candidate.pan_original_name
            },
            "aadhaar": {
                "uploaded": bool(candidate.aadhaar_filename),
                "validated": candidate.aadhaar_validated,
                "filename": candidate.aadhaar_original_name
            }
        },
        "submitted_at": candidate.documents_submitted_at.isoformat() if candidate.documents_submitted_at else None
    })

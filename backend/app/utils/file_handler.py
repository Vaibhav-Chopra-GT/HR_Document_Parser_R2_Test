import os
import uuid
import hashlib
from werkzeug.utils import secure_filename
from app.config import Config


def get_file_extension(filename):
    """Get file extension in lowercase"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def allowed_file(filename, file_type='resume'):
    """Check if file extension is allowed"""
    ext = get_file_extension(filename)
    if file_type == 'resume':
        return ext in Config.ALLOWED_RESUME_EXTENSIONS
    elif file_type == 'document':
        return ext in Config.ALLOWED_DOCUMENT_EXTENSIONS
    return False


def save_file(file, file_type, candidate_id):
    """
    Save file with secure naming

    Args:
        file: FileStorage object from Flask
        file_type: 'resume' or 'document'
        candidate_id: UUID of the candidate

    Returns:
        dict with filename, original_name, path, size, hash
    """
    original_name = secure_filename(file.filename)
    ext = get_file_extension(original_name)

    if not allowed_file(original_name, file_type):
        raise ValueError(f"File type '.{ext}' not allowed for {file_type}")

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset

    max_size = 10 * 1024 * 1024 if file_type == 'resume' else 5 * 1024 * 1024
    if size > max_size:
        raise ValueError(f"File too large: {size / 1024 / 1024:.1f}MB (max: {max_size / 1024 / 1024:.0f}MB)")

    # Generate secure filename
    secure_name = f"{candidate_id}_{uuid.uuid4().hex[:8]}.{ext}"

    # Determine storage path
    if file_type == 'resume':
        folder = os.path.join(Config.UPLOAD_FOLDER, 'resumes')
    else:
        folder = os.path.join(Config.UPLOAD_FOLDER, 'documents')

    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, secure_name)

    # Save file
    file.save(path)

    # Calculate hash for integrity
    with open(path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    return {
        'filename': secure_name,
        'original_name': original_name,
        'path': path,
        'size': size,
        'hash': file_hash
    }


def get_file_path(filename, file_type):
    """Get full path to a stored file"""
    if file_type == 'resume':
        return os.path.join(Config.UPLOAD_FOLDER, 'resumes', filename)
    else:
        return os.path.join(Config.UPLOAD_FOLDER, 'documents', filename)


def delete_file(filename, file_type):
    """Delete a stored file"""
    path = get_file_path(filename, file_type)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

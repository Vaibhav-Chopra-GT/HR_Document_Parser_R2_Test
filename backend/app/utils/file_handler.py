import os
import uuid
import hashlib
import tempfile
from werkzeug.utils import secure_filename
from app.config import Config

# Initialize Cloudinary if configured (with validation)
_cloudinary_available = False
if Config.USE_CLOUD_STORAGE and Config.CLOUDINARY_URL:
    if Config.CLOUDINARY_URL.startswith('cloudinary://'):
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
        cloudinary.config(secure=True)  # Uses CLOUDINARY_URL env var automatically
        _cloudinary_available = True
    else:
        print(f"Warning: Invalid CLOUDINARY_URL format, falling back to local storage")


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


def _get_fernet():
    """Get Fernet instance for file encryption"""
    import base64
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    secret = Config.SECRET_KEY or 'default-secret-key'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'talently_file_encryption_v1',
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return Fernet(key)


def encrypt_file_data(data: bytes) -> bytes:
    """Encrypt file data"""
    return _get_fernet().encrypt(data)


def decrypt_file_data(encrypted_data: bytes) -> bytes:
    """Decrypt file data"""
    return _get_fernet().decrypt(encrypted_data)


def save_file(file, file_type, candidate_id):
    """
    Save file with secure naming - supports both local and cloud storage
    Documents (PAN/Aadhaar) are encrypted, resumes are not (need parsing)

    Args:
        file: FileStorage object from Flask
        file_type: 'resume' or 'document'
        candidate_id: UUID of the candidate

    Returns:
        dict with filename, original_name, path, size, hash, encrypted
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
    # Add .enc extension for encrypted files
    is_encrypted = (file_type == 'document')  # Encrypt PAN/Aadhaar, not resumes
    if is_encrypted:
        secure_name = f"{candidate_id}_{uuid.uuid4().hex[:8]}.{ext}.enc"
    else:
        secure_name = f"{candidate_id}_{uuid.uuid4().hex[:8]}.{ext}"

    # Read file content
    file_content = file.read()

    # Calculate hash of original content
    file_hash = hashlib.sha256(file_content).hexdigest()

    # Encrypt if document
    if is_encrypted:
        file_content = encrypt_file_data(file_content)

    if _cloudinary_available:
        return _save_to_cloudinary(file_content, file_type, secure_name, original_name, size, file_hash, is_encrypted)
    else:
        return _save_locally(file_content, file_type, secure_name, original_name, size, file_hash, is_encrypted)


def _save_locally(file_content, file_type, secure_name, original_name, size, file_hash, is_encrypted):
    """Save file to local filesystem"""
    if file_type == 'resume':
        folder = os.path.join(Config.UPLOAD_FOLDER, 'resumes')
    else:
        folder = os.path.join(Config.UPLOAD_FOLDER, 'documents')

    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, secure_name)

    # Save file
    with open(path, 'wb') as f:
        f.write(file_content)

    return {
        'filename': secure_name,
        'original_name': original_name,
        'path': path,
        'size': size,
        'hash': file_hash,
        'encrypted': is_encrypted,
        'storage': 'local'
    }


def _save_to_cloudinary(file_content, file_type, secure_name, original_name, size, file_hash, is_encrypted):
    """Save file to Cloudinary"""
    import io

    folder = f"talently/{file_type}s"
    # Get base name for public_id (remove .enc if present)
    if secure_name.endswith('.enc'):
        base_name = secure_name[:-4]  # Remove ".enc" -> "abc.pdf"
    else:
        base_name = secure_name.rsplit('.', 1)[0] if '.' in secure_name else secure_name
    public_id = f"{folder}/{base_name}"

    # Upload to Cloudinary as raw file (since it may be encrypted)
    result = cloudinary.uploader.upload(
        io.BytesIO(file_content),
        public_id=public_id,
        resource_type="raw",  # Use raw for encrypted files
        overwrite=True
    )

    return {
        'filename': secure_name,
        'original_name': original_name,
        'path': result['secure_url'],
        'public_id': result['public_id'],
        'size': size,
        'hash': file_hash,
        'encrypted': is_encrypted,
        'storage': 'cloudinary'
    }


def get_file_path(filename, file_type):
    """Get full path/URL to a stored file"""
    if _cloudinary_available:
        folder = f"talently/{file_type}s"
        # Remove .enc to get base name for public_id
        if filename.endswith('.enc'):
            # filename like "abc.pdf.enc" -> base is "abc.pdf"
            base_name = filename[:-4]  # Remove ".enc"
        else:
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        public_id = f"{folder}/{base_name}"
        return cloudinary.CloudinaryResource(public_id, resource_type="raw").build_url()
    else:
        if file_type == 'resume':
            return os.path.join(Config.UPLOAD_FOLDER, 'resumes', filename)
        else:
            return os.path.join(Config.UPLOAD_FOLDER, 'documents', filename)


def delete_file(filename, file_type):
    """Delete a stored file"""
    if _cloudinary_available:
        folder = f"talently/{file_type}s"
        if filename.endswith('.enc'):
            base_name = filename[:-4]
        else:
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        public_id = f"{folder}/{base_name}"
        try:
            cloudinary.uploader.destroy(public_id, resource_type="raw")
            return True
        except:
            return False
    else:
        path = get_file_path(filename, file_type)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False


def get_file_for_download(filename, file_type):
    """
    Get file for download - handles decryption for encrypted files
    Returns: (file_path, is_temp_file)
    """
    is_encrypted = filename.endswith('.enc')

    if _cloudinary_available:
        import requests

        url = get_file_path(filename, file_type)
        response = requests.get(url)

        if response.status_code != 200:
            raise FileNotFoundError(f"File not found in cloud storage")

        file_content = response.content

        # Decrypt if encrypted
        if is_encrypted:
            file_content = decrypt_file_data(file_content)

        # Create temp file with original extension
        if is_encrypted:
            # Remove .enc to get original extension
            original_ext = filename.rsplit('.', 2)[-2] if '.enc' in filename else 'bin'
        else:
            original_ext = get_file_extension(filename)

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{original_ext}')
        temp.write(file_content)
        temp.close()
        return temp.name, True
    else:
        path = get_file_path(filename, file_type)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {filename}")

        if is_encrypted:
            # Read, decrypt, save to temp file
            with open(path, 'rb') as f:
                encrypted_content = f.read()

            decrypted_content = decrypt_file_data(encrypted_content)

            original_ext = filename.rsplit('.', 2)[-2] if '.enc' in filename else 'bin'
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{original_ext}')
            temp.write(decrypted_content)
            temp.close()
            return temp.name, True
        else:
            return path, False

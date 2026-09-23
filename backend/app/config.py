import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    """Get database URL, fixing Railway's postgres:// to postgresql+pg8000://"""
    url = os.environ.get('DATABASE_URL', 'sqlite:///talently.db')
    # Railway uses postgres:// but SQLAlchemy requires postgresql://
    # Use pg8000 driver (pure Python, no compilation needed)
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif url.startswith('postgresql://') and '+' not in url.split('://')[0]:
        url = url.replace('postgresql://', 'postgresql+pg8000://', 1)
    return url


class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # AI Provider
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'openai').lower()
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

    # Email
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    EMAIL_FROM = os.environ.get('EMAIL_FROM', 'Talently <noreply@talently.app>')

    # Security
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

    # URLs
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5000')

    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    # Cloud Storage (Cloudinary) - optional, falls back to local storage
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')  # Full URL from Cloudinary dashboard
    USE_CLOUD_STORAGE = bool(os.environ.get('CLOUDINARY_URL'))

    # Token expiry (days)
    SUBMISSION_TOKEN_EXPIRY_DAYS = 7

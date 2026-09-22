import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///talently.db')
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

    # Token expiry (days)
    SUBMISSION_TOKEN_EXPIRY_DAYS = 7

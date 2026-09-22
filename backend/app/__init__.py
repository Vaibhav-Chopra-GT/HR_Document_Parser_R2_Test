from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.models import db
import os


def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=[Config.FRONTEND_URL], supports_credentials=True)

    # Ensure upload directories exist
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'resumes'), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'documents'), exist_ok=True)

    # Register blueprints
    from app.routes.candidates import candidates_bp
    from app.routes.portal import portal_bp

    app.register_blueprint(candidates_bp, url_prefix='/api/candidates')
    app.register_blueprint(portal_bp, url_prefix='/api/portal')

    # Health check route
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'TraqCheck API is running'}

    # Create tables
    with app.app_context():
        db.create_all()

    return app

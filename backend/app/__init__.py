from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import Config
from app.models import db
import os

jwt = JWTManager()


def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=[Config.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired", "code": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token", "code": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization required", "code": "authorization_required"}), 401

    # Ensure upload directories exist
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'resumes'), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'documents'), exist_ok=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.candidates import candidates_bp
    from app.routes.portal import portal_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(candidates_bp, url_prefix='/api/candidates')
    app.register_blueprint(portal_bp, url_prefix='/api/portal')

    # Health check route
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Talently API is running'}

    # Create tables
    with app.app_context():
        db.create_all()

    return app

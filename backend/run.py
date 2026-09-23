"""
Run the Flask application
"""
import os
from app import create_app
from app.models import db

app = create_app()

# Create database tables on startup (safe for production - only creates if not exists)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Talently Backend API")
    print("="*50)
    print(f"Server running at: http://localhost:5000")
    print(f"Health check: http://localhost:5000/api/health")
    print("="*50 + "\n")

    app.run(debug=True, port=5000)

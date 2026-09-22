"""
Run the Flask application
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("TraqCheck Backend API")
    print("="*50)
    print(f"Server running at: http://localhost:5000")
    print(f"Health check: http://localhost:5000/api/health")
    print("="*50 + "\n")

    app.run(debug=True, port=5000)

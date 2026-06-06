"""
CampusHire Portal - Startup Script (MySQL version)
================================================
Before running, set your MySQL credentials in app.py -> DB_CONFIG:
    'host':     'localhost'
    'user':     'root'
    'password': 'Manager'
    'database': 'campushire'

Usage:
    python run.py

The app will be available at http://localhost:5000
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_db, DB_CONFIG

if __name__ == '__main__':
    print("=" * 60)
    print("   CampusHire Portal  -  Campus Recruitment System")
    print("=" * 60)
    try:
        init_db()
        print("[OK] Database connected and tables ready.")
    except Exception as e:
        print(f"\n[ERROR] Could not connect to MySQL: {e}")
        print("\nPlease check:")
        print("  1. MySQL server is running on your computer")
        print("  2. Your credentials in app.py -> DB_CONFIG are correct")
        print("  3. The database user has CREATE/INSERT/SELECT privileges")
        sys.exit(1)
    port = int(os.environ.get('PORT', 5000))
    print(f"[OK] Starting server -> http://localhost:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)

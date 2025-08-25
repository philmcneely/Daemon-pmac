#!/usr/bin/env python3
"""
Development server script with hot reload and debugging
"""

import os
import sys
from pathlib import Path

import uvicorn

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.auth import get_password_hash
from app.config import settings
from app.database import SessionLocal, User, create_default_endpoints, init_db


def setup_dev_environment():
    """Set up development environment"""
    print("🔧 Setting up development environment...")

    # Initialize database
    init_db()

    # Create default endpoints
    db = SessionLocal()
    create_default_endpoints(db)

    # Create default admin user if it doesn't exist
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@localhost",
            hashed_password=get_password_hash("admin123"),
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()
        print("✓ Default admin user created (admin/admin123)")

    # Optionally load resume data if file exists
    try:
        from app.resume_loader import (
            check_resume_file_exists,
            import_resume_to_database,
        )

        file_info = check_resume_file_exists()
        if file_info["exists"] and file_info["readable"]:
            print("📄 Found resume file, checking if already imported...")

            # Check if resume data already exists
            from app.resume_loader import get_resume_from_database

            resume_result = get_resume_from_database()

            if resume_result["success"] and resume_result["count"] == 0:
                print("📥 Importing resume data...")
                import_result = import_resume_to_database(
                    user_id=admin_user.id, replace_existing=False
                )
                if import_result["success"]:
                    print("✓ Resume data imported successfully")
                else:
                    print(f"⚠️  Resume import failed: {import_result['error']}")
            else:
                print("✓ Resume data already exists")
        else:
            print("📝 No resume file found at data/resume_admin.json (optional)")
    except Exception as e:
        print(f"⚠️  Resume auto-import failed: {e}")

    db.close()
    print("✓ Development environment ready")


def main():
    """Main development server"""
    print("🚀 Starting Daemon Development Server")

    # Setup development environment
    setup_dev_environment()

    # Create directories if they don't exist
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    print(f"📡 Server starting on {settings.host}:{settings.port}")
    print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"🔍 ReDoc Documentation: http://{settings.host}:{settings.port}/redoc")
    print(f"❤️ Health Check: http://{settings.host}:{settings.port}/health")
    print("🔄 Hot reload enabled")
    print("🛠️ Debug mode enabled")
    print("\n👤 Default admin credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n🔥 Ready for development!")

    # Start development server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Allow external connections in dev
        port=settings.port,
        reload=True,
        log_level="debug",
        reload_dirs=["app"],
        reload_includes=["*.py"],
    )


if __name__ == "__main__":
    main()

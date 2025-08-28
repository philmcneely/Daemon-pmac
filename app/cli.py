"""
Module: cli
Description: Command Line Interface for Daemon-pmac administration, user management,
             and data operations

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- click: 8.1.7+ - Command line interface framework
- sqlalchemy: 2.0+ - Database operations
- rich: 13.7.0+ - Rich console output and formatting

Usage:
    # Create new users
    python -m app.cli create-user pmac

    # Import data from JSON files
    python -m app.cli import-user-data pmac --data-dir data/private/pmac

    # Create database backups
    python -m app.cli backup create

Notes:
    - All commands support --help for detailed usage information
    - Automatic database initialization if not exists
    - Rich console output with colors and progress bars
    - Safe operations with confirmation prompts for destructive actions
"""

import os
import sys
from datetime import datetime

import click

from app.auth import get_password_hash
from app.config import settings
from app.database import Endpoint, SessionLocal, User, create_default_endpoints, init_db
from app.utils import (
    cleanup_old_backups,
    create_backup,
    export_endpoint_data,
    import_endpoint_data,
)

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@click.group()
def cli():
    """Daemon-pmac Command Line Interface"""
    pass


@cli.group()
def resume():
    """Resume management commands"""
    pass


@resume.command()
@click.option("--file", "-f", default=None, help="Path to resume JSON file")
def check(file):
    """Check if resume file exists and is valid"""
    try:
        from app.resume_loader import check_resume_file_exists, load_resume_from_file

        # Check file existence
        file_info = check_resume_file_exists(file)

        click.echo("Resume File Status:")
        click.echo(f"  Path: {file_info['file_path']}")
        click.echo(f"  Exists: {'✓' if file_info['exists'] else '✗'}")
        click.echo(f"  Readable: {'✓' if file_info['readable'] else '✗'}")

        if file_info["exists"]:
            click.echo(f"  Size: {file_info['size_bytes']} bytes")
            if file_info["last_modified"]:
                from datetime import datetime

                modified_time = datetime.fromtimestamp(file_info["last_modified"])
                click.echo(f"  Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Try to load and validate
            click.echo("\nValidating resume data...")
            load_result = load_resume_from_file(file)

            if load_result["success"]:
                click.echo("✓ Resume data is valid")
                resume_data = load_result["data"]
                click.echo(f"  Name: {resume_data.get('name', 'N/A')}")
                click.echo(f"  Title: {resume_data.get('title', 'N/A')}")
                click.echo(
                    f"  Experience entries: {len(resume_data.get('experience', []))}"
                )
                click.echo(
                    f"  Education entries: {len(resume_data.get('education', []))}"
                )
            else:
                click.echo(
                    f"✗ Resume data validation failed: {
                        load_result['error']}"
                )

    except Exception as e:
        click.echo(f"✗ Error checking resume: {e}")
        sys.exit(1)


@resume.command()
@click.option("--file", "-f", default=None, help="Path to resume JSON file")
@click.option("--replace", is_flag=True, help="Replace existing resume data")
@click.option("--user", "-u", default=None, help="Username to associate with resume")
def import_file(file, replace, user):
    """Import resume from JSON file"""
    try:
        from app.database import User
        from app.resume_loader import import_resume_to_database

        # Get user ID if username provided
        user_id = None
        if user:
            db = SessionLocal()
            user_obj = db.query(User).filter(User.username == user).first()
            if user_obj:
                user_id = user_obj.id
            else:
                click.echo(f"✗ User '{user}' not found")
                sys.exit(1)
            db.close()

        click.echo("Importing resume from file...")
        result = import_resume_to_database(
            file_path=file, user_id=user_id, replace_existing=replace
        )

        if result["success"]:
            click.echo(f"✓ Resume imported successfully")
            click.echo(f"  File: {result['file_path']}")
            click.echo(f"  Entry ID: {result['entry_id']}")
            if result.get("replaced_entries", 0) > 0:
                click.echo(
                    f"  Replaced {
                        result['replaced_entries']} existing entries"
                )
        else:
            click.echo(f"✗ Import failed: {result['error']}")
            if "existing_entries" in result:
                click.echo(
                    f"  Found {
                        result['existing_entries']} existing entries"
                )
                click.echo("  Use --replace flag to overwrite existing data")
            sys.exit(1)

    except Exception as e:
        click.echo(f"✗ Import failed: {e}")
        sys.exit(1)


@resume.command()
def show():
    """Show current resume data from database"""
    try:
        from app.resume_loader import get_resume_from_database

        result = get_resume_from_database()

        if result["success"]:
            if result["count"] == 0:
                click.echo("No resume data found in database")
                click.echo("\nTo import resume data:")
                click.echo("  python -m app.cli resume import-file")
            else:
                click.echo(f"Found {result['count']} resume entries:")
                for i, entry_info in enumerate(result.get("entries", [])):
                    click.echo(
                        f"  Entry {
                            i +
                            1}: ID {
                            entry_info['id']}, Created: {
                            entry_info['created_at']}"
                    )

                # Show basic info from first entry
                if result["data"]:
                    resume = result["data"][0]
                    click.echo(f"\nCurrent Resume:")
                    click.echo(f"  Name: {resume.get('name', 'N/A')}")
                    click.echo(f"  Title: {resume.get('title', 'N/A')}")
                    click.echo(
                        f"  Experience: {len(resume.get('experience', []))} entries"
                    )
                    click.echo(
                        f"  Education: {len(resume.get('education', []))} entries"
                    )
                    click.echo(
                        f"  Last Updated: {
                            resume.get(
                                'updated_at',
                                'N/A')}"
                    )
        else:
            click.echo(f"✗ Failed to get resume: {result['error']}")

    except Exception as e:
        click.echo(f"✗ Error: {e}")
        sys.exit(1)


@cli.group()
def db():
    """Database management commands"""
    pass


@db.command()
def init():
    """Initialize the database"""
    try:
        init_db()
        db = SessionLocal()
        create_default_endpoints(db)
        db.close()
        click.echo("✓ Database initialized successfully")
        click.echo("✓ Default endpoints created")
    except Exception as e:
        click.echo(f"✗ Database initialization failed: {e}")
        sys.exit(1)


@db.command()
def reset():
    """Reset the database (WARNING: This will delete all data!)"""
    if click.confirm("This will delete all data. Are you sure?", abort=True):
        try:
            # Remove database file
            db_path = settings.database_url.replace("sqlite:///", "")
            if db_path.startswith("./"):
                db_path = db_path[2:]

            if os.path.exists(db_path):
                os.remove(db_path)

            # Reinitialize
            init_db()
            db = SessionLocal()
            create_default_endpoints(db)
            db.close()
            click.echo("✓ Database reset successfully")
        except Exception as e:
            click.echo(f"✗ Database reset failed: {e}")
            sys.exit(1)


@cli.group()
def user():
    """User management commands"""
    pass


@user.command()
@click.argument("username")
@click.argument("email")
@click.option("--password", prompt=True, hide_input=True, help="User password")
@click.option("--admin", is_flag=True, help="Make user an admin")
def create(username, email, password, admin):
    """Create a new user"""
    try:
        db = SessionLocal()

        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )

        if existing_user:
            click.echo("✗ User with this username or email already exists")
            sys.exit(1)

        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_admin=admin,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        click.echo(f"✓ User '{username}' created successfully")
        if admin:
            click.echo("✓ User has admin privileges")

        db.close()
    except Exception as e:
        click.echo(f"✗ User creation failed: {e}")
        sys.exit(1)


@user.command()
def list():
    """List all users"""
    try:
        db = SessionLocal()
        users = db.query(User).all()

        if not users:
            click.echo("No users found")
            return

        click.echo(
            f"{
                'ID':<5} {
                'Username':<20} {
                'Email':<30} {
                    'Active':<8} {
                        'Admin':<8}"
        )
        click.echo("-" * 80)

        for user in users:
            click.echo(
                f"{user.id:<5} {user.username:<20} {user.email:<30} "
                f"{'Yes' if user.is_active else 'No':<8} "
                f"{'Yes' if user.is_admin else 'No':<8}"
            )

        db.close()
    except Exception as e:
        click.echo(f"✗ Failed to list users: {e}")
        sys.exit(1)


@cli.group()
def endpoint():
    """Endpoint management commands"""
    pass


@endpoint.command()
@click.argument("name")
@click.argument("description")
@click.option("--field", multiple=True, help="Field definition: name:type[:options]")
def create(name, description, field):
    """Create a new endpoint"""
    try:
        db = SessionLocal()

        # Check if endpoint already exists
        existing = db.query(Endpoint).filter(Endpoint.name == name).first()
        if existing:
            click.echo(f"✗ Endpoint '{name}' already exists")
            sys.exit(1)

        # Build schema from field definitions
        schema = {}
        for field_def in field:
            parts = field_def.split(":")
            field_name = parts[0]
            field_type = parts[1] if len(parts) > 1 else "string"
            field_options = parts[2] if len(parts) > 2 else ""

            field_schema = {"type": field_type}

            if field_options:
                if field_options == "required":
                    field_schema["required"] = True
                elif "," in field_options:  # Enum values
                    field_schema["enum"] = field_options.split(",")

            schema[field_name] = field_schema

        # Create endpoint
        endpoint = Endpoint(name=name, description=description, schema=schema)

        db.add(endpoint)
        db.commit()

        click.echo(f"✓ Endpoint '{name}' created successfully")

        db.close()
    except Exception as e:
        click.echo(f"✗ Endpoint creation failed: {e}")
        sys.exit(1)


@endpoint.command()
def list():
    """List all endpoints"""
    try:
        db = SessionLocal()
        endpoints = db.query(Endpoint).all()

        if not endpoints:
            click.echo("No endpoints found")
            return

        click.echo(
            f"{
                'ID':<5} {
                'Name':<20} {
                'Description':<40} {
                    'Active':<8} {
                        'Public':<8}"
        )
        click.echo("-" * 90)

        for ep in endpoints:
            desc = (
                (ep.description or "")[:37] + "..."
                if (ep.description or "") and len(ep.description) > 40
                else (ep.description or "")
            )
            click.echo(
                f"{ep.id:<5} {ep.name:<20} {desc:<40} "
                f"{'Yes' if ep.is_active else 'No':<8} "
                f"{'Yes' if ep.is_public else 'No':<8}"
            )

        db.close()
    except Exception as e:
        click.echo(f"✗ Failed to list endpoints: {e}")
        sys.exit(1)


@cli.group()
def backup():
    """Backup management commands"""
    pass


@backup.command()
def create():
    """Create a backup"""
    try:
        backup_info = create_backup()
        click.echo(f"✓ Backup created: {backup_info.filename}")
        click.echo(f"  Size: {backup_info.size_bytes} bytes")
        click.echo(f"  Created: {backup_info.created_at}")
    except Exception as e:
        click.echo(f"✗ Backup creation failed: {e}")
        sys.exit(1)


@backup.command()
def list():
    """List available backups"""
    try:
        backup_dir = settings.backup_dir
        if not os.path.exists(backup_dir):
            click.echo("No backups found")
            return

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                stat_info = os.stat(filepath)
                backups.append(
                    {
                        "filename": filename,
                        "size": stat_info.st_size,
                        "created": datetime.fromtimestamp(stat_info.st_ctime),
                    }
                )

        if not backups:
            click.echo("No backups found")
            return

        # Sort by creation date
        backups.sort(key=lambda x: x["created"], reverse=True)

        click.echo(f"{'Filename':<40} {'Size':<15} {'Created':<20}")
        click.echo("-" * 80)

        for backup in backups:
            size_str = f"{backup['size']:,} bytes"
            created_str = backup["created"].strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"{backup['filename']:<40} {size_str:<15} {created_str:<20}")

    except Exception as e:
        click.echo(f"✗ Failed to list backups: {e}")
        sys.exit(1)


@backup.command()
@click.argument("backup_filename")
def restore(backup_filename):
    """Restore from a backup"""
    if not click.confirm(
        f"This will overwrite the current database with '{backup_filename}'. Continue?"
    ):
        return

    try:
        import shutil

        backup_path = os.path.join(settings.backup_dir, backup_filename)

        if not os.path.exists(backup_path):
            click.echo(f"✗ Backup file '{backup_filename}' not found")
            sys.exit(1)

        # Get current database path
        db_path = settings.database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]

        # Create a backup of current database before restoring
        if os.path.exists(db_path):
            current_backup = (
                f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            current_backup_path = os.path.join(settings.backup_dir, current_backup)
            shutil.copy2(db_path, current_backup_path)
            click.echo(f"✓ Current database backed up as: {current_backup}")

        # Restore from backup
        shutil.copy2(backup_path, db_path)
        click.echo(f"✓ Database restored from: {backup_filename}")

    except Exception as e:
        click.echo(f"✗ Restore failed: {e}")
        sys.exit(1)


@backup.command()
def cleanup():
    """Clean up old backups"""
    try:
        cleanup_old_backups()
        click.echo("✓ Old backups cleaned up")
    except Exception as e:
        click.echo(f"✗ Cleanup failed: {e}")
        sys.exit(1)


@cli.group()
def data():
    """Data management commands"""
    pass


@data.command()
@click.argument("endpoint_name")
@click.option(
    "--format", default="json", type=click.Choice(["json", "csv"]), help="Export format"
)
@click.option("--output", help="Output file path")
def export(endpoint_name, format, output):
    """Export endpoint data"""
    try:
        db = SessionLocal()
        data = export_endpoint_data(db, endpoint_name, format)

        if output:
            with open(output, "w") as f:
                f.write(data)
            click.echo(f"✓ Data exported to: {output}")
        else:
            click.echo(data)

        db.close()
    except Exception as e:
        click.echo(f"✗ Export failed: {e}")
        sys.exit(1)


@data.command()
@click.argument("endpoint_name")
@click.argument("input_file")
@click.option(
    "--format", default="json", type=click.Choice(["json", "csv"]), help="Import format"
)
def import_data(endpoint_name, input_file, format):
    """Import data into an endpoint"""
    try:
        if not os.path.exists(input_file):
            click.echo(f"✗ Input file '{input_file}' not found")
            sys.exit(1)

        with open(input_file, "r") as f:
            data_content = f.read()

        db = SessionLocal()
        result = import_endpoint_data(db, endpoint_name, data_content, format)

        click.echo(f"✓ Import completed:")
        click.echo(f"  Imported: {result['imported_count']} items")
        click.echo(f"  Errors: {result['error_count']} items")

        if result["errors"]:
            click.echo("\nErrors:")
            for error in result["errors"][:5]:  # Show first 5 errors
                click.echo(
                    f"  - Item {error['index']}: "
                    f"{error.get('error', error.get('errors', []))}"
                )

        db.close()
    except Exception as e:
        click.echo(f"✗ Import failed: {e}")
        sys.exit(1)


@cli.command()
@click.option("--host", default=settings.host, help="Host to bind to")
@click.option("--port", default=settings.port, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host, port, reload):
    """Start the API server"""
    try:
        import uvicorn

        from app.main import app  # noqa: F401

        click.echo(f"Starting Daemon-pmac server on {host}:{port}")
        if reload:
            click.echo("Auto-reload enabled")

        uvicorn.run("app.main:app", host=host, port=port, reload=reload)
    except KeyboardInterrupt:
        click.echo("\nShutting down server...")
    except Exception as e:
        click.echo(f"✗ Server failed to start: {e}")
        sys.exit(1)


@cli.command()
def status():
    """Show system status"""
    try:
        from app.utils import get_system_metrics, health_check

        # Health check
        health = health_check()
        click.echo(f"System Status: {health['status'].upper()}")
        click.echo(f"Timestamp: {health['timestamp']}")
        click.echo("\nHealth Checks:")

        for check_name, check_result in health["checks"].items():
            status_icon = {
                "healthy": "✓",
                "degraded": "⚠",
                "unhealthy": "✗",
                "disabled": "-",
                "warning": "⚠",
                "critical": "✗",
                "unknown": "?",
            }.get(check_result["status"], "?")
            click.echo(
                f"  {status_icon} {check_name}: {
                    check_result['message']}"
            )

        # System metrics
        click.echo("\nSystem Metrics:")
        metrics = get_system_metrics()

        if "error" not in metrics:
            click.echo(f"  Memory: {metrics['memory']['percent']:.1f}% used")
            click.echo(f"  CPU: {metrics['cpu']['percent']:.1f}% used")
            click.echo(f"  Disk: {metrics['disk']['percent']:.1f}% used")
            click.echo(f"  Database: {metrics['database']['size_mb']:.1f} MB")
        else:
            click.echo(f"  Error getting metrics: {metrics['error']}")

    except Exception as e:
        click.echo(f"✗ Failed to get status: {e}")
        sys.exit(1)


@click.command()
@click.argument("username")
@click.option("--email", prompt=True, help="User email address")
@click.option("--password", prompt=True, hide_input=True, help="User password")
@click.option("--admin", is_flag=True, help="Make user an admin")
@click.option("--import-data", is_flag=True, default=True, help="Import example data")
def create_user(
    username: str, email: str, password: str, admin: bool, import_data: bool
):
    """Create a new user with optional data import"""
    from .auth import get_password_hash
    from .database import SessionLocal, User, UserPrivacySettings
    from .multi_user_import import (
        create_user_data_directory,
        import_user_data_from_directory,
    )

    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            click.echo(f"Error: User '{username}' already exists")
            return

        # Create user
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=admin,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create privacy settings
        privacy_settings = UserPrivacySettings(
            user_id=new_user.id,
            show_contact_info=True,
            show_location=True,
            show_current_company=True,
            show_salary_range=False,
            show_education_details=True,
            show_personal_projects=True,
            business_card_mode=False,
            ai_assistant_access=True,
            custom_privacy_rules={},
        )
        db.add(privacy_settings)
        db.commit()

        click.echo(f"✓ User '{username}' created successfully")

        # Create data directory and copy examples
        user_dir = create_user_data_directory(username)
        click.echo(f"✓ Data directory created: {user_dir}")

        # Import data if requested
        if import_data:
            result = import_user_data_from_directory(
                username=username,
                data_directory=user_dir,
                db=db,
                replace_existing=False,
            )

            if result["success"]:
                click.echo(
                    f"✓ Imported {
                        result['total_entries']} data entries from {
                        len(
                            result['imported_files'])} files"
                )
            else:
                click.echo(
                    f"⚠ Data import failed: {
                        result.get(
                            'error',
                            'Unknown error')}"
                )

        click.echo(f"\n🎉 User setup complete!")
        click.echo(f"Username: {username}")
        click.echo(f"Email: {email}")
        click.echo(f"Admin: {admin}")
        click.echo(f"Data directory: {user_dir}")

    except Exception as e:
        db.rollback()
        click.echo(f"Error creating user: {e}")
    finally:
        db.close()


@click.command()
@click.option(
    "--base-dir", default="data/private", help="Base directory containing user folders"
)
@click.option("--replace", is_flag=True, help="Replace existing data")
def import_all_data(base_dir: str, replace: bool):
    """Import data for all existing users"""
    from .database import SessionLocal
    from .multi_user_import import import_all_users_data

    db = SessionLocal()
    try:
        result = import_all_users_data(
            base_directory=base_dir, db=db, replace_existing=replace
        )

        if result["success"]:
            click.echo(
                f"✓ Successfully imported data for {
                    result['total_users']} users"
            )
            click.echo(f"✓ Total entries imported: {result['total_entries']}")

            for user_result in result["users_processed"]:
                click.echo(
                    f"  - {user_result['username']}: "
                    f"{user_result['total_entries']} entries"
                )

            if result["errors"]:
                click.echo(f"\n⚠ {len(result['errors'])} errors occurred:")
                for error in result["errors"]:
                    click.echo(f"  - {error['username']}: {error['error']}")
        else:
            click.echo(f"❌ Import failed: {result['error']}")

    except Exception as e:
        click.echo(f"Error importing data: {e}")
    finally:
        db.close()


@click.command()
@click.argument("username")
@click.option("--data-dir", help="Custom data directory")
@click.option("--replace", is_flag=True, help="Replace existing data")
def import_user_data_cli(username: str, data_dir: str, replace: bool):
    """Import data for a specific user"""
    from .database import SessionLocal
    from .multi_user_import import import_user_data_from_directory

    db = SessionLocal()
    try:
        result = import_user_data_from_directory(
            username=username, data_directory=data_dir, db=db, replace_existing=replace
        )

        if result["success"]:
            click.echo(f"✓ Successfully imported data for user '{username}'")
            click.echo(f"✓ Total entries imported: {result['total_entries']}")
            click.echo(f"✓ Files processed: {len(result['imported_files'])}")

            for file_info in result["imported_files"]:
                click.echo(
                    f"  - {
                        file_info['endpoint']}: {
                        file_info['entries']} entries from {
                        file_info['file']}"
                )

            if result["errors"]:
                click.echo(f"\n⚠ {len(result['errors'])} errors occurred:")
                for error in result["errors"]:
                    click.echo(f"  - {error['file']}: {error['error']}")
        else:
            click.echo(f"❌ Import failed: {result['error']}")

    except Exception as e:
        click.echo(f"Error importing data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    cli()

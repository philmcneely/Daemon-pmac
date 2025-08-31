#!/usr/bin/env python3
"""
Database Version Tracking System
Manages database schema versions and migration state
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base

# Add the app directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings

# Database setup
engine = create_engine(settings.database_url, echo=False)
Base = declarative_base()


class DatabaseVersion:
    """Database version tracking and migration management"""

    def __init__(self):
        self.engine = engine
        self._ensure_version_table()

    def _ensure_version_table(self):
        """Create database_versions table if it doesn't exist"""
        with self.engine.connect() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS database_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version VARCHAR(20) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    migration_script VARCHAR(100),
                    description TEXT,
                    rollback_notes TEXT
                )
            """
                )
            )
            conn.commit()

    def get_current_version(self) -> Optional[str]:
        """Get the current database version"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT version FROM database_versions
                ORDER BY applied_at DESC LIMIT 1
            """
                )
            ).fetchone()
            return result[0] if result else None

    def get_version_history(self) -> List[Dict]:
        """Get complete version history"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT version, applied_at, migration_script, description
                FROM database_versions
                ORDER BY applied_at DESC
            """
                )
            ).fetchall()

            return [
                {
                    "version": row[0],
                    "applied_at": row[1],
                    "migration_script": row[2],
                    "description": row[3],
                }
                for row in result
            ]

    def record_migration(
        self,
        version: str,
        migration_script: str,
        description: str,
        rollback_notes: str = "",
    ):
        """Record a successful migration"""
        with self.engine.connect() as conn:
            conn.execute(
                text(
                    """
                INSERT INTO database_versions
                (version, migration_script, description, rollback_notes)
                VALUES (:version, :script, :description, :rollback)
            """
                ),
                {
                    "version": version,
                    "script": migration_script,
                    "description": description,
                    "rollback": rollback_notes,
                },
            )
            conn.commit()

    def is_migration_needed(self, target_version: str) -> Tuple[bool, str]:
        """Check if migration is needed to reach target version"""
        current = self.get_current_version()

        if current is None:
            return True, "No version recorded - initial migration needed"

        if current == target_version:
            return False, f"Already at version {target_version}"

        # Version comparison logic
        current_parts = self._parse_version(current)
        target_parts = self._parse_version(target_version)

        if target_parts > current_parts:
            return True, f"Upgrade needed: {current} → {target_version}"
        elif target_parts < current_parts:
            return True, f"Downgrade needed: {current} → {target_version}"
        else:
            return False, f"Versions are equivalent: {current} = {target_version}"

    def _parse_version(self, version: str) -> Tuple[int, ...]:
        """Parse version string into comparable tuple"""
        # Remove 'v' prefix if present
        clean_version = version.lstrip("v")
        try:
            return tuple(int(x) for x in clean_version.split("."))
        except ValueError:
            # Fallback for non-standard versions
            return (0, 0, 0)

    def get_migration_path(self, current: str, target: str) -> List[str]:
        """Get the migration path between versions"""
        migration_map = {
            ("0.1.0", "0.2.0"): ["v0.1.0_to_v0.2.0"],
            ("0.1.0", "0.3.0"): ["v0.1.0_to_v0.2.0", "v0.2.0_to_v0.3.0"],
            ("0.2.0", "0.3.0"): ["v0.2.0_to_v0.3.0"],
            ("0.2.1", "0.3.0"): ["v0.2.x_to_v0.3.0"],
            ("0.2.2", "0.3.0"): ["v0.2.x_to_v0.3.0"],
            ("0.1.0", "0.3.1"): ["v0.1.0_to_v0.2.0", "v0.2.0_to_v0.3.0"],
            ("0.2.0", "0.3.1"): ["v0.2.0_to_v0.3.0"],
            ("0.2.1", "0.3.1"): ["v0.2.x_to_v0.3.0"],
            ("0.2.2", "0.3.1"): ["v0.2.x_to_v0.3.0"],
            ("0.3.0", "0.3.1"): [],  # No migration needed for patch version
        }

        # Normalize versions
        current_norm = current.lstrip("v")
        target_norm = target.lstrip("v")

        return migration_map.get((current_norm, target_norm), [])

    def check_schema_integrity(self) -> Dict[str, any]:
        """Check database schema integrity"""
        inspector = inspect(self.engine)

        # Expected tables for each version
        v3_tables = {
            "users",
            "endpoints",
            "data_entries",
            "api_keys",
            "audit_logs",
            "user_privacy_settings",
            "data_privacy_rules",
        }

        existing_tables = set(inspector.get_table_names())

        integrity_status = "PASS" if v3_tables.issubset(existing_tables) else "FAIL"

        return {
            "existing_tables": list(existing_tables),
            "expected_tables": list(v3_tables),
            "missing_tables": list(v3_tables - existing_tables),
            "extra_tables": list(existing_tables - v3_tables),
            "integrity_check": integrity_status,
        }

    def backup_before_migration(self) -> str:
        """Create a backup before migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_migration_backup_{timestamp}.db"

        # Use the app's backup functionality
        try:
            from app.utils import create_backup

            backup_result = create_backup()
            return backup_result.filename
        except ImportError:
            # Fallback: simple file copy
            import shutil

            source_db = "daemon.db"
            backup_path = f"backups/{backup_name}"

            os.makedirs("backups", exist_ok=True)
            shutil.copy2(source_db, backup_path)
            return backup_name


def main():
    """Main version tracking operations"""
    db_version = DatabaseVersion()

    print("🗄️  Database Version Tracking")
    print("=" * 50)

    # Get current version
    current = db_version.get_current_version()
    print(f"📍 Current Version: {current or 'Unknown (no migrations recorded)'}")

    # Check schema integrity
    integrity = db_version.check_schema_integrity()
    print(f"🔍 Schema Integrity: {integrity['integrity_check']}")

    if integrity["missing_tables"]:
        print(f"   ⚠️  Missing tables: {integrity['missing_tables']}")

    if integrity["extra_tables"]:
        print(f"   ℹ️  Extra tables: {integrity['extra_tables']}")

    # Show version history
    history = db_version.get_version_history()
    if history:
        print(f"\n📚 Migration History:")
        for entry in history:
            version = entry["version"]
            applied = entry["applied_at"]
            desc = entry["description"]
            print(f"   • {version} - {applied} - {desc}")

    # Check if migration to v0.3.1 is needed
    target_version = "0.3.1"
    needs_migration, reason = db_version.is_migration_needed(target_version)

    print(f"\n🎯 Target Version: v{target_version}")
    print(f"🔄 Migration Status: {reason}")

    if needs_migration and current:
        path = db_version.get_migration_path(current, target_version)
        if path:
            print(f"📋 Migration Path: {' → '.join(path)}")

    print("\n" + "=" * 50)

    # If this is the first time tracking versions, record current state
    if current is None:
        print("🆕 First time setup - recording current state as v0.3.1")
        db_version.record_migration(
            version="0.3.1",
            migration_script="initial_setup",
            description="Initial version tracking setup",
            rollback_notes="This is the baseline version",
        )
        print("✅ Version tracking initialized")


if __name__ == "__main__":
    main()

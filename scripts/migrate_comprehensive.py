#!/usr/bin/env python3
"""
Comprehensive Database Migration System
Handles all version migrations with safety checks and rollback capability
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the app directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.version_tracker import DatabaseVersion


class MigrationRunner:
    """Manages database migrations with safety checks"""

    def __init__(self):
        self.version_tracker = DatabaseVersion()
        self.backup_created = False
        self.backup_path = ""

    def run_migration(self, target_version: str, force: bool = False) -> bool:
        """Run migration to target version"""
        print(f"🚀 Starting migration to v{target_version}")
        print("=" * 60)

        # Check current state
        current_version = self.version_tracker.get_current_version()
        print(f"📍 Current Version: {current_version or 'Unknown'}")

        # Check if migration is needed
        needs_migration, reason = self.version_tracker.is_migration_needed(
            target_version
        )
        print(f"🔍 Migration Status: {reason}")

        if not needs_migration and not force:
            print("✅ No migration needed")
            return True

        # Pre-migration checks
        if not self._pre_migration_checks():
            print("❌ Pre-migration checks failed")
            return False

        # Create backup
        if not self._create_backup():
            print("❌ Failed to create backup")
            return False

        try:
            # Run migrations
            if current_version is None:
                success = self._initialize_version_tracking(target_version)
            else:
                success = self._run_version_migrations(current_version, target_version)

            if success:
                print("✅ Migration completed successfully")
                self._post_migration_verification(target_version)
                return True
            else:
                print("❌ Migration failed - rolling back")
                self._rollback_migration()
                return False

        except Exception as e:
            print(f"💥 Migration error: {e}")
            print("🔄 Rolling back...")
            self._rollback_migration()
            return False

    def _pre_migration_checks(self) -> bool:
        """Run pre-migration safety checks"""
        print("\n🔍 Running pre-migration checks...")

        # Check database file exists
        if not os.path.exists("daemon.db"):
            print("   ❌ Database file not found")
            return False

        # Check schema integrity
        integrity = self.version_tracker.check_schema_integrity()
        print(f"   📊 Schema integrity: {integrity['integrity_check']}")

        if integrity["missing_tables"]:
            print(f"   ⚠️  Missing tables: {integrity['missing_tables']}")

        # Check disk space (need ~3x database size for safety)
        db_size = os.path.getsize("daemon.db")
        free_space = shutil.disk_usage(".")[2]

        if free_space < (db_size * 3):
            print(f"   ❌ Insufficient disk space. Need {db_size * 3} bytes")
            return False

        print("   ✅ Pre-migration checks passed")
        return True

    def _create_backup(self) -> bool:
        """Create pre-migration backup"""
        print("\n💾 Creating backup...")

        try:
            backup_name = self.version_tracker.backup_before_migration()
            self.backup_path = f"backups/{backup_name}"
            self.backup_created = True
            print(f"   ✅ Backup created: {backup_name}")
            return True
        except Exception as e:
            print(f"   ❌ Backup failed: {e}")
            return False

    def _initialize_version_tracking(self, target_version: str) -> bool:
        """Initialize version tracking for first-time setup"""
        print("\n🆕 Initializing version tracking...")

        try:
            self.version_tracker.record_migration(
                version=target_version,
                migration_script="initial_setup",
                description="Initial version tracking setup",
                rollback_notes="Baseline version - use backup to restore",
            )
            print(f"   ✅ Version tracking initialized at v{target_version}")
            return True
        except Exception as e:
            print(f"   ❌ Version tracking initialization failed: {e}")
            return False

    def _run_version_migrations(self, current: str, target: str) -> bool:
        """Run specific version migrations"""
        print(f"\n🔄 Running migrations: {current} → {target}")

        # Get migration path
        path = self.version_tracker.get_migration_path(current, target)

        if not path:
            print(f"   ⚠️  No migration path defined for {current} → {target}")
            print("   ℹ️  Recording version change without schema migration")
            return self._record_direct_migration(current, target)

        # Run each migration in the path
        for migration in path:
            print(f"   🔄 Running migration: {migration}")
            success = self._run_single_migration(migration)
            if not success:
                return False

        # Record final version
        self.version_tracker.record_migration(
            version=target,
            migration_script="automated_migration",
            description=f"Migrated from {current} to {target}",
            rollback_notes=f"Restore from backup: {self.backup_path}",
        )

        return True

    def _run_single_migration(self, migration_name: str) -> bool:
        """Run a single migration script"""
        migration_scripts = {
            "v0.1.0_to_v0.2.0": self._migrate_v1_to_v2,
            "v0.2.0_to_v0.3.0": self._migrate_v2_to_v3,
            "v0.2.x_to_v0.3.0": self._migrate_v2_to_v3,
        }

        migration_func = migration_scripts.get(migration_name)
        if not migration_func:
            print(f"      ❌ Unknown migration: {migration_name}")
            return False

        try:
            migration_func()
            print(f"      ✅ {migration_name} completed")
            return True
        except Exception as e:
            print(f"      ❌ {migration_name} failed: {e}")
            return False

    def _migrate_v1_to_v2(self):
        """Migration from v0.1.x to v0.2.0 - Privacy System"""
        from sqlalchemy import text

        print("      📋 Adding privacy system tables...")

        with self.version_tracker.engine.connect() as conn:
            # Create user_privacy_settings table
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS user_privacy_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    setting_name VARCHAR(100) NOT NULL,
                    setting_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, setting_name)
                )
            """
                )
            )

            # Create data_privacy_rules table
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS data_privacy_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name VARCHAR(100) NOT NULL UNIQUE,
                    rule_type VARCHAR(50) NOT NULL,
                    rule_config TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )

            # Add default privacy rules
            default_rules = [
                {
                    "name": "personal_data_retention",
                    "type": "retention",
                    "config": '{"max_age_days": 365, "applies_to": ["personal_info"]}',
                },
                {
                    "name": "sensitive_data_encryption",
                    "type": "encryption",
                    "config": (
                        '{"encryption_level": "AES256", '
                        '"applies_to": ["passwords", "tokens"]}'
                    ),
                },
            ]

            for rule in default_rules:
                conn.execute(
                    text(
                        """
                    INSERT OR IGNORE INTO data_privacy_rules
                    (rule_name, rule_type, rule_config)
                    VALUES (:name, :type, :config)
                """
                    ),
                    rule,
                )

            conn.commit()

    def _migrate_v2_to_v3(self):
        """Migration from v0.2.x to v0.3.0 - Enhanced Features"""
        from sqlalchemy import text

        print("      📋 Adding v0.3.0 enhancements...")

        with self.version_tracker.engine.connect() as conn:
            # Add any new columns or tables for v0.3.0
            # Example: Add new columns to existing tables
            try:
                conn.execute(
                    text(
                        """
                    ALTER TABLE users ADD COLUMN last_login TIMESTAMP
                """
                    )
                )
            except Exception:
                # Column might already exist
                pass

            try:
                conn.execute(
                    text(
                        """
                    ALTER TABLE data_entries
                    ADD COLUMN validation_status VARCHAR(20) DEFAULT 'pending'
                """
                    )
                )
            except Exception:
                # Column might already exist
                pass

            # Update existing data if needed
            conn.execute(
                text(
                    """
                UPDATE data_entries
                SET validation_status = 'approved'
                WHERE validation_status IS NULL
            """
                )
            )

            conn.commit()

    def _record_direct_migration(self, current: str, target: str) -> bool:
        """Record migration without running schema changes"""
        try:
            self.version_tracker.record_migration(
                version=target,
                migration_script="direct_upgrade",
                description=f"Direct version upgrade from {current} to {target}",
                rollback_notes=f"Restore from backup: {self.backup_path}",
            )
            return True
        except Exception as e:
            print(f"   ❌ Failed to record migration: {e}")
            return False

    def _post_migration_verification(self, target_version: str):
        """Verify migration success"""
        print("\n🔍 Post-migration verification...")

        # Check version was recorded
        current = self.version_tracker.get_current_version()
        if current == target_version:
            print(f"   ✅ Version correctly set to {target_version}")
        else:
            print(f"   ⚠️  Version mismatch: expected {target_version}, got {current}")

        # Check schema integrity
        integrity = self.version_tracker.check_schema_integrity()
        print(f"   📊 Schema integrity: {integrity['integrity_check']}")

        if integrity["missing_tables"]:
            print(f"   ⚠️  Missing tables: {integrity['missing_tables']}")

        print("   ✅ Migration verification completed")

    def _rollback_migration(self):
        """Rollback migration using backup"""
        if not self.backup_created or not self.backup_path:
            print("   ❌ No backup available for rollback")
            return

        try:
            print(f"   🔄 Restoring from backup: {self.backup_path}")
            shutil.copy2(self.backup_path, "daemon.db")
            print("   ✅ Database restored from backup")
        except Exception as e:
            print(f"   ❌ Rollback failed: {e}")
            print(f"   🆘 Manual restore required from: {self.backup_path}")


def main():
    """Main migration interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Database Migration System")
    parser.add_argument("--target", default="0.3.1", help="Target version")
    parser.add_argument("--force", action="store_true", help="Force migration")
    parser.add_argument("--check-only", action="store_true", help="Check status only")

    args = parser.parse_args()

    runner = MigrationRunner()

    if args.check_only:
        # Just show current status
        print("🔍 Database Status Check")
        print("=" * 40)

        current = runner.version_tracker.get_current_version()
        print(f"📍 Current Version: {current or 'Unknown'}")

        integrity = runner.version_tracker.check_schema_integrity()
        print(f"📊 Schema Integrity: {integrity['integrity_check']}")

        history = runner.version_tracker.get_version_history()
        if history:
            print("\n📚 Recent Migrations:")
            for entry in history[:3]:  # Show last 3
                version = entry["version"]
                applied = entry["applied_at"]
                desc = entry["description"]
                print(f"   • {version} - {applied} - {desc}")

        return

    # Run migration
    success = runner.run_migration(args.target, args.force)
    exit_code = 0 if success else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

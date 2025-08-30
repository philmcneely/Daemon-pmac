#!/usr/bin/env python3
"""
Database Migration Script for Multi-User Features
Adds UserPrivacySettings and DataPrivacyRule tables with default data
"""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base

# Add the app directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Direct database setup to avoid importing the full app
DATABASE_URL = "sqlite:///daemon.db"
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()


def create_user_privacy_settings_table():
    """Create UserPrivacySettings table if it doesn't exist"""
    with engine.connect() as conn:
        # Check if table exists
        inspector = inspect(engine)
        if "user_privacy_settings" in inspector.get_table_names():
            print("✓ UserPrivacySettings table already exists")
            return

        print("Creating UserPrivacySettings table...")
        conn.execute(
            text(
                """
        CREATE TABLE user_privacy_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            privacy_level VARCHAR(20) DEFAULT 'public_full',
            show_contact_info BOOLEAN DEFAULT TRUE,
            ai_assistant_access BOOLEAN DEFAULT TRUE,
            business_card_mode BOOLEAN DEFAULT FALSE,
            custom_filters TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
        """
            )
        )
        conn.commit()
        print("✓ UserPrivacySettings table created")


def create_data_privacy_rules_table():
    """Create DataPrivacyRule table if it doesn't exist"""
    with engine.connect() as conn:
        # Check if table exists
        inspector = inspect(engine)
        if "data_privacy_rules" in inspector.get_table_names():
            print("✓ DataPrivacyRule table already exists")
            return

        print("Creating DataPrivacyRule table...")
        conn.execute(
            text(
                """
        CREATE TABLE data_privacy_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name VARCHAR(50) NOT NULL,
            pattern VARCHAR(200) NOT NULL,
            privacy_level VARCHAR(20) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
            )
        )
        conn.commit()
        print("✓ DataPrivacyRule table created")


def insert_default_privacy_rules():
    """Insert default privacy rules"""
    with engine.connect() as conn:
        # Check if rules already exist
        result = conn.execute(text("SELECT COUNT(*) FROM data_privacy_rules"))
        count = result.scalar()

        if count > 0:
            print("✓ Privacy rules already exist")
            return

        print("Inserting default privacy rules...")

        default_rules = [
            # Phone numbers - show only in business card mode
            ("phone", r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "business_card"),
            ("phone_alt", r"\(\d{3}\)\s*\d{3}[-.]?\d{4}", "business_card"),
            # SSN - most sensitive, only for AI assistance
            ("ssn", r"\b\d{3}-\d{2}-\d{4}\b", "ai_safe"),
            ("ssn_alt", r"\b\d{9}\b", "ai_safe"),
            # Email addresses - professional level
            (
                "email",
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "professional",
            ),
            # Financial information - professional level
            ("salary", r"\$[0-9,]+(\.[0-9]{2})?", "professional"),
            ("income", r"\b[0-9,]+\s*(dollars?|USD|\$)", "professional"),
            ("wage", r"\b\$?\d+(\.\d{2})?\s*per\s+(hour|hr)", "professional"),
            # Address information - professional level
            (
                "address",
                r"\d+\s+[A-Za-z0-9\s,.-]+\s+(Street|St|Avenue|Ave|Road|Rd|"
                r"Drive|Dr|Lane|Ln)",
                "professional",
            ),
            ("zip_code", r"\b\d{5}(-\d{4})?\b", "professional"),
            # Credit card numbers - most sensitive
            ("credit_card", r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "ai_safe"),
            # Driver's license - professional level
            ("drivers_license", r"\b[A-Z]\d{7,8}\b", "professional"),
            # Date of birth - professional level
            ("date_of_birth", r"\b\d{1,2}/\d{1,2}/\d{4}\b", "professional"),
            (
                "dob_alt",
                (
                    r"\b(January|February|March|April|May|June|July|August|"
                    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
                ),
                "professional",
            ),
        ]

        for field_name, pattern, privacy_level in default_rules:
            conn.execute(
                text(
                    """
            INSERT INTO data_privacy_rules (field_name, pattern, privacy_level)
            VALUES (:field_name, :pattern, :privacy_level)
            """
                ),
                {
                    "field_name": field_name,
                    "pattern": pattern,
                    "privacy_level": privacy_level,
                },
            )

        conn.commit()
        print(f"✓ Inserted {len(default_rules)} default privacy rules")


def create_default_privacy_settings_for_existing_users():
    """Create default privacy settings for existing users"""
    with engine.connect() as conn:
        # Get all users without privacy settings
        result = conn.execute(
            text(
                """
        SELECT u.id, u.username
        FROM users u
        LEFT JOIN user_privacy_settings ups ON u.id = ups.user_id
        WHERE ups.id IS NULL
        """
            )
        )

        users_without_settings = result.fetchall()

        if not users_without_settings:
            print("✓ All users already have privacy settings")
            return

        print(
            f"Creating default privacy settings for "
            f"{len(users_without_settings)} users..."
        )

        for user_id, username in users_without_settings:
            conn.execute(
                text(
                    """
            INSERT INTO user_privacy_settings
            (user_id, privacy_level, show_contact_info, ai_assistant_access,
             business_card_mode)
            VALUES (:user_id, 'public_full', TRUE, TRUE, FALSE)
            """
                ),
                {"user_id": user_id},
            )
            print(f"  ✓ Created privacy settings for user: {username}")

        conn.commit()


def init_basic_tables():
    """Create basic tables if they don't exist"""
    with engine.connect() as conn:
        # Create users table if it doesn't exist
        inspector = inspect(engine)
        if "users" not in inspector.get_table_names():
            print("Creating users table...")
            conn.execute(
                text(
                    """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                hashed_password VARCHAR(100) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
                )
            )
            conn.commit()
            print("✓ Users table created")
        else:
            print("✓ Users table already exists")


def add_full_name_column():
    """Add full_name column to users table if it doesn't exist"""
    with engine.connect() as conn:
        # Check if column exists
        inspector = inspect(engine)
        columns = inspector.get_columns("users")
        column_names = [col["name"] for col in columns]

        if "full_name" in column_names:
            print("✓ Users.full_name column already exists")
            return

        print("Adding full_name column to users table...")
        conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)"))
        conn.commit()
        print("✓ Users.full_name column added")


def main():
    """Run all migrations"""
    print("🚀 Running database migrations for multi-user features...")
    print("=" * 60)

    try:
        # Initialize the database (creates basic tables)
        print("Initializing base database...")
        init_basic_tables()
        print("✓ Base database initialized")

        # Add full_name column to users table
        add_full_name_column()

        # Create new tables
        create_user_privacy_settings_table()
        create_data_privacy_rules_table()

        # Insert default data
        insert_default_privacy_rules()
        create_default_privacy_settings_for_existing_users()

        print("=" * 60)
        print("✅ All migrations completed successfully!")

        # Show summary
        with engine.connect() as conn:
            user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            rule_count = conn.execute(
                text("SELECT COUNT(*) FROM data_privacy_rules")
            ).scalar()
            settings_count = conn.execute(
                text("SELECT COUNT(*) FROM user_privacy_settings")
            ).scalar()

            print(f"📊 Database Summary:")
            print(f"   Users: {user_count}")
            print(f"   Privacy Rules: {rule_count}")
            print(f"   Privacy Settings: {settings_count}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

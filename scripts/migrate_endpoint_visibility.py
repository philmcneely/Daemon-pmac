#!/usr/bin/env python3
"""
Database Migration Script for Endpoint Visibility Updates
Updates default visibility settings for funding_sources, risks, and threats endpoints
"""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm.attributes import flag_modified

# Import after path setup
from app.database import Endpoint, get_db


def migrate_endpoint_visibility():
    """Update endpoint default visibility settings"""
    print("🔄 Starting endpoint visibility migration...")

    # Get database session
    db = next(get_db())

    # Endpoints to update (private → public)
    endpoints_to_update = {
        "funding_sources": {
            "old_default": "private",
            "new_default": "public",
            "reason": "Financial transparency and systematic analysis",
        },
        "risks": {
            "old_default": "private",
            "new_default": "public",
            "reason": "Risk management transparency",
        },
        "threats": {
            "old_default": "private",
            "new_default": "public",
            "reason": "Security transparency and systematic analysis",
        },
    }

    updated_count = 0

    try:
        for endpoint_name, config in endpoints_to_update.items():
            print(f"\n📋 Processing {endpoint_name}...")

            # Find the endpoint
            endpoint = db.query(Endpoint).filter(Endpoint.name == endpoint_name).first()

            if not endpoint:
                print(f"  ⚠️  Endpoint '{endpoint_name}' not found - skipping")
                continue

            # Check current schema
            schema = endpoint.schema.copy()  # Make a copy to avoid mutation issues
            current_default = (
                schema.get("meta", {})
                .get("properties", {})
                .get("visibility", {})
                .get("default")
            )

            print(f"  📊 Current default: {current_default}")

            if current_default == config["old_default"]:
                print(
                    f"  🔄 Updating {endpoint_name}: {config['old_default']} → {config['new_default']}"
                )
                print(f"     Reason: {config['reason']}")

                # Update the schema
                if (
                    "meta" in schema
                    and "properties" in schema["meta"]
                    and "visibility" in schema["meta"]["properties"]
                ):
                    schema["meta"]["properties"]["visibility"]["default"] = config[
                        "new_default"
                    ]
                    endpoint.schema = schema

                    # Critical: Tell SQLAlchemy the JSON field changed
                    flag_modified(endpoint, "schema")

                    updated_count += 1
                    print(f"  ✅ Updated successfully")
                else:
                    print(f"  ❌ Unexpected schema structure - skipping")

            elif current_default == config["new_default"]:
                print(f"  ✅ Already up to date ({config['new_default']})")
            else:
                print(f"  ⚠️  Unexpected current default: {current_default} - skipping")

        if updated_count > 0:
            print(f"\n💾 Committing {updated_count} changes to database...")
            db.commit()
            print(f"✅ Migration completed successfully!")

        else:
            print(
                f"\n✅ No updates needed - all endpoints already have correct defaults"
            )

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print("Rolling back changes...")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main migration function"""
    print("=" * 60)
    print("ENDPOINT VISIBILITY MIGRATION")
    print("=" * 60)
    print("This script updates default visibility for:")
    print("- funding_sources: private → public")
    print("- risks: private → public")
    print("- threats: private → public")
    print("=" * 60)

    try:
        migrate_endpoint_visibility()
        print("\n🎉 Migration completed successfully!")

    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

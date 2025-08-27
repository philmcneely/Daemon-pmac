#!/usr/bin/env python3
"""
Fix Endpoint Schemas Script
Updates database endpoint records to use correct content/meta schemas
This script ensures consistency between database and code schemas.
"""

import json

from app.database import Endpoint, SessionLocal

# Content/Meta schema definition
CONTENT_META_SCHEMA = {
    "content": {"type": "string", "required": True, "description": "Markdown content"},
    "meta": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "date": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string"},
            "visibility": {
                "type": "string",
                "enum": ["public", "unlisted", "private"],
                "default": "public",
            },
        },
    },
}

# Resume schema (structured format)
RESUME_SCHEMA = {
    "name": {"type": "string", "required": True},
    "title": {"type": "string"},
    "bio": {"type": "string"},
    "experience": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "position": {"type": "string"},
                "duration": {"type": "string"},
                "description": {"type": "string"},
            },
        },
    },
    "education": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "institution": {"type": "string"},
                "degree": {"type": "string"},
                "year": {"type": "string"},
            },
        },
    },
    "skills": {"type": "array", "items": {"type": "string"}},
}

# Endpoints that should use content/meta schema
CONTENT_META_ENDPOINTS = [
    "about",
    "ideas",
    "skills",
    "favorite_books",
    "hobbies",
    "looking_for",
    "projects",
    "values",
    "quotes",
    "contact_info",
    "events",
    "achievements",
    "goals",
    "learning",
    "problems",
    "personal_story",
    "recommendations",
]


def main():
    """Update endpoint schemas in database to ensure consistency"""
    print("🔧 Fixing endpoint schemas...")

    db = SessionLocal()

    try:
        updated_count = 0

        # Get all endpoints that need fixing
        endpoints = (
            db.query(Endpoint)
            .filter(Endpoint.name.in_(CONTENT_META_ENDPOINTS + ["resume"]))
            .all()
        )

        for endpoint in endpoints:
            try:
                # Determine correct schema
                if endpoint.name == "resume":
                    correct_schema = RESUME_SCHEMA
                elif endpoint.name in CONTENT_META_ENDPOINTS:
                    correct_schema = CONTENT_META_SCHEMA
                else:
                    continue

                # Check if schema is currently a JSON string and needs conversion
                current_schema = endpoint.schema
                if isinstance(current_schema, str):
                    try:
                        # Parse JSON string to dict first
                        current_schema = json.loads(current_schema)
                        print(f"⚠️  {endpoint.name} had string schema, converting...")
                    except json.JSONDecodeError:
                        print(f"❌ {endpoint.name} has invalid JSON schema")
                        continue

                # Update the schema (store as Python dict)
                endpoint.schema = correct_schema
                updated_count += 1
                print(f"✅ Updated {endpoint.name} schema")

            except Exception as e:
                print(f"❌ Error updating {endpoint.name}: {e}")
                continue

        db.commit()
        print(f"\n🎉 Successfully updated schemas for {updated_count} endpoints!")
        print("✅ Database endpoint schemas are now consistent with code")
        print("✅ OpenAPI documentation will show correct schema types")

        # Verify the changes
        print("\n🔍 Verification:")
        verification_endpoints = (
            db.query(Endpoint)
            .filter(Endpoint.name.in_(CONTENT_META_ENDPOINTS + ["resume"]))
            .all()
        )

        for endpoint in verification_endpoints:
            schema_type = type(endpoint.schema).__name__
            if isinstance(endpoint.schema, dict):
                schema_keys = list(endpoint.schema.keys())
            else:
                schema_keys = "N/A"
            print(f"  - {endpoint.name}: {schema_type} with keys {schema_keys}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()

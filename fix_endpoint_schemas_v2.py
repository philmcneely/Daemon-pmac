#!/usr/bin/env python3
"""
Fix endpoint schemas - correct version that stores actual JSON objects
instead of JSON strings in the database.
"""

import json
import sys

from sqlalchemy.orm import Session

# Add the project directory to the path
sys.path.insert(0, "/Users/philmcneely/git/Daemon-pmac")

from app.database import Endpoint, SessionLocal


def fix_endpoint_schemas():
    """Update endpoint schemas from JSON strings to actual JSON objects"""

    db: Session = SessionLocal()

    try:
        # Define the correct content/meta schema as a Python dict (not JSON string)
        content_meta_schema = {
            "content": {
                "type": "string",
                "required": True,
                "description": "Markdown content",
            },
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

        # Define the resume schema (structured format)
        resume_schema = {
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
        content_meta_endpoints = [
            "about",
            "ideas",
            "skills",
            "favorite_books",
            "problems",
            "hobbies",
            "projects",
            "looking_for",
            "skills_matrix",
            "personal_story",
            "goals",
            "values",
            "recommendations",
            "learning",
            "quotes",
            "contact_info",
            "events",
        ]

        updated_count = 0

        # Get all endpoints that need fixing
        endpoints = (
            db.query(Endpoint)
            .filter(Endpoint.name.in_(content_meta_endpoints + ["resume"]))
            .all()
        )

        for endpoint in endpoints:
            try:
                # Check if schema is currently a JSON string
                current_schema = endpoint.schema
                if isinstance(current_schema, str):
                    # If it's a string, try to parse it
                    try:
                        parsed_schema = json.loads(current_schema)
                        print(
                            f"⚠️  {endpoint.name} has string schema, converting to object"
                        )
                        current_schema = parsed_schema
                    except json.JSONDecodeError:
                        print(f"❌ {endpoint.name} has invalid JSON string schema")
                        continue

                # Determine correct schema
                if endpoint.name == "resume":
                    correct_schema = resume_schema
                elif endpoint.name in content_meta_endpoints:
                    correct_schema = content_meta_schema
                else:
                    print(f"⚪ Skipping {endpoint.name} - not in update list")
                    continue

                # Update the schema (store as Python dict, SQLAlchemy will handle JSON conversion)
                endpoint.schema = correct_schema
                updated_count += 1
                print(f"✅ Updated {endpoint.name} schema")

            except Exception as e:
                print(f"❌ Error updating {endpoint.name}: {e}")
                continue

        # Commit all changes
        db.commit()
        print(f"\n🎉 Successfully updated schemas for {updated_count} endpoints!")

        # Verify the changes
        print("\n🔍 Verification:")
        verification_endpoints = (
            db.query(Endpoint)
            .filter(Endpoint.name.in_(content_meta_endpoints + ["resume"]))
            .all()
        )

        for endpoint in verification_endpoints:
            schema_type = type(endpoint.schema).__name__
            print(f"  - {endpoint.name}: schema type = {schema_type}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_endpoint_schemas()

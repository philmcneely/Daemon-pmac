#!/usr/bin/env python3
"""
Script to clean up duplicate data entries for Blackbeard and enable the about endpoint.
"""

import hashlib
import json
import sqlite3

DATABASE_PATH = "daemon.db"


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DATABASE_PATH)


def get_blackbeard_user_id(conn: sqlite3.Connection) -> int:
    """Get Blackbeard's user ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = 'blackbeard'")
    result = cursor.fetchone()
    if not result:
        raise ValueError("Blackbeard user not found")
    return result[0]


def get_data_hash(data: str) -> str:
    """Generate a hash for data content to identify duplicates."""
    # Parse JSON and create a normalized hash
    try:
        parsed = json.loads(data)
        # Sort keys and convert back to string for consistent hashing
        normalized = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
        return hashlib.md5(normalized.encode()).hexdigest()
    except json.JSONDecodeError:
        # Fall back to direct string hash if not valid JSON
        return hashlib.md5(data.encode()).hexdigest()


def cleanup_duplicate_data_entries(conn: sqlite3.Connection, user_id: int):
    """Remove duplicate data entries for a user, keeping the oldest entry."""
    cursor = conn.cursor()

    # Get all data entries for the user with endpoint names
    cursor.execute(
        """
        SELECT de.id, de.endpoint_id, de.data, de.created_at, e.name as endpoint_name
        FROM data_entries de
        JOIN endpoints e ON de.endpoint_id = e.id
        WHERE de.created_by_id = ?
        ORDER BY e.name, de.created_at
    """,
        (user_id,),
    )

    entries = cursor.fetchall()

    # Group by endpoint and track duplicates
    endpoint_data = {}
    duplicates_to_delete = []

    for entry_id, endpoint_id, data, created_at, endpoint_name in entries:
        if endpoint_name not in endpoint_data:
            endpoint_data[endpoint_name] = {}

        data_hash = get_data_hash(data)

        if data_hash in endpoint_data[endpoint_name]:
            # This is a duplicate - mark for deletion
            duplicates_to_delete.append(entry_id)
            print(f"Marking duplicate in {endpoint_name} for deletion: ID {entry_id}")
        else:
            # This is the first occurrence - keep it
            endpoint_data[endpoint_name][data_hash] = {
                "id": entry_id,
                "created_at": created_at,
            }
            print(f"Keeping {endpoint_name} entry: ID {entry_id}")

    # Delete duplicates
    if duplicates_to_delete:
        print(f"\nDeleting {len(duplicates_to_delete)} duplicate entries...")
        placeholders = ",".join(["?"] * len(duplicates_to_delete))
        cursor.execute(
            f"DELETE FROM data_entries WHERE id IN ({placeholders})",
            duplicates_to_delete,
        )
        print(f"Deleted {cursor.rowcount} duplicate entries")
    else:
        print("No duplicates found to delete")


def fix_meta_fields(conn: sqlite3.Connection, user_id: int):
    """Remove status field from meta and ensure visibility is set correctly."""
    cursor = conn.cursor()

    # Update all data entries to remove status field and set visibility to public
    cursor.execute(
        """
        UPDATE data_entries
        SET data = json_set(
            json_remove(data, '$.meta.status'),
            '$.meta.visibility', 'public'
        )
        WHERE created_by_id = ?
        AND json_extract(data, '$.meta') IS NOT NULL
    """,
        (user_id,),
    )

    if cursor.rowcount > 0:
        print(
            f"Fixed meta fields for {cursor.rowcount} records (removed status, set visibility to public)"
        )
    else:
        print("No records with meta fields found to update")


def show_final_counts(conn: sqlite3.Connection, user_id: int):
    """Show final counts after cleanup."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT e.name, COUNT(*) as count
        FROM data_entries de
        JOIN endpoints e ON de.endpoint_id = e.id
        WHERE de.created_by_id = ?
        GROUP BY e.name
        ORDER BY count DESC
    """,
        (user_id,),
    )

    print("\nFinal data counts after cleanup:")
    for endpoint_name, count in cursor.fetchall():
        print(f"  {endpoint_name}: {count}")


def main():
    """Main cleanup function."""
    try:
        conn = get_db_connection()
        user_id = get_blackbeard_user_id(conn)

        print(f"Cleaning up data for Blackbeard (user_id: {user_id})")
        print("=" * 50)

        # Show initial counts
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.name, COUNT(*) as count
            FROM data_entries de
            JOIN endpoints e ON de.endpoint_id = e.id
            WHERE de.created_by_id = ?
            GROUP BY e.name
            ORDER BY count DESC
        """,
            (user_id,),
        )

        print("Initial data counts:")
        for endpoint_name, count in cursor.fetchall():
            print(f"  {endpoint_name}: {count}")

        print("\nCleaning up duplicates...")
        cleanup_duplicate_data_entries(conn, user_id)

        print("\nFixing meta fields (removing status, setting visibility)...")
        fix_meta_fields(conn, user_id)

        # Commit changes
        conn.commit()

        # Show final counts
        show_final_counts(conn, user_id)

        print("\nCleanup completed successfully!")

    except Exception as e:
        print(f"Error during cleanup: {e}")
        if "conn" in locals():
            conn.rollback()
        raise
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()

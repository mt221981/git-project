"""Migration script to add featured image fields to articles table."""

import sqlite3
import sys


def migrate():
    """Add featured image columns to articles table."""
    conn = sqlite3.connect('legal_content.db')
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(articles)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    columns_to_add = [
        ("featured_image_url", "VARCHAR(500)"),
        ("featured_image_wp_id", "INTEGER"),
        ("featured_image_credit", "VARCHAR(200)"),
    ]

    for column_name, column_type in columns_to_add:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")
                print(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"Column {column_name} already exists or error: {e}")
        else:
            print(f"Column {column_name} already exists, skipping")

    conn.commit()
    conn.close()
    print("Migration completed successfully!")


if __name__ == "__main__":
    migrate()

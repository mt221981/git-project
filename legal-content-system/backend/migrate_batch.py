"""
Migration script to add batch support.

This script:
1. Creates the 'batches' table
2. Adds 'batch_id' column to 'verdicts' table

Run this script once before starting the server after updating the models.
"""

import sqlite3
import os

# Get database path from environment or use default
db_path = os.environ.get('DATABASE_PATH', './legal_content.db')

print(f"Migrating database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if batches table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='batches'")
    if cursor.fetchone() is None:
        print("Creating 'batches' table...")
        cursor.execute('''
            CREATE TABLE batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200),
                source_folder VARCHAR(500),
                total_files INTEGER DEFAULT 0 NOT NULL,
                processed_files INTEGER DEFAULT 0 NOT NULL,
                successful_files INTEGER DEFAULT 0 NOT NULL,
                failed_files INTEGER DEFAULT 0 NOT NULL,
                skipped_files INTEGER DEFAULT 0 NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                error_log JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                started_at DATETIME,
                completed_at DATETIME
            )
        ''')
        cursor.execute('CREATE INDEX ix_batches_id ON batches (id)')
        cursor.execute('CREATE INDEX ix_batches_status ON batches (status)')
        print("Created 'batches' table successfully")
    else:
        print("'batches' table already exists")

    # Check if batch_id column exists in verdicts
    cursor.execute("PRAGMA table_info(verdicts)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'batch_id' not in columns:
        print("Adding 'batch_id' column to 'verdicts' table...")
        cursor.execute('ALTER TABLE verdicts ADD COLUMN batch_id INTEGER REFERENCES batches(id)')
        cursor.execute('CREATE INDEX ix_verdicts_batch_id ON verdicts (batch_id)')
        print("Added 'batch_id' column successfully")
    else:
        print("'batch_id' column already exists in 'verdicts' table")

    conn.commit()
    print("Migration completed successfully!")

except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
    raise

finally:
    conn.close()

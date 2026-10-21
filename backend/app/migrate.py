import sqlite3
from pathlib import Path
from sqlalchemy import inspect
from backend.app.database import engine, Base
from backend.app.models import *

def migrate():
    print("Running ExamLoop database migration...")
    # 1. Create all new tables (SyllabusUnit, Topic, etc.)
    Base.metadata.create_all(bind=engine)
    print("[OK] Schema tables initialized/verified.")

    # 2. For SQLite, add any missing columns safely
    db_path = Path("backend/examloop.db")
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        def add_column_if_missing(table, column, col_type, default=None):
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            if column not in columns:
                default_clause = f" DEFAULT {default}" if default is not None else ""
                alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
                print(f"Adding column {table}.{column}...")
                cursor.execute(alter_sql)

        # documents
        add_column_if_missing("documents", "document_role", "VARCHAR(32)", "'notes'")

        # topics
        add_column_if_missing("topics", "is_deleted", "BOOLEAN", "0")

        # questions
        add_column_if_missing("questions", "subjective_subtype", "VARCHAR(32)", "NULL")
        add_column_if_missing("questions", "source_mode", "VARCHAR(32)", "'reference_grounded'")
        add_column_if_missing("questions", "topic_ids", "JSON", "'[]'")

        # tests
        add_column_if_missing("tests", "source_mode", "VARCHAR(32)", "'reference_grounded'")
        add_column_if_missing("tests", "target_topic_ids", "JSON", "'[]'")
        add_column_if_missing("tests", "test_config", "JSON", "'{}'")
        add_column_if_missing("tests", "total_raw_marks", "FLOAT", "10.0")
        add_column_if_missing("tests", "normalized_max_score", "FLOAT", "10.0")

        # attempts
        add_column_if_missing("attempts", "raw_score", "FLOAT", "0.0")
        add_column_if_missing("attempts", "max_raw_marks", "FLOAT", "0.0")
        add_column_if_missing("attempts", "normalized_score_10", "FLOAT", "0.0")

        # evaluations
        add_column_if_missing("evaluations", "subjective_subtype", "VARCHAR(32)", "NULL")
        add_column_if_missing("evaluations", "normalized_score_10", "FLOAT", "NULL")

        conn.commit()
        conn.close()
        print("[OK] SQLite columns safely updated.")

if __name__ == "__main__":
    migrate()

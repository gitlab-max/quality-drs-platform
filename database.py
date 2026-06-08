import sqlite3
import os

DB_PATH = "database/drs.db"


def get_connection():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    os.makedirs(
        "database",
        exist_ok=True
    )

    conn = get_connection()

    cur = conn.cursor()

    # =====================================
    # PROJECTS
    # =====================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        mode TEXT DEFAULT 'csv',

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =====================================
    # DRS MODELS
    # =====================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drs_models(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        project_id INTEGER,

        drs_json TEXT,

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(project_id)
        REFERENCES projects(id)

    )
    """)

    # =====================================
    # PARAMETERS
    # =====================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS parameters(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        project_id INTEGER,

        name TEXT,

        min_value REAL,

        max_value REAL,

        FOREIGN KEY(project_id)
        REFERENCES projects(id)

    )
    """)

    # =====================================
    # SAMPLES
    # =====================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS samples(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        project_id INTEGER,

        sample_json TEXT,

        prediction TEXT,

        drs_score REAL,

        used_for_drs INTEGER DEFAULT 0,

        created_at TEXT,

        FOREIGN KEY(project_id)
        REFERENCES projects(id)

    )
    """)

    conn.commit()

    conn.close()


if __name__ == "__main__":

    init_db()

    print(
        "Database created successfully."
    )
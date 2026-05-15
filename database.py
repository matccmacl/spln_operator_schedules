import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_PATH = "schedules.db"

def get_db_size():
    """Returns the size of the database file in human-readable format."""
    if not os.path.exists(DB_PATH):
        return "0 KB"
    size_bytes = os.path.getsize(DB_PATH)
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def init_db():
    """Initializes the SQLite database with required tables."""
    with sqlite3.connect(DB_PATH) as conn:
        # Table for processed movements (standardized schema)
        # We use the exact column names from the processors for easy pandas integration
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                "FILENAME" TEXT,
                "DATE TIME UTC" DATETIME,
                "DATE TIME LOCAL" DATETIME,
                "AIRLINE" TEXT,
                "FLT NUMBER" TEXT,
                "REG" TEXT,
                "FROM" TEXT,
                "TO" TEXT,
                "DIRECTION" TEXT
            )
        """)
        
        # Migration: Ensure FILENAME column exists in existing movements table
        try:
            conn.execute('ALTER TABLE movements ADD COLUMN "FILENAME" TEXT')
        except sqlite3.OperationalError:
            pass # Already exists
        
        # Table for locally tracking processed filenames
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table for Aircraft Registrations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                SSR TEXT,
                REG TEXT UNIQUE,
                OPERATOR TEXT,
                "AC TYPE" TEXT,
                MTOW INTEGER,
                SPECIES TEXT
            )
        """)
    print("Database initialized.")

def save_movements(df):
    """Saves a dataframe of movements to the database."""
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("movements", conn, if_exists="append", index=False)

def log_file_local(filename):
    """Logs a filename to the local processed_files table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO processed_files (filename) VALUES (?)", (filename,))

def check_file_processed_local(filename):
    """Checks if a file has already been processed locally."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_files WHERE filename = ?", (filename,))
        return cursor.fetchone() is not None

def get_all_movements():
    """Reads all movements from the database as a pandas DataFrame."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM movements", conn)

def get_all_filenames():
    """Reads all processed filenames from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM processed_files ORDER BY timestamp DESC", conn)

def get_all_registrations():
    """Reads all registrations from the database."""
    init_db() # Ensure table exists
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM registrations", conn)

def seed_registrations(csv_path="scratch/spln_reg.csv"):
    """Seeds the registrations table from a CSV file."""
    init_db() # Ensure table exists
    if not os.path.exists(csv_path):
        return False, f"CSV file not found at {csv_path}"
    
    try:
        df = pd.read_csv(csv_path)
        # 1. Clean REG: replace 8Q with 8Q- if not already present
        if 'REG' in df.columns:
            df['REG'] = df['REG'].astype(str).str.replace('8Q', '8Q-', regex=False).str.replace('8Q--', '8Q-', regex=False)
            
        # 2. Clean MTOW: remove commas and convert to int
        if 'MTOW' in df.columns:
            df['MTOW'] = df['MTOW'].astype(str).str.replace(',', '').str.split('.').str[0]
            df['MTOW'] = pd.to_numeric(df['MTOW'], errors='coerce').fillna(0).astype(int)
        
        with sqlite3.connect(DB_PATH) as conn:
            # Clear existing data before seeding to avoid UNIQUE constraint errors on REG
            conn.execute("DELETE FROM registrations")
            df.to_sql("registrations", conn, if_exists="append", index=False)
        return True, f"Successfully seeded {len(df)} registrations."
    except Exception as e:
        return False, str(e)

def ingest_bulk_csv(csv_path):
    """Ingests a large CSV file into the movements table."""
    if not os.path.exists(csv_path):
        return False, f"File not found: {csv_path}"
    
    filename = os.path.basename(csv_path)
    
    try:
        # Check if already processed
        with sqlite3.connect(DB_PATH) as conn:
            exists = conn.execute("SELECT 1 FROM processed_files WHERE filename = ?", (filename,)).fetchone()
            if exists:
                return False, f"File `{filename}` has already been processed."
        
        # Read and Normalize
        df = pd.read_csv(csv_path)
        df['FILENAME'] = filename
        
        if 'REG' in df.columns:
            df['REG'] = df['REG'].astype(str).str.replace('8Q', '8Q-', regex=False).str.replace('8Q--', '8Q-', regex=False)
            
        # Standardize Timestamps for SQLite compatibility
        for col in ['DATE TIME UTC', 'DATE TIME LOCAL']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        # Batch Insert
        with sqlite3.connect(DB_PATH) as conn:
            df.to_sql("movements", conn, if_exists="append", index=False, chunksize=10000)
            log_file_local(filename)
            
        return True, f"Successfully ingested {len(df):,} records from `{filename}`."
    except Exception as e:
        return False, str(e)

def delete_file(filename):
    """Deletes a file record and all its associated movements."""
    with sqlite3.connect(DB_PATH) as conn:
        # 1. Delete associated movements
        conn.execute('DELETE FROM movements WHERE "FILENAME" = ?', (filename,))
        # 2. Delete the file record
        conn.execute("DELETE FROM processed_files WHERE filename = ?", (filename,))

def clear_data():
    """Wipes all data from the database (for testing)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM movements")
        conn.execute("DELETE FROM processed_files")

import os
import sqlite3
import pandas as pd
from datetime import datetime
from src.config import DB_PATH
from src.database.connection import get_connection

def get_db_size() -> str:
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
    with get_connection() as conn:
        # Table for processed movements (standardized schema)
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

def save_movements(df: pd.DataFrame):
    """Saves a dataframe of movements to the database."""
    with get_connection() as conn:
        df.to_sql("movements", conn, if_exists="append", index=False)

def log_file_local(filename: str):
    """Logs a filename to the local processed_files table."""
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO processed_files (filename) VALUES (?)", (filename,))

def check_file_processed_local(filename: str) -> bool:
    """Checks if a file has already been processed locally."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_files WHERE filename = ?", (filename,))
        return cursor.fetchone() is not None

def get_all_movements() -> pd.DataFrame:
    """Reads all movements from the database as a pandas DataFrame."""
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM movements", conn)

def get_all_filenames() -> pd.DataFrame:
    """Reads all processed filenames from the database."""
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM processed_files ORDER BY timestamp DESC", conn)

def get_all_registrations() -> pd.DataFrame:
    """Reads all registrations from the database."""
    init_db() # Ensure table exists
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM registrations", conn)

def seed_registrations(csv_path: str = "scratch/spln_reg.csv") -> tuple[bool, str]:
    """Seeds the registrations table from a CSV file."""
    init_db() # Ensure table exists
    if not os.path.exists(csv_path):
        return False, f"CSV file not found at {csv_path}"
    
    try:
        df = pd.read_csv(csv_path)
        # Clean REG: replace 8Q with 8Q- if not already present
        if 'REG' in df.columns:
            df['REG'] = df['REG'].astype(str).str.replace('8Q', '8Q-', regex=False).str.replace('8Q--', '8Q-', regex=False)
            
        # Clean MTOW: remove commas and convert to int
        if 'MTOW' in df.columns:
            df['MTOW'] = df['MTOW'].astype(str).str.replace(',', '').str.split('.').str[0]
            df['MTOW'] = pd.to_numeric(df['MTOW'], errors='coerce').fillna(0).astype(int)
        
        with get_connection() as conn:
            # Clear existing data before seeding to avoid UNIQUE constraint errors on REG
            conn.execute("DELETE FROM registrations")
            df.to_sql("registrations", conn, if_exists="append", index=False)
        return True, f"Successfully seeded {len(df)} registrations."
    except Exception as e:
        return False, str(e)

def ingest_bulk_csv(csv_path: str) -> tuple[bool, str]:
    """Ingests a large CSV file into the movements table inside a single transaction."""
    if not os.path.exists(csv_path):
        return False, f"File not found: {csv_path}"
    
    filename = os.path.basename(csv_path)
    
    try:
        # Check if already processed
        with get_connection() as conn:
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

        # Batch Insert in a single transaction
        with get_connection() as conn:
            df.to_sql("movements", conn, if_exists="append", index=False, chunksize=10000)
            conn.execute("INSERT OR IGNORE INTO processed_files (filename) VALUES (?)", (filename,))
            
        return True, f"Successfully ingested {len(df):,} records from `{filename}`."
    except Exception as e:
        return False, str(e)

def delete_file(filename: str):
    """Deletes a file record and all its associated movements in a unified transaction."""
    with get_connection() as conn:
        # Delete associated movements
        conn.execute('DELETE FROM movements WHERE "FILENAME" = ?', (filename,))
        # Delete the file record
        conn.execute("DELETE FROM processed_files WHERE filename = ?", (filename,))

def clear_data():
    """Wipes all data from the database (for testing) in a transaction."""
    with get_connection() as conn:
        conn.execute("DELETE FROM movements")
        conn.execute("DELETE FROM processed_files")

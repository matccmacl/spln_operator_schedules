import os
import sys
import pandas as pd
import pytest

# Ensure the project root is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config

# Mock the database path to use a temporary file for tests
TEST_DB_PATH = "test_schedules.db"
src.config.DB_PATH = TEST_DB_PATH

from src.database import (
    get_connection,
    init_db,
    save_movements,
    log_file_local,
    check_file_processed_local,
    get_all_movements,
    get_all_filenames,
    get_all_registrations,
    delete_file,
    clear_data
)

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Fixture to ensure a clean test database before and after each test."""
    # Ensure any existing test DB is removed
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass
            
    # Initialize the test database
    init_db()
    
    yield
    
    # Cleanup after test
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
            # Clean up WAL files if any exist
            for ext in ["-wal", "-shm"]:
                if os.path.exists(TEST_DB_PATH + ext):
                    os.remove(TEST_DB_PATH + ext)
        except OSError:
            pass

def test_database_init():
    """Verify that tables are created properly during database initialization."""
    with get_connection() as conn:
        # Check that table names exist in sqlite_master
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "movements" in tables
        assert "processed_files" in tables
        assert "registrations" in tables

def test_save_and_retrieve_movements():
    """Verify that movements can be saved and read back as a DataFrame."""
    # Build a standardized mock movements DataFrame
    df = pd.DataFrame([
        {
            "FILENAME": "test_schedule.xlsx",
            "DATE TIME UTC": "2026-05-22 05:00:00",
            "DATE TIME LOCAL": "2026-05-22 10:00:00",
            "AIRLINE": "TEST AIRLINE",
            "FLT NUMBER": "TS101",
            "REG": "8Q-TST",
            "FROM": "MLE",
            "TO": "DRV",
            "DIRECTION": "TAKEOFF"
        }
    ])
    
    save_movements(df)
    
    retrieved_df = get_all_movements()
    assert len(retrieved_df) == 1
    assert retrieved_df["AIRLINE"].iloc[0] == "TEST AIRLINE"
    assert retrieved_df["FLT NUMBER"].iloc[0] == "TS101"
    assert retrieved_df["REG"].iloc[0] == "8Q-TST"
    assert retrieved_df["DIRECTION"].iloc[0] == "TAKEOFF"

def test_processed_files_logging():
    """Verify that processed files are logged and checked correctly."""
    filename = "test_schedule_file.xlsx"
    
    # Assert not processed initially
    assert not check_file_processed_local(filename)
    
    # Log the file
    log_file_local(filename)
    
    # Assert it is now processed
    assert check_file_processed_local(filename)
    
    # Verify it is retrieved in filenames list
    filenames_df = get_all_filenames()
    assert len(filenames_df) == 1
    assert filenames_df["filename"].iloc[0] == filename

def test_delete_file_and_movements():
    """Verify that deleting a file also transactionally clears its associated movements."""
    filename = "target_delete_schedule.xlsx"
    df = pd.DataFrame([
        {
            "FILENAME": filename,
            "DATE TIME UTC": "2026-05-22 05:00:00",
            "DATE TIME LOCAL": "2026-05-22 10:00:00",
            "AIRLINE": "TEST AIRLINE",
            "FLT NUMBER": "TS101",
            "REG": "8Q-TST",
            "FROM": "MLE",
            "TO": "DRV",
            "DIRECTION": "TAKEOFF"
        },
        {
            "FILENAME": "keep_this_schedule.xlsx",
            "DATE TIME UTC": "2026-05-22 06:00:00",
            "DATE TIME LOCAL": "2026-05-22 11:00:00",
            "AIRLINE": "TEST AIRLINE",
            "FLT NUMBER": "TS102",
            "REG": "8Q-TST",
            "FROM": "DRV",
            "TO": "MLE",
            "DIRECTION": "LANDING"
        }
    ])
    
    save_movements(df)
    log_file_local(filename)
    log_file_local("keep_this_schedule.xlsx")
    
    # Delete the target file
    delete_file(filename)
    
    # Assert target file no longer marked as processed
    assert not check_file_processed_local(filename)
    assert check_file_processed_local("keep_this_schedule.xlsx")
    
    # Assert movements associated with target file are deleted
    remaining_movements = get_all_movements()
    assert len(remaining_movements) == 1
    assert remaining_movements["FILENAME"].iloc[0] == "keep_this_schedule.xlsx"

def test_clear_data():
    """Verify that clear_data wipes all records from movements and processed_files tables."""
    df = pd.DataFrame([
        {
            "FILENAME": "some_schedule.xlsx",
            "DATE TIME UTC": "2026-05-22 05:00:00",
            "DATE TIME LOCAL": "2026-05-22 10:00:00",
            "AIRLINE": "TEST AIRLINE",
            "FLT NUMBER": "TS101",
            "REG": "8Q-TST",
            "FROM": "MLE",
            "TO": "DRV",
            "DIRECTION": "TAKEOFF"
        }
    ])
    save_movements(df)
    log_file_local("some_schedule.xlsx")
    
    # Wipe data
    clear_data()
    
    assert get_all_movements().empty
    assert get_all_filenames().empty

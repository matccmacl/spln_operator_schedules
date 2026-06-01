import os
import sys
import pandas as pd
import pytest

# Ensure the project root is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.processors import process_file
from src.processors.maldivian import MaldivianProcessor
from src.processors.villa import VillaProcessor
from src.processors.tma import TmaProcessor
from src.processors.manta import MantaProcessor

# Standardized columns expected from every processor
EXPECTED_COLUMNS = [
    'DATE TIME UTC',
    'DATE TIME LOCAL',
    'AIRLINE',
    'FLT NUMBER',
    'REG',
    'FROM',
    'TO',
    'DIRECTION'
]

def check_standard_schema(df, airline_name):
    """Helper assertions to check schema compliance and data integrity."""
    assert df is not None, "DataFrame is None"
    assert not df.empty, "DataFrame is empty"
    
    # Assert columns match exactly
    assert list(df.columns) == EXPECTED_COLUMNS, f"Columns do not match standard schema. Got: {list(df.columns)}"
    
    # Assert airline name is correct
    assert (df['AIRLINE'] == airline_name).all(), f"AIRLINE column does not contain all '{airline_name}' values."
    
    # Assert directions are strictly TAKEOFF or LANDING
    assert df['DIRECTION'].isin(['TAKEOFF', 'LANDING']).all(), "DIRECTION column contains invalid values."
    
    # Assert date-time fields are parsed successfully
    assert pd.api.types.is_datetime64_any_dtype(df['DATE TIME UTC']), "DATE TIME UTC is not datetime-like"
    assert pd.api.types.is_datetime64_any_dtype(df['DATE TIME LOCAL']), "DATE TIME LOCAL is not datetime-like"

def get_fixture_path(filename):
    """Retrieve absolute path to a schedule fixture in airline_schedules/."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "airline_schedules", filename))

def test_maldivian_excel():
    filename = "_MALDIVIAN_Aircraft Allocation for 14th May 2026  ISSUE 1.pdf.xlsx"
    filepath = get_fixture_path(filename)
    assert os.path.exists(filepath), f"Fixture not found: {filepath}"
    
    with open(filepath, "rb") as f:
        df, error = process_file(f, filename)
        
    assert error is None, f"Maldivian Excel processing failed: {error}"
    check_standard_schema(df, "MALDIVIAN")

def test_maldivian_pdf():
    filename = "Aircraft Allocation for 25TH Jan 2026  ISSUE 2.pdf"
    filepath = get_fixture_path(filename)
    assert os.path.exists(filepath), f"Fixture not found: {filepath}"
    
    with open(filepath, "rb") as f:
        df, error = process_file(f, filename)
        
    assert error is None, f"Maldivian PDF processing failed: {error}"
    check_standard_schema(df, "MALDIVIAN")

def test_villa_pdf():
    filename = "villa_air_DHC6  SCHEDULE  09-02-2026.pdf"
    filepath = get_fixture_path(filename)
    assert os.path.exists(filepath), f"Fixture not found: {filepath}"
    
    with open(filepath, "rb") as f:
        df, error = process_file(f, filename)
        
    assert error is None, f"Villa PDF processing failed: {error}"
    check_standard_schema(df, "VILLA AIR")

def test_tma_excel():
    filename = "_TMA_2026-05-05_E-01.03.14.Future TMA Flight Movement for MACL_R2.xlsx"
    filepath = get_fixture_path(filename)
    assert os.path.exists(filepath), f"Fixture not found: {filepath}"
    
    with open(filepath, "rb") as f:
        df, error = process_file(f, filename)
        
    assert error is None, f"TMA Excel processing failed: {error}"
    check_standard_schema(df, "TMA")

def test_manta_excel():
    filename = "_MANTA_2026-05-05_DHC-6 Flight Schedule.xlsx"
    filepath = get_fixture_path(filename)
    assert os.path.exists(filepath), f"Fixture not found: {filepath}"
    
    with open(filepath, "rb") as f:
        df, error = process_file(f, filename)
        
    assert error is None, f"Manta Excel processing failed: {error}"
    check_standard_schema(df, "MANTA AIR")

def test_unknown_operator():
    filename = "UNKNOWN_OPERATOR_SCHEDULE_2026.xlsx"
    # Create fake bytes
    df, error = process_file(None, filename)
    assert df is None, "Unknown operator should return None DataFrame"
    assert "Unknown operator" in error, f"Unexpected error message: {error}"

def test_maldivian_unsupported_format():
    filename = "Aircraft Allocation for 25TH Jan 2026.docx"
    df, error = process_file(None, filename)
    assert df is None, "Unsupported format should return None DataFrame"
    assert "Unsupported format for Maldivian" in error, f"Unexpected error message: {error}"

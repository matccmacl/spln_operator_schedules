import pandas as pd
import numpy as np
import io
import sys
import os

# Add project root to path to import processors
sys.path.append(os.getcwd())
from processors import _process_maldivian_excel

def test_maldivian_excel():
    # Mock CSV data with leading empty columns and COMPWASH
    mock_csv = """
,,,,,,,
,,,,,,,
,,FLT NUMBER,REG,FROM,TO,STD,STA
,,Q2 123,8Q-IAK,MLE,DRV,900.0,945
,,Q2 124,8Q-IAK,DRV,MLE,1000,1045
,,0:00 COMPWASH,,MLE,MLE,1100,1200
,,Q2 125,8Q-IAL,MLE,IFU,1200,1245
"""
    file_stream = io.StringIO(mock_csv.strip())
    filename = "Aircraft Allocation for 25TH Mar 2026.csv"
    
    df, error = _process_maldivian_excel(file_stream, filename)
    
    if error:
        print(f"Error: {error}")
        return

    print("--- Processed Data ---")
    print(df)
    
    # Assertions
    assert "COMPWASH" not in df["FLT NUMBER"].values
    assert len(df) == 3 # Q2 123 (Takeoff), Q2 124 (Landing), Q2 125 (Takeoff)
    # Let's count movements:
    # Q2 123: MLE -> DRV (Takeoff)
    # Q2 124: DRV -> MLE (Landing)
    # Q2 125: MLE -> IFU (Takeoff)
    # Total 3 movements.
    
    # Wait, my mock data:
    # Q2 123 (MLE->DRV) -> Takeoff
    # Q2 124 (DRV->MLE) -> Landing
    # Q2 125 (MLE->IFU) -> Takeoff
    # COMPWASH should be filtered out.
    
    print(f"\nRow count: {len(df)}")
    assert len(df) == 3
    assert all(df["AIRLINE"] == "MALDIVIAN")
    assert df["DATE TIME LOCAL"].iloc[0].year == 2026
    
    print("\nVerification Successful!")

if __name__ == "__main__":
    test_maldivian_excel()

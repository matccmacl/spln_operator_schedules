import pandas as pd

def test_column_alignment():
    # Mock master log with specific order
    master_df = pd.DataFrame(columns=['DATE TIME UTC', 'AIRLINE', 'FLT NUMBER', 'DIRECTION', 'REG'])
    
    # Mock extracted data with different order and one extra column
    df_extracted = pd.DataFrame({
        'AIRLINE': ['MALDIVIAN'],
        'DATE TIME UTC': [pd.Timestamp('2026-03-25 09:00')],
        'FLT NUMBER': ['Q2 123'],
        'EXTRA': ['Noise'],
        'REG': ['8Q-IAK'],
        'DIRECTION': ['TAKEOFF']
    })
    
    print("Master Columns:", master_df.columns.tolist())
    print("Extracted Columns (Before):", df_extracted.columns.tolist())
    
    # Alignment Logic from main.py
    target_columns = master_df.columns.tolist()
    for col in df_extracted.columns:
        if col not in target_columns:
            target_columns.append(col)
            
    for col in target_columns:
        if col not in df_extracted.columns:
            df_extracted[col] = None
            
    df_aligned = df_extracted[target_columns]
    
    print("Aligned Columns (After):", df_aligned.columns.tolist())
    
    # Assertions
    assert df_aligned.columns.tolist()[:5] == master_df.columns.tolist()
    assert 'EXTRA' in df_aligned.columns
    assert df_aligned.iloc[0]['AIRLINE'] == 'MALDIVIAN'
    
    print("\nColumn Alignment Verification Successful!")

if __name__ == "__main__":
    test_column_alignment()

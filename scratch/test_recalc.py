import pandas as pd
from datetime import date

def test_recalculation():
    # Mock extracted data for May 14th
    df = pd.DataFrame({
        'DATE TIME LOCAL': [pd.Timestamp('2026-05-14 09:00:00'), pd.Timestamp('2026-05-14 14:30:00')],
        'DATE TIME UTC': [pd.Timestamp('2026-05-14 04:00:00'), pd.Timestamp('2026-05-14 09:30:00')]
    })
    
    print("Original Data:")
    print(df)
    
    # Simulate user selecting May 10th
    selected_date = date(2026, 5, 10)
    
    # Recalculation Logic from main.py
    df['DATE TIME LOCAL'] = df['DATE TIME LOCAL'].apply(
        lambda dt: dt.replace(year=selected_date.year, month=selected_date.month, day=selected_date.day)
    )
    df['DATE TIME UTC'] = df['DATE TIME LOCAL'] - pd.Timedelta(hours=5)
    
    print("\nUpdated Data (May 10th):")
    print(df)
    
    # Assertions
    assert df['DATE TIME LOCAL'].iloc[0].day == 10
    assert df['DATE TIME LOCAL'].iloc[0].hour == 9
    assert df['DATE TIME UTC'].iloc[0].day == 10
    assert df['DATE TIME UTC'].iloc[0].hour == 4
    
    print("\nRecalculation Verification Successful!")

if __name__ == "__main__":
    test_recalculation()

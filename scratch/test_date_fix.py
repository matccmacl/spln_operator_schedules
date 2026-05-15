import re
import pandas as pd

def test_date_extraction():
    filenames = [
        "_MALDIVIAN_Aircraft Allocation for 14th May 2026 ISSUE 1.pdf.xlsx",
        "Aircraft Allocation for 25TH Jan 2026 ISSUE 2",
        "Aircraft Allocation for 1st Mar 2026"
    ]
    
    # Pattern from processors.py
    date_pattern = r"(?i)(\d{1,2})[a-z]{2}\s([a-z]+)\s(\d{4})"
    
    print(f"Testing pattern: {date_pattern}\n")
    
    for filename in filenames:
        match = re.search(date_pattern, filename)
        if match:
            clean_date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
            date_object = pd.to_datetime(clean_date_str)
            print(f"Filename: {filename}")
            print(f"✅ Extracted Date: {date_object.strftime('%Y-%m-%d')}\n")
            
            if "14th May" in filename:
                assert date_object.day == 14
        else:
            print(f"Filename: {filename}")
            print(f"❌ Match Failed\n")
            assert False, f"Failed to match {filename}"

    print("Verification Successful!")

if __name__ == "__main__":
    test_date_extraction()

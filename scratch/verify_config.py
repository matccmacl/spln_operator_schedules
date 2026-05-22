import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

def verify_config_switch():
    print("Checking main.py for configuration variables...")
    with open("main.py", "r") as f:
        content = f.read()
    
    # Check imports
    if "TEST_SHEET_URL" in content and "SHEET_URL" not in content.split("from config import")[1].split("\n")[0]:
        print("SUCCESS - Import correctly updated to use TEST_SHEET_URL and remove SHEET_URL.")
    else:
        print("FAILED - Import check failed.")
        
    # Check usages
    usage_counts = {
        "TEST_SHEET_URL": content.count("TEST_SHEET_URL"),
        "TEST_UPLOAD_SHEET": content.count("TEST_UPLOAD_SHEET"),
        "LOG_WORKSHEET": content.count("LOG_WORKSHEET"),
        "SCHEDULES_SHEET_URL": content.count("SCHEDULES_SHEET_URL")
    }
    
    print(f"\nUsage Counts:")
    for var, count in usage_counts.items():
        print(f"  {var}: {count}")
    
    if usage_counts["TEST_SHEET_URL"] > 1:
        print("\nSUCCESS - TEST_SHEET_URL is being used in multiple locations.")
    else:
        print("\nFAILED - TEST_SHEET_URL usage check failed.")

if __name__ == "__main__":
    verify_config_switch()

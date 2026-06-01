import pandas as pd
from src.processors.villa import VillaProcessor
from src.processors.maldivian import MaldivianProcessor
from src.processors.tma import TmaProcessor
from src.processors.manta import MantaProcessor

# Registry mapping keywords in filenames to their respective strategy processor
PROCESSOR_REGISTRY = [
    ("VILLA", VillaProcessor()),
    ("AIRCRAFT ALLOCATION", MaldivianProcessor()),
    ("MALDIVIAN", MaldivianProcessor()),
    ("TMA", TmaProcessor()),
    ("MANTA", MantaProcessor()),
]

def process_file(file, filename) -> tuple[pd.DataFrame | None, str | None]:
    """
    Dispatcher using the Strategy and Registry patterns to select the appropriate 
    ETL parser strategy based on the schedule's filename.
    
    Returns (DataFrame, ErrorMessage).
    """
    filename_upper = filename.upper()
    
    for keyword, processor in PROCESSOR_REGISTRY:
        if keyword in filename_upper:
            # Replicate original check for unsupported formats under Maldivian keyword
            if keyword in ["AIRCRAFT ALLOCATION", "MALDIVIAN"]:
                if not filename_upper.endswith((".PDF", ".XLSX", ".XLS", ".CSV")):
                    return None, f"Unsupported format for Maldivian: {filename}"
            return processor.process(file, filename)
            
    return None, f"Unknown operator for file: {filename}"

from src.processors import process_file

# --- LEGACY SUPPORT FOR SCRATCH & TESTING SCRIPTS ---
from src.processors.maldivian import MaldivianProcessor
from src.processors.villa import VillaProcessor
from src.processors.tma import TmaProcessor
from src.processors.manta import MantaProcessor

def _process_maldivian_excel(file, filename):
    return MaldivianProcessor()._process_excel(file, filename)

def _process_maldivian_pdf(file, filename):
    return MaldivianProcessor()._process_pdf(file, filename)

def _process_villa_air(file, filename):
    return VillaProcessor().process(file, filename)

def _process_tma_excel(file, filename):
    return TmaProcessor().process(file, filename)

def _process_manta_excel(file, filename):
    return MantaProcessor().process(file, filename)

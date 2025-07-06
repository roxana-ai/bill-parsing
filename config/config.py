import os

# Base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Input image path example (optional if hardcoding in main.py)
IMAGE_DIR = os.path.join(BASE_DIR, "data", "images")

# Tesseract settings

TESSERACT_PATH = "/opt/homebrew/bin/tesseract" 
TESSERACT_LANG = "ron"  # Romanian language
TESSERACT_PSM = "6"  # Assume a block of text
# Optional: if Tesseract is not in your system PATH
# TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Future use: regex patterns for field extraction
EXTRACTION_PATTERNS = {
    # Matches TOTAL, TOTALA, PTOTAL, etc. with comma or dot as decimal separator
    "total": r"(?:TOTAL(?:A)?|PTOTAL)[^\d]{0,10}([\d.,]+)",
    # Matches TVA (VAT) with comma or dot
    "tva": r"TVA[^\d]{0,10}([\d.,]+)",
    # Matches date in Romanian format (dd.mm.yyyy or dd/mm/yyyy)
    "date": r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
    # Matches invoice number if present
    "invoice_number": r"NR[^\w]?(\w+)"
}
# Optional: logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple"
        }
    },
    "loggers": {
        "bill_parser": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False
        }
    }
}
import sys
import logging
from pathlib import Path
import argparse

def parse_args(description_arg: str):
    parser = argparse.ArgumentParser(description=description_arg)
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD)")
    return parser.parse_args()

# Define bot keywords and exclusion terms
BOT_KEYWORDS = [
    "gptbot",
    "claudebot",
    "perplexitybot",
    "google-extended",
    "googlebot"
]
GOOGLEBOT_EXCLUSIONS = [
    "googlebot-image",
    "googlebot-video"
]

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def setup_logging(log_filename: str = 'download.log'):
    logger = logging.getLogger("ai_seo_analysis")
    logger.setLevel(logging.DEBUG)

    # Ensure data directory exists before creating log file
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    log_file = data_dir / log_filename
    log_file_full_name = 'data' + '/' + log_filename
    log_file.touch(exist_ok=True)  # Creates the file if it doesn't exist

    # Remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file_full_name, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler (optional)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
import sys
import logging
from pathlib import Path

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
    fh = logging.FileHandler(log_file_full_name)
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
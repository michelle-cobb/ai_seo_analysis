import csv
import re
from datetime import datetime
from pathlib import Path
from scripts.utils import setup_logging, BOT_KEYWORDS, GOOGLEBOT_EXCLUSIONS

# Directory containing log files
LOG_DIR = Path("data/raw")
# Output directory for processed CSVs
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Regex to extract all quoted strings (user agent is typically the second-to-last quoted string)
USER_AGENT_PATTERN = re.compile(r'"([^"]+)"')

def extract_log_fields(log_line: str, logger):
    try:
        # Extract all quoted strings
        parts = log_line.split('"')
        # Requested resource is usually in the first quoted string (parts[1])
        # User agent is usually in the fifth quoted string (parts[5])
        requested_resource = None
        user_agent = None
        
        if len(parts) >= 6:
            # Extract requested resource from the request string (e.g. "/robots.txt")
            requested_resource = parts[1].strip()

            # Extract the path using regex from the line
            match = re.search(r'(GET|POST|HEAD|PUT|DELETE|OPTIONS|PATCH)\s+([^\s]+)', log_line)
            if match:
                method = match.group(1)
                if method != "GET":
                    return "", ""  # Only count GET requests
            user_agent = parts[5].strip()
            if user_agent == '-':
                user_agent = ""
        return requested_resource or "", user_agent or ""
    except Exception as e:
        logger.error(f"Error extracting fields from log line: {log_line} ({e})")
        return "", ""

def is_ai_bot(user_agent: str) -> bool:
    ua = user_agent.lower()
    if "googlebot" in ua:
        if any(excl in ua for excl in GOOGLEBOT_EXCLUSIONS):
            return False
        return True
    return any(bot in ua for bot in BOT_KEYWORDS)

def process_logs():
    logger = setup_logging('aggregate.log')
    logger.info("Starting log aggregation and filtering process")

    bot_records = []
    for log_file in LOG_DIR.glob("*"):
        logger.info("Processing access log file: {log_file}".format(log_file=log_file))

        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                requested_resource, user_agent = extract_log_fields(line, logger)
                if not user_agent:
                    continue
                if is_ai_bot(user_agent):
                    bot_records.append([log_file.name, user_agent, requested_resource, line.strip()])

    if bot_records:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"ai_bot_traffic_{timestamp}.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["log_file", "user_agent", "requested_resource", "log_line"])
            writer.writerows(bot_records)
        logger.info(f"{len(bot_records)} AI bot traffic records saved to {output_file}")
    else:
        logger.info("No AI bot traffic records found.")

if __name__ == "__main__":
    process_logs()
import csv
import re
from datetime import datetime
from pathlib import Path
from scripts.common import parse_args, setup_logging, BOT_KEYWORDS, GOOGLEBOT_EXCLUSIONS

# Directory containing log files
LOG_DIR = Path("data/raw")
# Output directory for processed CSVs
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Regex to extract all quoted strings (user agent is typically the second-to-last quoted string)
USER_AGENT_PATTERN = re.compile(r'"([^"]+)"')

def extract_log_fields(log_line: str, logger, start_date, end_date):
    try:
        # Extract all quoted strings
        parts = log_line.split('"')
        # Requested resource is usually in the first quoted string (parts[1])
        # User agent is usually in the fifth quoted string (parts[5])
        requested_resource = None
        user_agent = None

        # Extract timestamp from log line
        # Example: [07/Jul/2025:00:03:40 +0000]
        timestamp_match = re.search(r'\[(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}) [+\-]\d{4}\]', log_line)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            # Convert to datetime object
            log_dt = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S")
            # If start_date or end_date are provided, filter by them
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                if log_dt.date() < start_dt.date():
                    return "", ""
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if log_dt.date() > end_dt.date():
                    return "", ""
        else: #unparseable record
            logger.error(f"Could not extract timestamp from log line: {log_line}")
            return "",""
        
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
        else:
            logger.error(f"Could not extract all fields from log line: {log_line}")
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

def process_logs(start_date=None, end_date=None):
    logger = setup_logging('aggregate.log')
    logger.info(f"Starting log aggregation and filtering process (start_date={start_date}, end_date={end_date})")

    bot_records = []
    for log_file in LOG_DIR.glob("access.log*"):
        logger.info(f"Processing access log file: {log_file}")

        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                requested_resource, user_agent = extract_log_fields(line, logger, start_date, end_date)
                if not user_agent:
                    continue
                if is_ai_bot(user_agent):
                    bot_records.append([log_file.name, user_agent, requested_resource, line.strip()])

    if bot_records:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            output_file = OUTPUT_DIR / f"ai_bot_traffic_{timestamp}.csv"
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["log_file", "user_agent", "requested_resource", "log_line"])
                writer.writerows(bot_records)
            logger.info(f"{len(bot_records)} AI bot traffic records saved to {output_file}")
            print(output_file)  
        except Exception as e:
            logger.error(f"Error saving bot traffic records to CSV: {e}")
    else:
        logger.info("No AI bot traffic records found.")

if __name__ == "__main__":
    args = parse_args("Aggregate AI bot traffic logs.")
    process_logs(start_date=args.start_date, end_date=args.end_date)
import csv
import subprocess
from pathlib import Path
from collections import Counter, defaultdict
from scripts.common import parse_args, BOT_KEYWORDS

def run_aggregation(start_date=None, end_date=None):
    cmd = "python -m scripts.aggregate_bot_traffic"
    if start_date:
        cmd += " --start-date " + start_date
    if end_date:
        cmd += " --end-date " + end_date
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    output_file = result.stdout.strip().splitlines()[-1]  # Get the last line
    return output_file

def analyze_bot_hits(csv_file):
    resource_counter = Counter()
    bot_resource_counter = defaultdict(Counter)

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            resource = row.get("requested_resource", "").strip()
            resource = resource.strip("/")  # Normalize resource path
            user_agent = row.get("user_agent", "").lower()
            if not resource or not user_agent:
                continue

            # Identify bot type from user agent using BOT_KEYWORDS
            bot = "other"
            for keyword in BOT_KEYWORDS:
                if keyword in user_agent:
                    bot = keyword
                    break

            resource_counter[resource] += 1
            bot_resource_counter[bot][resource] += 1

    return resource_counter, bot_resource_counter

def print_analysis(resource_counter, bot_resource_counter):
    print("=== Overall Resource Hit Counts (All AI Bots) ===")
    for resource, count in resource_counter.most_common():
        print(f"{resource}: {count}")

    print("\n=== Resource Hit Counts by Bot ===")
    for bot, counter in bot_resource_counter.items():
        print(f"\nBot: {bot}")
        for resource, count in counter.most_common():
            print(f"  {resource}: {count}")

if __name__ == "__main__":
    args = parse_args("Hit count analysis.")
    output_file = run_aggregation(start_date=args.start_date, end_date=args.end_date)
    print(f"Analyzing file: {output_file}")

    resource_counter, bot_resource_counter = analyze_bot_hits(Path(output_file))
    print_analysis(resource_counter, bot_resource_counter)
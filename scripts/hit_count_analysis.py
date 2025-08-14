import csv
from pathlib import Path
from collections import Counter, defaultdict
from scripts.utils import BOT_KEYWORDS

def get_latest_aggregated_file(processed_dir):
    files = list(processed_dir.glob("ai_bot_traffic_*.csv"))
    if not files:
        raise FileNotFoundError("No aggregated bot traffic files found.")
    return max(files, key=lambda f: f.stat().st_mtime)

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
    processed_dir = Path("data/processed")
    latest_file = get_latest_aggregated_file(processed_dir)
    print(f"Analyzing file: {latest_file}")

    resource_counter, bot_resource_counter = analyze_bot_hits(latest_file)
    print_analysis(resource_counter, bot_resource_counter)
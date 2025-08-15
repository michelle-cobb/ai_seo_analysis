import csv
import subprocess
from pathlib import Path
import importlib.util
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

# Try to import config
config = None
config_path = Path("config/credentials.py")
if config_path.exists():
    spec = importlib.util.spec_from_file_location("config", str(config_path))
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)

def get_llm_insights(csv_file):
    import openai

    # Read the CSV content as context
    with open(csv_file, "r", encoding="utf-8") as f:
        csv_content = f.read()

    prompt = (
        "Please describe the insights you glean from this listing of all the AI bot traffic that hit our site:\n\n"
        + csv_content
    )

    openai.api_key = getattr(config, "LLM_API_KEY", None)
    base_url = getattr(config, "LLM_API_BASE_URL", "https://api.openai.com/v1")
    model = getattr(config, "LLM_MODEL", "gpt-4")

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert in web analytics and SEO."},
            {"role": "user", "content": prompt}
        ],
        api_base=base_url
    )
    print("\n=== LLM Qualitative Insights ===")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    args = parse_args("Qualitative analysis.")
    output_file = run_aggregation(start_date=args.start_date, end_date=args.end_date)
    print(f"Qualitative analysis of file: {output_file}")

    # If LLM config is present, get insights
    if config and hasattr(config, "LLM_API_KEY") and getattr(config, "LLM_API_KEY"):
        try:
            get_llm_insights(output_file)
        except Exception as e:
            print(f"Error getting LLM insights: {e}")
    else:
        print("Please configure LLM API credentials in config/credentials.py")
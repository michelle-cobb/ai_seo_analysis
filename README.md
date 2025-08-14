# AI SEO Log Analysis

This project automates the download, aggregation, and analysis of web server access logs to track AI bot traffic (such as GPTBot, ClaudeBot, PerplexityBot, and Googlebot) for SEO insights.

## Features

- **Automated SFTP log downloads:** Securely fetches rotated access logs from your hosting provider.
- **Duplicate prevention:** Only downloads logs not already present in the `data/raw` folder and that are prior to today's date (i.e., not potentially still being written to).
- **Bot traffic aggregation:** Extracts and aggregates records for major AI bots.
- **Flexible date filtering:** Aggregate and analyze logs for any date range.
- **Hit count analysis:** Ranks requested resources by AI bot hit counts, both overall and per bot.
- **Modular scripts:** Easily extend or integrate with other analytics workflows.

## Directory Structure

```
ai_seo_analysis/
│
├── Scripts/
│   ├── download_logs.py          # Downloads logs via SFTP
│   ├── aggregate_bot_traffic.py  # Aggregates AI bot traffic from logs
│   ├── hit_count_analysis.py     # Analyzes and ranks resource hits
│   ├── common.py                 # Shared utilities and constants
│   └── __init__.py               # Makes Scripts a Python package
│
├── config/
|   └── credentials.py.example    # Example SFTP credentials and log paths (template)
│   └── credentials.py            # SFTP credentials and log paths (not tracked)
│
├── data/
│   ├── raw/                      # Downloaded log files
│   ├── processed/                # Aggregated CSV files
│   └── download.log              # Download process logs
│   └── aggregate.log             # Aggregation process logs
│
├── .gitignore
└── README.md
└── requirements.txt
```

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/michelle-cobb/ai_seo_analysis.git
   cd ai_seo_analysis
   ```

2. **Create and activate a Python virtual environment:**
   ```sh
   python -m venv venv
   venv\scripts\activate   # On Windows
   source venv/bin/activate  # On Mac/Linux
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure SFTP credentials:**
   - Copy `config/credentials.py.example` to `config/credentials.py`
   - Fill in your SFTP details and log directory paths.

## Usage

### 1. Download Logs

```sh
python -m scripts.download_logs
```
Downloads new access logs to `data/raw/`. You'll want to set up a process to run this daily to gather new data as it becomes available.

### 2. Aggregate AI Bot Traffic

```sh
python -m Scripts.aggregate_bot_traffic --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```
Aggregates AI bot traffic for the specified date range (optional). If no date range is provided, all AI bot traffic is included.

### 3. Analyze Hit Counts

```sh
python -m Scripts.hit_count_analysis --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```
Runs aggregation and then analyzes the aggregated file for resource hit counts. If no date range is provided, all AI bot traffic is included in the analysis.

## Customization

- **Add new bots:** Update `BOT_KEYWORDS` and potentially `GOOGLEBOT_EXCLUSIONS` in `scripts/common.py`.
- **Change log format parsing:** The current parsing logic is based on the Kinsta access log format. If your access logs are formatted differently, edit the extraction logic in `aggregate_bot_traffic.py`.

## Troubleshooting

- **Module import errors:** Make sure you run scripts from the project root and use the `-m` flag.
- **SFTP issues:** Check your credentials and network connectivity.
- **Log encoding errors:** Ensure your terminal and log files use UTF-8 encoding.

## Contributing

Pull requests and issues are welcome! Please follow best practices for Python projects and keep sensitive credentials out of version control.

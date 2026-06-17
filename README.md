# News

News is a Python 3.11+ project for generating a daily Word report of major global news from the past 24 hours.

This project uses the DeepSeek API as the model provider. It depends on the `openai` Python SDK only because DeepSeek exposes an OpenAI-compatible API; the SDK is initialized with `base_url=https://api.deepseek.com`, so model calls go to DeepSeek, not OpenAI.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configure DeepSeek

Copy `.env.example` to `.env`, then set your DeepSeek API key:

```powershell
Copy-Item .env.example .env
```

Required values:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

Do not commit `.env`. It is ignored by Git.

## Run

Run the complete pipeline:

```powershell
python -m src.main
```

The default command runs:

1. Fetch RSS articles.
2. Process candidates with extraction, deduplication, classification, and ranking.
3. Analyze selected candidates with DeepSeek.
4. Render the Word document.

Generated files:

```text
data/raw/YYYYMMDD_HHMM_articles.json
data/processed/YYYYMMDD_HHMM_candidates.json
data/processed/YYYYMMDD_HHMM_report.json
output/News_Report_YYYYMMDD_HHMM.docx
logs/YYYYMMDD_HHMM.log
```

Useful pipeline commands:

```powershell
python -m src.main --fetch-only
python -m src.main --process-only
python -m src.main --analyze-only --dry-run
python -m src.main --analyze-only
python -m src.main --render-only
python -m src.main --dry-run
```

`--dry-run` does not call DeepSeek. With no `--*-only` flag, it runs fetch and process, previews the selected analysis candidates, then stops before report generation and Word rendering.

If the DeepSeek API call fails, or DeepSeek returns empty content, invalid JSON, missing fields, or URLs outside the input candidates, the analysis step retries according to `DEEPSEEK_JSON_RETRY_TIMES`. If retries are exhausted, the pipeline stops and does not generate an empty Word report.

Image download failures during Word rendering are logged as warnings and do not stop document generation.

## Test

Run the test suite:

```powershell
pytest
```

Tests use mocks and sample data. They do not require a real `DEEPSEEK_API_KEY`.

## Windows Scheduled Task

The project includes a Windows batch script for daily automation:

```text
scripts\run_news.bat
```

The script automatically switches to the project root, activates `.venv` if it exists, runs the complete `python -m src.main` pipeline, and appends stdout/stderr plus the start time, end time, project root, command, and exit code to:

```text
logs\scheduler.log
```

To configure Windows Task Scheduler:

1. Open **Task Scheduler**.
2. Select **Create Basic Task...**.
3. Name it `News Daily Report`.
4. Choose **Daily**.
5. Set the start time to `08:00`.
6. Choose **Start a program**.
7. Set **Program/script** to the full path of the batch file, for example:

```text
<PROJECT_ROOT>\scripts\run_news.bat
```

8. Set **Start in** to the project root:

```text
<PROJECT_ROOT>
```

9. Finish the wizard.

For a command-line setup, run PowerShell as your normal user and adjust the path if your project is elsewhere:

```powershell
schtasks /Create /TN "News Daily Report" /SC DAILY /ST 08:00 /TR "<PROJECT_ROOT>\scripts\run_news.bat"
```

Secrets are not stored in the batch file. DeepSeek credentials continue to be read from `.env`.

Manual test:

```powershell
.\scripts\run_news.bat
Get-Content .\logs\scheduler.log -Tail 40
```

## Directory Structure

```text
scripts/
  run_news.bat
src/
  main.py
  config.py
  fetchers/
  processing/
  llm/
  render/
  utils/
config/
  sources.yaml
data/
  raw/
  processed/
  cache/
output/
logs/
tests/
```

## Current MVP Status

Implemented:

- Environment-based configuration loading.
- Per-run logging to `logs/YYYYMMDD_HHMM.log`.
- DeepSeek OpenAI-compatible client using `base_url=https://api.deepseek.com`.
- RSS fetching, article extraction, deduplication, classification, ranking, DeepSeek structured analysis, and Word rendering.
- Windows batch script for Task Scheduler automation.

Not implemented yet:

- Tests for the full pipeline.

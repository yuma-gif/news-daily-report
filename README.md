# News Daily Report

Daily AI-powered news report generator using RSS, DeepSeek API, and Word output.
基于 RSS、DeepSeek API 和 Word 输出的每日新闻日报生成器。

This project fetches news from RSS sources, extracts article content, removes duplicates, classifies and ranks candidates, uses DeepSeek to generate structured Chinese analysis, and finally renders a Word report.

本项目会从 RSS 新闻源抓取新闻，提取正文，去重，分类，排序，再调用 DeepSeek 生成中文结构化分析，最后输出 Word 新闻日报。

---

## 1. Main Features / 主要功能

* Fetch RSS news from Chinese and international sources.
* Extract article text from original news pages.
* Remove duplicate or highly similar articles.
* Classify news into:

  * `domestic_china`
  * `china_related_international`
  * `international`
* Rank articles by importance.
* Select final candidate articles before LLM analysis.
* Use DeepSeek API to generate structured Chinese analysis.
* Validate and normalize DeepSeek JSON output.
* Render a `.docx` Word report.
* Support Windows Task Scheduler for daily automatic execution.

---

## 2. Project Pipeline / 项目流程

```text
RSS sources
→ fetch articles
→ extract full text
→ deduplicate
→ classify
→ rank
→ select final articles
→ DeepSeek structured analysis
→ render Word report
```

Generated files are stored locally:

```text
data/raw/
data/processed/
output/
logs/
```

These folders are ignored by Git and should not be uploaded to GitHub.

---

## 3. Directory Structure / 目录结构

```text
news-daily-report/
├─ config/
│  └─ sources.yaml
├─ scripts/
│  └─ run_news.bat
├─ src/
│  ├─ config.py
│  ├─ main.py
│  ├─ fetchers/
│  │  └─ rss_fetcher.py
│  ├─ processing/
│  │  ├─ classifier.py
│  │  ├─ content_extractor.py
│  │  ├─ deduplicate.py
│  │  ├─ ranker.py
│  │  └─ selector.py
│  ├─ llm/
│  │  ├─ deepseek_client.py
│  │  ├─ prompts.py
│  │  └─ schemas.py
│  ├─ render/
│  │  ├─ docx_writer.py
│  │  └─ image_handler.py
│  └─ utils/
│     └─ logger.py
├─ tests/
├─ .env.example
├─ .gitignore
├─ pytest.ini
├─ requirements.txt
├─ sample_report.json
└─ README.md
```

---

## 4. Requirements / 环境要求

Recommended environment:

```text
Windows 10/11
Python 3.11+
PowerShell
DeepSeek API Key
```

This project uses the `openai` Python SDK because DeepSeek provides an OpenAI-compatible API. The actual model provider is DeepSeek, configured by:

```env
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

---

## 5. Installation / 安装步骤

### Step 1: Clone the repository / 克隆项目

```powershell
git clone https://github.com/yuma-gif/news-daily-report.git
cd news-daily-report
```

### Step 2: Create virtual environment / 创建虚拟环境

```powershell
python -m venv .venv
```

### Step 3: Activate virtual environment / 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies / 安装依赖

```powershell
pip install -r requirements.txt
```

---

## 6. Environment Configuration / 环境变量配置

### Step 1: Copy `.env.example` to `.env`

```powershell
Copy-Item .env.example .env
```

### Step 2: Open `.env`

```powershell
notepad .env
```

Or open it in VS Code.

### Step 3: Fill in your DeepSeek API key

In `.env`, modify line 1:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

Example:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

Do not upload `.env` to GitHub.
不要把 `.env` 上传到 GitHub。

---

## 7. `.env` Configuration Details / `.env` 配置说明

The template file is `.env.example`.

Current key settings:

```env
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_TEMPERATURE=0.2
DEEPSEEK_MAX_TOKENS=12000
DEEPSEEK_JSON_RETRY_TIMES=3
DEEPSEEK_THINKING_ENABLED=false
DEEPSEEK_REASONING_EFFORT=medium
NEWS_OUTPUT_DIR=output
NEWS_TIMEZONE=Asia/Shanghai
NEWS_TARGET_HOUR=8
NEWS_TOTAL_ITEMS=12
NEWS_CHINA_MIN_RATIO=0.30
NEWS_CHINA_MAX_RATIO=0.40
NEWS_LOOKBACK_HOURS=24
NEWS_MAX_IMAGES_PER_ITEM=3
```

### Common fields to modify / 常用修改项

#### 7.1 DeepSeek API Key

File:

```text
.env
```

Modify:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

This is required.

---

#### 7.2 DeepSeek model

File:

```text
.env
```

Modify:

```env
DEEPSEEK_MODEL=deepseek-v4-flash
```

If you want to use another DeepSeek model, replace this value.

---

#### 7.3 Number of news items

File:

```text
.env
```

Modify:

```env
NEWS_TOTAL_ITEMS=12
```

Example:

```env
NEWS_TOTAL_ITEMS=15
```

This controls the final number of news items in the report.

---

#### 7.4 News lookback window

File:

```text
.env
```

Modify:

```env
NEWS_LOOKBACK_HOURS=24
```

Example:

```env
NEWS_LOOKBACK_HOURS=48
```

This controls how many hours of news are considered.

---

#### 7.5 Time zone

File:

```text
.env
```

Modify:

```env
NEWS_TIMEZONE=Asia/Shanghai
```

Examples:

```env
NEWS_TIMEZONE=Asia/Shanghai
NEWS_TIMEZONE=America/New_York
NEWS_TIMEZONE=Europe/London
```

---

#### 7.6 Maximum images per news item

File:

```text
.env
```

Modify:

```env
NEWS_MAX_IMAGES_PER_ITEM=3
```

Example:

```env
NEWS_MAX_IMAGES_PER_ITEM=1
```

---

## 8. Important Code Modification Map / 重要代码修改位置

Most users only need to modify `.env` and `config/sources.yaml`.

普通用户一般只需要修改 `.env` 和 `config/sources.yaml`，不建议直接修改 Python 源码。

---

### 8.1 API and runtime settings

File:

```text
src/config.py
```

Current relevant lines:

```text
Line 40: deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "")
Line 41: deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
Line 42: deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
Line 48: news_output_dir=Path(os.getenv("NEWS_OUTPUT_DIR", "output"))
Line 49: news_timezone=os.getenv("NEWS_TIMEZONE", "Asia/Shanghai")
Line 51: news_total_items=int(os.getenv("NEWS_TOTAL_ITEMS", "12"))
Line 54: news_lookback_hours=int(os.getenv("NEWS_LOOKBACK_HOURS", "24"))
Line 55: news_max_images_per_item=int(os.getenv("NEWS_MAX_IMAGES_PER_ITEM", "3"))
```

Do not hard-code your API key in `src/config.py`.
不要把 API Key 直接写进 `src/config.py`。

Correct method:

```text
Modify .env instead.
```

---

### 8.2 News source configuration

File:

```text
config/sources.yaml
```

Each RSS source uses this structure:

```yaml
- name: Source Name
  url: https://example.com/rss.xml
  region: domestic_china
  language: zh
  weight: 1.00
  enabled: true
```

Supported `region` values:

```text
domestic_china
china_related_international
international
```

Meaning:

```text
domestic_china:
Chinese domestic news sources.

china_related_international:
International or English-language sources focused on China-related issues.

international:
General international news sources.
```

To disable a source, change:

```yaml
enabled: true
```

to:

```yaml
enabled: false
```

To add a new source, add a new block under `rss_sources:`.

Example:

```yaml
  - name: Example News
    url: https://example.com/rss.xml
    region: international
    language: en
    weight: 1.00
    enabled: true
```

After modifying sources, run:

```powershell
python -m src.main --source-audit
```

This checks whether the configured RSS sources can fetch articles.

---

### 8.3 Final news selection ratio

File:

```text
src/main.py
```

Current relevant lines:

```text
Line 168: selection = select_final_articles(
Line 169:     candidates,
Line 170:     total_items=settings.news_total_items,
Line 171:     domestic_min=4,
Line 172:     china_related_max=2,
Line 173: )
```

Meaning:

```text
total_items:
Total final news count. It comes from NEWS_TOTAL_ITEMS in .env.

domestic_min=4:
At least 4 domestic China news items will be selected if enough candidates exist.

china_related_max=2:
At most 2 China-related international news items will be selected before filling with international news.
```

Example: if you want 15 total news items, at least 5 domestic China items, and at most 3 China-related international items:

Modify `.env`:

```env
NEWS_TOTAL_ITEMS=15
```

Modify `src/main.py` lines 171-172:

```python
domestic_min=5,
china_related_max=3,
```

After modification, test:

```powershell
python -m src.main --dry-run
```

---

### 8.4 LLM writing style and analysis requirements

File:

```text
src/llm/prompts.py
```

Current relevant lines:

```text
Line 105-122: build_user_prompt(...)
Line 111: importance_score requirement
Line 112: every candidate must become one report item
Line 115: positive_impacts cannot be empty
Line 116: detailed_report length and structure
Line 117: negative_impacts / risks / lessons requirements
Line 118: bans generic empty phrases
```

If the generated report is too short, modify line 116:

Current requirement:

```python
"detailed_report 必须包含事件背景、最新进展、关键主体、多方反应、后续观察点；单来源不超过350字，多来源重大新闻可写500-800字。\n"
```

Example: make reports longer:

```python
"detailed_report 必须包含事件背景、最新进展、关键主体、多方反应、后续观察点；单来源可写400-600字，多来源重大新闻可写700-1000字。\n"
```

If the analysis is too generic, strengthen line 118.

Example:

```python
"lessons 禁止写空泛句式，必须具体说明政策制定、企业经营、投资决策、就业选择或个人学习方向上的可执行启发。\n\n"
```

Do not put API keys in this file.

---

### 8.5 Windows scheduled execution script

File:

```text
scripts/run_news.bat
```

Current relevant lines:

```text
Line 4: automatically detects project root
Line 22-24: activates .venv if it exists
Line 26: logs command
Line 27: python -m src.main
Line 31: logs exit code
```

Usually, you do not need to modify this file.

If your system cannot find `python`, modify line 27:

Original:

```bat
python -m src.main >> "logs\scheduler.log" 2>&1
```

Change to:

```bat
".venv\Scripts\python.exe" -m src.main >> "logs\scheduler.log" 2>&1
```

Then test:

```powershell
.\scripts\run_news.bat
Get-Content .\logs\scheduler.log -Tail 80
```

A successful run should include:

```text
Exit code: 0
```

---

## 9. Manual Usage / 手动运行

### 9.1 Run complete pipeline

```powershell
python -m src.main
```

This runs:

```text
fetch
process
analyze
render
```

Output:

```text
output/News_Report_YYYYMMDD_HHMM.docx
```

---

### 9.2 Audit RSS sources

```powershell
python -m src.main --source-audit
```

Use this after modifying `config/sources.yaml`.

---

### 9.3 Dry run without calling DeepSeek

```powershell
python -m src.main --dry-run
```

This runs fetch and process, then prints selected candidates. It does not call DeepSeek and does not generate a Word report.

---

### 9.4 Fetch only

```powershell
python -m src.main --fetch-only
```

This saves raw RSS articles to:

```text
data/raw/
```

---

### 9.5 Process only

```powershell
python -m src.main --process-only
```

This uses the latest raw file from `data/raw/`, then saves processed candidates to:

```text
data/processed/
```

---

### 9.6 Analyze only

```powershell
python -m src.main --analyze-only
```

This uses the latest processed candidate file and calls DeepSeek.

---

### 9.7 Render only

```powershell
python -m src.main --render-only
```

This uses the latest structured report JSON and generates a Word document.

---

## 10. Testing / 测试

Run:

```powershell
pytest
```

The project uses:

```ini
addopts = --basetemp=.pytest_tmp
```

in `pytest.ini`.

This means pytest temporary files are created in:

```text
.pytest_tmp/
```

This folder is ignored by Git.

If tests pass, you should see something like:

```text
22 passed
```

---

## 11. Windows Task Scheduler Setup / Windows 定时任务设置

The automation script is:

```text
scripts\run_news.bat
```

It automatically:

```text
1. switches to the project root
2. activates .venv if it exists
3. runs python -m src.main
4. writes logs to logs\scheduler.log
```

---

### 11.1 Manual test before scheduling

Run:

```powershell
.\scripts\run_news.bat
```

Then check logs:

```powershell
Get-Content .\logs\scheduler.log -Tail 80
```

If successful, the log should include:

```text
Exit code: 0
```

---

### 11.2 Create scheduled task using GUI

1. Press `Win + S`.
2. Search `Task Scheduler`.
3. Open Task Scheduler.
4. Click `Create Basic Task...`.
5. Name:

```text
News Daily Report
```

6. Choose:

```text
Daily
```

7. Set time, for example:

```text
08:00
```

8. Choose:

```text
Start a program
```

9. In `Program/script`, enter the full path to the batch file:

```text
<PROJECT_ROOT>\scripts\run_news.bat
```

Example:

```text
E:\news-daily-report\scripts\run_news.bat
```

10. In `Start in`, enter the project root:

```text
<PROJECT_ROOT>
```

Example:

```text
E:\news-daily-report
```

11. Finish the wizard.
12. Right-click the task.
13. Click `Run`.
14. Check:

```powershell
Get-Content .\logs\scheduler.log -Tail 80
```

---

### 11.3 Recommended advanced settings

After creating the task:

1. Right-click the task.
2. Click `Properties`.
3. Open `Conditions`.
4. If you want the task to run while the computer is asleep, enable:

```text
Wake the computer to run this task
```

5. Open `Settings`.
6. Recommended:

   * Enable `Allow task to be run on demand`.
   * Disable or extend `Stop the task if it runs longer than`.
   * If enabled, set it to at least `1 hour`.

Windows must also allow wake timers:

```text
Control Panel
→ Power Options
→ Change plan settings
→ Change advanced power settings
→ Sleep
→ Allow wake timers
→ Enable
```

---

### 11.4 Create scheduled task using command line

Replace `<PROJECT_ROOT>` with your actual path:

```powershell
schtasks /Create /TN "News Daily Report" /SC DAILY /ST 08:00 /TR "<PROJECT_ROOT>\scripts\run_news.bat" /F
```

Example:

```powershell
schtasks /Create /TN "News Daily Report" /SC DAILY /ST 08:00 /TR "E:\news-daily-report\scripts\run_news.bat" /F
```

Manual run:

```powershell
schtasks /Run /TN "News Daily Report"
```

---

## 12. Output Files / 输出文件

After a successful run, the Word report is saved to:

```text
output/
```

Example:

```text
output/News_Report_20260617_0800.docx
```

Logs are saved to:

```text
logs/
```

Scheduler log:

```text
logs/scheduler.log
```

---

## 13. GitHub Safety Checklist / GitHub 上传安全检查

Do not upload:

```text
.env
data/raw/
data/processed/
data/cache/
output/
logs/
.pytest_cache/
.pytest_tmp/
.tmp/
__pycache__/
*.pyc
.venv/
```

Before committing, run:

```powershell
git status
```

Make sure `.env` is not listed.

Before publishing publicly, also check:

```powershell
Select-String -Path .\* -Pattern "sk-" -Recurse
```

If a real API key appears, do not publish.

If an API key has ever been exposed in screenshots, logs, or commits, revoke it in the DeepSeek console and create a new key.

---

## 14. Git Update Workflow / 后续修改后如何更新 GitHub

After modifying files locally:

```powershell
git status
```

Stage changes:

```powershell
git add .
```

Commit:

```powershell
git commit -m "update documentation"
```

Push:

```powershell
git push
```

After pushing, refresh the GitHub repository page.

---

## 15. Common Problems / 常见问题

### Problem 1: `DEEPSEEK_API_KEY` is missing

Check `.env`:

```powershell
notepad .env
```

Make sure line 1 is filled:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

---

### Problem 2: `python` is not recognized

Use:

```powershell
python --version
```

If it fails, install Python or add Python to PATH.

Alternatively, modify `scripts/run_news.bat` line 27:

```bat
".venv\Scripts\python.exe" -m src.main >> "logs\scheduler.log" 2>&1
```

---

### Problem 3: Scheduled task runs but no Word file appears

Check scheduler log:

```powershell
Get-Content .\logs\scheduler.log -Tail 100
```

Common causes:

```text
1. .env is missing.
2. DeepSeek API key is invalid.
3. Network failed.
4. Python environment is not activated.
5. Computer slept during execution.
6. Task was stopped before completion.
```

---

### Problem 4: GitHub push fails because of network reset

If using Clash, configure Git proxy.

Example:

```powershell
git config --global http.proxy http://127.0.0.1:7897
git config --global https.proxy http://127.0.0.1:7897
git config --global http.version HTTP/1.1
```

Then:

```powershell
git push
```

To remove Git proxy:

```powershell
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## 16. License / 许可证

No license has been selected yet.

If you want others to freely use and modify this project, consider adding an open-source license such as MIT.

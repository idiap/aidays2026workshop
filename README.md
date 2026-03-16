# AI Days 2026 Workshop - Getting Started with AI Agents in Python

The slides are available [here](https://wdroz.pages.idiap.ch/aidays2026workshop).

## Learning Objectives

- Build AI agents in Python with **pydantic-ai** and **smolagents**
- Use **structured output** to get typed, validated responses from LLMs
- Analyze data with coding agents and safe tool-based approaches
- Expose and consume tools via the **Model Context Protocol** (MCP)
- Automate browser interactions with **browser-use**

## Prerequisites

### Install uv

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (WSL2 recommended):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Configure your LLM provider

Copy one of the example env files to `.env` and fill in your API key:

| Provider | Example file | Notes |
|---|---|---|
| OpenAI | `env.openai.example` | No `LLM_BASE_URL` needed |
| Grok (xAI) | `env.grok.example` | Uses `https://api.x.ai/v1/` |
| vLLM (local) | `env.vllm.example` | Run your own model locally |

```bash
cp env.openai.example .env   # or env.grok.example / env.vllm.example
# Then edit .env and set your LLM_API_KEY
```

**Environment variables:**

| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | Yes | Your LLM provider API key |
| `LLM_BASE_URL` | No | Custom endpoint (defaults to OpenAI) |
| `LLM_MODEL_NAME` | No | Model to use (defaults to `gpt-5.2`) |
| `LLM_USE_OPENRESPONSES` | No | `true` to use the OpenAI Responses API when possible |

## Workshop 0x - Data Analysis

### Install dependencies

```bash
uv sync
```

### Exercises

| # | Topic | File | Run command |
|---|---|---|---|
| 01 | **Your first agent** - build an agent with pydantic-ai | `src/aidays2026workshop/01_first_agent.py` | `uv run python -m aidays2026workshop.01_first_agent` |
| 02 | **Structured output** - Connect Four against an LLM using Pydantic models | `src/aidays2026workshop/02_connect_4_structured_output.py` | `uv run python -m aidays2026workshop.02_connect_4_structured_output` |
| 03 | **Naive data analysis** - pass raw CSV data to the LLM | `src/aidays2026workshop/03_naive_data_analysis.py` | `uv run python -m aidays2026workshop.03_naive_data_analysis` |
| 04 | **CodeAgent** - let smolagents write & execute pandas/polars code | `src/aidays2026workshop/04_data_analysis_codeagent.py` | `uv run python -m aidays2026workshop.04_data_analysis_codeagent` |
| 05 | **CodeAgent + plots** - generate plotly plots via grimoireplot | `src/aidays2026workshop/05_data_analysis_codeagent_plots.py` | `uv run grimoireplot serve` then `uv run python -m aidays2026workshop.05_data_analysis_codeagent_plots` |
| 06 | **CodeAgent + tools** - expose `push_plot_sync` as a smolagents tool | `src/aidays2026workshop/06_data_analysis_codeagent_plot_with_tools.py` | `uv run grimoireplot serve` then `uv run python -m aidays2026workshop.06_data_analysis_codeagent_plot_with_tools` |
| 07 | **Safe data analysis** - structured queries instead of code execution | `src/aidays2026workshop/07_data_analysis_without_codeagent.py` | `uv run python -m aidays2026workshop.07_data_analysis_without_codeagent` |
| 08 | **MCP data analysis** - expose tools via FastMCP (stdio transport) | `src/aidays2026workshop/08_data_analysis_mcp.py` | `uv run grimoireplot serve` then `uv run python -m aidays2026workshop.08_data_analysis_mcp` |

### Datasets

| File | Source | License |
|---|---|---|
| `dataset/voting.csv` | [Swiss Popular Voting](https://www.kaggle.com/datasets/vascos/swiss-popular-voting) | MIT |
| `dataset/cs_students.csv` | [CS Students Performance](https://www.kaggle.com/datasets/zahranusratt/cs-students-performance-dataset) | Public domain |

## Workshop 1x - Building Tools (MCPs) for Digitec/Galaxus

### Install dependencies

```bash
uv sync --extra scraping
uv run playwright install
```

### Exercises

| # | Topic | File | Run command |
|---|---|---|---|
| 11 | **Product search MCP** - build an MCP server to search & filter Digitec products | `src/aidays2026workshop/11_search_product_mcp.py` | `uv run src/aidays2026workshop/11_search_product_mcp.py --server` (terminal 1) then `uv run src/aidays2026workshop/11_search_product_mcp.py` (terminal 2) |
| 12 | **Browser-use MCP** - wrap browser-use in an MCP tool for web automation | `src/aidays2026workshop/12_search_product_browser_use.py` | `uv run src/aidays2026workshop/12_search_product_browser_use.py --server` (terminal 1) then `uv run src/aidays2026workshop/12_search_product_browser_use.py` (terminal 2) |

## Bonus - MCP Apps Data Analysis

### Install dependencies

The bonus exercises require additional dependencies. Install them with the `bonus` extra:

```bash
uv sync --extra bonus
```

### Exercises

| # | Topic | File | Run command |
|---|---|---|---|
| 21 | **MCP Apps charts** - render AreaChart / BarChart inline via MCP Apps (prefab_ui) | `src/aidays2026workshop/21_bonus_mcps_app_data_analysis.py` | `uv run python -m aidays2026workshop.21_bonus_mcps_app_data_analysis` |

You can also register it as an MCP server in VS Code (`.vscode/mcp.json`) to use it directly from Copilot Chat - see the slides for details.

## For Developers

Install all optional dependencies:

```bash
uv sync --all-groups --extra scraping
uv run playwright install
```

### Run tests

```bash
uv run pytest
```

### Build the slides

```bash
uv run mkslides build docs
```

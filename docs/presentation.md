---
slides:
    theme: solarized
    title: AI Days 2026 Workshop - Martigny
revealjs:
    height: 1080
    width: 1920
plugins:
    - extra_css:
        - custom.css
---

<!--
SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
SPDX-FileContributor: William Droz <william.droz@idiap.ch>
SPDX-License-Identifier: GPL-3.0-only
-->


# Workshop

## Getting Started with AI Agents in Python

---

# Learning Objectives

### What you will learn

- Build AI agents in Python with **pydantic-ai** and **smolagents**
- Use **structured output** to get typed, validated responses from LLMs
- Analyze data with coding agents and safe tool-based approaches
- Expose and consume tools via the **Model Context Protocol** (MCP)
- Automate browser interactions with **browser-use**

### What is NOT covered

- Prompt injection, jailbreaking, and LLM security
- Fine-tuning or training models
- Retrieval-Augmented Generation (RAG)
- Multi-agent orchestration and planning strategies
- Evaluation and benchmarking of agents
- Production deployment, observability, and cost management

---

# Planning

  - Setup a modern Python environment
    - Setup using uv
    - Standalone scripts vs full python project
    - Your first agent using pydantic-ai
    - Structured output with pydantic
  - Workshop data analysis
    - Naive approach to data analysis
    - Coding agent to the rescue!
    - Safer approach with tools
  - Workshop Tools (MCPs)
    - From framework-specific tools to MCPs
    - Converting data analysis tools to MCPs
    - MCPs to help us search for relevant PC components
    - Comparing with browser-use and ChatGPT

---

# Workshop git

<https://github.com/idiap/aidays2026workshop>

If you want to keep/commit your solution, *fork* the repo.

Slides are available as GitHub Pages

<https://idiap.github.io/aidays2026workshop/>

---

# Installing uv

## macOS and Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Windows (but I recommend to use WSL2 instead)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

# Standalone script

```bash
#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic-ai[web]"]
# ///

# Your python code here
```
---

# Full project with pyproject.toml

```toml
[build-system]
requires = ["uv_build>=0.10.2,<0.11.0"]
build-backend = "uv_build"
[project]
name = "aidays2026workshop"
version = "0.0.1"
description = "AI Days 2026 Workshop - First step with Agents"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    { name = "William Droz", email = "william.droz@idiap.ch" },
]
dependencies = [
    "pydantic-ai[web]>=1.59.0",
]
```

---

# Install the workshop "project"

```bash
uv sync
```

*Optionally, add `.venv/bin/python` as the Python interpreter in your IDE*

---

# What is an Agent?

An **agent** is a program that uses an LLM as its reasoning engine to **decide** what actions to take.

- **Takes a goal** - a user prompt or task description
- **Reasons** - the LLM interprets the goal and plans steps
- **Acts** - it can call tools, run code, or fetch data
- **Iterates** - it loops until the goal is satisfied

### Agent vs. simple LLM call

| Simple LLM call | Agent |
|---|---|
| One prompt → one response | Multi-step reasoning loop |
| No side effects | Can call tools & APIs |
| Stateless | Maintains context across steps |

> Think of an agent as an LLM **in a loop**, equipped with **tools** and **autonomy**.

---

# Exercise 01 - Your first agent

**How to make your first agent with pydantic-ai**

- Implement the `build_agent()` function
- Use environment variables for configuration (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_NAME`)
- Run the agent and ask it a question

File: `src/aidays2026workshop/01_first_agent.py`

```bash
uv run python -m aidays2026workshop.01_first_agent
```

---

# Exercise 01 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_01.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Structured Output with Pydantic

Instead of parsing free-form text, you can **constrain** the LLM to return data matching a **Pydantic model**.

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent

class CityInfo(BaseModel):
    name: str
    country: str
    population: int = Field(description="Estimated population")

agent = Agent("openai:gpt-4o", output_type=CityInfo)
result = agent.run_sync("Tell me about Martigny")
print(result.output)  # CityInfo(name='Martigny', country='Switzerland', population=20000)
```

### Why structured output?

- **No manual parsing** - the response is already a typed Python object
- **Validation built-in** - Pydantic enforces types and constraints automatically
- **Composable** - use `Field(ge=0, le=6)`, `Literal`, enums, nested models, ...

> Pass `output_type=YourModel` to `Agent()` and the LLM is forced to return valid, schema-conforming JSON.

---

# Exercise 02 - Connect Four with structured output

**Use Pydantic models to constrain LLM output**

- Define a `ConnectFourMove` Pydantic model with a constrained `column` field
- The agent returns valid JSON matching the schema - no parsing needed
- Play Connect Four against an LLM in the browser!

File: `src/aidays2026workshop/02_connect_4_structured_output.py`

```bash
uv run python -m aidays2026workshop.02_connect_4_structured_output
```

---

# Exercise 02 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_02.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Exercise 03 - Naive data analysis

**Give raw CSV data directly to the LLM**

- Read the `dataset/voting.csv` file
- Pass its content to the agent along with a prompt
- Try asking for the average number of voters
- Tip: you can use `instructions` (system prompt) with `agent.run_sync`

File: `src/aidays2026workshop/03_naive_data_analysis.py`

```bash
uv run python -m aidays2026workshop.03_naive_data_analysis
```

---

# Exercise 03 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_03.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# smolagents & CodeAgent

**smolagents** is Hugging Face's lightweight library for building agents that can **write and execute code**.

### CodeAgent

A `CodeAgent` **writes Python code** to solve the task, then runs it in a sandboxed interpreter.

```
User question → LLM generates Python code → execute in sandbox → return result
```

| Feature | Description |
|---|---|
| **Code generation** | The LLM writes full Python snippets (pandas, polars, plotly, ...) |
| **Sandboxed execution** | Code runs in a restricted environment with controlled imports |
| **Tool integration** | You can register custom tools the agent can call from generated code |
| **Iterative** | If execution fails, the agent retries with corrected code |

### What about pydantic-ai?

Pydantic is also exploring code agents with **[Monty](https://github.com/pydantic/monty)**

---

# Exercise 04 - Data analysis with CodeAgent

**Let the agent write and execute code to analyze data**

- Use `smolagents` `CodeAgent` to analyze the dataset
- The agent can write Python code using pandas or polars
- Build a prompt that provides the dataset path and the user question

File: `src/aidays2026workshop/04_data_analysis_codeagent.py`

```bash
uv run python -m aidays2026workshop.04_data_analysis_codeagent
```

---

# Exercise 04 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_04.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Exercise 05 - CodeAgent with plots

**Generate plots using plotly and grimoireplot**

- The agent creates plots with plotly and pushes them via `push_plot_sync`
- How do you explain to the model how to use `push_plot_sync`?
- Run `uv run grimoireplot serve` first, then browse to `http://localhost:8080`

File: `src/aidays2026workshop/05_data_analysis_codeagent_plots.py`

```bash
uv run grimoireplot serve  # in a separate terminal
uv run python -m aidays2026workshop.05_data_analysis_codeagent_plots
```

---

# Exercise 05 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_05.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Exercise 06 - CodeAgent with tools

**Expose `push_plot_sync` as a proper smolagents tool**

- Use the `@tool` decorator from smolagents to wrap `push_plot_sync`
- Add the tool to the `CodeAgent`
- Docs: https://huggingface.co/docs/smolagents/en/guided_tour#tools

File: `src/aidays2026workshop/06_data_analysis_codeagent_plots_with_tools.py`

```bash
uv run grimoireplot serve  # in a separate terminal
uv run python -m aidays2026workshop.06_data_analysis_codeagent_plots_with_tools
```

---

# Exercise 06 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_06.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Exercise 07 - Data analysis without CodeAgent

**Structured queries instead of arbitrary code execution**

- Define a `DataQuery` schema with pydantic (filters, group_by, aggregation, ...)
- Implement the `query_dataframe` tool to safely query a pandas DataFrame
- The agent translates natural language into structured queries
- Expose as a web app with `agent.to_web()`

File: `src/aidays2026workshop/07_data_analysis_without_codeagent.py`

```bash
uv run python -m aidays2026workshop.07_data_analysis_without_codeagent
```

---

# Exercise 07 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_07.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# MCPs - Model Context Protocol

A **standard protocol** for AI agents to discover and call external tools, data sources, and services.

### The problem

Without MCP, every agent framework needs **custom glue code** for every tool → M×N integrations.

MCP reduces this to **M + N** - one protocol both sides implement.

### How it works

| Component | Role |
|---|---|
| **MCP Server** | Exposes **tools** (functions), **resources** (data), **prompts** (templates) |
| **MCP Client** | Embedded in the agent - discovers and invokes capabilities at runtime |
| **Transport** | **stdio** (local) or **Streamable HTTP** (remote) |

> Think of MCP as **USB-C for AI integrations** - plug any tool into any agent.

---

# Exercise 08 - Data analysis with MCP

**From framework-specific tools to the Model Context Protocol**

- The tools from exercise 07 are already implemented as plain functions
- Decorate each one with `@mcp.tool` to expose them via FastMCP
- The agent discovers and calls the tools at runtime over MCP (stdio transport)
- Functions to expose: `list_csv_files`, `get_csv_info`, `query_csv`, `create_and_push_plot`

File: `src/aidays2026workshop/08_data_analysis_mcp.py`

```bash
uv run grimoireplot serve  # in a separate terminal
uv run python -m aidays2026workshop.08_data_analysis_mcp
```

---

# Exercise 08 - Demo (1/2)

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_08_01.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Exercise 08 - Demo (2/2)

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_08_02.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# SubAgents

**Subagents** are child agents spawned by an orchestrator to handle specific subtasks.

The parent **plans and delegates**; each subagent runs independently, then returns results.

### Common patterns

| Pattern | Description |
|---|---|
| **Delegation** | Orchestrator assigns one subtask per subagent (e.g. one CSV each) |
| **Specialization** | Each subagent can use different tools or prompts |
| **Parallel execution** | Independent subtasks run concurrently |

### Why subagents?

- **Modularity** - focused prompt & toolset per subagent
- **Parallelism** - simultaneous execution, lower wall-clock time
- **Separation of concerns** - orchestrator plans, subagents execute
- **Scalability** - add a subagent, don't rewrite the orchestrator

---

# Second part of the workshop (1/2)

Sometimes you want to interface with existing website/intranet.

MCPs can help in this regard as we can use external web content as a database.

---

# Second part of the workshop (2/2)

Sometimes some website are quite hostile to be used by agents/bots.

Fortunately, it's still possible to extract usable MCPs by using browser-based automation.

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_scraping.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Setup - Workshop 1x

### Install dependencies

```bash
uv sync --extra scraping
uv run playwright install
```

---

# Exercise 11 - Search products with MCP

**Build an MCP server that lets an agent search & filter Digitec products**

- The MCP server already defines several tool stubs - fill in the two `TODO`s
- The imported helper functions have everything you need
- Don't forget to remove the `type: ignore` comments once implemented
- Run the MCP server first (`--server`), then the agent in a separate terminal
- The agent connects over **Streamable HTTP** and discovers tools at runtime

File: `src/aidays2026workshop/11_search_product_mcp.py`

```bash
uv run src/aidays2026workshop/11_search_product_mcp.py --server   # terminal 1
uv run src/aidays2026workshop/11_search_product_mcp.py            # terminal 2
```

---

# Exercise 11 - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_11.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# browser-use

**Let an LLM control a real browser** - navigate, click, type, extract data.

### How it works

```
Agent prompt → browser-use Agent → Chromium (via Playwright) → structured result
```

- The LLM decides **what to click, scroll, and type** in a live browser session
- Works with any OpenAI-compatible model (`ChatOpenAI`)
- Returns structured output via `output_model_schema`
- Useful when **no API exists** - scrape, fill forms, compare prices, ...

### Trade-offs

| Pros | Cons |
|---|---|
| Works on any website | Slow (real browser interactions) |
| No custom scraping code | Non-deterministic (results vary between runs) |
| Visual understanding | Expensive (many LLM calls per task) |

---

# Exercise 12 - Browser-use as an MCP tool

**Wrap a browser-use agent inside an MCP tool so your main agent can browse the web**

- Define the `BrowserResult` Pydantic model with a field to hold the browser agent's answer
- The MCP server exposes a `browser_use` tool that spawns a full browser automation agent
- The main agent discovers it over **Streamable HTTP** and delegates web tasks
- Run the MCP server first (`--server`), then the agent in a separate terminal
- Try asking: *"What is the cheapest RTX 5090 on digitec.ch?"*

File: `src/aidays2026workshop/12_search_product_browser_use.py`

```bash
uv run src/aidays2026workshop/12_search_product_browser_use.py --server   # terminal 1
uv run src/aidays2026workshop/12_search_product_browser_use.py            # terminal 2
```

---

# Exercise 12 - Demo (1/3)

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_12_01.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Exercise 12 - Demo (2/3)

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_12_02.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Exercise 12 - Demo (3/3)

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_12_03.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# Setup - Bonus

### Install dependencies

```bash
uv sync --extra bonus
```

---

# Bonus - MCP Apps with prefab_ui

**Render charts directly inside VS Code Copilot using MCP Apps**

Instead of pushing plots to an external server, tools return a `PrefabApp` that the client renders inline.

```python
# Omitted import
mcp = FastMCP("CSV Data Analysis Server (MCP Apps)")

@mcp.tool
def create_chart(request: ChartRequest) -> PrefabApp:
    #  data = ... record-like datastructure
    chart_cls = {"area": AreaChart, "bar": BarChart}[request.chart_type]
    view = chart_cls(
        data=data,
        series=[ChartSeries(data_key=s.data_key, label=s.label) for s in request.series],
        x_axis=request.x_axis,
        show_legend=True,
    )
    return PrefabApp(view=view)
```

File: `src/aidays2026workshop/21_bonus_mcps_app_data_analysis.py`

---

# Bonus - Demo

<video controls width="70%">
  <source src="https://www.idiap.ch/~wdroz/workshop_videos/compressed/workshop_demo_21.mp4" type="video/mp4" />
    Sorry, your browser doesn't support embedded videos.
</video>

---

# End of the workshop

William Droz <william.droz@idiap.ch>

![qr code linkedin](./qr_image.png)

---

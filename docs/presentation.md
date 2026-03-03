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

# Workshop

## Getting Started with AI Agents in Python

---

# Planning

  - Setup a modern python environment
    - Setup using uv
    - Standalone scripts vs full python project
    - Your first agent using pydantic-ai
  - Workshop data analysis
    - Naive approach to data analysis
    - Coding agent to the rescue!
    - Safer approach with tools
  - Workshop Tools (MCPs)
    - From framework-specifc tools to MCPs
    - Converting data analysis tools to MCPs
    - MCPs to help us searching relevant PC components
    - Comparing with browser-use and ChatGPT

---

# Workshop git

TODO add github link and github pages for slides

If you want to keep/commit your solution, *fork* the repo.

---

# Installing uv

## Macos and Linux

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
name = "workshop"
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

*Optionnaly, add `.venv/bin/python` as the python interpreter in your IDE*

---

# What is an Agent?

An **agent** is a program that uses an LLM as its reasoning engine to **decide** what actions to take.

- **Takes a goal** — a user prompt or task description
- **Reasons** — the LLM interprets the goal and plans steps
- **Acts** — it can call tools, run code, or fetch data
- **Iterates** — it loops until the goal is satisfied

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

File: `src/workshop/01_first_agent.py`

```bash
uv run python -m workshop.01_first_agent
```

---

# Exercise 02 - Naive data analysis

**Give raw CSV data directly to the LLM**

- Read the `dataset/voting.csv` file
- Pass its content to the agent along with a prompt
- Try asking for the average number of voters
- Tip: you can use `instructions` (system prompt) with `agent.run_sync`

File: `src/workshop/02_naive_data_analysis.py`

```bash
uv run python -m workshop.02_naive_data_analysis
```

---

# Exercise 03 - Data analysis with CodeAgent

**Let the agent write and execute code to analyze data**

- Use `smolagents` `CodeAgent` to analyze the dataset
- The agent can write Python code using pandas or polars
- Build a prompt that provides the dataset path and the user question

File: `src/workshop/03_data_analysis_codeagent.py`

```bash
uv run python -m workshop.03_data_analysis_codeagent
```

---

# Exercise 04 - CodeAgent with plots

**Generate plots using plotly and grimoireplot**

- The agent creates plots with plotly and pushes them via `push_plot_sync`
- How do you explain to the model how to use `push_plot_sync`?
- Run `uv run grimoireplot serve` first, then browse to `http://localhost:8080`

File: `src/workshop/04_data_analysis_codeagent_plots.py`

```bash
uv run grimoireplot serve  # in a separate terminal
uv run python -m workshop.04_data_analysis_codeagent_plots
```

---

# Exercise 05 - CodeAgent with tools

**Expose `push_plot_sync` as a proper smolagents tool**

- Use the `@tool` decorator from smolagents to wrap `push_plot_sync`
- Add the tool to the `CodeAgent`
- Docs: https://huggingface.co/docs/smolagents/en/guided_tour#tools

File: `src/workshop/05_data_analysis_codeagent_plot_with_tools.py`

```bash
uv run grimoireplot serve  # in a separate terminal
uv run python -m workshop.05_data_analysis_codeagent_plot_with_tools
```

---

# Exercise 06 - Data analysis without CodeAgent

**Structured queries instead of arbitrary code execution**

- Define a `DataQuery` schema with pydantic (filters, group_by, aggregation, ...)
- Implement the `query_dataframe` tool to safely query a pandas DataFrame
- The agent translates natural language into structured queries
- Expose as a web app with `agent.to_web()`

File: `src/workshop/06_data_analysis_without_codeagent.py`

```bash
uv run uvicorn workshop.06_data_analysis_without_codeagent:app
```

---

# MCPs — Model Context Protocol

A **standard protocol** for AI agents to discover and call external tools, data sources, and services.

### The problem

Without MCP, every agent framework needs **custom glue code** for every tool → M×N integrations.

MCP reduces this to **M + N** — one protocol both sides implement.

### How it works

| Component | Role |
|---|---|
| **MCP Server** | Exposes **tools** (functions), **resources** (data), **prompts** (templates) |
| **MCP Client** | Embedded in the agent — discovers and invokes capabilities at runtime |
| **Transport** | **stdio** (local) or **Streamable HTTP** (remote) |

> Think of MCP as **USB-C for AI integrations** — plug any tool into any agent.

---

# Exercise 07 - Data analysis with MCP

**From framework-specific tools to the Model Context Protocol**

- The tools from exercise 06 are already implemented as plain functions
- Decorate each one with `@mcp.tool` to expose them via FastMCP
- The agent discovers and calls the tools at runtime over MCP (stdio transport)
- Functions to expose: `list_csv_files`, `get_csv_info`, `query_csv`, `create_and_push_plot`

File: `src/workshop/07_data_analysis_mcp.py`

```bash
uv run grimoireplot serve  # in a separate terminal
uv run uvicorn workshop.07_data_analysis_mcp:app
```

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

- **Modularity** — focused prompt & toolset per subagent
- **Parallelism** — simultaneous execution, lower wall-clock time
- **Separation of concerns** — orchestrator plans, subagents execute
- **Scalability** — add a subagent, don't rewrite the orchestrator

---

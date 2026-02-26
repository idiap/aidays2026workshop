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

# AIDays2026Workshop

The slides are available [here](https://wdroz.pages.idiap.ch/aidays2026workshop)

TODO: learning objectives

## Setup which LLMs provider you want to use?


```bash
# Optional if you use openai
LLM_BASE_URL=
LLM_MODEL_NAME=

# Required
LLM_API_KEY=
```

TODO: add .env.x.example for each provider with the base_url

## Workshop steps

### Setup a modern python environment

TODO: explain uv, script with PEP723

### Data Analysis

TODO

### Building tools (MCPs) for Digitec/Galaxus

TODO

## Devs

Make sure to install optional `dev` and `docs` dependencies

```bash
uv sync --extra dev,docs
```

### Building the slides

```bash
uv run mkslides build docs
```

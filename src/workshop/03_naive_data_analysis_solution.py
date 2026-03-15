# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""
Naive data analysis - solution
"""

from pathlib import Path
from pydantic_ai import Agent
from dotenv import load_dotenv
import uvicorn

from workshop.common import pydantic_ai_build_model

load_dotenv()


def build_agent() -> Agent:
    model = pydantic_ai_build_model()
    agent = Agent(model)
    return agent


def run_agent():
    agent = build_agent()
    dataset_path = Path(__file__).parent.parent.parent / "dataset" / "voting.csv"
    data = dataset_path.read_text()
    print("Data loaded, asking the agent to analyze it... length:", len(data))
    intruction = f"""You are a data analyst, you have the following dataset:
{data}
Please analyze it and give me insights about when the user asks for it. Be concise and precise, do not give me the whole dataset back, just what the user asks for."""
    app = agent.to_web(instructions=intruction)
    uvicorn.run(app, host="127.0.0.1", port=9000, reload=False)


if __name__ == "__main__":
    run_agent()

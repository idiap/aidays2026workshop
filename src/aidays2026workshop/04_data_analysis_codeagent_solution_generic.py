# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""
Data analysis with CodeAgent - solution
"""

from pathlib import Path
from dotenv import load_dotenv
from smolagents import CodeAgent
from aidays2026workshop.common import smolagents_build_model

load_dotenv()


def build_agent():
    model = smolagents_build_model()
    agent = CodeAgent(
        model=model, tools=[], additional_authorized_imports=["polars", "pandas"]
    )
    return agent


if __name__ == "__main__":
    agent = build_agent()
    user_question = input("Ask the agent: ")
    dataset_path = Path(__file__).parent.parent.parent / "dataset" / "voting.csv"
    prompt = f"You are a data analyst, you have the following dataset:\n{dataset_path}\nPlease use polars to answer the user's question: {user_question}"
    result = agent.run(prompt)
    print(result)

# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""
How to make your first agent with pydantic - solution
"""

from pydantic_ai import Agent
from dotenv import load_dotenv

from aidays2026workshop.common import pydantic_ai_build_model

load_dotenv()


def build_agent() -> Agent:
    model = pydantic_ai_build_model()
    agent = Agent(model)
    return agent


if __name__ == "__main__":
    agent = build_agent()
    user_input = input("Ask the agent: ")
    result = agent.run_sync(user_input)
    print(result.output)

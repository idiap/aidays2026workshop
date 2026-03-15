# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""Thin wrapper so the plot_mcp console script can import from 08_data_analysis_mcp_solution."""

import importlib

_mod = importlib.import_module("workshop.08_data_analysis_mcp_solution")
main = _mod.main

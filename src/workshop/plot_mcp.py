"""Thin wrapper so the plot_mcp console script can import from 08_data_analysis_mcp_solution."""

import importlib

_mod = importlib.import_module("workshop.08_data_analysis_mcp_solution")
main = _mod.main

"""Paths shared by CLI entry points."""

from pathlib import Path

# backend/outputs — sibling of src/ under backend/
CLI_OUTPUTS_DIR = Path(__file__).resolve().parents[4] / "outputs"

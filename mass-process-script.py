#!/usr/bin/env python3
"""Repo-root launcher — delegates to GKS2365/mass-process-script.py."""

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "GKS2365" / "mass-process-script.py"), run_name="__main__")
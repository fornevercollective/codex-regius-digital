#!/usr/bin/env python3
"""Backward-compatible alias → qc-pipeline.py"""

import runpy

runpy.run_path(str(__import__("pathlib").Path(__file__).resolve().parent / "qc-pipeline.py"), run_name="__main__")
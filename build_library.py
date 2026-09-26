#!/usr/bin/env python3
"""Локальный launcher. После pip install используй: milenium-build-library"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from milenium.scripts.build_library import main

if __name__ == "__main__":
    main()

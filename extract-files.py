#!/usr/bin/env python3
"""Entry point seguro para a versão local do laboratório.

Delegates to the Python 3 local implementation. Remote URL extraction is
intentionally not implemented.
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    implementation = Path(__file__).with_name("extract-files copy.py")
    runpy.run_path(str(implementation), run_name="__main__")

"""Locate the project root and make both script folders importable.

The scripts address their inputs and outputs from the project root -- they read
`philidor2.txt` and `games.json`, and write `philidor.md`, `pgn/` and
`book/games/`. Importing this module sets the working directory there and puts
both script folders on the import path, so a script runs the same from
anywhere:

    uv run --with chess python scripts/extraction/build.py

The two folders import across each other: the algebraic-notation scripts read
the transcription through `build` and `extract`, which live in `extraction`.
"""

import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)

# The scans and the text extracted from them live beside the scripts that read
# them, so `extraction` holds everything needed to rebuild the transcription.
SOURCE_DIR = os.path.join(SCRIPTS, "extraction")


def source(name):
    """Path to one of the source texts, from wherever a script is run."""
    return os.path.join(SOURCE_DIR, name)

for _folder in ("extraction", "algebraic_notation"):
    _path = os.path.join(SCRIPTS, _folder)
    if _path not in sys.path:
        sys.path.insert(0, _path)

os.chdir(ROOT)

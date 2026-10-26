"""TLDR: Resolve unchanged local checkpoint/scorer dependencies without editing earlier experiments."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
V2=HERE.parents[1]/'expt_v2'
for path in (V2/'phase2',V2/'phase1',V2/'R0_attempt_2',V2):
    if str(path) not in sys.path:sys.path.append(str(path))

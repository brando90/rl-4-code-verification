"""Write skampere/tasks.tsv (env_id <TAB> seed): 48 lines, seed-major so every environment gets seed 0 first, then 1, then 2."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18c as K18C  # noqa: E402

H = Path(__file__).resolve().parent
sel = json.loads(K18C.SELECTION_PATH.read_text())["selected"]
(H / "skampere" / "tasks.tsv").write_text("".join(f"{s['env_id']}\t{seed}\n" for seed in K18C.SEEDS for s in sel))

"""Write slurm/tasks.tsv (env_id <TAB> seed, 32 lines = array indices 0-31) from selection_18b.json."""

import json
from pathlib import Path

H = Path(__file__).resolve().parent
sel = json.loads((H / "selection_18b.json").read_text())["selected"]
(H / "slurm" / "tasks.tsv").write_text("".join(f"{s['env_id']}\t{seed}\n" for s in sel for seed in (0, 1)))

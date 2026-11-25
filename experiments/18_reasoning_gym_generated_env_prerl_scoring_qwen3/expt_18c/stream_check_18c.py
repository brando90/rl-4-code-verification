"""18c CPU check before the freeze: item-stream prefix equals 18b's, and distinct questions in each environment's 32,000-index stream.

    python stream_check_18c.py --out stream_check_18c.json [--seeds 0 1 2] [--procs 32]

For each of the 16 environments and each seed: sha256 of the first 1,280 questions (must equal `items_sha256` of the 18b run for seeds 0 and 1)
and the number of distinct questions among all ITEMS_PER_RUN indices (seed 0 only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18c as K18C  # noqa: E402

K = K18C.K
C = K.C


def one(args):
    env_id, seed, full = args
    spec = K.train_spec(C.sets_by_id()[env_id], seed)
    ds = C.rg_dataset(spec, K18C.ITEMS_PER_RUN if full else K18C.PREFIX_ITEMS)
    n = K18C.ITEMS_PER_RUN if full else K18C.PREFIX_ITEMS
    qs = [ds[i]["question"] for i in range(n)]
    sha = hashlib.sha256("".join(C.sha256_text(q) for q in qs[: K18C.PREFIX_ITEMS]).encode()).hexdigest()
    return {"env_id": env_id, "seed": seed, "prefix_sha256": sha, "n_indices": n, "distinct_prefix": len(set(qs[: K18C.PREFIX_ITEMS])),
            "distinct_all": len(set(qs)) if full else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2])
    ap.add_argument("--procs", type=int, default=32)
    a = ap.parse_args(argv)
    envs = [s["env_id"] for s in json.loads(K.SELECTION_PATH.read_text())["selected"]]
    jobs = [(e, s, s == 0) for e in envs for s in a.seeds]
    with Pool(a.procs) as p:
        rows = p.map(one, jobs, chunksize=1)
    Path(a.out).write_text(json.dumps(rows, indent=1) + "\n")
    for r in rows:
        print(r["env_id"], r["seed"], r["prefix_sha256"][:12], r["distinct_prefix"], r["distinct_all"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

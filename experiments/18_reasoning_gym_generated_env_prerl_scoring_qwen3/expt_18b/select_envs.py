"""Select the 16 training environments for 18b from the Qwen3-1.7B cells of envs_18a.jsonl (deterministic; no training outcome is read).

Rule (PROTOCOL_18b.md): eligible = complete cell, not format-dominated (answer-tag rate >= 0.5), rho > 0 (the law takes log rho),
0.02 <= pass rate <= 0.98. From the eligible pool take N_SELECT by farthest-point sampling in the standardised space
(log rho, H, alignment, pass rate) with at most MAX_PER_FAMILY per family; the first point is the one farthest from the pool centroid.

    python select_envs.py            # writes selection_18b.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18b as K  # noqa: E402


def eligible_pool(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if r["model_size_b"] != K.POLICY_SIZE_B or not r["complete"] or r["format_dominated"]:
            continue
        if r["answer_tag_rate"] < 0.5 or not r["rho"] > 0:
            continue
        if not K.MIN_PASS <= r["pass_rate"] <= K.MAX_PASS:
            continue
        out.append(r)
    return sorted(out, key=lambda r: r["env_id"])


def features(pool: list[dict]) -> np.ndarray:
    x = np.array([[math.log(r["rho"]), r["H"], r["alignment"], r["pass_rate"]] for r in pool], dtype=float)
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - x.mean(axis=0)) / sd


def farthest_point(pool: list[dict], n: int, max_per_family: int) -> list[int]:
    z = features(pool)
    fam = [r["family"] for r in pool]
    count: dict[str, int] = {}
    chosen: list[int] = []
    d_centroid = np.linalg.norm(z - z.mean(axis=0), axis=1)
    mind = d_centroid.copy()
    while len(chosen) < min(n, len(pool)):
        order = sorted((i for i in range(len(pool)) if i not in chosen and count.get(fam[i], 0) < max_per_family),
                       key=lambda i: (-mind[i], pool[i]["env_id"]))
        if not order:
            break
        i = order[0]
        chosen.append(i)
        count[fam[i]] = count.get(fam[i], 0) + 1
        mind = np.minimum(mind, np.linalg.norm(z - z[i], axis=1))
    return chosen


def build_selection(rows: list[dict]) -> dict:
    pool = eligible_pool(rows)
    idx = farthest_point(pool, K.N_SELECT, K.MAX_PER_FAMILY)
    chosen = [pool[i] for i in idx]
    excluded = [{"env_id": r["env_id"], "why": why(r)} for r in rows
                if r["model_size_b"] == K.POLICY_SIZE_B and r["env_id"] not in {p["env_id"] for p in pool}]
    return {"schema": "selection_18b/v1", "policy": K.POLICY_TAG, "n_pool": len(pool),
            "pool": [r["env_id"] for r in pool],
            "selected": [{"env_id": r["env_id"], "family": r["family"], "level": r["level"],
                          "probe_seed": r["probe_seed"], "pass_rate": r["pass_rate"], "rho": r["rho"], "H": r["H"],
                          "alignment": r["alignment"], "answer_tag_rate": r["answer_tag_rate"]} for r in chosen],
            "not_selected_in_pool": [r["env_id"] for r in pool if r["env_id"] not in {c["env_id"] for c in chosen}],
            "excluded_from_pool": excluded}


def why(r: dict) -> str:
    if not r["complete"]:
        return "incomplete cell"
    if r["format_dominated"] or r["answer_tag_rate"] < 0.5:
        return f"format-dominated (answer-tag rate {r['answer_tag_rate']:.2f})"
    if not r["rho"] > 0:
        return "rho = 0 (no mixed groups)"
    return f"pass rate {r['pass_rate']:.3f} outside [{K.MIN_PASS}, {K.MAX_PASS}]"


def main() -> int:
    rows = list(K.C.read_jsonl(K.ENVS_18A))
    sel = build_selection(rows)
    sel["envs_18a_sha256"] = K.C.sha256_text(K.ENVS_18A.read_text(encoding="utf-8"))
    K.SELECTION_PATH.write_text(json.dumps(sel, indent=2) + "\n", encoding="utf-8")
    for s in sel["selected"]:
        print(f"{s['env_id']:30s} pass={s['pass_rate']:.3f} rho={s['rho']:.0f} H={s['H']:.3f} align={s['alignment']:+.3f}")
    print(f"pool {sel['n_pool']}, selected {len(sel['selected'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

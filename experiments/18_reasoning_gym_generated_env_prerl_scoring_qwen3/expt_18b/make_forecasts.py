"""Compute and freeze the 18b forecasts from envs_18a.jsonl and selection_18b.json (no training outcome exists or is read).

Every forecast is a score per selected environment; a higher score predicts a larger held-out gain after single-env GRPO on that
environment. All inputs are Qwen3-1.7B cells of 18a except `smaller_model` (Qwen3-0.6B).

  rho_h        env_term of the paper's frozen Eq. 7 law (rl4cv.utility_model.paper_frozen_14b_model): b_rho*z(log rho)+b_H*z(H),
               with the paper's own coefficients and standardisers; s(C) and the scale terms are constants within one scale and budget.
  law_alpha    z(rho_h) + z(alignment), z over the eligible pool (equal weights, no fit: nothing exists to fit alpha's weight on).
  alpha        18a alignment score (primary).
  difficulty   -RG level (a higher level is harder: lower forecast).
  smaller_model  0.6B p(1-p), p = 0.6B pass rate on the same environment (signal a smaller model would see).
  random       fixed-seed permutation (np.random.default_rng(0)).
Secondary, declared now: rho_only, H_only, pass_band (-|p - 0.5|, p the 1.7B pass rate).

    python make_forecasts.py            # writes forecasts_18b.json (+ .sha256, forecast_ledger.jsonl); refuses to overwrite
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18b as K  # noqa: E402
import select_envs as S  # noqa: E402

PRIMARY = ["rho_h", "law_alpha", "alpha", "difficulty", "smaller_model", "random"]
SECONDARY = ["rho_only", "H_only", "pass_band"]


def _z(x: dict[str, float]) -> dict[str, float]:
    v = np.array(list(x.values()), dtype=float)
    sd = v.std() or 1.0
    return {k: float((val - v.mean()) / sd) for k, val in x.items()}


def compute_forecasts(rows: list[dict], selection: dict) -> dict[str, dict[str, float]]:
    from rl4cv.utility_model import paper_frozen_14b_model

    law = paper_frozen_14b_model()
    big = {r["env_id"]: r for r in rows if r["model_size_b"] == K.POLICY_SIZE_B}
    small = {r["env_id"]: r for r in rows if r["model_size_b"] == 0.6}
    pool = selection["pool"]
    sel = [s["env_id"] for s in selection["selected"]]
    pool_law = {e: law.env_term(big[e]["rho"], big[e]["H"]) for e in pool}
    pool_alpha = {e: big[e]["alignment"] for e in pool}
    zl, za = _z(pool_law), _z(pool_alpha)
    rng = np.random.default_rng(0)
    perm = rng.permutation(len(sel))
    out: dict[str, dict[str, float]] = {k: {} for k in PRIMARY + SECONDARY}
    zr = _z({e: math.log(big[e]["rho"]) for e in pool})
    zh = _z({e: big[e]["H"] for e in pool})
    for i, e in enumerate(sel):
        out["rho_h"][e] = float(pool_law[e])
        out["law_alpha"][e] = zl[e] + za[e]
        out["alpha"][e] = float(big[e]["alignment"])
        out["difficulty"][e] = -float(big[e]["level"])
        p6 = small[e]["pass_rate"]
        out["smaller_model"][e] = p6 * (1 - p6)
        out["random"][e] = float(perm[i])
        out["rho_only"][e] = zr[e]
        out["H_only"][e] = zh[e]
        out["pass_band"][e] = -abs(big[e]["pass_rate"] - 0.5)
    return out


def main() -> int:
    import json

    from rl4cv.forecast import freeze_forecast

    rows = list(K.C.read_jsonl(K.ENVS_18A))
    selection = json.loads(K.SELECTION_PATH.read_text())
    assert selection["envs_18a_sha256"] == K.C.sha256_text(K.ENVS_18A.read_text(encoding="utf-8")), "selection is stale"
    fc = compute_forecasts(rows, selection)
    doc = {"schema": "forecasts_18b/v1", "primary": PRIMARY, "secondary": SECONDARY,
           "higher_score_means": "larger predicted held-out gain", "envs_18a_sha256": selection["envs_18a_sha256"],
           "selected": [s["env_id"] for s in selection["selected"]], "forecasts": fc,
           "law": "rl4cv.utility_model.paper_frozen_14b_model().env_term(rho, H) (Eq. 7, paper Appendix D coefficients)"}
    entry = freeze_forecast(doc, K.HERE, "forecasts_18b", outcomes_observed=False)
    print(entry)
    for name in PRIMARY:
        top = max(fc[name], key=fc[name].get)
        print(f"{name:14s} picks {top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

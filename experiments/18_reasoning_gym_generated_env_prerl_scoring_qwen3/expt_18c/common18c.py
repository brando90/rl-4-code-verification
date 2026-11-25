"""Frozen definitions for experiment 18c (token-matched rerun of 18b); everything not listed here is imported unchanged from common18b.py."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
B18 = HERE.parent / "expt_18b"
sys.path.insert(0, str(B18))
import common18b as K  # noqa: E402,F401  (18b frozen definitions: HP, eval settings, run_name, train_spec, C = e18a_common)

C = K.C

SELECTION_PATH = K.SELECTION_PATH  # the same 16 environments as 18b (selection_18b.json, sha256 in PROTOCOL_18c.md)
FORECASTS_PATH = HERE / "forecasts_18c.json"  # byte-identical copy of forecasts_18b.json (same sha256)

# --- what changes against 18b (PROTOCOL_18c.md) ---
SEEDS = (0, 1, 2)  # 0 and 1 are 18b's item streams (first 40 steps identical in items), 2 is new
TOKEN_BUDGET = 2_000_000  # generated response tokens per run (EOS included, the 18b `response_tokens` count)
MIN_STEPS = 10  # never stop before this many updates (warm-up is 3)
MAX_STEPS = 1000  # step cap; a run that reaches it below TOKEN_BUDGET is budget_limited
ITEMS_PER_RUN = MAX_STEPS * K.HP["prompts_per_step"]  # 32,000 item indices per run; the first 1,280 are exactly 18b's
PREFIX_ITEMS = K.HP["steps"] * K.HP["prompts_per_step"]  # 1,280
NEAR_BUDGET = 1.25  # a run counts as matched when TOKEN_BUDGET <= tokens < NEAR_BUDGET * TOKEN_BUDGET (one-step overshoot allowed)
REPEAT_LIMITED_MIN_DISTINCT = 5_000  # an environment with fewer distinct questions than this in its 32,000-index stream is flagged repeat_limited

# 18c training hyper-parameters = 18b's, with `steps` replaced by the stopping rule (steps is only the stream length bound)
HP = dict(K.HP)
HP["steps"] = MAX_STEPS


def stop_reason(steps_done: int, cum_tokens: int) -> str | None:
    """None to continue; "budget" when the token budget is met after at least MIN_STEPS updates; "cap" at MAX_STEPS below budget.

    steps_done counts completed updates; cum_tokens is the cumulative generated response tokens after them.
    """
    if steps_done >= MIN_STEPS and cum_tokens >= TOKEN_BUDGET:
        return "budget"
    if steps_done >= MAX_STEPS:
        return "budget" if cum_tokens >= TOKEN_BUDGET else "cap"
    return None


def classify(steps: int, tokens: int, stop: str) -> str:
    """matched | budget_limited (hit the step cap below budget) | overshoot (met the budget but beyond NEAR_BUDGET x budget)."""
    if stop == "cap":
        return "budget_limited"
    return "matched" if tokens < NEAR_BUDGET * TOKEN_BUDGET else "overshoot"


def run_name(env_id: str, seed: int) -> str:
    return K.run_name(env_id, seed)

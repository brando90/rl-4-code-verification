"""Frozen definitions for experiment 18b (single-env GRPO selection test on Qwen3-1.7B); builds on expt_v1/e18a_common.py."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "expt_v1"
sys.path.insert(0, str(V1))
sys.path.insert(0, str(HERE.parents[2] / "src"))
import e18a_common as C  # noqa: E402,F401

ENVS_18A = V1 / "results" / "envs_18a.jsonl"
SELECTION_PATH = HERE / "selection_18b.json"
FORECASTS_PATH = HERE / "forecasts_18b.json"

POLICY_TAG = "qwen3_1p7b"
POLICY_SIZE_B = 1.7
SMALLER_TAG = "qwen3_0p6b"

# --- selection (PROTOCOL_18b.md) ---
N_SELECT = 16
MAX_PER_FAMILY = 3
MIN_PASS, MAX_PASS = 0.02, 0.98

# --- training (frozen before any job) ---
SEEDS = (0, 1)
TRAIN_SEED_OFFSET = 1_000_000  # item seed = probe_seed + 1_000_000 + 1000 * run_seed (never a probe item)
HP = {
    "steps": 40,
    "prompts_per_step": 32,
    "group_size": 8,
    "max_new_tokens": 1024,
    "temperature": 1.0,
    "top_p": 1.0,
    "top_k": 0,  # HF spelling of "no top-k"
    "lr": 3e-6,
    "warmup_steps": 3,
    "adam_betas": (0.9, 0.99),
    "adam_eps": 1e-8,
    "weight_decay": 0.0,
    "grad_clip": 1.0,
    "kl_coef": 0.0,
    "advantage": "r - mean_group(r), no std normalisation (Dr. GRPO), token-level loss normalisation",
    "micro_batch_seqs": 8,
    "weights": "bf16 model, fp32 master copy in AdamW",
}

# --- evaluation (identical for pre and post) ---
EVAL_N = 8
EVAL_MAX_TOKENS = 2048
EVAL_MAX_MODEL_LEN = 4608
EVAL_SAMPLING_SEED_BASE = 5000
ENV_PROBE_ITEMS = 64  # first 64 of the 18a probe items of the trained env (secondary, in-env)
TARGET_IDS = [f"rg/{fam}" for fam, _ in C.TARGET_RG] + [C.GSM8K_ID]


def eval_sampling_seed(spec: "C.SetSpec") -> int:
    return EVAL_SAMPLING_SEED_BASE + spec.set_index


def run_name(env_id: str, seed: int) -> str:
    return f"{env_id.replace('/', '__')}__s{seed}"


def train_spec(spec: "C.SetSpec", seed: int) -> "C.SetSpec":
    """The training-item spec of an environment: same family/level config, a train-only item seed."""
    import dataclasses

    return dataclasses.replace(spec, seed=spec.seed + TRAIN_SEED_OFFSET + 1000 * seed)


def hp_total_samples() -> int:
    return HP["steps"] * HP["prompts_per_step"] * HP["group_size"]

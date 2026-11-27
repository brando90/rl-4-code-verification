"""CPU memory budget and single-node admission for the four missing experiment 08 version-3 14B rungs.

This module does not launch training, import a GPU library, or read a validation outcome.
"""
from __future__ import annotations

# Empirical planning peak from results/multinode_eight_gpu_recovery02.json. The same
# receipt says this figure is not an upper bound.
PLANNING_PEAK_GIB = 73.18
PLANNING_PEAK_IS_UPPER_BOUND = False
# results.md, 10-18-2026: the skampere3 card that OOM'd was 178 GiB, with a foreign
# process holding 130.69 GiB. scripts/cc_prompt_run_experiment_on_snap.md lists the
# node as 8× B200, about 179 GiB.
RECORDED_OOM = {
    "host": "skampere3",
    "when": "10-17-2026 22:03 PDT",
    "during_step": 184,
    "last_completed_step": 183,
    "segment_target_step": 335,
    "condition": "E",
    "foreign_process_gib": 130.69,
    "card_gib": 178,
}
# Public Qwen3 Base vocabulary (Qwen/Qwen3-14B-Base config). Not re-downloaded here.
QWEN3_VOCAB = 151936
GEMMA3_VOCAB = 262144
GEMMA_SMOKE_LONGEST_TOKENS = 17221
MAX_SEQ = 16384
TENSOR_PARALLEL = 8

# Free-memory floors leave room above the non-upper-bound 73.18 GiB peak.
# 160 GiB on a ~178 GiB B200; 120 GiB on an H200 (idle H200s reported 143,157 MiB free
# on 11-25-2026). A100-80GB is refused: 73.18 GiB is not an upper bound and the margin
# on an 80 GB card is under 7 GiB.
HOST_BUDGET = {
    "skampere3": {
        "kind": "B200",
        "min_total_mib": 170_000,
        "min_free_mib": 160 * 1024,
        "max_used_mib": 0,
        "max_utilization": 0,
        "gpus_required": 8,
    },
    "skampere2": {
        "kind": "H200",
        "min_total_mib": 130_000,
        "min_free_mib": 120 * 1024,
        "max_used_mib": 0,
        "max_utilization": 0,
        "gpus_required": 8,
    },
}
HOST_PRIORITY = ("skampere3", "skampere2")
REFUSED_HOSTS = {
    "skampere1": (
        "A100-80GB is refused for this tensor-parallel 14B rank: the 73.18 GiB planning "
        "peak is not an upper bound, so an 80 GB card has no safe margin"
    ),
}

# Already set in configs/e08_v3_{E,R}_14B.yaml. This relaunch does not change them.
LOCKED_TRAINING = {
    "precision": "bfloat16",
    "train_global_batch_size": 2,
    "train_micro_batch_size": 1,
    "max_total_sequence_length": 16384,
    "activation_checkpointing": True,
    "cpu_offload": False,
    "tensor_parallel_size": 8,
    "context_parallel_size": 1,
    "sequence_packing": False,
}
# Allocator flag only. The Gemma smoke note (11-26-2026) records no numerical effect.
LAUNCH_ENV = {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}

# Scientific rungs, in launch order. Expansion first, because the dead job was E and
# the historical sequencer trains E before R. Steps are the frozen schedule checkpoints.
RUNGS = (
    {"system": "v3_E_14b_f0p5", "condition": "E", "fraction": "f0p5", "step": 335, "declared_cells": 1080},
    {"system": "v3_E_14b_f1p0", "condition": "E", "fraction": "f1p0", "step": 667, "declared_cells": 1080},
    {"system": "v3_R_14b_f0p5", "condition": "R", "fraction": "f0p5", "step": 334, "declared_cells": 1080},
    {"system": "v3_R_14b_f1p0", "condition": "R", "fraction": "f1p0", "step": 658, "declared_cells": 1080},
)
MEASURED_CELLS_UNTOUCHED = 12960
DECLARED_VALIDATION_CELLS = 17280
MISSING_CELLS = 4320
START_WEIGHTS = "ckpt/14B/hf/step_658"


def logit_gib(seq_tokens: int, vocab: int, *, bytes_per_elem: int = 4, tensor_parallel: int = 1) -> float:
    """GiB of one full logit tensor. tensor_parallel shards the vocabulary, as NeMo TP does."""
    if seq_tokens < 1 or vocab < 1 or bytes_per_elem < 1 or tensor_parallel < 1:
        raise ValueError("logit size arguments must be positive")
    if vocab % tensor_parallel != 0:
        raise ValueError("vocabulary is not divisible by the tensor-parallel size")
    return seq_tokens * (vocab // tensor_parallel) * bytes_per_elem / 2**30


def chunked_lm_head_applies() -> dict:
    """The v28 Gemma chunked-loss fix is not the binding cause of the recorded 14B OOM.

    Gemma-3 on one GPU materialises fp32 logits of shape (sequence, 262144). Qwen3 under
    the locked tensor-parallel size 8 shards that projection. Activation checkpointing and
    microbatch 1 are already on in the 14B YAML.
    """
    gemma = logit_gib(GEMMA_SMOKE_LONGEST_TOKENS, GEMMA3_VOCAB, tensor_parallel=1)
    qwen_unsharded = logit_gib(MAX_SEQ, QWEN3_VOCAB, tensor_parallel=1)
    qwen_tp8 = logit_gib(MAX_SEQ, QWEN3_VOCAB, tensor_parallel=TENSOR_PARALLEL)
    return {
        "applies_to_this_oom": False,
        "reason": (
            "locked layout is NeMo tensor parallel 8 with activation checkpointing already "
            "true and microbatch 1; the recorded failure is a foreign allocation on skampere3, "
            "not an unsharded 262144-way logit tensor"
        ),
        "gemma3_unsharded_fp32_logits_gib": gemma,
        "qwen3_unsharded_fp32_logits_gib_at_16384": qwen_unsharded,
        "qwen3_tp8_fp32_logits_gib_at_16384": qwen_tp8,
        "do_not_enable_cpu_offload": True,
        "do_not_edit_locked_yaml": True,
    }


def work_root(hostname: str, user: str) -> str:
    """SNAP work directory. Never DFS home."""
    host = hostname.split(".")[0]
    if host not in {"skampere1", "skampere2", "skampere3"}:
        raise ValueError(f"unsupported host {hostname}")
    if not user or "/" in user or user in {".", ".."}:
        raise ValueError("user must be a single path segment")
    return f"/lfs/{host}/0/{user}/rl4cv_e08_v3_r1_14b"


def _device_ok(device: dict, budget: dict, apps: list[dict]) -> str | None:
    uuid = device["uuid"]
    foreign = [a for a in apps if a.get("uuid") == uuid]
    if foreign:
        return f"gpu {device['index']}: foreign compute pid {[a.get('pid') for a in foreign]}"
    if device["total_mib"] < budget["min_total_mib"]:
        return f"gpu {device['index']}: total {device['total_mib']} MiB below {budget['min_total_mib']}"
    if device["used_mib"] > budget["max_used_mib"]:
        return f"gpu {device['index']}: used {device['used_mib']} MiB"
    if device["free_mib"] < budget["min_free_mib"]:
        return f"gpu {device['index']}: free {device['free_mib']} MiB below {budget['min_free_mib']}"
    if device["utilization"] > budget["max_utilization"]:
        return f"gpu {device['index']}: utilization {device['utilization']}"
    return None


def admit_node(inventories: dict) -> dict:
    """Pick eight exclusive GPUs on one node: B200 skampere3, else H200 skampere2.

    inventories maps a host name to {"devices": [...], "apps": [...]}. A device needs
    index, uuid, total_mib, used_mib, free_mib and utilization. This never selects
    skampere1 and never splits one job across hosts.
    """
    reasons: list[str] = []
    for host in HOST_PRIORITY:
        budget = HOST_BUDGET[host]
        inv = inventories.get(host)
        if not inv:
            reasons.append(f"{host}: no inventory")
            continue
        devices = list(inv.get("devices") or [])
        apps = list(inv.get("apps") or [])
        indexes = {d["index"] for d in devices}
        if indexes != set(range(budget["gpus_required"])) or len(devices) != budget["gpus_required"]:
            reasons.append(f"{host}: need GPUs 0-7, saw {sorted(indexes)}")
            continue
        problems = [msg for d in devices if (msg := _device_ok(d, budget, apps))]
        if problems:
            reasons.append(f"{host}: " + "; ".join(problems))
            continue
        return {
            "admitted": True,
            "host": host,
            "kind": budget["kind"],
            "gpus": list(range(8)),
            "min_free_mib": budget["min_free_mib"],
            "planning_peak_gib": PLANNING_PEAK_GIB,
            "planning_peak_is_upper_bound": False,
            "launch_env": dict(LAUNCH_ENV),
            "reasons": reasons,
        }
    for host, why in REFUSED_HOSTS.items():
        reasons.append(f"{host}: {why}")
    return {
        "admitted": False,
        "host": None,
        "kind": None,
        "gpus": [],
        "min_free_mib": None,
        "planning_peak_gib": PLANNING_PEAK_GIB,
        "planning_peak_is_upper_bound": False,
        "launch_env": dict(LAUNCH_ENV),
        "reasons": reasons,
    }


def planned_command(admission: dict, condition: str) -> list[str]:
    """Argv of the locked single-node continuation. Does not start a process."""
    if condition not in {"E", "R"}:
        raise ValueError("condition must be E or R")
    if not admission.get("admitted"):
        raise ValueError("refusing a command when admission failed")
    gpus = ",".join(str(i) for i in admission["gpus"])
    env = [f"{key}={value}" for key, value in LAUNCH_ENV.items()]
    return ["env", *env, "bash", "train_continuation.sh", condition, "14b", gpus, "production"]


def foreign_pids(apps: list[dict], owned_pids: set[int], leased_uuids: set[str]) -> list[int]:
    """Compute PIDs on leased GPUs that are not in the job's own set. The watchdog stops before the next step if this is non-empty."""
    found = []
    for app in apps:
        if app.get("uuid") not in leased_uuids:
            continue
        pid = int(app["pid"])
        if pid not in owned_pids:
            found.append(pid)
    return sorted(set(found))

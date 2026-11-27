"""Check the 11-27-2026 02B v2 config against the locked protocol constants. It never marks the run admitted."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPT = HERE.parent
CONFIG_NAME = "production_config_11-27-2026.json"
MANIFEST = EXPT / "results/training_readiness_manifest_2026-10-06.json"

REQUIRED_UNSET = (
    "group_size", "response_cap_tokens", "rollout_token_cap",
    "learning_rate", "dtype", "mismatch_baseline",
)


def load(path: Path | None = None) -> dict:
    return json.loads((path or (HERE / CONFIG_NAME)).read_text())


def validate(config: dict, manifest: dict) -> dict:
    """Return PREPARED_NOT_ADMITTED plus the blockers still required before any GPU launch."""
    blockers: list[str] = []
    model = manifest["model_and_code"]
    design = manifest["design"]
    if config.get("status") != "PREPARED_NOT_ADMITTED":
        blockers.append("status must stay PREPARED_NOT_ADMITTED until references, probes and a forecast exist")
    if config.get("training_entrypoint") is not None:
        blockers.append("training_entrypoint must stay null; this folder has no Lean GRPO entrypoint")
    pinned = config.get("model") or {}
    if pinned.get("id") != model["candidate_initialization"]:
        blockers.append("model id drifted from the 10-06-2026 readiness manifest")
    if pinned.get("revision") != model["reachable_local_revision"]:
        blockers.append("model revision drifted from the 10-06-2026 readiness manifest")
    if pinned.get("weights_rehashed_this_commit") is not False:
        blockers.append("this commit did not re-hash the Hugging Face snapshot")
    got = config.get("design") or {}
    if got.get("environments") != design["environments"]:
        blockers.append("environments must stay full_file and theorem_completion")
    if got.get("seeds_per_environment") != design["seeds_per_environment"]:
        blockers.append("seeds per environment must stay 2")
    if got.get("optimizer_steps_per_trajectory") != design["optimizer_steps_per_trajectory"]:
        blockers.append("optimizer steps must stay 64")
    if got.get("declared_trajectories") != design["declared_trajectories"]:
        blockers.append("trajectory count must stay 4")
    if got.get("reward") != "kernel_binary":
        blockers.append("reward must stay kernel_binary")
    if got.get("lean") != "4.22.0":
        blockers.append("Lean must stay 4.22.0")
    if got.get("protected_corpus") != "all_VeriBench" or got.get("veribench_in_training") is not False:
        blockers.append("VeriBench stays out of training, tuning and checkpoint selection")
    if got.get("seed_values") is not None:
        blockers.append("seed integers are not in the locked protocol; leave them null")
    unset = config.get("unset_because_the_locked_protocol_does_not_name_them") or {}
    for key in REQUIRED_UNSET:
        if unset.get(key) is not None:
            blockers.append(f"{key} is not named by the locked protocol and must stay null")
    blockers.extend([
        "Accepted reference proofs are still missing: VERINA originals are 6/24 kernel-honest, 16/24 forbidden sorryAx, 2/24 unknown (phase A v2 results.md). The 11-25 adapter's 24/24 support is a behavioral gate, not proof acceptance.",
        "No measured pre-RL rho and H on the two external environments, so freeze_forecast must not be given a winner or a delta.",
        "No vLLM-versus-trainer mismatch baseline for this Qwen3-1.7B-Base revision, so dtype stays unset.",
        "paper_frozen_14b_model() is an OpenR1-Math fit. It is not a Lean-fold standardizer and cannot fill the forecast.",
    ])
    return {
        "status": "PREPARED_NOT_ADMITTED",
        "admitted": False,
        "blockers": blockers,
        "model": {"id": model["candidate_initialization"], "revision": model["reachable_local_revision"]},
    }


def main() -> int:
    report = validate(load(), json.loads(MANIFEST.read_text()))
    print(json.dumps(report, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

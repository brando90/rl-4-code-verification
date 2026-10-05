# Run and verify the retained artifact audit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v1/cc.md>

**TLDR:** Run the frozen deterministic audit on the Stanford Network Analysis Project (SNAP) host and publish its availability verdict. Success means every input hash verifies, every saved row and declared original version-1 cell is accounted for, and reports and receipts are retained. Do not run models, judges, training or proof search, and do not treat historical replay as strict kernel proof credit.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

Read the current shared index and repository CLAUDE.md, then this experiment's PROTOCOL.md. Preserve unrelated work. This version invokes only Python's standard library, so no model executor or account credit is needed. The local coordinator owns publication to main under the repository convention.

The snapshot lives under `/lfs/skampere1/0/brando9/rl4cv_azalia_audit/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/`. It is a dedicated artifact directory, not another agent's working tree. The named terminal session is `rl4cv-azalia-artifact-audit`. Audit budget: one processor, at most 300 seconds, zero model calls, zero graphics processors, zero new provider charges. No automatic retries or new experimental conditions. A failed deterministic command may be repaired, with its failed receipt preserved and a new receipt path.

Before running, compare transferred script, protocol and input-manifest hashes. Execute `expt_v1/run_audit.sh` in the named remote session. Its timeout and exit record provide a non-model completion observer; this short bounded command does not claim general unattended agent recovery. Confirm `results/audit.json`, `RESULTS_existing_artifacts.md` and `execution_receipt.json` exist, their hashes agree, and exit code is zero. An ended session alone is not success.

A long or dispatched run keeps results.md live in the repo, not a report at the end. Update the experiment-root results.md at launch and whenever a meaningful result lands, with exact denominator, outcome and limitation. The coordinator mirrors remote progress and publishes task-owned records if the deterministic worker cannot push. Keep CKPT_azalia.md resumable.

Run the experiment's targeted tests and repository `make test`, inspect the exact staged diff for secrets and scope, then commit and push explicit paths. Do not change pinned scorers, benchmark references or the existing experiments. Do not start PLAN.md's later stages under this version; they require a separately frozen manifest and validated endpoint harness.

**TL;DR:** Verify the frozen inputs, run a zero-model-call remote inventory, and publish the retained-data feasibility report. No fresh benchmark or training outcome is claimed.

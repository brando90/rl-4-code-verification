# Overnight factored-score training checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1/CKPT_e09.md>

**TLDR:** Brando approved automatic overnight experiments on 10-08-2026. Freeze and execute the three-arm exploratory comparison, preserving full factor semantics, common evaluation and cluster ownership.

Created: 10-08-2026 19:01 PDT. Current status: **FAILED_TECHNICAL_GATE**, 10-08-2026. The historical updates below are retained; this paragraph and the terminal section supersede their running/pending status.

Master: Codex thread `01a11d6a-30aa-7020-a672-6b34546fdeee`; checkpoint `experiments/CKPT_MASTER_tmuxnone_cxd_01a11d6a.md`. No training launched yet.

Run identity: `0c84fdc2-d5cf-4a04-9137-e214edbd8c36`; start 2026-10-09T02:13:36Z; hard deadline 2026-10-09T18:13:36Z; maximum two A100 devices / 32 device-hours / 200 GiB new owned data / eight scorer workers.

Verified 10-08-2026 19:51 PDT: source NeMo RL is exactly `c751f811217db7df0d4c94abdeaada6626cfc150`; the step-658 Qwen 1.7B config and tokenizer SHA-256 values are in the sanitized runtime receipt. The experiment-08 owner supplied a locked lease interface and active acknowledgement. A bounded lease on GPU 3 passed Qwen3 1.7B raw-feedback/context preflight and was released at 2026-10-09T02:42:44Z. Both validated Vals judge configurations completed 25/25 live positive/negative control cells and the control gate passed. The one-worker frozen-scorer adapter control passed all 14 files in about five minutes; its receipt is owned by experiment09. CPU remains saturated, so this timing is capacity evidence rather than an authorization for unbounded CPU work.

The validated judge control service was torn down at 2026-10-09T02:55:44Z after harvest; its port is free and no child remains. An experiment09-owned NeMo checkout is pinned at the required commit with its declared submodules initialized. Its isolated vLLM actor environment is provisioning; it is not yet a usable trainer and no GPU lease is held.

Historical next action: verify the isolated actor environment, finish the actual two-turn optimizer path and run the fixed 256-rollout calibration. Superseded by the terminal gate below; no new admission.

## Terminal gate — 10-08-2026

Actual real rollout: 32 two-turn disposable trajectories, 64 short technical responses, 4,077 assistant tokens. Boundary/mask/terminal-only reward/final-metadata audit PASS. Old-policy calculation failed before optimization; exact-batch read-only replay found 4/4,077 out-of-support actions and 367/4,073 finite-action absolute log-probability errors above the prospective .05 tolerance (maximum .7402789593). Recomputed support permitted zero mismatches. The candidate is not admitted; no probability floor, sample deletion/replacement or sampler change was used.

No optimizer/save-reload/refit or full-context memory gate passed. No horizon or main-training freeze exists. Calibration 0/256 rollouts, 0/512 responses; trajectories 0/6; validation 0/945; test 0/1554. All 2,499 aligned factor/strict-target rows and 2,142 before/after rows preserve nulls. Test source/outcomes remain unopened. This is a technical implementation failure, not a measured learning effect or failed differentiation gate. The original wall deadline/capacity is not exhausted; the one bounded integration's actual compatibility gate failed.

Final checks: repository 158 passed/4 skipped; separate native adapter suite 42 passed. Ten initialization-manifest file hashes verified. Existing 14/14 scorer controls and both 25-rating judge suites were preserved, not rerun; 50 measured ratings cost $3.0558, not a 50/50 accuracy claim. On-policy compiler/judge service transport exists but was not admitted or live-verified.

All owned leases released; reserved device-hours .553611; no registered child or run-tagged control remnant. Preserve the earlier unverified physical-device incident rather than claiming every attempt had verified identity. Whole-runtime plus conservatively charged whole uv cache about 51.4 GiB; original disk/deadline limits unchanged. Parent watchdog/lock/attempt ledger untouched. Published source snapshots distinguish failed control from diagnostic extension. See `../results.md`, `execution_manifest.json`, `results/technical_gate.json`, `results/resource_closeout.json` and `results/aligned/`. After publication, `results/terminal_receipt.json` and the private runtime `terminal_receipt.json` bind the actual results commit. Do not restart or launch follow-on training under this terminal run.

## Recovery attempt 2 — 10-08-2026 20:47 PDT

Same session/run/deadline; actual native turn metadata is `gpt-6-astra` / `ultra`, `danger-full-access`, approval policy `never`. Parent owns the coordinator attempt ledger/lock and unchanged ordinary-code watchdog. Private `owner_recovery_ack.json`, `supervisor_mailbox_ack.json`, `progress.json` and real `child_receipts.json` are under the runtime root. No model-worker fan-out or reviewer was launched.

Owned actor imports pass. The adapter preserves T=.6, top-p=.95, top-k=20 and matches pinned native support semantics; current candidate is one full-batch optimizer update with zero reference-KL coefficient. Twenty-seven deterministic adapter tests pass, including actual pinned rollout code with transport doubles and the real Qwen tokenizer. Full project tests: 145 passed, 4 skipped. No real optimizer/save-reload control has passed, so this is not an execution freeze.

GPU receipts: initial CUDA enumeration was not UUID-verified and engine initialization failed; PCI ordering and UUID checks now bind driver/worker to the admitted physical device. Another user's process then appeared after the next lease, stopping both that initialization and its one identical contention retry before generation. All healthy foreign work remained untouched; failed leases were released. A pre-engine foreign-process check and 90-second quiet-window admission guard are prospective. The current child waits under the fixed technical budget, not as a claim of study completion.

Train-only prompt audit covers 539/539 tasks, maximum 7,757 tokens. Conservative full two-turn context bound is 32,241; candidate context increased to 32,768 before measurement. Schedule code preserves all 539 tasks cyclically, including the final three. Exact-six-rating queue validates both three-rating medians and blocks the entire batch on missing/duplicate/error/hash-mismatched constituents; real on-policy transport remains to be verified. No completed judge control was rerun. Total measured control charges remain $3.0558.

Native subscription telemetry now reports 20% weekly included allowance used (80% remaining); credit presence does not authorize credit spending. No allowance/credit/spending settings were changed. Scientific counts remain calibration 0/512 responses, main 0/6 trajectories, validation 0/945, test 0/1554. No held-out source/outcome has been opened and no endpoint exists.

Updated 20:54 PDT: 28 native adapter tests pass; full repository check is 146 passed, 4 skipped. Completion-reminder-inclusive prompt bound is now 7,893 + 16,384 + 8,236 = 32,513 tokens. The reminder is adapted only for the absence of execution tools and the required Lean-only response; all arms and both turns share it. An offline three-task judge pack round trip passed without a call. Backend source snapshots and hashes are recorded under `adapters/`; reverse-apply validation passed. The pending real control uses the prospective 32,768 context and a foreign-process quiet-window guard.

Updated 21:11 PDT: native adapter tests **29 passed**, repository **146 passed, 4 skipped**. Engine initialization passed on the leased physical GPU. The training worker exposed a constant-scheduler configuration-shape error before generation; corrected to the supported dictionary form. A subsequent technical setup was interrupted before generation to remove an initialization-flag exemption that could survive a spawned engine. Only the native synthetic sampler-warmup stack now exempts strict sampling-metadata checks, with an inherited-flag negative test. The `profile_scope_fix` child is registered and active; no real optimizer/save-reload or scientific gate has passed. Technical response cap was prospectively declared as 65 short responses, including one post-update refit probe, before any response was generated. Original deadline/caps unchanged; no completed judge/scorer control rerun.

# Factored-score model learning, repair validation and Lean recovery

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/CKPT_MASTER_tmuxnone_cxd_01a11d6a.md>

**TLDR:** Brando approved automatic overnight model-improvement experiments on 10-08-2026. The new factored-score reinforcement-learning study has passed scorer and live judge controls but has no calibration or training outcomes; its implementation owner was recovered in the same session. The warm-start study continues. The repair study exhausted its coordinator allocation before official admission and is now explicitly blocked.

Created: 10-08-2026 16:28 PDT. Last updated: 10-08-2026 20:18 PDT. **Status:** ACTIVE for learning and warm-start supervision; repair allocation blocked.

## 1. Identity and recovery

Codex desktop on Brando's Mac; thread `01a11d6a-30aa-7020-a672-6b34546fdeee`; no tmux. Owned detached checkout: `/Users/brandomiranda/.codex/worktrees/factor-feedback-validation/rl-4-code-verification`, starting commit `e6f31b836c976923020af33a0e3ce850b41f317b`. Resume with `codex resume 01a11d6a-30aa-7020-a672-6b34546fdeee`. Runtime identifies the Codex family; exact parent backend model/effort are not exposed to this tool session, so configured master defaults are not represented as measured metadata. Effective permissions: danger-full-access / never.

Preserve the original shared checkout and other owners' dirty files. Publish only validated owned paths directly to main after deterministic checks. The requested single opposite-company review of the repair implementation is already complete; no new reviewer is requested. No email or other-chat messages are authorized.

## 2. Current measured state

| Experiment | Verified state and declared denominators |
|---|---|
| `09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` | Scorer controls 14/14 matched expected outcomes. Live coverage controls 50/50 measured ratings, all frozen category gates passed; this is not a claim of 50/50 expected-label accuracy. Read-only model/feedback forward pass passed. Calibration 0/256 rollouts, 0/512 responses; training 0/6 trajectories and zero optimizer updates; validation 0/945 cells, test 0/1,554 cells. Actual two-turn optimizer, sampler, loss-mask and save/reload controls remain pending. |
| `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` | At 20:03 PDT, 8/20 matched validation rungs fully scored (8,640 scored responses in those eight rungs). The 1.7B full-data rung has 7/8 scorer shards, the 4B full-data rung 5/8. The 8B 12.5% and 25% generations each completed 1,080/1,080 responses and are scoring; 50%/75% generations run on leased devices 3/6. Five exports each exist for 1.7B/4B/8B; 14B training remains pending. No checkpoint-selection or held-out test manifest has been admitted. |
| `06_swebench_lite_factor_feedback_matched_budget` | Version 3 BLOCKED: all 3/3 coordinator launches used. Last owner exited at 19:34:21 PDT with `error_max_turns`, 90 configured turns/91 reported. Official controls 0/16, author calls 0/8, solver cells 0/56. Five preliminary smoke executions remain non-admitted; four lacked enforced CPU/memory bounds and the fifth failed its observer. This is infrastructure/coordinator blockage, not evidence about repair efficacy. |
| `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics` | Phase-A version 3 completed/PARTIAL in `572e28f`: 587 kept pairs over 455/970 tasks, 42/2,910 cells unmeasured. Below frozen SUFFICIENT thresholds of 1,024 pairs and 512 tasks. Do not restart completed work. |

These are descriptive execution counts, not estimated treatment effects; confidence intervals and significance tests are not applicable to this status table. Learned model-weight improvement, repair improvement and correlation remain separate questions.

## 3. Learning study owner and recovery

`09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` runtime: `skampere1:/lfs/skampere1/0/brando9/rl4cv_e09`; run `0c84fdc2-d5cf-4a04-9137-e214edbd8c36`; boot `83765e57-f5f3-4202-b7b4-18f1eb506043`. Start 10-08-2026 19:13:36 PDT; absolute deadline **10-09-2026 11:13:36 PDT**. Maximum two A100 devices, 32 device-hours, eight scorer workers, 200 GiB new owned data and three coordinator attempts. No budget or clock was reset.

Attempt 1 used personal Codex 0.154.0, actual gpt-5.6-terra/high, danger-full-access/never, native session `01a11e70-91cc-72c1-8ab7-a9dfe8494a3e`. It published the primitives and controls, then exited normally at 20:06 PDT with unfinished integration and dependency compilation children surviving. A live coordinator or compiler was never counted as training.

Parent confirmed the old writer stopped and the exclusive coordinator lock was free. The last checked installer PID 3293058 and matching compilation children were gone before recovery; the new owner must inspect built artifacts and adopt any other healthy owned children before reinstalling. Attempt 2 resumed the same native session at **20:14:44 PDT**, named tmux **`codex-rl4cv-e09-grpo-resume2`**, coordinator PID 3559408/start ticks 1683853. The actual native turn context verifies **gpt-6-astra/ultra**, approval policy never, danger-full-access and the owned directory. Successful actions read the mailbox/integration map, original run/exit records and refreshed instructions. `parent_resume2_verification.json` records actual metadata and first useful actions. The first launch record retained its old static tmux label; the verification receipt gives the actual name and the launcher was corrected for subsequent attempts. **2/3 attempts used; no fresh budget.**

The stronger implementation executor is justified by concrete sampler/probability and multi-turn correctness requirements, not a new acceptance review. Desktop Pro usage was observed at 86% weekly allowance remaining, ordinary included usage enabled, no purchased balance/overage; exact remote profile allowance is not separately exposed. One implementation owner, no extra model-worker fan-out; estimated next integration phase 30–90 minutes before reassessment, with finalization reserve. Preserve scientific model pins. Measured judging remains Vals-funded Valkyrie; no personal measured fallback, credit purchase, reset, direct provider call or shared-configuration change.

Private recovery artifacts at the runtime root: `parent_resume2_receipt.json`, `parent_resume2_verification.json`, `recovery_brief_10-08-2026.md`, `integration_next.md`, `supervisor_mailbox.md`, `owner_attempt_2.events.jsonl`, `coordinator_attempts.json`, `owner_launch.json`, and verified `owner_recovery_ack.json`/`supervisor_mailbox_ack.json`. Both acknowledgments confirm the exact transferred digests, model, permissions and unchanged deadline. The owner bounded this integration attempt through 10-08-2026 22:15 PDT, with a one-hour finalization reserve; the original experiment deadline remains authoritative. Integration handoff SHA-256: `6dc494d5bcf23dbd2e4bdd035d2e3b2211835216bf58291ef95062310f170949`. The handoff explicitly distinguishes source-verified defects from an unimplemented adapter candidate.

### Admission requirements still pending

- The pinned NeMo Reinforcement Learning source rejects frozen temperature 0.6, top-p 0.95 and top-k 20. Its current generation/training log-probabilities do not consistently implement that truncation. Do not remove guards alone or silently change sampling. An owned probability-consistent adapter requires numerical support/order/gradient controls and a real disposable optimizer/save-reload test. A zero Kullback–Leibler penalty with one optimizer step per complete batch is an unimplemented candidate within still-unfrozen optimizer choices, not a certified solution.
- Real rollout code tokenizes raw feedback without applying a chat template; the existing rendering helper is not proof of actual message boundaries. Verify the real token stream and assistant-only loss masks, retain final trajectory measurements durably, seed generation correctly, isolate Ray and preserve all 539 training tasks in scheduling.
- The actor runtime is an experiment09-owned clone at pinned NeMo commit `c751f811217db7df0d4c94abdeaada6626cfc150`; verify completed imports/versions. Do not mutate experiment08's environment or treat its newer generation packages as compatible substitutes.
- Complete the real coverage-judge queue: at most six constituent ratings per eligible file, exact validated aggregation, correct cache identity and missing-rating batch blocking. Completed 50 control ratings must not be repeated.
- Only then run the frozen first 32 training tasks × 8 rollouts. Require positive within-group smooth-score variance and at least one full smooth score unequal to the strict conjunction. Do not add tasks to rescue a failed gate. Choose the largest horizon from 32/16/8 by full-pipeline throughput only, freeze runtime/optimizer, then execute six trajectories.
- Freeze all six endpoint hashes before the common one-turn, no-feedback held-out test evaluation. Preserve the aligned per-item factor matrix, strict target, regressions and every missing declared cell.

### Completed control evidence

The scorer accepted/rejected all 14 expected controls. The GPU preflight was a read-only forward pass with 18 feedback tokens, not full-context training or a real two-turn optimizer test. Its lease was released at 19:42:44 PDT; about 0.078 device-hours was recorded at that boundary.

Both live coverage-judge configurations completed 25/25 control cells: `H2_sol_high` (selector `openai/gpt-6-sol-high`, high) and `H2_opus55_max` (selector `anthropic/claude-opus-5-5-no-fallback`, max). Each used frozen rubric `H2_human_mirror_conventions_demos` and maximum 32,000 tokens. Each category gate passed: blank/oracle/shuffled/vacuous 5/5 expected; half-deletion 4/5 in the accepted score range 1–4 against the prospectively frozen 80% threshold. Reported completed charges were $0.5979 + $2.4579 = $3.0558; earlier failed-admission charges were not reported and remain unknown. Judge run identifiers and receipts are in `receipts/judge_e09/state.json` and `controls_check.json`. The collect-only service/tunnel was torn down after harvesting. No new control calls are needed.

## 4. Warm-start owner and shared devices

`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` remains with original Claude session `d3968eac-37d1-4b77-b339-a69389689c9c`, tmux `claude-rl4cv-e08-recovery`, runtime `skampere1:/lfs/skampere1/0/brando9/rl4cv_e08`. Original launch verified Fable 5.1/high and full permissions; a later owner acknowledgment said max, so retain that discrepancy rather than infer actual effort. At 20:03:49 PDT the current pipeline PID 3371983 had fresh progress; the independent watchdog checked at 20:00:03 PDT within its 15-minute cadence. Preserve all completed exports/generations and source pins; no duplicate teacher sampling.

The original owner repaired isolation after two experiment09 failed-admission records were misplaced in experiment08 judge state. Both lacked run identifiers. Exact original bytes were archived at `expt_v1/results/judge/incidents/e09_misplaced_controls_state_10-08-2026.json`, SHA-256 `783111ade27d9432c274474cec8053191ba053b89926d5934ff16388a30cdfbe`, with a provenance receipt. The active misplaced file was removed, and `pipeline_e08.py` now rejects foreign benchmark/failed-admission records for its own gates. Published `55d32e2`, integrated in `5f6048c`. Experiment09's bridge state routing was fixed separately in `751a0f6`; no completed controls were rerun.

Use only the shared lease tool at the experiment08 repo's `expt_v1/scripts/gpu_lease_e08.py` and registry `/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/leases.json`. Inventory errors fail closed. At 20:03 PDT only device 7 was idle; devices 3/6 belonged to experiment08 and 0–2/4–5 to other users. Read fresh state before admission; these are not reservations. A lease must name the real bounded calibration/trajectory driver, never the coordinator. Release/re-request at each trajectory boundary, respect 14B admission priority and never kill healthy work. One-device execution is prospectively allowed within the unchanged maximum if actually validated.

## 5. Repair allocation blocked and preserved

`06_swebench_lite_factor_feedback_matched_budget`, version 3, runtime `skampere2:/var/tmp/brando9-rl4cv-e06-v3` (symlink `/lfs/skampere2/0/brando9/rl4cv_e06_v3`). Original start 10-08-2026 16:50 PDT/deadline 10-09-2026 10:50 PDT and all 18-hour/160-processor-hour, container, storage and headroom limits remain unchanged. First Codex Vals authentication failure, second Claude launch and third same-session resume exhaust the 3-attempt allocation. Last actual coordinator was Sonnet 5/high with bypassPermissions, session `ce1f226b-000e-4413-adc8-5030d07dfee6`; its exit was a turn limit, not authentication or quota exhaustion.

Published receipt **`c53c0e2`**: `experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v3/results/supervision_blocked_10-08-2026.json`, also copied to runtime `blocked_receipt.json`. It retains all 16 null official-control cells and conditional 8 author/56 solver denominators, the five non-admitted smokes, unresolved cumulative resource/payer/provenance gates and runtime-test failures. Version 3 isolated tests: 146 passed / 2 failed; separate repository tests 113 passed / 11 skipped. These are distinct from parent main's passing suite. Backend clean imports still miss dependencies; no official measured admission occurred.

Twenty-three unfinished owner files were preserved without publishing them as validated source: `supervision/pending_owner_changes_10-08-2026.tar.gz`, SHA-256 `cc6c35bb5cd888925d9813de56af9b529ca8525a2d4d711e43b91c0a2ac0d4d1`. No coordinator, scientific child or owned container remained at verification. Only the experiment06 observer and its exact tagged cron entries were stopped; receipt `supervision/observer_cleanup_receipt.json`. Do not launch a fourth coordinator, reset budgets or count incomplete infrastructure as a negative efficacy result. Future measured recovery needs a revised explicit allocation, not an automatic follow-on experiment.

## 6. Watches and continuation

The experiment09 ordinary-code watcher is **`parent_watchdog_e09.py`**, two-minute/reboot cron, exclusive watcher lock, run/boot/PID/start identity checks, bounded recovery and no model polling. Updated source SHA-256 **`f9b6b676d87b9b432d64219ba751755996b36fb274148cf95ee6ae9badb067f8`** exposes pending mailbox state; 24 harmless tests passed locally and remotely, receipt `parent_watch_update_receipt.json`. The earlier observation-only watchdog remains preserved but stopped. Register detached drivers in `child_receipts.json` before directory changes. Healthy surviving children prevent automatic coordinator duplication. Authentication/allowance/model-access failure and exit-zero without terminal evidence require changed-evidence clearance. The launcher enforces the exclusive coordinator lock, original deadline and at most 3 attempts. Mere terminal-file presence is not scientific completion.

Current-chat heartbeat **`overnight-factored-score-learning`** remains ACTIVE every 45 minutes. Keep unchanged checks quiet; notify meaningful progress, failure, completion or required user action only. After original deadlines, finalize results and missing-cell accounting, then pause the heartbeat when the final report is published or every remaining task needs concrete external intervention. The Mac/app must be available for desktop follow-ups; remote watchers are independent. No fourth repair owner or unapproved follow-on study.

SSH must use `-S none -o ControlMaster=no`; SCP uses `-o ControlPath=none -o ControlMaster=no`. Restore native remote shell with `/dfs/scratch0/brando9/.bashrc`; never assign HOME manually. At 20:10 PDT, skampere1 health passed relevant native-shell/authentication/LFS checks (about 8,523 GiB free, 85% used). DFS warned near 5% free and is not an experiment data destination; stale tool alternates remain irrelevant warnings, not permission to alter shared configuration.

## 7. Verification, publication and next actions

Parent tested current main at `1ef583d`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 make test` passed **138/138 tests in 16.12 seconds** on 10-08-2026. This verifies published source only; it does not validate unfinished remote integration or repair files. Private native-resume launcher syntax compiled, actual child permissions/model/first actions were verified, and the watcher retains its 24 passing checks. Preserve exact staged-diff and secret inspection before publishing this checkpoint and owned lifecycle updates.

1. Read fresh experiment09 `owner_recovery_ack.json`, mailbox acknowledgment, actual child/progress receipts and latest attempt 2 events. Verify the resumed owner finishes the sampler/two-turn/coverage controls and registered bounded driver before admitting any calibration response. A candidate patch or live coordinator is not a passed gate.
2. Continue the original warm-start owner through every admitted validation rung, frozen selection and conditional test/judge stages. Inspect output counts and devices, not just pipeline liveness.
3. Preserve repair and completed phase-A terminal accounting; no new calls or relaunches. At learning/warm-start completion or deadline, reconcile full manifests and aligned item-by-factor matrices, publish results and clean only owned task monitors.

The meeting image/interpretation remain in `meetings/oct_7_2026/item_factor_matrix_experiment_design.md`. The adopted executable design is experiment09. No additional human labels are required for its admitted work.

**TLDR-end:** [rl-4-code-verification: 09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013] Factored-score model learning has passed scorer and judge controls and resumed verified integration; no calibration, learned-weight improvement or held-out efficacy is measured yet. The repair allocation is blocked, while warm-start evaluation continues.
**Snapshot:**
```text
learning coordinator: gpt-6-astra / ultra; native resume attempt 2/3
permissions: danger-full-access / never
scorer controls: 14/14 expected outcomes
judge controls: 50/50 measured; all frozen category gates passed
calibration: 0/256 rollouts; training: 0/6 trajectories
validation: 0/945 cells; test: 0/1554 cells
learning deadline: 10-09-2026 11:13:36 PDT
repair v3: BLOCKED; official controls 0/16; solver cells 0/56
```

# Matched replay versus expansion continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_e08_v3.md>
**TLDR:** All Phase A training/generation verified; Phase A complete, all eight rungs and diagnostics checked; replay 4B half and expansion 4B full pass gates and all remaining cells still required.
Created: 10-15-2026 20:22 PDT
Last updated: 10-16-2026 02:55 PDT
## Goal
- Complete all 17,280 validation cells, paired bootstrap, namespace diagnostic, forecast assessment, publication and actual DONE notification; zero paid experimental model calls; test split unopened.
## Current execution
- Sole writer recovery-02: native gpt-6-astra/ultra, never/danger-full-access; PID 3022155, boot 839e7dd6-64e1-4a80-9498-31d30b3cc2df, start 38249185. Six current hashes and all 2,650 Phase A token counts reverified. [Receipt](results/owner_recovery02_v3.json).
- Phase A DONE. Phase B PID3066041/start38277673 adopts unchanged E14 controller; recovered E8 training on skampere3 GPUs2,4,5,7, 96 exact token steps checked. Runtime /lfs/skampere1/0/brando9/rl4cv_e08/sft_v3.
- E/R 1.7B and 4B training and eight exports verified: 23,021,424 additional loss tokens, 41,508,194 processed real tokens. [Receipt](results/phase_a_training_verification.json). Both retained post-export exit 2 incidents were reconciled without replay.
- Eight complete generated rungs = 8,640 exact cells. All generation children exited 0; all eight Phase A rungs scored/analyzed (8,640/17,280 cells). Replay 4B half and expansion 4B full pass gates; eight namespace diagnostics have zero score delta.
- Primary scoring and namespace diagnostics use eight workers per rung, at most six combined jobs (48 active compilation slots), frozen 600s timeout; expired orphan children cleaned separately by exact pidfd guard. All generation finished; future remote shell launches use immutable snapshots.
- All four training sizes and exact generator environments verified on skampere2/3. Pending large-model routes remain remote. 14B training must use eight devices; inference uses the frozen permitted layout.
- Latest full suite: 1,294 passed / 17 skipped / 6 subtests / 286.86s; 45 focused recovery/closeout checks plus 6 subtests pass. Native Vals weekly usage at acceptance 53%, credits 0. Keep personal reserve and original finite deadline/attempt limits.
## Waits and recovery
- Host recovery cron every five minutes/reboot; orphan cleanup every minute; capacity probe every 15min. Active owner; old external wait disarmed. Original deadline 10-18-2026 21:21 PDT and six-recovery/two-Vals limits unchanged; actual fallback exclusions updated.
- Slurm association was already requested 10-14; do not duplicate. Inventory and real release events are in host recovery_config.json. No paid cloud or smaller 14B training layout.
## Next steps
- [p 10/10] Preserve live Phase B controllers and admit exact 8B/14B layouts when devices become available; finish all remaining 8,640 cells, their diagnostics and paired comparisons.
- [p 9/10] After all declared cells: analyze_validation.py, finalize_results.py, verify/publish parent and v3 reports, actual deduplicated DONE email, checked completion receipt, retire only owned cron entries.
## Brando to-do
- None. START already sent; checkout and native evidence retained. See [continuation runbook](RUNBOOK_continuation_owner.md).
## Log
- 10-15-2026 20:22 PDT -- Prepared schedules and forecast; static checks running before lock.
- 10-15-2026 20:33 PDT -- Static checks passed (1,183 tests, all corpus/tokenizer/weight checks); locked recommended defaults before dry run.
- 10-15-2026 20:36 PDT -- START mail sent; dry session rl4cv-e08-v3-dry admitted GPU 1 under shared leases; training steps observed.
- 10-15-2026 20:48 PDT -- Dry inference recovered with CUDA 12.8; complete dry receipt PASS and disposable weights removed; Phase A queue launched.
- 10-15-2026 20:50 PDT -- First production initialization failed before updates because Ray dashboard UNIX socket path exceeded 107 bytes; shortened temp directory, preserved failure logs, verified previous coordinator exited, reconciled FAILED state and restarted.
- 10-15-2026 20:52 PDT -- Production 1.7B expansion verified through step 9; all nine loss-token counts match the frozen schedule.
- 10-15-2026 20:53 PDT -- Updated full suite passed: 1,184 passed / 17 skipped / zero failures in 339.81 seconds.
- 10-15-2026 21:11 PDT -- Expansion 1.7B reached/exported step 335; all 335 counts match 2,878,589 tokens. Prepared shared-storage route and persistent ownership continuation.
- 10-15-2026 21:25 -- Accepted ownership with 6/6 hashes and 433/433 token counts; installed five-minute/reboot recovery, passed real harmless-failure test and 5 focused tests; discovered personal quota risk and authenticated alternate subscription routes.
- 10-15-2026 21:29 PDT -- Expansion 1.7B completed all 667 updates; 667/667 token counts match 5,757,776 loss tokens. Final export underway. Full deterministic suite passed: 1,212 passed / 17 skipped in 305.20 seconds.
- 10-15-2026 21:32 PDT -- Full expansion export checksum check passed; retained wrapper exit 2 after export (post-loop syntax error; current script syntax passes). Both validation generations are live. Published recovery implementation and full training log, preparing verified Vals owner transfer for personal quota reserve.
- 10-15-2026 21:45 PDT -- Recovery-01 verified 6/6 hashes, 667/667 counts and both exports; reconciled exit2 without retraining; retained two interrupted generation batches and isolated new children; Phase A resumed. Phase B/forecast implementation and clean-environment full tests underway.
- 10-15-2026 22:04 PDT -- E4B half checkpoint verified (335 steps, 2,878,589 tokens and export checksums); both remote copied environments verified; latest full suite 1,224 passed/17 skipped. Phase B waits on Phase A; preparing queued replay on spare remote devices with unchanged layouts.

- 10-15-2026 22:30 PDT: recovery-01 continues as sole writer. Phase A scheduler now PID 595641 (`rl4cv-e08-v3-phase-a-recovery01-gen`); exact existing children preserved. Expansion 4B 667/667 token counts verified; replay 1.7B remote GPU2 399 checked counts pass. Generator environment copied/verified on both remote hosts; validation-only inputs staged; remote two-rung route active. See host `scheduler_adoption_generation_routes.json`, `recovery01_token_progress.json`, and public remote preparation receipt. Full test suite running; 0/17,280 scored cells.

- 10-15-2026 22:39 PDT: 1.7B replay all 658 native token counts verified (5,752,936 loss tokens); exports synchronizing home. 4B replay first 195 counts pass. Remote expansion generators PID1451417/GPU2 and PID1464872/GPU7 boot `562c249b-58a5-4d2a-b17d-3377147592a0`, start ticks263549233/263549408, are warming up. All pending gen routes remote; local 4B full generator preserved. Published 5325384, 1,233 passed / 17 skipped; native weekly usage41%.

- 10-15-2026 22:47 PDT: replay 1.7B exports334/658 both fully verified; all658 counts PASS. Native wrapper exit2 was post-export NFS stale handle, not training failure; retained receipt and reconciled DONE without replay. Phase A PID1968738 now adopts all7 surviving jobs; verificationR1.7DONE. Future remote shell launches immutable snapshots; do not replace current original remote shell sources while R4/initialgens run. Forecast canonical/file hash distinction corrected and positive test passes.

- 10-15-2026 23:00 PDT: both expansion 1.7B canonical raw outputs pass exact handoff (2,160 generated cells); scoring now eight workers per rung, maximum two scoring/namespace jobs, with all original children preserved. E4B half and R1.7B full remotely admitted on GPUs2/7; other generation controllers wait for eligible devices. Current Phase A identity remains PID1968738/start36815884; Phase B PID652391/start36742141 waits. Native wrapper source paths stay preserved.

- 10-15-2026 23:05 PDT: replay 4B all 658 counts match; remote export wrapper native exit 0, final canonical copy still active. Three complete raw rungs = 3,240 cells, zero scored rungs yet. Full suite: 1,235 passed / 17 skipped / 322.46s; current native usage 43%. CPU scorer parallelism receipt retained.

- 10-15-2026 23:09 PDT: all four Phase A training/verification jobs DONE; combined public receipt verifies 23,021,424 additional loss tokens and eight export manifests. Four complete raw rungs (4,320 cells), CPU scoring active, no failed jobs. Replay 4B full generator now admitted/queued by the existing scheduler; original live training source is no longer held.

- 10-15-2026 23:15 PDT: five exact raw rungs (5,400 cells); all 1.7B generations complete. First scorer sample completed all 135 mapped tasks; whole-rung score tables pending. Namespace concurrency aligned to eight workers per rung under the existing combined two-job limit, maximum sixteen Lean processes; full checks running.

- 10-15-2026 23:21 PDT: full suite passes 1,235/17 skipped after namespace worker increase; refreshed direct capacity inventory, kept finite route limits and all live workloads.

- 10-15-2026 23:26 PDT: six checked raw rungs (6,480 cells), two complete scorer samples. Remote GPU4 contention observed from a different user; own replay half generator healthy and preserved. Event-driven resource-wait guard is being implemented but is not armed; current owner remains active.

- 10-15-2026 23:35 PDT: seven exact raw rungs (7,560 cells), only healthy local E4B full generation remains. Resource-wait guard implemented, 14 focused tests and real harmless event-triggered recovery PASS; not armed. Root owner remains active; full suite running.

- 10-15-2026 23:42 PDT: all eight Phase A raw rungs verified (8,640 exact cells); all four training runs/eight exports already verified. Full suite 1,243/17 skipped/6 subtests; focused recovery 16/6 subtests. Event-wait guard and native harmless test ready but unarmed. Owner active, usage 45%, no paid experimental calls.

- 10-15-2026 23:53 PDT: frozen scorer leaves orphan Lean children after its 600s parent timeout. External exact pidfd guard retired 25 expired primary children; five observed live children excluded, all primary results preserved. Fourteen focused tests pass; per-minute host cron installed with original deadline/two-phase stop, route inventory updated. Earlier “sixteen Lean processes” wording described active slots and omitted this native orphan leak. Full tests passed: 1,259/17 skipped/6 subtests in 294.97s.

- 10-16-2026 00:00 PDT: CPU concurrency increased to four rungs (32 active slots) after observed 71–83% idle on 128 CPUs/1.8TiB available RAM. Both original E1.7 scorers preserved; new A/B identities recorded and both R1.7 scorer rungs launched. Diagnostic finalization now validates complete receipt coverage while retaining native timeout unknowns and omitting affected point estimates; all primary 17,280 known-cell gates unchanged. Eighteen focused checks pass; full suite 1,268 passed/17 skipped/6 subtests in299.40s.

- 10-16-2026 00:03 PDT: first full scored rung E1.7-half has 1,080 known cells, extracted936 (gate972), capped144 (limit108), mixed18 (minimum7), kernel53/1080 = 0.0491 [0.0250,0.0769], 10,000 task-bootstrap draws seed0, p-val=n/a. Missing checkout scorer dependency repaired via exact clean pinned clone link; only deterministic analysis rerun. All four active scorer roots adopted unchanged; analysis_error cleared. Native failure retained.

- 10-16-2026 00:16 PDT: full-budget E1.7 completes: 959/1,080 extracted (<972),121 capped (>108),19/135 mixed (>=7),55 kernel successes; 0.0509 [0.0278,0.0769],10,000 task-bootstrap draws seed0,p-val=n/a. Both E1.7 rungs fail gates; all16 remain required. Alternate capacity producer passes35 focused checks/6 subtests and actual harmless event-triggered recovery; installed15min cron, inactive while independent work continues. No eligible local4-device or Slurm8-device route in native preflight.

- 10-16-2026 00:20 PDT: capacity/full validation checks passed1,286/17 skipped/6 subtests in385.51s;35 focused checks pass after explicit14B inference routing case. Native Vals weekly usage48%,credits0. Existing four CPU scoring rungs remain healthy;17 complete sample batches,2 whole rungs analyzed. Global agents-config refresh is up to date.

- 10-16-2026 00:48 PDT -- Increased permitted CPU concurrency to six rungs after observed 68–79% idle / 1.8 TiB available. Exact pidfd scheduler replacement preserved all four active jobs; both E4 rungs now compile. Thirteen native new Lean children verified, CPU 49.5% idle after increase, original 600s caps unchanged. Phase B staging/config/layout audit passes; actual GPU admission remains pending. Receipt: results/cpu6_adoption_recovery01.json.

- 10-16-2026 00:53 PDT -- Six-rung full suite passes 1,287 tests / 17 skipped / 6 subtests in 331.82s. Host watch reports OBSERVING with no issues. Native Vals weekly allowance used 49%, credits 0; original finite recovery limits remain unchanged.

- 10-16-2026 00:54 PDT -- Replay 4B half completes exact 1,080 raw/scored/table cells; 1,006 extracted (>=972), 74 capped (<=108), 31/135 mixed (>=7), all gates PASS. Kernel success 90/1,080 = 0.0833 [0.0537,0.1167], 10,000 task-bootstrap draws seed0, p-val=n/a; training-seed variability unmeasured. Native exit0 retained; namespace diagnostic started. Coverage3,240/17,280; all remaining rungs mandatory.

- 10-16-2026 01:03 PDT -- Replay 1.7B full exact 1,080 cells verified: 946 extracted (<972),134 capped (>108),27/135 mixed (>=7); format/cap FAIL. Kernel65/1,080, mean0.0602 [0.0380,0.0861]. Matched expansion-minus-replay delta−0.0093 [−0.0259,0.0074],10,000 paired task-bootstrap draws seed0,p-val=n/a, training-seed variation unmeasured. Namespace started; coverage4,320/17,280.

- 10-16-2026 01:07 PDT -- Replay 4B full exact 1,080 cells verified: 970 extracted (<972), 110 capped (>108), 40/135 mixed (>=7); format/cap FAIL. Kernel 132/1,080 = 0.1222 [0.0833,0.1639], 10,000 task-bootstrap draws, seed0, p-val=n/a. Four completed namespace diagnostics pass exact hashes/coverage; expansion1.7B half changes one cell, others zero, all score deltas 0 [0,0]. Original first-error samples retain one native timeout. Coverage 5,400/17,280.

- 10-16-2026 01:12 PDT -- Replay 1.7B half exact 1,080 cells verified: 955 extracted (<972), 125 capped (>108), 20/135 mixed (>=7); format/cap FAIL. Kernel 40/1,080 = 0.0370 [0.0204,0.0565]. Expansion-minus-replay +0.0120 [−0.0037,0.0296], 10,000 paired task-bootstrap draws, seed0, p-val=n/a. All four 1.7B rungs fail gates, excluding a primary common checkpoint; full manifest and separate three-size assessment remain mandatory. Coverage 6,480/17,280.

- 10-16-2026 01:15 PDT -- Expansion 1.7B full namespace diagnostic verified: exact 1,080 cells, zero changed/unknown cells, delta0 [0,0], 10,000 paired task-bootstrap draws seed0,p-val=n/a. All24 original-error sample receipts verified; two native timeouts retained. Five diagnostics complete; both expansion4B scorers and replay1.7B half diagnostic continue.

- 10-16-2026 01:22 PDT -- Replay 1.7B half namespace coverage and hashes pass for all1,080 cells; zero changed/unknown cells and delta0 [0,0] under10,000 paired task-bootstrap draws seed0,p-val=n/a. One native timeout retained in24 original-error sample receipts. Six diagnostics complete; only both expansion4B primary scorers and their subsequent diagnostics remain in Phase A. Recovery inventory reconciled to both current scheduler identities; native Vals weekly use50%,credits0, rules refresh unchanged at01:15.

- 10-16-2026 01:37 PDT -- Expansion 4B full passes gates (981 extracted,98 capped,36/135 mixed);153/1,080 kernel successes,0.1417 [0.0972,0.1907]. Paired expansion-minus-replay +0.0194 [−0.0019,0.0426],10,000 task-bootstrap draws seed0,p-val=n/a. Exact primary and namespace checks pass, diagnostic unchanged. Coverage7,560/17,280; only expansion4B half remains in Phase A. Native namespace exit0 reconciles transient observer poll race; no job failure.

- 10-16-2026 01:57 PDT -- All Phase A primary cells complete:8,640/17,280. Expansion4B half fails format/cap (953 extracted,127 capped,35/135 mixed),125/1,080 kernel successes =0.1157 [0.0769,0.1583]. Matched expansion-minus-replay +0.0324 [0.0111,0.0546],10,000 paired task-bootstrap draws seed0,p-val=n/a; training-seed variation unmeasured. Exact keys/hashes/tables pass. Final namespace diagnostic running, Phase B still gated on it.

- 10-16-2026 02:00 PDT -- Phase A DONE: four trained runs/eight exports,8,640 exact primary cells,four paired comparisons,eight namespace diagnostics and192 original-error receipts checked. Three namespace cells changed,zero score deltas/unknowns. Phase B E8/E14 controllers launched and native output says WAITING_DEVICES on both prepared hosts. Published phase_a_validation_verification.json; no completion/DONE claim for the full experiment.

- 10-16-2026 02:05 PDT -- External-capacity continuation prepared after Phase A checks: exact E8/E14 controller identities alive, shared admission records absent, local four-device predicate false, Slurm association absent and all allowed eight-GPU nodes non-idle. Current-state shadow checks DEFER/DEFER/WAKE pass; prior real admission/capacity wake tests retained. Native Vals weekly use52%,credits0. Final resource wait/release will be written only after publication; no full-completion receipt or DONE mail.

- 10-16-2026 02:07 PDT -- Final Phase A publication checks pass:1,287 tests,17 skipped,6 subtests in287.62s. All available scientific work complete; resource wait/release prepared as final mutation after this publication. E8/E14 controllers remain alive with no admission. Full experiment stays INCOMPLETE:8,640 known/17,280 declared; no DONE notification sent.
- 10-16-2026 02:55 PDT -- Recovery-02 accepted 6/6 current hashes and 2,650 Phase A steps; retained zero-step E8 Ray auto-discovery failure, fixed RAY_ADDRESS=local and retried exact layout. E14 child preserved; recovered E8 first96 steps match803,444 loss tokens. Added full cell coverage and deterministic closeout recomputation; forecast reachability displayed alongside original operational interpretation.

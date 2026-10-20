**TLDR:** CPU implementation and tests are complete; launch admission is BLOCKED because the frozen top-20 generator receipt cannot recover exact tie-expanded support.

# Experiment 13 v4 implementation checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/CKPT_v4_implementation.md>
**Companion:** <https://docs.google.com/document/d/1KqUi39sz532dIGg8EYCy6w62Q0KzO2XWhpM2MMSWvHE/edit>
**Created:** 10-20-2026 15:27 PDT. **Last updated:** 10-20-2026 15:56 PDT.

## State

- Scope: `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4`, CPU implementation and tests only.
- Owner: Codex gpt-6-astra, requested high effort; skampere1, full filesystem access, approval policy never.
- Status: CPU components complete; launch admission BLOCKED on the frozen generator-information contract.
- Protocol: d4778e25, SHA-256 `fb741636844294fb76667c4d6928ddbef1c7e28fde0fd1093ae834876764e063`; unchanged.
- Runtime: Torch 2.7.1+cu128, vLLM 0.10.0, NeMo RL 0.4.0; shared venv read-only, bytecode writes disabled.
- Done: native support and blocker reproducer; actual installed NeMo loss wrapper, old-weight hook, once-only float32 temperature hook.
- Done: all-split context computation, migrated validators, G0, T1–T4, placebo, T5, T and all-six extension.
- Done: anonymous A6 reducer, device guard, watchdog/cron installer and admission/update binding.
- Context: generator/trainer 20,041; maxima train 7,753 / validation 4,399 / test 4,996; model limit 32,768.
- A6: 48 successes / 496 measured / 512 declared; 16 missing; 8/54 mixed strict and 49/54 varying B; no discrepancy.
- V4 tests: 89 passed, 0 skipped, 0 failed in 26.14 seconds, using the pinned venv Python and installed NeMo source.
- Repository tests: 1,388 passed, 15 skipped, 0 failed, 6 warnings in 361.96 seconds with historical dependencies restored read-only.
- Admission: 29 protocol/code/test/evidence bindings plus four installed source bindings; CPU check passes, launch-check refuses.
- Admission SHA-256: `a7b50b9813914085a974d27b678dce9e12ddb5e4d97fdb7d3e18e834dde35099`.
- Blocker: raw top-20 cannot certify or reconstruct omitted kth-logit ties; no substitute objective.
- Amendment proposal: expose actual filtered support/probabilities or tie-expanded top-k with order/completeness evidence.
- Launch: no valid launch command under the frozen contract; actual worker/model integration and all measured gates remain pending.
- GPU census 10-20-2026 15:40 PDT: all 24 devices occupied; skampere1 0/5/7 belong to v3 workers.
- Experiment 120: canonical folder and process attribution unresolved; no unsupported attribution to another user's jobs.
- No GPU allocation, model generation, optimizer step, provider call, cron install, tmux mutation or v2/v3 edits; $0.
- Publication: final staged review, rebase and push follow this checkpoint; the master can verify the remote commit containing this file.

## Implemented contracts and decisive checks

See [README.md](README.md) for the component map. Installed-source comparison tests cover native tie handling and the retained top-p boundary token; a 40-way equal-logit control leaves 38 tokens in the true support while a top-20 receipt carries at most 21. Positive reconstruction tests require a complete vocabulary or an external completeness certificate; the pinned engine supplies neither for ordinary top-20 requests. This is an information limitation, not a tolerance failure. Source evidence is bound in [admission_cpu.json](phase2/admission_cpu.json).

The actual NeMo loss executes forward/backward on synthetic CPU logits with sparse fixed old support. NeMo scales logits before calling the loss: v4 hooks use float32 division once, and the loss wrapper does not divide twice. The synthetic full-length probe is written but has not run on the real model; its target builder has a tiny CPU backward control preventing mutation of embedding indices saved by autograd. No CPU test is counted as a real T1–T4 gate.

G0 uses seeds 1304001/1304002, 10,000 paired whole-task bootstrap draws, both missing-slot completions and exact known-value controls. Gate tests cover fallback to B rewards or stop without resampling, five T2 criteria including pre-clipping gradient norm, T3 replay identity, T4 required records, gate single-attempt reservations and the three-attempt infrastructure-only cap. Placebo tests bind the sorted 17-significant-digit reference digest, the ≥90% rule, counter draws before P and density/variance denominators. Pilot controls cover conservative T5, all-six 30→60 extension and T from both A seeds' updates 1–30 only.

[context_values.json](phase2/context_values.json) covers 539 train, 135 validation and 222 test prompts for each engine. It rejects 8,192 and 15,945 context lengths. Only held-out instruction text was read to compute lengths. [A6_counts.json](phase2/A6_counts.json) contains no task identities: histogram `{0:51,1:2,2:3,3:3,4:0,5:2,6:1,7:1,8:1}`, 54 complete groups, eight mixed strict groups and 49 varying B groups, with 512 input receipt hashes and source manifest/aggregate hashes. The frozen protocol's counts agree exactly. These are exhaustive descriptive counts, not new outcome estimates.

## Test reproduction and environment recovery

The v4 suite uses only the original pinned NeMo runtime. Pytest 8.4.2 and its dependencies reside in the separate work-directory `test_deps`; nothing was installed into the shared venv. Logs remain at `/lfs/skampere1/0/brando9/rl4cv_e13v4/v4_tests_final.log` and `make_test_configured.log`.

The first repository-wide run had seven environment failures (1,355 passed, 41 skipped): missing external scoring repositories/legacy utility path and the historical experiment-09 test's `e09_seeds` dependency. Restored local untracked symlinks to existing pinned `external/veribench` and `external/veribench_scorer` (c11b99… / 59059…), plus `/lfs/skampere1/0/ultimate-utils` pointing to Brando's existing utility checkout. Added the existing experiment-09 NeMo source to PYTHONPATH **only for the root historical suite**; no source was changed. All seven failed tests then passed, followed by the full 1,388-pass suite. Six warnings concern existing deprecations/fork behavior. The v4 suite ran separately without this alternate source path.

Exact CPU commands (run from the indicated checkout):

```bash
cd /lfs/skampere1/0/brando9/rl4cv_e13v4/rl-4-code-verification
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/lfs/skampere1/0/brando9/rl4cv_e13v4/test_deps:$PWD/src
V4_PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
V4_ROOT=$PWD/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4
"$V4_PY" -m pytest -q "$V4_ROOT/tests"
"$V4_PY" "$V4_ROOT/phase2/admission.py" check --record "$V4_ROOT/phase2/admission_cpu.json"
# Expected nonzero exit with the documented frozen-contract blocker:
"$V4_PY" "$V4_ROOT/phase2/admission.py" launch-check --record "$V4_ROOT/phase2/admission_cpu.json"
# Historical root suite only (keep this source override out of the v4 suite):
PATH=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin:$PATH PYTHONPATH=/lfs/skampere1/0/brando9/rl4cv_e09/nemo_rl:$PYTHONPATH make test
```

## Remaining launch work and exact command boundary

There is **no valid model-launch command under this frozen protocol**. The implemented admission guard deliberately blocks launch even if someone changes its JSON status. This dispatch supplies tested components and a bound rejection receipt, not a runnable end-to-end pilot or evidence that the technical gates passed.

1. [p 8/10] Resolve the source-proven receipt insufficiency: the smallest amendment exposes actual filtered token IDs and normalized probabilities at sampling time, or a complete tie-expanded top-k set with original order and a completeness certificate. Keep the objective/sampler unchanged; the master owns any amendment to the frozen protocol.
2. [p 8/10] After that amendment, integrate concrete generator/scorer/update/recovery commands with these components and bind new admission. Actual NeMo worker integration, sampler backend, raw receipt extraction and full-length memory behavior still need launch measurement. Do not restore the old v3 runner's retired lengths/objective.
3. [p 7/10] After the master's v3 release condition and an idle-device lease, execute T1/G0/T2/T3/T4 and B audits in frozen order, bind measured cost/reserve, freeze all placebo draws before P, then run the six trajectories and conditional extension. No gate may be silently repeated; partial samples must be diagnosed and retained.
4. [p 5/10] Resolve the canonical identity/location of experiment 120 before attributing any GPU process to it; the census below is verified, its experiment label is not.

The future watchdog requires an existing admission-bound plan at `/lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json` with concrete argument-vector commands. This path is reserved for the future plan; no such launch plan or cron entry was created. Once all preceding requirements have been met, these are the exact watchdog commands (the install command is currently rejected by admission):

```bash
# With V4_PY and V4_ROOT set as above, preview only:
"$V4_PY" "$V4_ROOT/phase2/install_watchdog.py" --python "$V4_PY" --plan /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json --log /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog.log --admission "$V4_ROOT/phase2/admission_cpu.json"
# Launch-time only, after the plan and a new valid admission exist:
"$V4_PY" "$V4_ROOT/phase2/install_watchdog.py" --python "$V4_PY" --plan /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog_plan.json --log /lfs/skampere1/0/brando9/rl4cv_e13v4/watchdog.log --admission "$V4_ROOT/phase2/admission_cpu.json" --install
```

## Experiment 120 GPU report

At 10-20-2026 15:40 PDT, all 24 devices across skampere1/2/3 had compute processes; zero were idle. [gpu_inventory.json](phase2/gpu_inventory.json) preserves device IDs, owners, process IDs/names and Brando-owned ancestry. The three eligible skampere1 devices are attributed to `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3` by their process working directories and pilot ancestry, not to experiment 120:

| Host/device | Owner | PID | Process |
|---|---|---|---|
| skampere1/0 | brando9 | 1258391 | ray::DTensorPolicyWorker.__ray_call__ |
| skampere1/5 | brando9 | 875936 | ray::DTensorPolicyWorker.train |
| skampere1/7 | brando9 | 904183 | ray::DTensorPolicyWorker.__ray_call__ |

The other skampere1 devices belong to eth127 (1/3/6) and srivatsavad (2/4). Skampere2 devices 0–7 are held by vmadan/alexspan/srivatsavad; skampere3 devices 0–7 by vmadan/alexspan/ruhana. Full per-device process rows are in the linked receipt. No process was killed or modified. Local relevant repository searches, current remote VeriBench main trees, owned tmux/process names and this census did not establish a canonical experiment-120 folder or matching owner/process. Its GPU use is **unresolved**, not zero. Refresh the census at launch; this is a dated observation, not a reservation.

## Copy-ready message

I have the experiment 13 v4 CPU implementation passing 89 tests, with the historical repository suite also passing. Launch remains blocked because the frozen top-20 generator receipt cannot recover the exact sampling support when cutoff logits tie; the protocol is unchanged and no training or generation has run.

## Event log
- 10-20-2026: Loaded frozen protocol and installed sampler sources; identified top-20 information loss at the k-th tie before any model execution.

- 10-20-2026 15:44 PDT: CPU implementation reaches 80 passing tests; complete prompt-length and A6 count receipts written. Read-only three-host inventory found all devices occupied; no v4 launch.

- 10-20-2026 15:56 PDT: Final v4 suite 89/89 passes; configured root suite 1,388 passes/15 skips/0 failures. Bound 29 local artifacts plus four runtime sources, preserving the code-level launch blocker. Corrected once-only worker temperature scaling and verified synthetic probe targets do not mutate saved embedding indices. No launch or cron installation.

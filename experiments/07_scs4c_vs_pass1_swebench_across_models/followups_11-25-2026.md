# 11-25-2026 — Experiment 07 issue #5 follow-ups and remaining work

**Date:** 11-25-2026.

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/followups_11-25-2026.md>

**TLDR:** New CPU diagnostics explain the existing +0.193 SCS4C-T level bias and show that changing aggregation reduces, but does not remove, the held-out ranking disadvantage. Phase B now has a verified public 731-task manifest, tested D_gold receipt/control code, and one real task with 256/256 gold-repeat agreements and 256/256 base disagreements. The initial preparation count was 0/731; the real-control follow-up reaches 1/731. Full Phase B still needs task-specific input/interface definitions, its separate locked protocol and authenticated included-funded generation; Phase C has not run. Issue #5 stays open. Original locked results, tables, CSVs and forecasts are unchanged.

**Harness:** Codex CLI, GPT-6 Astra ultra (Vals account). These are deterministic CPU computations on saved SWE-bench Verified execution receipts, not model readings or Lean checks. Phase A is **no DT**: its test factors do not include gold-patch differential testing. No new solver generation, judge calls, paid API calls, GPU jobs or emails occurred. The experiments 01–25 QA was not repeated.

**Evidence and scope:** [issue #5](https://github.com/brando90/rl-4-code-verification/issues/5), including both existing comments; [original results](results.md); [original analysis](expt_v1/results/analysis_e07.json); [new analysis with input hashes](followups_11-25-2026/analysis_11-25-2026.json). The original Phase A solver systems and their settings remain the 182 public submissions in the pinned inventory, with 164 included; no replacement solver or judge was introduced.

## Completed CPU follow-ups

The original saved receipts remain on `skampere1` at `/lfs/skampere1/0/brando9/rl4cv_e07/rl-4-code-verification/experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz`. The new script reads this file without changing it and requires all 164 × 424 original common-cohort measurements, exactly once each. It rejects missing, duplicate, out-of-range or changed score evidence.

**The +0.193 level bias is mostly aggregation.** The original mean system SCS4C-T is 0.767192 and mean pass@1 is 0.573933. The mean of the per-artifact smooth scores is 0.639849. Of the original +0.193259 difference, +0.127343 comes from taking the geometric mean after averaging the factors, and +0.065916 comes from per-artifact credit above binary resolution. The latter includes +0.065927 on unresolved tasks and −0.000010 from the original known inconsistent resolved report. That report remains in the denominator and retains its original score. Mean gated T_fix is 0.632854; mean gated T_keep is 0.942752.

**The per-task variance result does not support a simple “partial credit adds variance” explanation.** Averaged over the 164 systems, within-system task variance is 0.216083 for binary resolution and 0.191983 for per-artifact SCS4C-T. The score-minus-resolution variance is 0.050870; twice its covariance with resolution is −0.074970. The additive identity closes to 1.46e−16. Lower task variance alone does not guarantee better system ranking; the additional aggregation step changes the ranking target.

**Independent post-hoc splits separate aggregation and level prediction.** The new diagnostic uses seed 20261125, 2,000 splits, 50 tasks in A and 374 in B. It is not a replacement for the original seed-20261007 locked H2 result. Every statistic is defined on all 2,000 requested splits. The brackets below are 5th–95th split percentiles, not population confidence intervals; p-val=n/a.

| Quantity | Original locked result retained | New post-hoc diagnostic |
|---|---|---|
| System SCS4C-T rank difference versus pass@1 | −0.012139 [−0.024764, −0.000228]; positive 92/2,000 | −0.011737 [−0.024246, −0.000193]; positive 97/2,000 |
| Mean per-artifact score rank difference | Not measured in original H2 | −0.004944 [−0.016095, +0.005298]; positive 406/2,000 |
| T_fix mean rank difference | Not measured in original H2 | −0.005477 [−0.016447, +0.004356]; positive 344/2,000 |
| Raw system SCS4C-T median absolute level error | Original whole-cohort mean bias/MAE +0.193259; different evaluation | 0.192465 on held-out B |
| Affine-calibrated SCS4C-T median absolute level error | No original calibration | 0.054341 on held-out B |
| pass@1 from A median absolute level error | No original level-error diagnostic | 0.049399 on held-out B |

The calibration fits intercept and slope across systems using only their A-task smooth scores and A-task pass@1, then evaluates predictions against B-task pass@1. It uses no B outcome for fitting and makes no claim about new solver families. Predictions are unbounded; no clipping is applied. Its rank performance remains effectively unchanged apart from floating-point tie effects. It substantially improves the raw smooth level prediction but still has higher median absolute error than pass@1 from A. The aggregation ablations reduce the ranking deficit without reversing its median sign. These observations support keeping pass@1 as the headline level; they do not establish a causal explanation or change the original H2 failure.

## SCS4CV explanation requested in issue #5

The requested reading material is now summarized here for the owner: **IC_tests** checks the submitted Lean tests, **IC_proofs** checks the submitted proved theorems, and **formal specification coverage (FSC)** compares the submitted specification against the gold specification using the validated judge. IC_tests and IC_proofs measure internal consistency of the submitted artifact; FSC provides the gold-reference comparison. Compilation gates the usable artifact. A geometric mean gives zero if any required factor is zero while retaining partial progress when all factors are positive. The official system summary takes the geometric mean of the gated factor means on one common measured cohort; averaging per-artifact scores is a separate diagnostic. See [repository scientific-integrity rules](../../CLAUDE.md#scientific-integrity) and the [experiment definition](README.md#definition).

SCS4C-T uses the gold FAIL_TO_PASS and PASS_TO_PASS test fractions for ordinary code. Full SCS4C adds D_gold, agreement with the gold patch on fixed generated inputs. This note supplies the explanation; it does not claim that Emily and Lethan have met or that a human review occurred.

## Phase B preparation completed

The [primary paper, version 3](https://arxiv.org/html/2609.08149v3) identifies the public [SWE-Bench Pro Verified dataset](https://huggingface.co/datasets/opencompass/SWEBench-Pro-Verified) and its 731 tasks. Its relevant dataset and execution sections were read to locate the actual release. The public dataset was downloaded without authentication or model calls at revision `ae466f824cdee69d2c010b6c954b7418c411b6e4`; file SHA-256 is `9eeac2c01fcbf25fd8db4254a23b9e0d306eb659e9c14dd1308b9fda10faf6d8`. The local 24,830,864-byte gold-bearing input remains in ignored `followups_11-25-2026/raw_inputs/swebench_pro_verified.jsonl` under this fresh clone.

[The committed task manifest](followups_11-25-2026/phase_b_manifest_11-25-2026.json) records all 731 unique task IDs, repository/base commits, image tags, test counts and patch hashes. All test counts match their source lists. It covers 11 repositories: 280 Go, 266 Python, 165 JavaScript and 20 TypeScript tasks. It contains no gold patch text and is preparation only, not measured controls. A six-model minimum panel would declare at least 4,386 model/task attempts before retries; no exact solver IDs or vendor harness versions have been silently chosen.

[D_gold receipt/control code](followups_11-25-2026/d_gold_controls.py) now compares canonical serialized values or qualified exception types, enforces identical nonempty input manifests, treats timeouts/infrastructure failures as unmeasured, and independently checks gold-repeat agreement of at least 99% and at least one base-versus-gold disagreement. Candidate generation is not needed to check controls. The coverage calculation retains every declared task and requires at least 658 of 731 tasks to pass. It is a tested scoring/control component, **not a completed benchmark execution harness**. Its tests use synthetic receipts, so they supply no real-task D_gold pass count.

The concrete execution design is to run base, gold, a gold repeat and then each candidate in separate pinned task environments; use adapters for the task's language and changed function interfaces; fix property-based and fuzz input IDs before any candidate outcome is observed; save the input hash, image digest, patch hash, stdout/stderr, exit status and one behavior receipt per input. Solver environments must not expose gold patches, hidden tests or generated inputs. Unsupported interfaces and unavailable executions keep explicit unmeasured receipts. Gold-repeat/base controls happen before solver generation. Per-artifact and common-cohort system aggregates follow the existing definition. This preparation does not edit or create a `PROTOCOL.md`.

**Host checks:** Docker server version 28.1.1 responded successfully. `valkyrie whoami`, `valkyrie provider list` and `valkyrie benchmark service list` each exited 1 with “Your Valkyrie login has expired. Run `valkyrie login` again.” No provider call or login mutation was attempted. Expired login prevents verifying organization, funding and the SWE-Bench Pro Verified service; it does not prove the service is absent.

## Real CPU control follow-up — 11-25-2026

The initial manifest's **0/731 controls measured** is preserved as the preparation snapshot. The subsequent [real control receipt](followups_11-25-2026/real_fncli_controls_11-25-2026.json) establishes **1/731 tasks with real function-level D_gold controls measured**, with 730 still unmeasured. This is **DT** (differential testing) on executed real code, a pre-admission engineering check rather than full Phase B admission or a solver score.

The task is `instance_internetarchive__openlibrary-6afdb09df692223c3a31df65cfa92f15e5614c01-v08d8e8889ec945ab821fb156c04c7d2e2810debb`. Its complete `scripts/solr_builder/solr_builder/fn_to_cli.py` module was fetched at the dataset's base commit `1a3fab3f0b319e0df49dd742ce2ffa0d747d1b44`; the dataset's unchanged gold patch applied with `patch --fuzz=0` and exit 0. No function was extracted or substituted. The real module imports only Python's standard library, and both base and gold modules imported and executed successfully in separate Python processes.

Before any base/gold execution, the adapter wrote and hashed 256 generated CLI inputs: 20 boundary cases and 236 seeded fuzz cases across scalar integers, asynchronous scalar callbacks, integer lists and path lists. The callbacks are inputs to the real FnToCLI API and do not access files. Both versions use the same original no-argument `run()` API; the observed difference is behavior, not a fabricated signature mismatch. Fixed [inputs](followups_11-25-2026/real_fncli_inputs_11-25-2026.json), [per-input observations](followups_11-25-2026/real_fncli_observations_11-25-2026.json) and source/patch hashes are retained.

Gold-repeat agreement is **256/256 (1.0)**, and the base disagrees with gold on **256/256 inputs**. Gold and gold-repeat each return a value for all 256 inputs; base returns a value for 133 and an exception for 123. Therefore the function-level positive and negative controls pass. No candidate patch or learned policy was scored. The complete OpenLibrary package installation/import gate was not run, so this is not a full task-environment gate. Its official Docker manifest was also inspected successfully (exit 0; about 1.19 GB compressed layers); image access is **not** a demonstrated blocker. No image pull or container mutation was required for this standard-library control.

The full dataset contains actual base commits, gold patches, tests, narrative requirements/interfaces and publicly discoverable image tags. It does **not** supply a frozen D_gold property/fuzz input manifest or a common callable interface across its four languages. Those evaluation definitions need to be completed and fixed before full Phase B measurement; they are not being mislabeled as missing data or unavailable GPUs. Serial execution kept this additional check small on the busy host. Full Phase B also requires the separate locked protocol specified in the original experiment design; the present user instruction prohibits editing any `PROTOCOL.md`.

## Remaining work and why issue #5 stays open

1. **Phase B real D_gold controls: initial preparation 0/731; follow-up 1/731 function-level controls measured, 730 unmeasured.** Task-specific property/fuzz input generators, callable adapters and pinned task-environment executions across four languages remain to be defined and run; the separate Phase B protocol is not locked. These are scientific-definition and CPU engineering prerequisites, not GPU blockers. The one successful real module control does not establish package-level admission. No Phase B admission or full-SCS4C result is claimed.
2. **Phase B solver panel and service:** exact current models, vendor harness versions, model/task receipts and a locked Phase B procedure remain unset. Valkyrie authentication is expired, so the organization, funded providers and benchmark service cannot currently be verified. Included-only use is required; no paid fallback is authorized.
3. **Phase C reward experiment:** training-pool selection and exact-hash/word-5-gram exclusion against the full evaluation manifest, prospective forecast, group-size-eight mixed-group/ρ/H measurements, matched-budget learning and held-out pass@1 remain unmeasured. The real D_gold reward and separate locked procedure are prerequisites. Generations and learning need newly authorized capacity under the existing included-usage rule; no run was launched here.
4. **Owner review and live explanation:** the explanatory note and all evidence are ready for Emily/Lethan review, but no message was sent and no completed human discussion is claimed. The user limited posting to this repository's issue updates.

Suggested continuation, **“Experiment 07: real D_gold task adapters and controls”**: Codex CLI, GPT-6 Astra, ultra effort, with deterministic CPU/container execution and retained logs. Keep issue #5 open until its remaining phases or explicitly revised scope are complete.

## Reproduction and tests

Run from the repository root:

```bash
PYTHONPATH=src python3 experiments/07_scs4c_vs_pass1_swebench_across_models/followups_11-25-2026/analyze_followups.py \
  --receipts /lfs/skampere1/0/brando9/rl4cv_e07/rl-4-code-verification/experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz \
  --original experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/analysis_e07.json \
  --systems experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_system_e07.csv \
  --out /tmp/e07_followup_reproduction_11-25-2026.json
PYTHONPATH=src python3 -m pytest -q experiments/07_scs4c_vs_pass1_swebench_across_models tests/test_scs4c.py
```

The analyzer requires a new output path and refuses to overwrite an existing result. Actual analysis exit code: **0**; [log](followups_11-25-2026/analysis_11-25-2026.log). Manifest preparation exit code: **0**. Initial diagnostics plus existing metric tests: **67 passed, exit 0**, [log](followups_11-25-2026/pytest_11-25-2026.log). Tests including D_gold controls and manifest validation: **75 passed in 4.42 seconds, exit 0**, [test log](followups_11-25-2026/pytest_controls_11-25-2026.log). The subsequent [real control run](followups_11-25-2026/real_fncli_controls_11-25-2026.log) exited **0**, including gold, gold-repeat and base worker exits 0. After that addition, the same touched-folder command again passed: **75 passed in 4.72 seconds, exit 0**, [final log](followups_11-25-2026/pytest_real_controls_11-25-2026.log).

To reproduce the real control, use new output/work paths (the runner refuses to overwrite either):

```bash
nice -n 10 python3 experiments/07_scs4c_vs_pass1_swebench_across_models/followups_11-25-2026/run_real_fncli_controls.py \
  --dataset experiments/07_scs4c_vs_pass1_swebench_across_models/followups_11-25-2026/raw_inputs/swebench_pro_verified.jsonl \
  --work experiments/07_scs4c_vs_pass1_swebench_across_models/followups_11-25-2026/raw_inputs/real_fncli_controls_reproduction \
  --out /tmp/e07_fncli_reproduction_11-25-2026.json
```

**TLDR-end:** [rl4cv: experiment 07 issue #5] CPU follow-ups quantify the level bias and aggregation effect; all 731 Phase B tasks are pinned, and one real task passes generated-input function controls. Full D_gold task definitions, a separate locked Phase B protocol, authenticated generation and Phase C remain incomplete, so #5 stays open.

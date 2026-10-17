# Experiment 13 v3: prospective local pilot execution

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/PILOT_EXECUTION.md>

**TLDR:** The `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3` runner completes six paired 30-update trajectories after the technical gates pass, with one possible extension for both factored-reward seeds. All generation, optimization and Lean verification remain local at $0 provider spend; missing formal-specification coverage remains explicit.

Recorded prospectively: 10-16-2026, before any v3 pilot response or validation outcome.

## Population and frozen numerical method

- Arms B (factored reward), A (strict binary reward), and P (independent placebo); seeds 1301 and 1302.
- Each update has 32 declared groups of eight responses. The same seed produces the same task and rollout-seed stream across arms; group indices advance cumulatively. Missing scorer outcomes mask whole groups for A/B. Placebo rewards were drawn independently before generation and do not depend on scoring availability.
- Reuse the frozen 539 train prompts, 4,302 measured placebo values, Qwen3-4B `step_658`, float16 NeMo distributed-tensor worker, AdamW learning rate 0.000001, loss, sampler, native optimizer state and checkpoint export. The complete inputs and source are hash-bound.
- Reuse the inherited B/1301 feasibility gate: reward gain at least 0.02 between updates 1–10 and 21–30, with explicit missingness bounds. B/1302 is a replication. If the B/1301 result requires extension, both B seeds run through update 60 once and are evaluated again. The replication never rescues the gating seed.

## Validation and coverage

Each 30-update checkpoint is evaluated on all 135 D-013 validation tasks with eight responses per task. Extended B checkpoints receive the same evaluation. The adapter changes only identity admission to record the actual pilot arm, seed and update; it preserves the historical prompt, thinking mode, temperature 0.6, top-p 0.95, top-k 20, 12,288-token output cap and sample seed `91*100003+sample_idx`. No test prompt or outcome is loaded.

The local strict oracle supplies pass@1 and the two mechanical SCSC factors. The composite is the cube root of test correctness times proof correctness times formal-specification coverage. A known compilation failure has zero compiled coverage under the inherited rule; a known zero factor determines a zero composite. Positive mechanical factors with unknown coverage retain the interval from zero to the cube root of their product. Unmeasured cells retain [0,1]. Bounds are averaged over all 1,080 declared cells; no unknown coverage is imputed. The factored training reward is not substituted for this composite.

Validation receipts include 10,000 bootstrap replicates over the frozen task groups, retaining all responses within each group. These intervals describe task variability for a fixed trained seed; they do not establish uncertainty across only two training seeds. No efficacy significance claim is made from a technical feasibility gate.

The original full-study protocol also called for hosted coverage and mutation admission. This explicitly local-only dispatch cannot claim that hosted admission. Local pilot execution follows the user's specific instruction to run B/A/P; official coverage requiring the validated judge remains pending. This is an explicit scope qualification, not a claimed pass of the original hosted controls or authorization for main runs.

## Resources and accounting

Only physical GPUs 0, 5 and 7 on `skampere1` are eligible. Each stage takes a v3 device lock, checks physical identity and current foreign occupancy, and sets numeric `CUDA_VISIBLE_DEVICES`. The guard rechecks ownership during execution. No foreign process is signalled, including on an eligible device.

The prospective maximum is 240 updates: 180 for the six initial trajectories and 60 for two optional B extensions. Validation has at most 8,640 responses: six initial and two extended checkpoints. Existing valid starting-policy evidence is reusable; the preparation check rendered prompts only and did not generate a fresh baseline.

The local T4 cost gate projects these populations from the actual v3 update, retained 256-response generation/scoring costs, and the new eight-cell train evaluation probe. It reports device hours, scoring processor hours and peak storage with a 25% reserve. It does not claim the original full main-study projection is complete. The older 260–350 A100-hour figure was an estimate, not a fixed allocation ceiling.

The fixed execution ceiling is **2,100 device-hours**, derived before the T4 measurement from the complete declared workload: at most 480 training GPU stages and 40 validation segments, each bounded to four hours plus two minutes of cleanup. This is a hard upper bound, **not an expected runtime**. The retained strict run already used about 2.00 device-hours for one update and 0.515 for generation; the requested pilot therefore takes days, with runtime dependent on available devices. The actual T4 estimate must fit the fixed ceiling and available storage before admission. An atomic accounting lock charges both finished leases and outstanding stage reservations, so concurrent workers cannot independently spend the same remaining allocation.

The runner retains every generation, scorer receipt, saved loss batch, per-step summary and checkpoint hash. It keeps the latest native before/after checkpoints and current export per trajectory; older large tensors are retired only after a newer completed opportunity is durable and their metadata is archived. The cost projection includes concurrent-transition headroom. Partial opportunities are retained for diagnosis rather than resampled or silently repeated.

## Durable execution and publication

The technical follow-through completes the retained update's reporting, saved-batch replay and cost probe. The paired dispatcher watches that process's identity and death, then requires successful gate receipts. A dead process without complete receipts produces an error and cannot admit training. At most three trajectories run concurrently, with CPU scoring serialized by an experiment-owned lock.

The progress writer derives `results.md`, machine-readable status and the training-trajectory CSV from durable receipts. A terminal publisher waits for the dispatcher, runs the full repository tests with Lean integration, checks the exact staged paths/content, and pushes only v3 result artifacts to `origin/main`. It stops if tests fail, another writer has staged files, runtime source changed, or the remote branch advanced incompatibly; such an event remains an explicit publication error.

No provider client, hosted judge, key loader, paid reviewer or external message is part of this runner. `HF_HUB_OFFLINE=1` and the local model paths remain enforced.

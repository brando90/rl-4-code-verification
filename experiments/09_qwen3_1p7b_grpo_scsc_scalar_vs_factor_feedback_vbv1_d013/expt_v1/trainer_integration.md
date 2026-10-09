# Verified trainer integration handoff for experiment09

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1/trainer_integration.md>

**TLDR:** `09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013` has an available fixed supervised fine-tuning (SFT) checkpoint and a NeMo reinforcement-learning (RL) runtime with multi-turn support. Its Lean environment, online formal specification coverage (FSC) bridge, token masks, live judge controls and complete optimizer path remain to be validated. This is a technical handoff, not an execution-admission or scientific-readiness receipt; the parent [PROTOCOL.md](../PROTOCOL.md) governs the design.

Written from read-only source and host observations on 10-08-2026. The resource/readiness snapshot below was taken at approximately 18:52 PDT; later bounded path/control-receipt verification was on the same date. Availability must be rechecked by the execution owner. No remote files, workers or model calls were changed during the audit. Effective audit permissions were inherited `danger-full-access` / approval `never`, and useful file reads succeeded.

## Existing paths and source identities

Let `W=/lfs/skampere1/0/brando9/rl4cv_e08` and `R=$W/rl-4-code-verification`. These are the existing experiment08 owner's paths: read them as sources; create experiment09-owned mutable runtime, judge packs, logs and checkpoints. Do not redirect experiment08 state or overwrite its exports.

| Component | Verified location or identity | Remaining admission check |
|---|---|---|
| NeMo RL source | `$W/nemo_rl`, Git commit `c751f811217db7df0d4c94abdeaada6626cfc150`, observed version 0.4.0 | Pin actual source and any experiment09 integration diff |
| Trainer interpreter | `$W/nemo_rl/.venv/bin/python` exists | Import and execute the complete intended training path |
| Generation interpreter | `$W/venv_gen/bin/python` exists | Record generation engine/version and actual loaded libraries |
| Project interpreter | `$R/.venv/bin/python` exists | Record interpreter, dependencies and scorer imports |
| Observed SFT libraries | PyTorch `2.7.1+cu128`; Transformers `4.55.4` | These observations do not prove every trainer worker loads those versions |
| Fixed initialization | `$W/ckpt/1.7B/hf/step_658` exists | Verify every export checksum, model configuration, tokenizer and chat template before use |
| Lean working tree | `$W/grading/lean_src`; `lean-toolchain` exists | Record its literal version, dependency hashes and effective compiler executable |
| VeriBench task/judge repository pin | `external/deps.lock.json`: `c11b99badfa386fd26810b208eef1eb8dc9f6806` | Verify source checkout and required bundle bytes |
| Frozen VeriBench scorer pin | `external/deps.lock.json`: `59059a20d40adf3289869e58302169ad78102877` | Use the pinned scorer with `--skip-tc`; verify its files, not just a directory name |
| Historical RL environment-scaling pin | `7118b86f84e8ce0d8607b09c9826a4a6ffbbd015` | D-105 labels this provisional; do not claim the installed runtime reproduces that paper's trainer |

The export is chosen by the completed training schedule, independent of validation scores. Preserve D-013's exact train/validation/test split of **539 / 135 / 222** and contamination screens. Do not use the older all-VeriBench-held-out experiment03 protocol as authorization for this warm start.

For remote access, disable stale multiplexed sockets with `ssh -S none -o ControlMaster=no -o BatchMode=yes -o ConnectTimeout=12`. The audit reached `brando9@skampere1.stanford.edu` through `brando9@whale.stanford.edu`. On skampere1, `bash --rcfile /dfs/scratch0/brando9/.bashrc -ic '<command>'` restores the native home/path; the default remote AFS home was unavailable. Avoid printing environment or credential contents. Local command execution used `login:false`.

## NeMo interfaces and correctness traps

Relevant source paths below are relative to `$W/nemo_rl` at the observed commit.

- `examples/run_grpo_math.py` imports `MasterConfig`, `grpo_train` and `setup` from `nemo_rl.algorithms.grpo`, `AllTaskProcessedDataset` / `load_response_dataset`, `TaskDataSpec`, and the actor environment helper. The data configuration supports `ResponseDataset` with local train/validation paths and input/output keys. This is a starting integration example, not the frozen experiment09 configuration.
- `nemo_rl/environments/interfaces.py` defines `EnvironmentInterface.step(message_log_batch, metadata) -> EnvironmentReturn`. The return contains `observations` (role/content messages), `metadata`, `next_stop_strings`, tensor `rewards`, tensor `terminateds`, and optional `answers`. It also exposes `global_post_process_and_metrics(batch)`.
- `nemo_rl/experience/rollouts.py` supports `max_rollout_turns`; set it explicitly to two. At observed line 433, `total_rewards[active_indices] += env_output.rewards`: **turn rewards accumulate**. Emit zero after the initial answer and only the selected arm's reward after the final answer.
- At observed lines 441–444, the environment observation is passed directly to the tokenizer with `add_special_tokens=False`; the source explicitly lacks chat-template handling there. Serialize the Qwen user-feedback message and following assistant-generation boundary correctly, with no duplicate end/start tokens. Freeze and hash the rendered template and token-level boundary example. Merely returning a message with `role="user"` does not establish correct boundaries in this path.
- At observed lines 448–463, context exhaustion can truncate the observation and terminate a rollout. Verify that the maximum frozen prompt, both 8,192-token assistant turns and bounded feedback fit the configured context. The protocol minimum is 24,576 tokens, subject to the actual tokenizer bound. Preserve which turn was capped, stop reason and final-answer availability. Never relabel an episode that ended after its initial answer as a valid two-turn final response.
- Metadata updates occur at observed lines 500–502. Preserve task, seed, group/sample, turn, checkpoint and exact scorer/judge identities through compaction and active-batch reindexing.
- The mathematics environment concatenates assistant answers before scoring; this is wrong for the repair task. Extract and score **only the last assistant response** for the terminal outcome. Preserve the initial response separately for its feedback measurement.
- Do not silently inherit the mathematics environment's `batch["rewards"] *= batch["is_end"]` postprocessing. Record and test how overlong or interrupted episodes are admitted, retained or blocked under the frozen protocol; do not manufacture a scientific failure from missing measurement.

**Loss-mask evidence is still required.** Multi-turn support is not proof that the intended tokens receive policy gradients. On a deterministic two-turn trace, inspect token IDs, roles, attention/position handling, response mask, log-probability alignment and final loss mask. All prompt/environment tokens, padding and inserted boundary tokens that are not generated actions must be excluded; both turns' generated assistant tokens must receive the declared treatment. Verify the reference-policy/Kullback–Leibler (KL) term uses the same action positions. Freeze any deliberate first-versus-second-turn weighting. Test rollout-to-optimizer weight synchronization, one actual optimizer step, save/reload and exact resume before declaring the path usable.

The inspected mathematics configuration defaults include reward normalization, a leave-one-out baseline, one rollout turn, disabled dynamic sampling and overlong filtering, KL coefficient 0.01 and clipping 0.2. These are **observations, not scientific defaults to inherit**. The execution manifest must explicitly freeze the chosen advantage normalization, loss aggregation, learning rate, clipping, KL/reference behavior, minibatches, sampling and termination settings. Do not alter these after observing main-training outcomes.

## Full reward semantics and missingness

`src/rl4cv/rewards.py` is the local reward source. Its factors are `t = IC_tests` (extracted, compiling file with at least one example), `p = IC_proofs` (proved/stated theorem fraction), and `f = FSC` on [0,1]. The allowed kernel axioms remain `{propext, Classical.choice, Quot.sound}`. Vacuity remains disqualifying.

- A's terminal reward is the gated strict conjunction **H = 1[t=1 and p=1 and f=1]**, not `kernel_binary`. Implement and test H explicitly; the inspected reward registry does not already expose this full conjunction.
- B/C's terminal reward is the existing gated per-response geometric mean **S = (t*p*f)^(1/3)**. Initial reward is zero in every arm. Initial feedback contains the same S, H and capped compiler text for all arms; only C additionally reveals the named factor vector. No gold text or judge rationale enters model feedback.
- Use the same eligibility and judge procedure in A/B/C and for both initial and final responses. `needs_judge(scored, "scsc")` is true exactly when `t*p > 0` and no vacuous theorem is present. A still needs this common procedure because it receives S feedback and must preserve the matched measurement process.
- If a known deterministic gate forces S/H to zero, skip an unnecessary judge and mark FSC **not required / unmeasured**, not measured zero. A scalar zero can be known while a factor remains null.
- If the response requires FSC and no valid judged value exists, preserve null/error status and block the optimizer batch. Never fill zero, drop the sample, resample a favorable replacement or normalize only the measured group members.
- Compiler infrastructure failure is different from a recorded Lean rejection. Preserve both native status and declared denominator. Validate factor ranges and denominators; do not clip invalid scorer output silently.
- Per-response S is the training reward. Official aggregate SCSC is the geometric mean of factor means on a common measured cohort; mean per-response S is a separate diagnostic.

The parent's locked informativeness gate uses the first 32 train tasks in the first seed's fixed shuffled schedule, eight two-turn samples each: **256 rollouts / 512 assistant responses**. Require at least one within-group positive S variance and at least one S unequal to H. Do not expand the calibration sample or change the reward if these conditions fail. The disposable optimizer-plumbing checkpoint never initializes a main arm.

## Validated judge bridge and route controls

Existing source: `$R/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts/judge_rl4cv_e08.py`.

Its frozen imports reside under:

```text
$R/external/veribench/experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/scripts
$R/external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/scripts
```

The referenced task pack exists at `/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896`. Keep test material isolated from the training owner until all endpoint hashes freeze.

Verified bridge identifiers:

```text
agent: vb103_judge
configs: H2_sol_high, H2_opus55_max
rubric: H2_human_mirror_conventions_demos
rubric fingerprint: 469a2ac3875c1ffc2efaa75290c5c854151191e87fefe76cd5abfc9f219b36c9
repeats: 1, 2, 3 for each of two ensemble members
aggregation: mean(two member medians) / 5
command-line client: /dfs/scratch0/brando9/bin/valk
private configuration exists: /lfs/skampere1/0/brando9/rl4cv_e08/private/valkyrie.yaml
```

The rubric models remain GPT-6 Sol high and Claude Opus 5.5 max, with actual delivered identities/efforts verified. Do not divide an already normalized FSC twice. The `valk --version` diagnostic exited 2 because that option is unsupported; this is not evidence of an authentication failure.

The existing adapter exposes `build_controls`, `build_test`, `admit`, `poll`, `harvest`, `controls_check` and `fsc`. Its suite resolver only accepts experiment08 control/test suites, and its test builder consumes test-system manifests and test cells. It is **not an online training callback**. Build an experiment09-owned batch adapter/service around the frozen judge modules and approved command-line transport; do not edit experiment08 or experiment103 state, packs or benchmarks. Do not introduce host-authored provider application programming interface calls.

Observed receipts under experiment08's `expt_v1/results/`:

- `route_identity_e08.json`: PASS, with non-secret route, organization, payer and credential-source metadata. Reverify for experiment09; a working login alone is insufficient.
- `judge/judge_pack_controls.json`: 25 controls, 25/25 pack round trips, zero failures, PASS. These are five train tasks with oracle/vacuous/shuffled/half-deleted/blank controls.
- `judge/state.json` and `judge/controls_check.json`: absent during the bounded read. **Static pack validation is not live judge acceptance.** Execute and record the required positive/negative controls on the admitted route before reward use, preserving the frozen prompts, model efforts and aggregation.

Cache identity must bind exact candidate bytes, reference/Python-source bytes, rendered prompt/rubric fingerprint, selector/model/effort, judge bundle, extraction/scorer configuration and aggregation. Retain each of six ratings, route/run identity, native errors and reported charges. Reuse only an accepted byte-identical logical invocation; changed candidates or configurations cannot share a cached result. Bounded infrastructure retries follow the protocol and frozen judge procedure, never score-driven replacement.

## Observed experiment08 readiness: not an admission shortcut

At approximately **10-08-2026 18:52 PDT**, `/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/state.json` last tick was `2026-10-09T01:52:39Z`. Eight of twenty trained validation rungs were completed; no `selection.json` existed. All five exports (steps 82, 164, 334, 497, 658) existed for 1.7B, 4B and 8B; none existed for 14B. The inspected completed rungs did not pass the full earlier gate. The full-schedule 1.7B/4B generations were undergoing central-processing-unit (CPU) scoring; 8B inference occupied two devices; the 14B stage needed all eight devices.

Direct file audit of the 75% validation rung, **135 tasks × eight samples = 1,080 rows per model**, found every row `status="scored"`, zero missing kernel/proof rewards and zero differences between `kernel_binary` and `proof_fraction`:

| File in `$W/ladder/validation/scored/` | Pair (0,0) | Pair (1,1) | Intermediate proof fraction | FSC |
|---|---:|---:|---:|---|
| `scored_sft_1p7B_f0p75_g8.jsonl` | 1,036/1,080 | 44/1,080 | 0/1,080 | Null / unmeasured |
| `scored_sft_4B_f0p75_g8.jsonl` | 1,040/1,080 | 40/1,080 | 0/1,080 | Null / unmeasured |

Thus the two existing kernel channels were identical on **2,160/2,160 observed samples**; this is a complete description of those files, not evidence about full S versus H or a training-effect estimate. There is no hypothesis-test claim (`p-val=n/a`). For context, extraction was 875/1,080 and 916/1,080, while capped responses were 205/1,080 and 164/1,080 respectively. These fail the earlier protocol's extraction ≥0.90 and cap ≤0.10 gates. Preserve that conclusion; experiment09's separately frozen exploratory admission does not retroactively pass experiment08.

## Capacity, ownership and bounded execution

The same approximately **18:52 PDT on 10-08-2026** skampere1 observation showed eight A100 80 GiB devices: devices 0–3 had zero observed allocation, devices 4–5 contained another user's resident workload, and devices 6–7 contained experiment08 inference (approximately 70,625 MiB each, 100% utilization). Physical idleness is not a lease. Coordinate with experiment08's owner and its pending all-eight-device 14B stage before acquiring two devices; set explicit device visibility and preserve other users' processes.

The host reported 128 logical CPUs and load averages **989.60 / 977.85 / 946.29**. Memory was approximately 2 TiB total with 1.84 TiB available. Native scratch had **9,209,611,366,400 bytes** available, approximately 15% free; root had **298,675,589,120 bytes** available. These measurements do not support assuming cheap or immediate CPU scoring.

Recommend an execution cap of **at most eight local scorer workers**, matching the protocol's eight-worker ceiling, starting lower if load remains extreme. Use a bounded owned queue, measure compiler latency/timeouts at the chosen concurrency and avoid parallel bulk builds. Reduce concurrency or defer CPU work when throughput deteriorates; never relax scorer timeouts or semantics to hide congestion. A proposed alternative is a healthy mercury1 root-backed owned runtime (parent observed approximately 62 GiB free), subject to relevant health/disk checks. This route was not verified by this audit: preserve exact scorer/toolchain bytes and dependencies, demonstrate matching deterministic controls, and keep data/cache growth within that filesystem's headroom. Do not copy credentials or consume its entire free space.

At the maximum 32-update horizon, six trajectories × 32 updates × four groups × eight samples produce **6,144 main-training rollouts / 12,288 assistant responses**. The worst case is **73,728 main-training judge ratings** if every response is eligible, plus calibration, controls and the separately declared 945 validation / 1,554 test cells. Eligibility and exact-cache savings are unmeasured; do not project a guaranteed call count from the partial validation files.

Select the largest horizon in **{32,16,8}** that conservatively fits the protocol's two-A100, **32 device-hour / 16 elapsed-hour** allocation, including setup, calibration, evaluation and cleanup. Use measured full rollout → Lean → FSC → optimizer latency, memory, lengths and communication, not optimizer speed alone, and freeze the horizon before main training. If eight updates cannot fit, publish capacity blocked. The historical generation and scoring times do not establish an overnight estimate under the observed CPU load. Bound and record reserved-but-idle graphics-processing-unit time during judge waits. Preserve the 200 GiB owned-data cap and at least 5% filesystem headroom.

No experiment09 implementation, model invocation, optimizer step, live judge-control acceptance, device lease or full resource estimate was verified by this handoff. Those are the execution owner's concrete admission tasks; the parent protocol specifies the terminal handling when any gate fails.

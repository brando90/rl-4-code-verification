**TLDR:** This CPU-tested v4 implementation preserves the filtered objective, but launch is blocked because the frozen top-20 generator receipt cannot determine tie-expanded sampling support.

# Experiment 13 v4 implementation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/README.md>

`experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4` implements the frozen [protocol](PROTOCOL.md), commit `d4778e25`, without modifying v2, v3 or the installed runtime. See [the checkpoint](CKPT_v4_implementation.md) for verified counts, limitations and continuation commands.

## Objective and blocking source evidence

The installed vLLM 0.10.0 v1 sampler records raw log-probabilities **before** temperature and filtering. Its native `apply_top_k_top_p` sorts logits ascending, removes logits **strictly below** the kth logit (so all kth ties survive), renormalizes, then removes the ascending probability tail with cumulative mass **≤ 1 − p**. The remaining boundary token stays. Seeded requests use the native path even when FlashInfer is installed; launch must verify that backend. Ties in `torch.sort` are not made stable by this implementation because the installed sampler does not make them stable.

The generator's `gather_logprobs` returns exactly `torch.topk(..., 20)` plus the sampled token, not the complete tie-expanded top-k set. For 40 equal logits, the native filter retains 38 tokens, but the top-20 receipt contains only 20 (at most 21 including a sampled token outside that list). Exact support and normalization cannot be reconstructed. Even an apparently untied bottom entry cannot certify that the next omitted logit differs. Sorting a truncated list also loses the full-vocabulary tie order at a top-p boundary.

`filtered_policy.reconstruct` therefore refuses uncertified truncated receipts. Its positive reconstruction tests cover complete tiny vocabularies and a certified tie-free top-k list; **no generator-side completeness certificate exists in the frozen receipt**. These tests do not admit real generation. The smallest proposed amendment records the actual filtered support and normalized log-probabilities at sampling time (or a complete tie-expanded set with original ordering and a completeness certificate), keeping temperature, sampling, trainer support and objective unchanged. The protocol is left untouched.

`trainer_support.collect_old_support` is a removable forward hook on the actual NeMo worker model. It captures the old full-vocabulary logits during `get_logprobs`, freezes the old support and trainer log-probabilities, and discards NeMo's unfiltered result. `nemo_objective.FilteredClippedPGLossFn` gathers the once-scaled current logits at those frozen IDs and passes the equivalent compact vocabulary to **the installed NeMo clipped policy-gradient loss**. Its asymmetric clipping, importance cap 2 and global token normalization remain installed code. `train_filtered` passes that callable to `Policy.train`; launch must make the v4 directory importable in every worker. `worker_hooks.py` installs float32 temperature division on the owned worker: NeMo already scales logits before invoking its loss, so the wrapper must not divide again. The old-weight capture runs before that scaling. Only the single-device, one-rank distributed tensor path is admitted by the wrapper.

The CPU integration test executes that installed loss and backward on tiny synthetic logits. It redirects only the parent's hard-coded target-ID `.cuda()` to CPU. It constructs no model engine and performs no optimizer step. Full worker/device integration remains a launch measurement; the code does not claim that it passed.

## Directory structure

| File under `phase2/` | Purpose |
|---|---|
| `filtered_policy.py`, `generation_contract.py` | Exact native support, conditional reconstruction, raw top-20 sampler settings and preservation |
| `trainer_support.py`, `worker_hooks.py`, `nemo_objective.py` | Old-weight support hook and actual NeMo loss interface |
| `context_contract.py`, `pilot_configuration.py` | Complete prompt inventory and migrated response/context validators |
| `group_selection.py` | Seeded G0 tasks, unbiased mixed-group estimate, paired 10,000-draw bootstrap, T2 subset |
| `gates.py`, `gate_receipts.py`, `maximum_length_probe.py` | T1–T4 measurements, reward fallback and replay binding; launch-only full-length forward/backward |
| `placebo.py` | 90% measured-slot admission, sorted `.17g` hash, counter draws bound before responses, density/variance |
| `pilot_metrics.py` | Conservative A/1301 T5, all-six extension, fixed two-seed first-30-update token budget |
| `a6_counts.py`, `A6_counts.json` | Read-only private receipt reducer and identity-free aggregate output/input hashes |
| `device_guard.py`, `gpu_inventory.py` | Idle-device/ownership guard and read-only three-host inventory |
| `autoresume_watchdog.py`, `install_watchdog.py` | v4-only restart decisions, locks, attempt cap and explicit cron installer |
| `admission.py`, `admission_cpu.json` | Complete code/test/evidence binding and explicit frozen-objective launch refusal |
| `context_values.json`, `gpu_inventory.json` | CPU-derived lengths and dated device/process census |
| `common.py` | Streaming hashes and exclusive durable receipts |
| `tests/*.py` | Synthetic controls and installed-source/installed-loss CPU integration |

The watchdog requires an admission-bound argument-vector plan with the owner's concrete recovery commands. It refuses uncertain liveness, preserves partial samples, reserves at most three attempts per update and distinguishes an extended 60-update trajectory from a completed 30-update trajectory. No cron entry or tmux hook is installed by importing or testing it. Recovery commands and the measured rollout/scorer/pilot orchestration must be finalized after the generator contract is implementable; copying the old v3 runner would silently restore its retired objective and lengths.

## Bound CPU evidence

Both engines need **20,041** positions: max prompt **7,753** train / **4,399** validation / **4,996** test, plus **12,288** response tokens; model maximum **32,768**. All 539/135/222 prompt inventories were measured locally. Only held-out instructions needed for length rendering were read; no held-out reference, outcome or generated output was used or exposed. The rendering/tokenizer/config hashes are retained, not held-out text or identities.

The private A6 reducer reproduces the protocol: strict-success histogram `{0:51, 1:2, 2:3, 3:3, 4:0, 5:2, 6:1, 7:1, 8:1}`, complete groups 54, mixed strict groups 8, varying B groups 49. It retains all 512 slots: 496 measured, 16 missing, 48 known successes. These are exact descriptive counts, not fresh statistical estimates; intervals/p-values are not applicable to byte-for-byte count reproduction. No discrepancy or protocol edit.

The placebo serialization is numeric ascending rewards, one 17-significant-digit ASCII decimal per line including a final newline. Keys are `e13v4-placebo\0seed\0update\0slot`; SHA-256 counter blocks with rejection sampling avoid modulo bias. All planned draws, including optional pilot updates 31–60, must be frozen before the first P response. Missing reward groups have explicit measured/declared denominators in density reports.

## CPU verification

From the checkout root, with pytest installed into the **separate** `/lfs/skampere1/0/brando9/rl4cv_e13v4/test_deps` directory:

```bash
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/lfs/skampere1/0/brando9/rl4cv_e13v4/test_deps:$PWD/src
/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python -m pytest -q experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/tests
```

No installation is permitted into the shared NeMo runtime. The checkpoint contains final test counts and publication status. The admission command's CPU `check` verifies bytes; `launch-check` must fail under this frozen protocol. A successful CPU test is not a technical-gate measurement or launch authorization.

# Experiment 13 v4 Amendment V4-A2: receipt-invariance criterion and sampler-backend binding

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/AMENDMENT_V4-A2_receipt_invariance_and_sampler_backend_10-20-2026.md>

**Status:** adopted 10-20-2026 by the experiment 13 master, before any v4 generation or gate statistic. The general coordinator's light QA (Claude Fable 5.1, max effort, run at Brando's request) judged [V4-A1](AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md) correct (9/10) and asked for these two additions. Nothing else in [PROTOCOL.md](PROTOCOL.md) or V4-A1 changes.

**TLDR:** V4-A1 said the top-64 receipt changes only what is recorded, not sampling, but gave no pass criterion for checking that. This amendment adds one. It also pins the vLLM sampler path that the reconstruction mirrors, the PyTorch-native top-k/top-p rather than FlashInfer, and logs the selected path in the V4-T1 receipt.

## (a) Receipt invariance: pass criterion

The check runs inside V4-T1 and has two parts. Both must pass, or V4-T1 fails.

1. **Exact unit check on the installed sampler.**
   - Run the installed vLLM 0.10.0 `Sampler.forward` on synthetic logits and fixed per-request generators: at least 10,000 positions, including the tie cases from V4-A1.
   - Do it once without log-probabilities and once with 64.
   - The sampled token IDs must be identical at every position.
2. **Engine check on the frozen 8-response T1 probe.**
   - **Runs:** generate R0 without the receipt and R1 with it. Both use the same prompts, per-request seeds, batch composition (all 8 submitted together), engine settings and device type, so the receipt is the only difference.
   - **Pass:** R0 and R1 are token-identical on all 8 responses.
   - **If any response differs:** generate R2, a repeat of R0. If R0 and R2 also differ, the engine itself is not deterministic. The check then passes only if the number of responses that differ between R0 and R1 is at most the number that differ between R0 and R2, plus one. Otherwise V4-T1 fails.
   - **Reported:** the first divergence position of every differing response.

The extra generations are technical probes. They enter no learning or comparison statistic.

## (b) Sampler backend binding

- **Background.** In vLLM 0.10.0's V1 engine, an unset `VLLM_USE_FLASHINFER_SAMPLER` means FlashInfer is used whenever it is installed (version ≥ 0.2.3). FlashInfer's top-k/top-p kernel is a different algorithm from the native `apply_top_k_top_p` that V4-A1 reconstructs.
- **Current state.** The pinned venv (`/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv`) has no `flashinfer`. The v2 and v3 generation logs show vLLM's warning "FlashInfer is not available. Falling back to the PyTorch-native implementation".
- **Rules.**
  - Every v4 generator sets `VLLM_USE_FLASHINFER_SAMPLER=0` explicitly.
  - The admission records an import check showing `flashinfer` is absent.
  - Each V4-T1, V4-G0 and update generation receipt logs the selected `TopKTopPSampler.forward` (`forward_native`), read in the worker process, plus the vLLM backend log line.
  - Any other selected path fails V4-T1 as unimplementable, the same rule V4-A1 applies to the engine limit.

**Disclosure.** The A6 diagnostic that motivated the sampler ran on the native path: its attempt-2 generation log (`/lfs/skampere1/0/brando9/rl4cv_e13v2/phase1/A6/execution_attempt2/generation.log`) carries the "FlashInfer is not available … PyTorch-native" warning. v4's sampling algorithm is therefore the one A6 used.

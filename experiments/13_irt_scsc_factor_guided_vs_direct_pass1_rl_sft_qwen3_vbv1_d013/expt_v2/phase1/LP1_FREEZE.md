# Experiment 13 version 2: LP-1 generation admission freeze

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/LP1_FREEZE.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` has published G0 PASS. This lock admits one generation-only probability probe when an idle, unreserved device is available. It records no probability result or training admission.

The [LP-1 lock](../locks/LP1.json) binds the sampler, probe, runtime, dispatcher, tests and private route configuration. The launcher verifies the exact published lock, all bindings and the G0 result before any lease claim. A persistent exclusive attempt ledger prevents a second probe across polls, restarts and hosts. The existing fifteen-minute poller starts the dispatcher only after the owner installs a launch plan naming the verified publication revision. No cron entry is replaced.

## Probe and probability rule

Eight train tasks were chosen by an outcome-independent identifier hash, one sample each. The private manifest has eight responses; its digest and the exact 539-task train allowlist are bound. No test prompt is loaded. Full 4B supervised fine-tuning export step 658 is the common generator/trainer policy. The export, tokenizer, chat template and all installed NeMo source files are bound per route.

Generation uses vLLM 0.10.0, bfloat16, temperature 1, top-p 1, disabled top-k, no other sampling filter, no stop string, and 8,192 new tokens. Context length 15,945 accommodates the longest train prompt (7,753 tokens). Thinking is enabled. End tokens 151643 and 151645 remain in the generated-token probability mask. Per-cell seeds are recorded before the model call; batches retain all raw outputs before per-cell validation. A capped response remains in the denominator and can pass the official scorer.

The installed NeMo RL `Policy.get_logprobs` path evaluates the identical token sequence after generation exits and its processes are cleaned up. It uses the original distributed-tensor worker, a new local Ray instance, and no optimizer or reference model. The newer worker's missing package is not bypassed at runtime. Package versions and CPU imports were checked on every route; actual generator/trainer agreement remains unmeasured.

Admission requires zero unsupported tokens, median absolute log-probability error at most 0.01, 99th-percentile error at most 0.10, and importance-ratio truncation above 2 on at most 1% of generated tokens (PROTOCOL sections 5–6). Prompt tokens are excluded; every generated token is included. Structural or incomplete receipts cannot pass. This fixed technical probe has no population hypothesis test or confidence interval (p-val=n/a).

## Device and storage plan

The first eligible device on skampere1, skampere2 or skampere3 may be claimed through the experiment-13 registry. Eligibility requires no compute processes, no foreign lease or reservation, at least 40,000 MiB device memory, 64 GiB available host memory and 8 GiB free local scratch after deployment. Current compute processes are checked again after claiming and at each model-stage boundary. Only processes carrying this attempt's exact execution marker may use the leased device.

Own runtime/model copies on skampere2/3 fit the recorded 50 GiB preparation allowance per node. [CPU route verification](LP1_route_verification.json) passed 132 bindings and eight package-version checks on each of three hosts, with zero model calls and zero device allocations. Local free bytes were 5,620,187,435,008; 311,721,664,512; and 117,161,537,536, respectively. These bounded requirements use actual free space; a percentage-free warning does not make a busy device a terminal blocker.

The attempt has a 1,800-second device limit, at most 65,536 generated tokens, zero optimizer updates and zero retries. The cumulative LP-1 allowance is 0.6 device-hours including any abandoned prelaunch claims; no new paid service is used. Remaining Phase 1 anchor generation is separately planned at approximately 4–6 large-device-hours under PLAN section 5 and is not launched by this dispatcher.

[Foreign reservation review](LP1_foreign_reservations.json) reconciles all 33 canonical experiment-08 leases as released, eight experiment-09 historical control snapshots against matching releases, and its old preflight snapshot against the canonical release. Bounded experiment-12/14 root searches found no lease/reservation files. The master reservation record is hash-bound; a change requires a fresh owner review. Canonical foreign leases are reread before every claim. Unknown or active reservations exclude a device.

Mercury1/2 remain permitted for generation-only work if an admitted plan fits their 16 GiB devices and local storage. They are observed by the poller but are not routes in this single-device full trainer probe. No other user's process or storage is changed.

## Exit and continuation

The dispatcher registers with the owner's watchdog. Each stage runs in an owned process group; cleanup signals only exact marked processes using process-identifier file descriptors. It must verify cleanup before retiring the remote lease and releasing the canonical lease. An uncertain remote exit retains `CLEANUP_REQUIRED`, requiring adoption/cleanup, never a probe retry. Receipts retain partial generation and errors.

After publication, arm the private launch plan and verify the first useful dispatch result. A busy-device result is `WAIT_FOR_IDLE_UNRESERVED_DEVICE`; continue anchor scoring and the final G1 input/bounds implementation while polling. A completed probe gets a published LP-1 report before any anchor generation. G1 remains draft until final historical input bindings and publication; no actual-data fit has run.

Publication verification: `E13_REQUIRE_LEAN_INTEGRATION=1 make test` exited 0; **512 passed, 23 skipped, zero failed in 240.62 seconds**. Receipt: [LP1_publication_test.json](LP1_publication_test.json).

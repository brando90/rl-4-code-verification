# 1.7B seen-versus-fresh diagnostic continuation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v7/CKPT_seen_fresh.md

**TLDR:** The user authorized proposal 1: run 50 seen and 50 fresh functions on
the augmented 1.7B export, checking exact response format and correctness.

Created: 10-19-2026 03:51 PDT. Last updated: 10-19-2026 04:05 PDT.

## State

- Owned checkout: `/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-tiny-training-10-19-2026`.
- Remote root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/diagnostic_seen_fresh_v7`.
- Original session: `rl4cv-tiny-seen-fresh`; coordinator PID 681970, superseded.
- Final CPU continuation: `rl4cv-tiny-seen-fresh-12`, `parallel_checking.py`; COMPLETE.
- Admission passed: 100 tasks, 50/50 cohorts. Manifest SHA-256
  `6235207934fab08f9cb157351a80c61e8e3261daa2234b2a2ec972905ea93f8d`.
- Exact consumed training source SHA-256
  `2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119`.
- All five checker controls passed. All 100 responses are generated and extracted,
  zero truncated, 118–222 generated tokens; all 100 CPU checks are complete.
- Strict successes: seen 29/50, fresh 9/50; all 100 meet formatting gates.
- Linux repository gate: 1362 passed, 24 skipped, 6 subtests passed.
- Device 1 was released after successful generation. Model identities and complete
  allocation/release receipts are in results/.
- Main v6 jobs continue unchanged. Local `rl4cv-tiny-training-watch` observer was
  stopped gracefully to keep one Git writer during this publication; resume it.
- Linux gate uses owned isolated test venv/ripgrep and historical dependency layout;
  inaccessible foreign optional fixtures skip explicitly.
- No subagents, hosted calls, new optimizer updates or benchmark test evaluation.

## Next actions

The verified results and compact evidence are published at commit `da4a153`.
Mirror version 7 into the canonical checkout, then restart the version-6 observer.
This owned checkout remains necessary for that active training observer; remove it
only after version-6 training/evaluation and publication finish.
No new training or generations are authorized by this diagnostic.

## Event log

- 10-19-2026 03:51 PDT: Defined the 100-function diagnostic, verified admission,
  and started the persistent coordinator at the checker-control phase.

- 10-19-2026 03:54 PDT: Five controls passed and all 100 short responses generated; GPU released, checking started. Local full-suite tests expose preexisting Linux-specific failures; running the Linux gate with unavailable foreign experiment-13 integration fixtures explicitly skipped.

- 10-19-2026 04:00 PDT: Recorded CPU-admission amendment, preserved 30 completed check records, verified the waiting checker had no children, and ended only that owned process. Started a continuation with the unchanged verifier and original deadline, allowing two diagnostic workers beside eight control scorers.

- 10-19-2026 04:03 PDT: On user request, increased CPU checking from two to twelve workers, preserving 66 complete records and archiving two interrupted checks. All 100 checks completed in about 33 seconds after restart; seen 29/50, fresh 9/50. Linux make test passes.

- 10-19-2026 04:05 PDT: Published complete diagnostic source, all 100 judgments, compiler/proof evidence and passing Linux test receipt to main at da4a153; preserving the checkout for the ongoing version-6 observer.

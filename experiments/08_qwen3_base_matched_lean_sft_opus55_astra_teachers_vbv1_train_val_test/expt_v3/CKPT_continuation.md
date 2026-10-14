# Matched warm start continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_continuation.md>
**TLDR:** Meeting plan and deterministic preparation complete; new training not launched.
Created: 10-13-2026 17:41 PDT
Last updated: 10-13-2026 17:50 PDT
## Goal
- Help Lethan (1.7B/8B) and Rakshit (4B/14B) improve matched warm starts.
## What ran
- Existing-record audit, short evidence lookups, and host hash verification (685 responses +587 Lean files); zero model-generation calls.
- Checks: 5 focused passed; Linux full suite 323 passed/24 skipped (287.25s); see results/verification.json.
## Results
- 685 cached candidates, zero additional source tasks; MBPP source 587 pairs/455 tasks before conversion.
- Validation: all four ×1,080 known cells; full values/intervals in RESULTS_continuation_audit.md.
## Stuck / blocked
- No preparation blocker; admission, rendering and prospective protocol still required before training.
- Existing v2 evaluation is owned by codexv-rl4cv-e08v2-matched-test; verified live 17:33 PDT.
## Next steps
- [p 9/10] Reproduce: `python experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/prepare_continuation.py`; then on-host joint admission.
- [p 8/10] Freeze matching token/optimizer rules and execute the two-condition plan.
## Brando to-do
- None.
## Ownership and cleanup
- Canonical: /Users/brandomiranda/rl-4-code-verification; temporary: /Users/brandomiranda/.codex/worktrees/meeting-sft-continuation/rl-4-code-verification.
- Root agent owns publication, canonical synchronization and managed-worktree removal after verification.
## Log
- 10-13-2026 17:41 PDT -- Prepared meeting plan, validation audit and cached train manifest; no new training.
- 10-13-2026 17:46 PDT -- Verified all cached source hashes on skampere1; local platform failures routed to isolated Linux tests.
- 10-13-2026 17:50 PDT -- Linux make test passed (323/24); audit reproduced byte-for-byte; source code hashes match tested checkout.

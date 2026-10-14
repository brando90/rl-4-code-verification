# Matched warm start continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_continuation.md>
**TLDR:** Failure taxonomy of the four step-658 validation ladders is published (zero model calls); the shared corpus admission runs on skampere1 and the two-condition protocol is drafted but not locked; no training launched.
Created: 10-13-2026 17:41 PDT
Last updated: 10-14-2026 13:45 PDT
## Goal
- Help Lethan (1.7B/8B) and Rakshit (4B/14B) improve matched warm starts: (a) failure taxonomy, (b) shared corpus admission, (c) draft two-condition protocol. Prepared for them; no training launched by this worker.
## What ran
- 10-13: existing-record audit, host hash verification (685 responses + 587 Lean files); Linux full suite 323 passed/24 skipped (results/verification.json).
- 10-14 (Claude Code worker, ultracode round, zero model calls, Valkyrie route down): `failure_taxonomy.py` on skampere1 over 4 x 1,080 validation cells from the saved generations, scored rows and kernel receipts; deterministic `lake env lean` recheck of 4 representative plus 48 sampled compile-error files (tmux `rl4cv-e08v3-admission-10-14`, logs under `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/results/lean_recheck*/`); `admit_corpus_v3.py` launched in the same tmux session (window `admit`, log `sft_v3/results/admit.log`).
## Results
- Taxonomy (per 1,080 cells; primary, mutually exclusive): no Lean extracted 183 / 134 / 106 / 85 for 1.7B / 4B / 8B / 14B; compile error 844 / 846 / 870 / 865; kernel success 53 / 100 / 104 / 130; the "compiles but unproved" buckets are empty at every size because the frozen scorer reports `compiles` only for files whose every proof checks. Every capped cell (184 / 134 / 106 / 84) is an unterminated file. Full numbers and task-bootstrap intervals: [RESULTS_failure_taxonomy.md](RESULTS_failure_taxonomy.md), results/failure_taxonomy.json.
- Corpus admission: see results/admitted_corpus_stats.json once the host job finishes (this line is updated by the worker at publication).
## Stuck / blocked
- Valkyrie route HTTP 403 since 10-13-2026 03:27 PDT: no judged SCSC evaluation and no new teacher data; corpus preparation does not need it.
- No GPU training this round by instruction; mentees own the launches.
## Next steps
- [p 9/10] Lethan/Rakshit: read the taxonomy; the 1.7B and 4B deficits are the 184 / 134 unterminated generations plus the 78% compile-error mass, not missing format markers.
- [p 9/10] Finish admission: `ssh brando9@skampere1.stanford.edu 'tail -40 /lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/results/admit.log'`; if it ended with EXIT=0 copy `sft_v3/results/admitted_corpus_{manifest.csv,stats.json}` into expt_v3/results/ and commit; otherwise rerun `source /lfs/skampere1/0/brando9/rl4cv_e08/env_e08.sh && /lfs/skampere1/0/brando9/rl4cv_e08/venv_gen/bin/python /lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/scripts/admit_corpus_v3.py`.
- [p 8/10] Lock PROTOCOL.md (currently DRAFT) with the admitted counts, then run the two-condition continuation.
## Brando to-do
- Confirm the draft decision rule and the 5,752,936-token continuation budget before the mentees lock PROTOCOL.md; Vals route restoration remains the judged-evaluation dependency.
## Ownership and cleanup
- 10-14 worker: detached worktree of the Mac checkout; host files only under `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/`; version-1 and version-2 host files untouched; tmux `rl4cv-e08v3-admission-10-14` left running only while its jobs run.
## Log
- 10-13-2026 17:41 PDT -- Prepared meeting plan, validation audit and cached train manifest; no new training.
- 10-13-2026 17:46 PDT -- Verified all cached source hashes on skampere1; local platform failures routed to isolated Linux tests.
- 10-13-2026 17:50 PDT -- Linux make test passed (323/24); audit reproduced byte-for-byte; source code hashes match tested checkout.
- 10-13-2026 17:52 PDT -- Integrated concurrent c7940fe closeout; corrected plan to PARTIAL, preserved tested continuation code.
- 10-13-2026 17:53 PDT -- Integration checks 11 passed; incoming v2 tree preserved exactly; Linux verification clone removed.
- 10-14-2026 13:20 PDT -- Taxonomy computed for 4 x 1,080 validation cells; RUN START email sent (Gmail connector); Lean rechecks launched in tmux.
- 10-14-2026 13:45 PDT -- Taxonomy with task-bootstrap intervals and sampled error kinds published; admission job running; PROTOCOL draft in progress.

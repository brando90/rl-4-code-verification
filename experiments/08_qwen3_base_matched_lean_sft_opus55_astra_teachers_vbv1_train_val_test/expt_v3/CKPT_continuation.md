# Matched warm start continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_continuation.md>
**TLDR:** Failure taxonomy of the four step-658 validation ladders is published (zero model calls); the shared corpus admission runs on skampere1 and the two-condition protocol is drafted but not locked; no training launched.
Created: 10-13-2026 17:41 PDT
Last updated: 10-14-2026 14:02 PDT
## Goal
- Help Lethan (1.7B/8B) and Rakshit (4B/14B) improve matched warm starts: (a) failure taxonomy, (b) shared corpus admission, (c) draft two-condition protocol. Prepared for them; no training launched by this worker.
## What ran
- 10-13: existing-record audit, host hash verification (685 responses + 587 Lean files); Linux full suite 323 passed/24 skipped (results/verification.json).
- 10-14 (Claude Code worker, ultracode round, zero model calls, Valkyrie route down): `failure_taxonomy.py` on skampere1 over 4 x 1,080 validation cells from the saved generations, scored rows and kernel receipts; deterministic `lake env lean` recheck of 4 representative plus 48 sampled compile-error files (tmux `rl4cv-e08v3-admission-10-14`, logs under `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/results/lean_recheck*/`); `admit_corpus_v3.py` launched in the same tmux session (window `admit`, log `sft_v3/results/admit.log`).
## Results
- Taxonomy (per 1,080 cells; primary, mutually exclusive): no Lean extracted 183 / 134 / 106 / 85 for 1.7B / 4B / 8B / 14B; compile error 844 / 846 / 870 / 865; kernel success 53 / 100 / 104 / 130; the "compiles but unproved" buckets are empty at every size because the frozen scorer reports `compiles` only for files whose every proof checks. Every capped cell (184 / 134 / 106 / 84) is an unterminated file. Full numbers and task-bootstrap intervals: [RESULTS_failure_taxonomy.md](RESULTS_failure_taxonomy.md), results/failure_taxonomy.json.
- Corpus admission (host job EXIT=0, 10-14 ~13:55 PDT): 2,585 / 2,587 candidates admitted — 1,315 / 1,315 originals, 685 / 685 cached responses (2,924,523 loss tokens, 360 train tasks), 585 / 587 MBPP pairs (2,505,008 tokens, 453 tasks; 2 rejected `over_length_cap`: `mbpp__task_173` 19,499 and `mbpp__task_761` 17,866 total tokens); 0 exact / 0 near duplicates; 0 / 7,761 held-out screen hits; corpus `sft_v3/s_v3_candidates.jsonl` SHA-256 `7fa02557…`; manifest SHA-256 `3ed7cb7a…`. Files: results/admitted_corpus_manifest.csv, results/admitted_corpus_stats.json, mbpp_conversion_spec.md.
- PROTOCOL.md drafted (DRAFT, NOT LOCKED) with both conditions, token accounting, learning-rate reset, gates, decision rule, compute estimate and owner split.
## Stuck / blocked
- Valkyrie route HTTP 403 since 10-13-2026 03:27 PDT: no judged SCSC evaluation and no new teacher data; corpus preparation does not need it.
- No GPU training this round by instruction; mentees own the launches.
## Next steps
- [p 9/10] Lethan/Rakshit: read the taxonomy; the 1.7B and 4B deficits are the 184 / 134 unterminated generations plus the 78% compile-error mass, not missing format markers.
- [p 9/10] Owners lock PROTOCOL.md (confirm the two `[decide at lock]` items), precompute `sft_schedule_v3_{R,E}.json` from `results/admitted_corpus_manifest.csv` (`n_assistant_tokens` + 1 end-of-text token per example, global batch 2, hash order), freeze `results/ladder_manifest_v3.json` and the forecast, dry-run the E data path on 1.7B, then train. Exact next command on the host: `source /lfs/skampere1/0/brando9/rl4cv_e08/env_e08.sh && /lfs/skampere1/0/brando9/rl4cv_e08/venv_gen/bin/python /lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/scripts/admit_corpus_v3.py` reproduces the admitted corpus if it is ever rebuilt (deterministic; same hashes expected).
- [p 7/10] Close the tmux session `rl4cv-e08v3-admission-10-14` on skampere1 once the owners have copied what they need (`tmux kill-session -t rl4cv-e08v3-admission-10-14`); it holds no running job after the admission exit.
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
- 10-14-2026 14:02 PDT -- Taxonomy committed (a6ac53b, macOS tests 320 passed / 36 skipped / 4 known failures); admission finished EXIT=0 (2,585 / 2,587 admitted); PROTOCOL draft, README, results.md updated; publishing (b)+(c).

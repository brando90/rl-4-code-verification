# V18 checkpoint: Complete original-pool explicit proof cleanup

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Local source and protocol are ready for a new 1,540-case continuation. The existing SNAP SSH master died during deployment, so no V18 model call has started; resume upload, preparation, controls and the first real four-file batch once the root restores login.

Created: 10-19-2026 10:45 PDT
Last updated: 10-19-2026 10:45 PDT

## State

- Owner `/root/cleanup_original_pool`; edits only V18, no Git staging/pushing; V13 completed artifacts remain immutable.
- Remote root `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v18`; code in matching remote repo experiment V18 directory.
- Original manifest 2,585 rows; inherit 818 exact-byte V13 successes, CPU-kernel-check 227 unchanged originals, attempt remaining 1,540 in 385 four-file batches.
- Terra `gpt-5.6-terra`, high; Codex CLI 0.114.0; max32 identities,16compiler slots;2CLI attempts/batch,4candidate hashes/case,900sec/CLI,120sec/compiler.
- Shared budget helper V15/campaign_budget.py deployed by root before transport broke; shared total authorization900, cleanup780/adaptation120; prior cleanup conservative469.991219 counts.
- Prospective additional conservative cost154–308, uncertain. Per-call reserve10/observedstop1.20; helper activates preapproved third tranche early for useful parallelism.
- Blocker: old local tmux ssh-tiny-training pane died255 at10:40:39; old control socket missing. Canceled own hanging ssh/scp processes; no gateway retry loop. Root restoring human-only login.
- Next after live control: upload all V18sources; run repair_batches.py prepare; controls.py; repair_batches.py launch --first; start ordinary watcher. Verify actual model, first batch receipts/cost and then automatic fanout.
- Watcher timer15sec; observes dead/idle/missing outcomes, adopts healthy child within original bounds, never counts unattempted proof as irreparable.
- Final contract: accepted-only fully_cleaned_existing_training.jsonl + replacements.jsonl +2,585-row outcome CSV +bound completion; no automated fallback training rows.
- V19 training owner/root waits for immutable V18 completion. Current V12 partial cleaned comparison remains separately frozen.

## Event log

- 10-19-2026 10:45 PDT: New user request expands authorized total to900; focused four-file continuation source/protocol prepared. SNAP master died during attempted upload; no V18 paid calls. Root restoring transport while ordinary watcher/finalizer code is prepared locally.

# V24: retained compiler diagnostics for three completed1.7B runs

**Doc link:** [diagnostic runner](diagnose.py)

**TLDR:** User requested a comparable failure breakdown and durable future error logs. Reuse all851 existing V12 failure logs, recover missing V20/V23 compiler diagnostics, and retain exact stdout/stderr/source/exit/timeout evidence. Existing official scores and outputs remain unchanged.

## Diagnostic recovery

- Analyze all1080cells per completed run: V12continued checkpoint(11.11%),V20freshbase(1.85%),V23freshbase+500tiny(1.57%). Preserve official extraction/compilation/success statuses, row identities and saved raw/model-source hashes.
- Reuse V12's existing20-second diagnostic checks with exact source/hash agreement. For each extracted failed V20/V23 source, run pinned Lean4.22.0 through the unchanged saved Lake adapter in its original grading environment, one compiler thread and20seconds per diagnostic. This is not an official rescoring or the600/900-second scoring limit.
- User requested maximum practical parallelism: host128logicalCPUs, observed load18, availablememory~1.9TiB; use96workers leaving capacity for other users and orchestration. No GPUs, teacher/modelcalls or model regeneration.
- Classify the first recorded compiler error into mutually exclusive symptom categories. Count additional error flags separately; lexical presence does not establish blame. Unknown names may include wrong namespaces/fields rather than invented mathematical concepts. A false decide/native_decide proposition does not identify whether implementation, test or statement is wrong. Report proof-search failure only when a diagnostic names the tactic and failure, not merely when the source contains it.
- Retain separate stdout/stderr, command, sourcehash, returncode, diagnostic-timeout flag and compiler/toolchain identity. Original V12 logs were combined and are labeled as such; their streams cannot be reconstructed separately. Diagnostic timeouts, no formatted error and diagnostic recompiles that pass remain explicit unresolved categories.
- Output RUN/failure_diagnostics_v24/{protocol,progress,summary}.json, all_cells.csv, and per-source cells/diagnostic.json+stdout.log+stderr.log. Resume only exactsource/hash-matching existing diagnostic receipts. Record partial progress; do not present a partial sweep as complete.

## Future logging

Owned future_logging/ sources provide an explicitly amended scoring entry that retains stdout/stderr and command/result/source/timeout sidecars for initial Lean compilation and kernel probes, without changing proof acceptance or frozen timeout rules. OldV20/V23 sources and verdicts remain immutable. Actual success/error/timeout and deleted-temp-directory survival controls must pass before using this future path.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

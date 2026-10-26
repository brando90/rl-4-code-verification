# Dispatch 8: experiment 13 v4, foreign-GPU flapping and zero-effect stage failures (CPU only; no GPU)

**TLDR:** v4's first live T1 attempt failed after 13.4 s on `device_guard.Busy('compute ownership unreadable')`. Another user's process appeared on the leased GPU, and the guard correctly refused it. No generation happened, but the real stage path writes no `infrastructure_failure.json`, so `recovery.py` returns `STOP_PARTIAL` and the v4 watchdog sits in DIAGNOSE.

Meanwhile `alexspan` runs short jobs on authorized GPU 7, so GPU 7 looks idle in the gaps and then turns busy. The same foreign-GPU aborts killed four v3 runs today. Make leasing robust, classify zero-effect failures honestly, test, and re-admit. Use no GPU and run no gate.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

**Owner:** Codex `gpt-6-astra`, **ultra** effort, on skampere1. The dispatcher is the experiment 13 master, on 10-21-2026 at about 19:15 PDT. All earlier binding limits still apply.

## Evidence

- **The failed attempt.** `run/T1/probe/attempt_01/R0`:
  - `run.log` ends in `stage_worker.py: check(config)`, then `device_guard.py:91`, then `Busy('compute ownership unreadable')`;
  - `execution.json` records `device_seconds` 13.44 and `exit_code` 1;
  - there are 0 `*.generation.json` files and no `statistics_reserved.json`.
- **v4 watchdog log:** `{"recovery": {"action": "STOP_PARTIAL", "path": ".../T1/probe/attempt_01"}, "status": "DIAGNOSE"}`.
- **GPU census at 18:45 and 19:00.** GPUs 0 and 5 held brando9's v3 stages. GPU 7 held `alexspan` processes that were 2:39 old, then a different PID 0:18 old, so short jobs come and go.
- **v3 deaths 18:10–18:40.** The frozen v3 device guard raised `PermissionError` on `/proc/<foreign pid>/environ`, for runs A_1302 u7, B_1301 u22, B_1302 u13 and P_1302 u10.

## What to build

1. **Sustained-idle leasing** in the v4 device guard. Lease an authorized device only after two complete observations at least 60 s apart, each with no compute process from any user and no v3 lock or lease. Recheck immediately before the stage starts its engine.
2. **Pre-engine refusal is not an attempt.** If the device check refuses before any engine or model load, generation, optimizer step or statistic, the worker releases the lease and writes a `lease_refused.json` receipt. The stage then waits and retries the lease later. It does **not** create a consumed A4 attempt. Bound the retries and log them.
3. **Real zero-effect failures are recorded.** Any real stage failure that started an attempt but provably generated 0 responses, started no optimizer and reserved no statistic writes `infrastructure_failure.json` with the exact fields `recovery.py` expects. "Provably" is checked from durable files, never assumed. Anything else stays `STOP_PARTIAL`.
4. **Existing `attempt_01`.** Classify it from its files under the new rules, which most likely makes it a pre-engine refusal. Record the classification and its evidence, and do not delete the directory. If it must count as an A4 attempt under the frozen rules, say so explicitly. Never generate a T1 statistic in this dispatch.
5. **Tests.**
   - Flapping-foreign-process fakes.
   - Lease refusal does not consume an attempt.
   - The zero-effect record is written only when provable.
   - `recovery.py` gives RETRY_EMPTY versus STOP_PARTIAL correctly.
   - Rerun the v4 suite, the watchdog test and the root suite.
6. **Re-admission.** The admission binds stage receipts, and T1 has no completed stage, so state how the new admission relates to `attempt_01`. Keep the A_1302 pause record valid. Update the master commands, covering how the running v4 watchdog and controller pick up the new admission, in `CKPT_v4_implementation.md`.

## Binding limits

- No GPU allocation, generation or optimizer step.
- Do not start T1 or any gate.
- Do not change the v4 cron line until the master does it.
- Do not touch v3 runs beyond read-only inspection.
- The shared venv is read-only.
- $0.
- Kill only processes you started.
- No edits to the protocol, the amendments or the operational records.
- Commits use explicit pathspecs; rebase, then push to `main`.

## Deliverables

- Code and tests, with counts.
- The `attempt_01` classification.
- The new admission SHA-256.
- Exact master commands to resume the gate chain.
- One copy-ready sentence in `CKPT_v4_implementation.md`.

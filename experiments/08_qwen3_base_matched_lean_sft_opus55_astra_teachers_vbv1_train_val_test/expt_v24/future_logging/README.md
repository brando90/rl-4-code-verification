# Durable diagnostics for future scoring

Use **`parallel_scoring_logged.py --version N` for new scoring phases (N ≥ 25)**.
It is the prospective default entry, derived from the completed typed 32-worker
coordinator. Its `scorer_command()` always launches `logged_scorer.py`; there is
no unlogged worker option. It consumes the same frozen 1,080-cell `partition.json`
under `corpus_training_vN/scoring_parallel_v1/`, shares the existing global
32-process lock pool, retains completed positive and negative measurements, and
uses that version's frozen `summarize.py` after merging all eight samples.

The next experiment's CPU materialization handoff must point to this entry instead
of the historical `expt_v20/parallel_scoring_resume.py`. This directory is code for
future experiments; no new production experiment was started to test logging.
Completed V12/V20/V23 verifier files, source pins, caches and verdicts are unchanged.

## Evidence retained for every actual compiler command

Each cell's scoring output now contains:

```text
compiler_diagnostics/
  launcher.json
  call_<pid>_<unique>/
    execution.json
    stdout.log
    stderr.log
    source_0.lean             # actual compiler input snapshot
    setup_0.json              # when the kernel passes --setup
```

`execution.json` records the exact command/cwd, configured timeout, stage
(`initial_compile`, `kernel_compile`, `kernel_inspect`), start/end, returned exit
code or timeout/raised status, untruncated stream sizes and hashes, native
compiler path/version/SHA, resolved lake wrapper path/SHA, actual input-source
SHA/snapshot, evaluated agent-source path/SHA, and frozen verifier/CLI hashes.
No API keys or full environment variables are recorded.

Source snapshots, setup snapshots and both raw streams live outside the kernel
helper's temporary directory. They survive its normal cleanup. Stdout and stderr
exist while the compiler runs, so bytes already written also survive an owner or
whole-process-group stop. If the owner dies before finalization, its receipt stays
`RUNNING`, with unknown exit status; that is not fabricated as a compile failure or
timeout. A timeout is recorded as such without inventing a numeric compiler exit
code. Completed and timed-out streams are flushed/fsynced before final receipt
publication. Logs are not size capped.

## What changes, and what stays identical

The frozen initial compile, kernel probe and kernel check use their **original
function bytecode** in private logging namespaces. The original `subprocess.run`
still launches the same native command with the same arguments, cwd, timeout and
check policy. There is no extra compiler process wrapper, timeout manager,
acceptance fallback, theorem rewrite or changed axiom policy.

The explicit observability amendment is **PIPE → durable regular-file transport
for stdout/stderr**. The logger reconstructs the captured `CompletedProcess`
strings/bytes, universal newlines and `TimeoutExpired` partial-byte interface for
the unchanged verifier. The native process has the same configured deadline and
kill/wait behavior. Code that deliberately inspects whether stdout is a pipe could
observe this transport change; this is recorded rather than claimed to be a
bitwise runtime identity. Sudden host/storage loss cannot guarantee physical
durability of an in-flight write. A completed cache hit performs no compiler
command and therefore has no new per-command stream to record.

## Verified controls

Actual SNAP controls: `RUN/future_logging_v24_controls/final/controls.json`.

- Real valid and invalid Lean files: original and logged `CompileResult` fields
  match exactly, including diagnostic text.
- Real kernel check: theorem resolution, honesty/axiom policy, scores and stable
  report fields match; original function bytecode is unchanged.
- Kernel temporary source/inspector deletion: durable snapshots and both streams
  remain with matching hashes.
- Captured text with CRLF/CR normalization matches the original subprocess API.
- Timeout control retains both partial streams and matches the original timeout
  exception's public interface.
- Controlled owner/process-group SIGKILL retains written stdout/stderr, with
  `RUNNING` and unknown exit rather than a fabricated result.

Actual default-entry control:
`RUN/future_logging_v24_controls/entry/control.json`. It executes the exact
`scorer_command()` used by the new parallel coordinator against a separately
labelled tiny fixture, through the complete frozen CLI. Initial compilation,
kernel compilation and kernel inspection all pass and emit durable evidence.
This fixture is not a model output or benchmark measurement.

The coordinator's inherited deterministic partition, typed-cache and shared
32-slot refill controls pass. No model/provider calls were made. An initial
control exposed the redirected-file subprocess API returning the remaining
timeout instead of the requested timeout; the adapter now restores the caller's
requested timeout field, and the final parity/survival controls pass.

## Summary

First pull request for #66 (portable formal-verification CLI), Lean first. It adds the contracts and a no-prover path, and leaves the released Vero evidence unchanged.

- RFC 0008 defines three versioned, content-addressed interfaces: source driver, verifier driver, and prover runner. A candidate contract binds one of each.
- `anarres_formal_adapter` implements them. The Vero drivers delegate to the existing qualification code and do not rewrite released reports.
- A deterministic fixture driver and an external runner (`anarres-formal-fixture`) give the contracts something to run against without a prover or network.
- The Rust core gains a `probe-plan` adapter capability and `anarres probe --dry-run`. The plan is the ordered attempts for qualified, non-held-out tasks. Nothing executes in this pull request.
- The path `init`, `inspect`, `qualify`, `probe --dry-run` works outside the checkout and is covered by the installed-adapter smoke.
- `anarres formal contracts` prints the driver descriptors.
- A regression test re-hashes every entry of both pinned released manifests (110 entries) and checks that released evidence, pins, and frozen execution files have no diff from `d168e2a`.

Dafny, Verus, and Rocq drivers are not included. They are follow-ups behind the same interfaces.

How this was made: AI coding agents prepared it on my behalf (Codex CLI with GPT-6 Astra at ultra effort, and Claude Code with Opus 5.5). Three independent AI review passes (GPT-6 Astra at ultra effort in Codex CLI, then Claude Opus 5.5 in Claude Code, then GPT-6 Astra at ultra effort again) found three, then five, then two should-fix items. All are fixed in the last three commits, each with a test that fails on the previous code (shown by mutation in a disposable copy). The last commit fixes a CLI test that could run a stale binary under `CARGO_TARGET_DIR` and a hang on a named pipe (FIFO) given as a source artifact.

## Validation

- [x] `make check`: exit 0 on a fresh clone of head `402e26e` (346 Python integration tests, 14 + 32 Rust tests, ruff, clippy, hygiene, prose style).
- [x] Relevant integration tests: `test_formal_portable*.py` (32 tests) and `test_vero_released_manifest_regression.py` (3 tests), exit 0.
- [x] `make study-check`: 32 of 32 passed on the fresh clone.
- [x] `cargo fmt --all -- --check` and `git diff --check d168e2a..HEAD`: exit 0.
- [x] `make adapter-smoke`: exit 0 (fixture qualifies, 4 attempts planned, plan deterministic, held-out task absent).
- [x] Schema compatibility considered: no schema file changed.
- [x] No large artifacts, credentials, or machine-specific paths added.

`make benchmark` was run against a release build on a shared 128-CPU machine at load 110 to 140. It fails the same five timing guards on this branch and on unmodified `main` (3 of 3 alternating rounds each, with comparable values). I could not get a quiet machine, so this is not a pass. Please run it on a quiet one before merging.

## Scientific impact

None. No protocol, frozen artifact, metric, prospective boundary, or supported claim changes. Released Vero evidence is byte-identical.

## Artifacts and compatibility

- New artifact references: none. The fixture's bytes are synthetic literals in the package.
- No schema changes. One new adapter capability (`probe-plan`) and one new core flag (`probe --dry-run`) are additive. RFC 0008 explains why `--dry-run` is opt-in here and how it differs from RFC 0004's and the molecular adapter's `--execute`.
- RFC number: RFC 0007 belongs to the open robotics pull request (#83), so this uses 0008. Rename if that changes.
- Not run: no Lean build, no real Vero checkout, no prover model call, no Dafny, Verus, or Rocq. The Vero source and runtime qualification paths are unchanged and only routed.

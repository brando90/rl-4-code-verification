Findings 1 and 2 are fixed in commit `402e26e547839258c6bc241d319e9a402d4aa258` (`Fix formal artifact reads and CLI test executable selection`). This is exactly one new commit above `7dc4c97885e333c37fbad75ca94d99daeb8722dc`, on branch `pa` in the fresh clone `/lfs/skampere1/0/brando9/at3557/fixA`. The committed tree matches the tree validated below, and the working tree is clean.

Bundle: [prA-v4.bundle](/lfs/skampere1/0/brando9/at3557/prA-v4.bundle). SHA-256: `01a342c42fbeace8d438fd29551d32b8c8c74b5b416c13dafc2c6e28d556464c`. Size: 45847 bytes. The incremental bundle requires base `d168e2a33205bec9af766314d4f1f11839f28078`.

Implementation and mutation harness: Claude Code 2.1.318, Claude Opus 5.5 (`claude-opus-5-5`), effort `max`, Vals authentication. The run log reports that model for every assistant message. Codex (GPT-6) coordinated setup, final validation, delivery, and auxiliary read-only review. Its effort setting is not exposed in this session. These results are executable software checks. No new Lean-checked proof or differential-testing metric was produced.

[Claude run log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/claude-implementation-v2.jsonl) · [Claude result](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/claude-result.md) · [Complete targeted command and exit-code index](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/targeted-command-index.md)

**Changes per finding**

1. [test_formal_portable_cli.py](/lfs/skampere1/0/brando9/at3557/fixA/tests/integration/test_formal_portable_cli.py) now builds with `cargo build --quiet --message-format=json -p anarres-cli` and selects the executable from the `compiler-artifact` for the expected `anarres-cli` manifest, `anarres` target, and binary kind. The integration test runs that path. Its new regression uses real Cargo to build a minimal executable that exits 3 into a configured `CARGO_TARGET_DIR`, while a stale default executable exits 0. It verifies the selected path, preservation of the stale file, and the current executable's exit status.

2. [contracts.py](/lfs/skampere1/0/brando9/at3557/fixA/data/formal-verification/vero/src/anarres_formal_adapter/contracts.py) now requires `stat.S_ISREG(path.lstat().st_mode)` before returning a source-artifact path. The same metadata result supplies the hard-link check. Existing traversal and symlink checks remain in place. The guard covers both `fixture.json` and development source artifacts before their reads. [FIFO regressions](/lfs/skampere1/0/brando9/at3557/fixA/tests/integration/test_formal_portable_contracts.py) cover both locations through qualification and dry-run planning. Each child process has a 10-second timeout, and reaching it fails the test. A third regression forbids Python-level opens during classification. The guide and RFC describe regular-file rejection.

3. Finding 3 concerned an untracked author report. No change was made for it.

The new commit changes five files: the implementation, two test files, the formal portability guide, and RFC 0008. Scope remains Lean-first. No Dafny, Verus, or Rocq code was added. Released evidence, manifests, and frozen protocols were not changed.

**Mutation proof**

All mutations ran in disposable copies created with `mktemp -d` under `$TMPDIR` (`/tmp/user/22003`). Each copy began with all 1,611 tracked files from the fixed working tree. The table lists every new test. Exit 1 denotes the expected test failure after removing its fix. Restored runs exit 0.

| New test | Mutation and observed failure | Unfixed exit | Restored exit | Evidence |
| --- | --- | --- | --- | --- |
| `CargoExecutableSelectionTest.test_stale_default_executable_cannot_mask_a_broken_current_build` | Return the default target/debug path. The selected path is outside CARGO_TARGET_DIR. | 1 | 0 | [failure](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f1-03-mutation-a-default-path-expected-fail.log), [restored](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f1-08-regression-after-restore-expected-pass.log) |
| `PortableFormalContractsTest.test_fifo_development_artifact_is_rejected_without_blocking` | Restore contracts.py from 7dc4c97. Qualification and planning each time out and fail. | 1 | 0 | [failure](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-04-mutation-a-without-fix-expected-fail.log), [restored](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-18-tests-after-restore-expected-pass.log) |
| `PortableFormalContractsTest.test_fifo_fixture_json_is_rejected_without_blocking` | Restore contracts.py from 7dc4c97. Qualification and planning each time out and fail. | 1 | 0 | [failure](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-04-mutation-a-without-fix-expected-fail.log), [restored](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-18-tests-after-restore-expected-pass.log) |
| `PortableFormalContractsTest.test_contained_file_checks_fifo_metadata_without_opening` | Restore contracts.py from 7dc4c97. The expected ValueError is absent. | 1 | 0 | [failure](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-04-mutation-a-without-fix-expected-fail.log), [restored](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-18-tests-after-restore-expected-pass.log) |

The baseline and fixed targeted suites passed: 27 original contract tests and 1 original CLI test, then 30 contract tests and 2 CLI tests. The fixed CLI suite also passed with a fresh configured `CARGO_TARGET_DIR`.

Additional mutation checks:

- Restoring both the original Cargo command and the hard-coded executable also makes the new Cargo regression fail (exit 1). [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f1-06-mutation-b-original-logic-expected-fail.log)
- In a copy of the real repository, Rust main was changed to exit 3 while a working default executable was retained. With a separate `CARGO_TARGET_DIR`, the original CLI test falsely passed (exit 0). The built executable exited 3, and the fixed CLI test failed (exit 1). [Original test](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f1-12-e2e-original-test-with-target-dir-masks-broken-build-expected-pass.log), [built executable](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f1-13-e2e-current-build-is-broken-expected-exit-3.log), [fixed test](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f1-15-e2e-fixed-test-with-target-dir-detects-broken-build-expected-fail.log)
- Checking file type after a nonblocking open fails the no-open test (exit 1). Bypassing contained_file for fixture.json or development artifacts fails the corresponding timeout-bounded regression (exit 1 each). [Open-before-check](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-08-mutation-b-opening-check-expected-fail.log), [fixture.json bypass](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-11-mutation-c-unchecked-fixture-json-expected-fail.log), [artifact bypass](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-15-mutation-d-unchecked-artifact-expected-fail.log)

After each mutation, restoration was verified with `cmp` and SHA-256. Both completed copies matched all 1,611 tracked files and were then removed. The before/after fixA fingerprints matched. [Finding 1 restoration](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f1-17-copy-matches-fixA-after-restore.log), [finding 2 restoration](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/f2-19-copy-matches-fixA-after-restore.log), [fixA unchanged](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/fix12/logs/fixA-snapshot-compare.log). Timeout cleanup checks found no remaining fixture CLI children.

The mutation wrapper commands both exited 0:

```text
.fix3-logs/fix12/logrun.sh f1-mutation-script .fix3-logs/fix12/mutation-finding1.sh
.fix3-logs/fix12/logrun.sh f2-mutation-script .fix3-logs/fix12/mutation-finding2.sh
```

The linked command index preserves every targeted command, working directory via its log, and exit code. Exact executed scripts are saved as `mutation-finding1.executed.sh` and `mutation-finding2.executed.sh`. Their companion rerunnable scripts now explicitly name `7dc4c97` where the executed versions used HEAD, which was 7dc4c97 at execution time. That script-only pinning was not rerun. `.fix3-logs` is a locally ignored symlink to `.anarres/fix3-logs`.

**Final checks in requested order**

All commands ran in fixA on the final source tree before committing. No tracked file changed during them. The branch-range diff check was also repeated after committing, covering the new commit. The literal final output line is recorded below. For an empty log there is no final line.

| Order | Command | Exit | Literal final output line | Log |
| --- | --- | --- | --- | --- |
| 1 | `uv run python -m unittest discover -s tests/integration -p 'test_formal_portable*.py' -v` | 0 | `OK` | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/01-formal-portable.log) |
| 2 | `uv run python -m unittest discover -s tests/integration -p test_vero_released_manifest_regression.py -v` | 0 | `OK` | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/02-released-manifest.log) |
| 3 | `cargo test -p anarres-cli --locked` | 0 | Blank line. Last nonempty line reproduced below. | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/03-cargo-cli.log) |
| 4 | `make check` | 0 | `Prose style check passed` | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/04-make-check.log) |
| 5 | `make study-check` | 0 | `All 32 study checks passed in 147.98s.` | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/05-study-check.log) |
| 6 | `make adapter-smoke` | 0 | Full JSON line reproduced below. | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/06-adapter-smoke.log) |
| 7 | `cargo fmt --all -- --check` | 0 | (no output) | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/07-cargo-fmt.log) |
| 8 | `git diff --check d168e2a..HEAD` | 0 | (no output) | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/08-diff-check.log) |

The portable suite ran 32 tests, and the released-manifest regression ran 3. The CLI Rust checks passed 14 unit tests and 32 integration tests. `make check` passed 346 Python integration tests, the package suites, Rust tests, formatting, Clippy, schemas, hygiene, and prose checks. `make study-check` passed all 32 checks. Adapter smoke built 9 wheels and discovered 8 adapters. Its external formal fixture qualified and produced four deterministic planned attempts with the held-out task absent.

The last nonempty line of `cargo test -p anarres-cli --locked` was:

```text
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

The exact final line of `make adapter-smoke` was:

```json
{"adapters": ["finance", "formal", "formal-fixture", "legal", "materials", "molecular", "robotics", "vulnerability"], "contracts": {"finance": ["finance.business-bench-starting-policy-qualification.v1"], "formal": ["vero-codex-sol-repeated-measurement-v2:codeproof", "vero-codex-sol-repeated-measurement-v2:proof", "vero-leanstral-development-probe-v5:codeproof", "vero-leanstral-development-probe-v5:proof"], "formal-fixture": [], "legal": ["harvey-lab-workflow-intake-v1", "syllogym-stage-a-policy-response-v1"], "materials": ["materials.mlip-phonon-candidate-measurement.v2"], "molecular": ["q07820-starting-policy-endpoint-qualification-v2", "rxnflow-q07820-bank-v4"], "robotics": ["robotics.cupid-can-v141-candidate-measurement.v1"], "vulnerability": []}, "source_formats": {"finance": ["business-bench-process-v1"], "formal": ["vero-checkout-v1"], "formal-fixture": ["formal-fixture-v1"], "legal": ["harvey-lab-checkout-v1"], "materials": ["atomistic-candidate-bank-v1"], "molecular": ["rxnflow-molecular-environment-v1"], "robotics": ["robomimic-can-v141-hdf5"], "vulnerability": ["cybergym-sanitized-panel-v1"]}, "source_installed_adapters": ["finance", "formal", "formal-fixture", "legal", "materials", "molecular", "robotics", "vulnerability"], "statuses": {"finance": "reported", "formal": "ready_repeated_development_measurement", "legal": "reported", "materials": "reported", "molecular": "reported", "robotics": "reported", "vulnerability": "reported"}, "user_flow": {"compatible_panels": ["legal", "materials", "molecular", "robotics"], "formal_fixture_held_out_task_absent": true, "formal_fixture_native_source_qualified": true, "formal_fixture_plan_attempts": 4, "formal_fixture_plan_deterministic": true, "formal_incompatibility_rejected": true, "legal_native_source_qualified": true, "molecular_native_source_qualified": true, "profile_inputs": 33, "records": 33, "robotics_native_source_routed": true, "robotics_unpinned_source_rejected": true}, "wheels": 9}
```

[Structured final command results](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/final-checks.json) and [tracked-tree hash verification](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/final-tree-verification.json) preserve the exact results. A supplementary working-tree `git diff --check d168e2a` also exited 0 with no output.

Prerequisites and delivery commands:

| Command | Exit | Evidence |
| --- | --- | --- |
| `UV_CACHE_DIR=.uv-cache uv sync --all-packages --dev` | 0 | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/setup-uv.log) |
| `cargo build --release --locked -p anarres-cli` | 0 | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/setup-release.log) |
| `git commit -m "Fix formal artifact reads and CLI test executable selection"` | 0 | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/commit.log) |
| `git diff --check d168e2a..HEAD` | 0 | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/postcommit-diff-check.log) |
| `git bundle create /lfs/skampere1/0/brando9/at3557/prA-v4.bundle d168e2a..HEAD HEAD` | 0 | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/bundle-create.log) |
| `git bundle verify /lfs/skampere1/0/brando9/at3557/prA-v4.bundle` | 0 | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/bundle-verify.log) |
| `git bundle list-heads /lfs/skampere1/0/brando9/at3557/prA-v4.bundle` | 0 | [Log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/bundle-heads.log) |

The bundle advertises HEAD `402e26e547839258c6bc241d319e9a402d4aa258` and passed `git bundle verify`. No amend, push, or external post was performed.

A separate byte comparison confirmed both released manifests and all 110 listed evidence entries equal `d168e2a` (exit 0). [Audit log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/released-byte-audit.log), [manifest hashes](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/released-byte-audit.json). Its initial ad hoc attempt passed an unnormalized `./` path to `git show` and failed with git exit 128. The saved audit normalizes paths through pathlib and passed.

**Resolved setup failures and limits**

The installed Vals launcher initially selected Claude Code 2.1.270. Opus 5.5 rejected it as too old (launcher exit 1). The successful job used installed Claude Code 2.1.318 with the same Vals authentication and a fresh configuration directory within fixA (exit 0). [Initial error run log](/lfs/skampere1/0/brando9/at3557/fixA/.anarres/fix3-logs/claude-implementation.jsonl). A preliminary hygiene check exited 1 because transient logs were initially under `.fix3-logs`. Moving them under excluded `.anarres` resolved this. The final `make check` hygiene check passed for 1,611 files.

No new native Vero checkout qualification, Lean/Lake compilation, real prover execution, differential-testing evaluation, or downstream training was run. FIFO rejection was tested through the fixture adapter's qualification and planning commands. The native CLI was exercised separately by the portable flow and installed-adapter smoke. Windows and concurrent filesystem replacement were not tested. The metadata check precedes the read and does not establish atomic protection against a concurrent replacement. Other integration suites were checked in the default Cargo configuration. `make benchmark` was not run, as requested.

TLDR-end: [Anarres: review fixes 1 and 2] Both findings are fixed, every new regression failed under its corresponding mutation, and all eight requested final checks passed. One new commit and the verified bundle are ready.

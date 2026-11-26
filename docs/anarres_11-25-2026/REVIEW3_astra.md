SHIP WITH FIXES

## Findings

### 1. should-fix: the CLI regression can still pass against a stale executable

**File and line:** [tests/integration/test_formal_portable_cli.py:15](/lfs/skampere1/0/brando9/at3557/review-clone3/tests/integration/test_formal_portable_cli.py:15), with the build at line 25.

The test always invokes Cargo after `7dc4c97`, but Cargo honors `CARGO_TARGET_DIR` while `BINARY` always names `ROOT/target/debug/anarres`. A configured target directory therefore builds one executable and tests another. This defeats the stated purpose of the last commit's always-build change and can conceal a real Rust regression.

**Evidence:** In a throwaway copy, retain the correct default executable, change `probe_plan_ready: source_valid && can_plan_probe` to `probe_plan_ready: false`, and set `CARGO_TARGET_DIR` to a separate directory. Run:

```text
CARGO_TARGET_DIR=<alternate-target> <python> -m unittest test_formal_portable_cli.FormalPortableCliTest.test_outside_checkout_init_inspect_qualify_dry_run -v
Ran 1 test
OK
EXIT=0
```

The same test, with only its `BINARY` pointed at the newly built alternate executable, reports:

```text
File ".../test_formal_portable_cli.py", line 93
    self.assertTrue(inspection["probe_plan_ready"])
AssertionError: False is not true
FAILED (failures=1)
EXIT=1
```

Reproduction script: [check_build_target.py](/tmp/user/22003/anarres-review-mutations-byy9hcoa/check_build_target.py). Exact commands, outputs, and mutation: [stale executable passes](/tmp/user/22003/anarres-review-mutations-byy9hcoa/build-target-stale-pass.log), [new executable fails](/tmp/user/22003/anarres-review-mutations-byy9hcoa/build-target-new-binary-fails.log), [patch](/tmp/user/22003/anarres-review-mutations-byy9hcoa/build-target-mutation.patch). The source was restored afterward.

**Suggested fix:** Execute the path Cargo reports through `--message-format=json`, or explicitly pass a target directory matching `BINARY`. Add a regression using a configured target directory and a stale default executable.

### 2. should-fix: a nonregular source artifact hangs qualification and planning

**File and line:** [contracts.py:90](/lfs/skampere1/0/brando9/at3557/review-clone3/data/formal-verification/vero/src/anarres_formal_adapter/contracts.py:90), consumed by [fixture.py:222](/lfs/skampere1/0/brando9/at3557/review-clone3/data/formal-verification/vero/src/anarres_formal_adapter/fixture.py:222).

`contained_file()` rejects traversal and links but does not require a regular file. A FIFO at the otherwise valid `development/a.txt` path has link count one and passes these checks. The subsequent `read_bytes()` blocks waiting for a writer, before the digest or size can be checked. Both qualification and dry-run planning use this path and have no timeout for the read. The same helper reads `fixture.json`.

**Evidence:** `python3 /tmp/anarres-review-root-VOcood/formal_fifo_repro.py` generates a normal fixture, replaces only its development task with a FIFO, and bounds the child process with a two-second timeout:

```text
FIFO stat: st_nlink=1; is_file=False
qualification timed out after 2 seconds: blocked opening development/a.txt FIFO
```

[Reproduction script](/tmp/anarres-review-root-VOcood/formal_fifo_repro.py) and [output](/tmp/anarres-review-root-VOcood/fifo.log). No repository input was changed.

**Suggested fix:** Require `stat.S_ISREG()` before reading source artifacts. Add a FIFO regression that requires prompt rejection, with a subprocess timeout to prevent the regression itself hanging.

### 3. nit: the author report transcribes the canonical byte vector incorrectly

**File and line:** [RESULT_FIX2.md:47](/lfs/skampere1/0/brando9/at3557/review-clone3/RESULT_FIX2.md:47), an untracked author report.

S4 calls `{"count":3,"name":"é","ratio":0.1}` the pinned bytes. The actual RFC and test correctly pin the ASCII-escaped `{"count":3,"name":"\u00e9","ratio":0.1}`. These byte strings have different digests; the implementation and committed documentation are correct.

**Evidence:** Ruby's independent JSON implementation, using `JSON.generate(value.sort.to_h, ascii_only: true)`, produces the escaped bytes and digest `cb4388342572d2ff789acd0763d43b173b05ba7d2a402e1850adaa737d39fa25`. With `ascii_only: false`, the displayed UTF-8 bytes produce `ff410e4483dc3e8c07d0f906093297dcf930bb366ad2142808a88ca2291052d0`. [Output](/tmp/anarres-review-root-VOcood/author-vector-check.log).

**Suggested fix:** Correct the byte literal in the untracked report. No code or RFC change is needed.

## Checked and fine

### Review basis and first-PR scope

Reviewed all 2,957 lines of `git diff d168e2a..HEAD` before defect investigation, including the RFC, guide, Python implementation, Rust changes, tests, and installation smoke script. Read `git show 7dc4c97`, `AGENTS.md`, `CONTRIBUTING.md`, `ISSUE66.md`, RFCs 0003/0004/0006, and the writing standard. The branch has exactly the five specified commits and HEAD is `7dc4c97885e333c37fbad75ca94d99daeb8722dc`. The three author result files were read after the independent checks, and their claims were compared with those checks.

The five “First pull request” items are implemented, subject to the findings above:

| Requirement | Verified implementation |
| --- | --- |
| Study-independent interfaces | Separate source-driver, verifier-driver, and prover-runner protocols, versioned descriptor schemas, raw implementation-file hashes, and canonical content identities |
| Tiny deterministic fixture | Synthetic source, literal verifier, external stdin/stdout runner, deterministic request ordering and artifact identity |
| Vero routing | CLI source qualification and runtime preflight delegate through Vero wrappers; existing source/runtime modules are unchanged |
| Outside-checkout path | Native fixture creation followed by `init -> inspect -> qualify -> probe --dry-run`, including isolated installed wheels with `PYTHONPATH` removed |
| Released evidence | Both pinned manifests, all 110 entries, and frozen execution identities match the base and their recorded hashes |

This is a software review using the GPT-6 Codex harness and collaboration agents, with executable Python/Rust checks. It is not a new Lean-checked result or model measurement.

### Required commands in this clone

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run python -m unittest discover -s tests/integration -p 'test_formal_portable*.py' -v` | Exit 0; 28 tests, OK | [Log](/tmp/anarres-review-root-VOcood/formal-portable.log) |
| `uv run python -m unittest discover -s tests/integration -p 'test_vero_released_manifest_regression.py' -v` | Exit 0; 3 tests, OK | [Log](/tmp/anarres-review-root-VOcood/released-manifest.log) |
| `cargo test -p anarres-cli --locked` | Exit 0; 14 unit and 32 integration tests passed | [Log](/tmp/anarres-review-root-VOcood/cargo-cli.log) |

Additional checks ran in a disposable clone to protect the reviewed branch:

- `make check` passed, including 342 Python integration tests, package tests, Rust tests, formatting, Clippy, schemas, hygiene, and prose checks. [Log](/tmp/anarres-review-rust-frozen-check.log).
- `make study-check` passed all 32 checks after `uv sync --all-packages --dev`. The first attempt failed because adapter commands were not installed; that environment failure is preserved in its log. The successful run left the disposable clone clean. [Initial log](/tmp/anarres-review-rust-frozen-study-check.log), [successful log](/tmp/anarres-review-rust-frozen-study-check-rerun.log).
- Release build and installed-adapter smoke passed: nine wheels, eight discovered adapters, a qualified external fixture, four ordered attempts, byte-identical plans, and no held-out task file. [Smoke log](/tmp/anarres-review-rust-frozen-smoke.log).
- `git diff --check d168e2a..HEAD` passed.

### Mutation verification

All implementation mutations were confined to a separate archive copy. Seventeen mutations caused failures in nine distinct new test methods. This includes every test method added or changed by `7dc4c97`; separate mutations exercised the different additions inside its single CLI test.

| Test method | Behavior deliberately broken | Observed result |
| --- | --- | --- |
| `test_canonical_json_matches_the_fixed_rfc_test_vector` | Disable ASCII escaping; separately allow nonfinite numbers | Both mutations fail |
| `test_failure_outcomes_do_not_become_strict_proof_failure` | Classify bare newline as proof failure; separately classify infrastructure failure as proof failure | Both fail |
| `test_fixture_requires_typed_assumption_lists_and_lineage_strings` | Restore truthiness-only assumption checks; remove source lineage type checks; remove group lineage checks | All three fail |
| `test_fixture_rejects_resealed_task_digest_with_valid_bytes_and_size` | Remove only the digest comparison, preserving size and syntax checks | Fails with `ValueError not raised` |
| `test_plan_never_opens_held_out_tasks_or_calls_network_processes_or_runner` | Read a held-out task; open a socket; invoke the runner | All three fail at the corresponding guard |
| `test_verifier_identity_changes_with_its_advertised_command_implementation` | Omit `fixture_cli.py` from the verifier identity | Fails |
| `test_fixture_rejects_hard_link_to_held_out_payload_before_reading` | Remove the hardlink guard | Fails on attempted alias read |
| `test_fixture_qualification_and_plan_are_deterministic_across_directories` | Sort seeds instead of preserving supplied order | Fails on attempt order |
| `test_outside_checkout_init_inspect_qualify_dry_run` | Restore the old readable printer; emit a bad descriptor seal; remove the external-manifest overwrite guard | All three fail |

The configured-Cargo-target experiment in finding 1 is an additional mutation that survives the current test, then fails when the correct executable is selected. It is not counted among the seventeen successful detections.

The copied portable suite passed all 28 tests before and after restoration. Hash comparison against HEAD verified restoration of all 1,611 tracked files. [Runnable mutation matrix](/tmp/user/22003/anarres-review-mutations-byy9hcoa/run_mutations.py), [test names, exit codes, and individual log paths](/tmp/user/22003/anarres-review-mutations-byy9hcoa/summary.json), [restoration record](/tmp/user/22003/anarres-review-mutations-byy9hcoa/restoration.json).

### Contracts, safety boundaries, and the last commit

Checked every sentence of RFC 0008's “Native contracts and evidence boundaries” section against `vero_drivers.py`, `fixture.py`, `contracts.py`, and the released source pin:

- The four endpoints remain distinct, and endpoint is defined separately from the downstream target. Specification construction is not presented as specification faithfulness.
- Fixture source metadata records language, toolchain, repository, task set, license, endpoint, task references, partitions, dependency/context/reference fields, and all six grouping keys. Its trusted-axiom and unsafe-feature lists are empty, with admitted proofs forbidden. The verifier records the corresponding policies, toolchain, command, outcomes, and exact-byte success rule.
- Vero's source descriptor includes the complete pin, Lean toolchain string, endpoint/native-mode mapping, and the expected count of 81 trusted axioms. Its verifier descriptor has free-text trusted assumptions and no toolchain field. Its implementation identity includes `source-pin.json`. Structured admitted-proof/unsafe-feature records, a new axiom audit, and leakage checks are correctly described as absent.
- Artifact metadata and raw-byte digests match the implementation. Static traversal, direct and parent symlinks, and hardlink aliases are rejected before task reads. The nonregular-file omission is finding 2.
- Source qualification, runtime qualification, task containment, policy support, measurement readiness, and downstream evidence remain separate. Fixture planning advances only its declared qualification steps; it does not issue a containment receipt or enable execution.

Also verified:

- `anarres formal contracts --json` produces repeatable sealed descriptors, and its readable printer works. Mutations detect bad seals and the prior readable formatting.
- `--dry-run` is a core planning option requiring `probe-plan`; copies after `--` are rejected. The fixture lacks `policy-probe`; Vero lacks both `probe-plan` and `policy-probe`. The docs distinguish this from molecular's existing adapter-owned `--execute` convention. The new formal paths do not enable real policy execution.
- Actual `anarres probe --help` matches the revised capability and argument-forwarding descriptions.
- The canonical JSON specification matches the Python implementation, including ASCII escapes, compact sorted keys, and rejection of nonfinite numbers. Ruby independently reproduced the RFC vector and SHA-256; this did not call the Python serializer or its test helper. [Ruby result](/tmp/anarres-review-root-VOcood/rfc-vector-ruby.log).
- Bare newline and empty proof output are parser failures. Only literal `false\n` is strict proof failure. Infrastructure, parser, build, verifier, timeout, and unsupported outcomes retain separate labels and do not acquire proof-failure flags or a reward field. Fixture model tokens are zero and wall time is unmeasured.
- The new typed assumption/lineage checks and external-manifest overwrite guard work and are mutation-sensitive. The last commit's always-build change has the residual defect in finding 1.
- The earlier `a260f64` fixes remain effective: the verifier identity includes its CLI implementation, qualification agrees with the runner's development artifact requirements, every planned fixture attempt is accepted, and the digest-only regression fails when the digest comparison is removed.
- RFC/guide/README terminology and evidence limits conform to the writing standard in the reviewed additions. I found no additional substantive overclaim in the committed native-contract prose. Finding 3 concerns only the author's untracked report.

### Released evidence and Rust compatibility

Recomputed the two manifest hashes from base bytes:

```text
repeated-measurement.codex-sol-v2:
c143f2918434cf85fb61785f6e1dbe26b5cfed1d587f194e3611d9a4068e5a6f
public-evidence:
89d404d5fb0435d37bd2d413213f82b9b50d47ef9310965ffbfb7da60e3c07be
```

Verified raw bytes and hashes of every entry (98 + 12), all eleven unique protocol/receipt-pinned execution files, both source-pin copies, legacy qualification modules, the frozen protocol, and the task-boundary receipt against `d168e2a`. No frozen or hash-pinned released Vero file changed. The manifest tests also reject evidence-only changes and coordinated evidence/manifest rewriting. [Audit script](/tmp/anarres-review-frozen-audit.py), [audit output](/tmp/anarres-review-frozen-audit.log).

Compared base and HEAD executables using the same fake adapter: direct invocation, qualification, and ordinary probe preserve literal arguments, stdout, stderr, and exit status 23. All preexisting inspection fields agree; the new planning fields are false for the existing adapter. Existing Rust tests also pass. The deliberate reservation of `--dry-run` is documented by RFC 0008. [Comparison script](/tmp/anarres-review-rust-compare.py), [output](/tmp/anarres-review-rust-compare.log).

### Lean-first scope

Only Vero (Lean) supplies real proof-assistant drivers; the fixture uses literal bytes and no proof assistant. No Dafny, Verus, or Rocq driver code was added.

The additions mentioning those languages are explicit future-work statements:

- RFC 0008 line 20: their drivers remain follow-ups.
- RFC 0008 lines 274–276: they need their own source, verifier, assumptions, grouping, and conformance checks.
- Formal portability guide lines 126–128: those drivers are follow-up work.

The released Vero pin's existing source-language counts describe upstream provenance; they do not implement those verifiers.

## Not checked

- No fresh native Vero checkout qualification, real Lean/Lake build, prover model call, task-containment qualification, or downstream training/evaluation was run. Vero routing was checked through unchanged implementations, software tests, released-record reproduction, and byte comparisons.
- No general driver discovery or real external-policy execution was validated; these remain explicitly deferred.
- Static path protections were tested. Atomic protection against concurrent filesystem replacement was not established; the guide explicitly acknowledges checking paths before opening them. This review does not treat the fixture as a filesystem sandbox.
- Windows behavior was not exercised; the new CLI integration test is POSIX-only.
- A passing performance gate was **not** established. `make benchmark` ran and failed timing thresholds: adapter-list p95 255.65 ms versus 50 ms, and finance medians about 217–249 ms versus 200 ms. An additional interleaved 20-sample comparison also failed these thresholds on the base: adapter-list p95 83.664 ms base / 86.298 ms HEAD, finance-status median 234.795 ms / 238.467 ms. This does not establish an attributable branch regression or performance equivalence. [Full failed benchmark](/tmp/anarres-review-rust-frozen-benchmark.log), [base/HEAD comparison](/tmp/anarres-review-rust-compare.log).
- Historical author log claims were not taken as proof of past execution. The results above are this review's own runs; the reported historical durations were not independently reconstructed.

No tracked file in the reviewed clone was modified. The only new nonignored review artifact there is this uncommitted `REVIEW.md`; test and build caches are ignored. No push, post, PR, or external publication was made.

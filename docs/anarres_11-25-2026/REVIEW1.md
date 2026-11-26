SHIP WITH FIXES

## Findings

### 1. should-fix: The verifier identity omits the implementation of its advertised command

**File and line:** `data/formal-verification/vero/src/anarres_formal_adapter/fixture.py:239`; advertised command at line 248; command implementation in `fixture_cli.py:62`.

`FixtureVerifierDriver.descriptor()` advertises `anarres-formal-fixture verify-fixture`, but hashes only `fixture.py` and `contracts.py`. Changing verification in `fixture_cli.py` changes that native command's outcomes without changing the descriptor or its content identity. This contradicts RFC 0008's implementation-identity claim at `docs/rfcs/0008-portable-formal-verification-contracts.md:43` and leaves an implementation of the advertised verifier outside its identity boundary. The runner's in-process verifier is covered; the advertised command is not fully covered.

**Evidence:** The following reproducer copies the package to a temporary directory and changes only the copied CLI verification branch to return `parser-failure`:

```text
python3 /tmp/anarres-review-native-verifier-identity.py

before native command true: {'exit': 0, 'output': {'outcome': 'strict-success'}}
before native command false: {'exit': 0, 'output': {'outcome': 'strict-proof-failure'}}
after native command true: {'exit': 0, 'output': {'outcome': 'parser-failure'}}
after native command false: {'exit': 0, 'output': {'outcome': 'parser-failure'}}
descriptor identity before: sha256:2463f859177fe1e593ef64a59fd982d1cccffbcb09b48232388d3228bdb275b3
descriptor identity after:  sha256:2463f859177fe1e593ef64a59fd982d1cccffbcb09b48232388d3228bdb275b3
descriptor unchanged: True
implementation keys: ['fixture.py', 'anarres_formal_adapter/contracts.py']
```

**Suggested fix:** Include `fixture_cli.py` in the verifier's implementation files, or advertise only an entrypoint whose implementation is already bound. Add a regression that changes the advertised command's implementation in a copy and requires the verifier identity to change. The existing descriptor test verifies the hashes of listed files, so it cannot detect an omitted implementation file.

### 2. should-fix: Qualification and planning accept fixture requests that the named runner rejects

**File and line:** `data/formal-verification/vero/src/anarres_formal_adapter/fixture.py:173` and line 178 permit artifact metadata that the runner rejects at line 306. Planning copies that metadata into requests at line 347.

Qualification accepts a canonical renamed development file, an alternate nonempty producing-run identity, or a consistent alternate source/artifact license. These sources retain the exact supported task bytes and valid source seals. Planning reports qualification and emits attempts, but `FixtureRunner.run()` compares the complete artifact against `artifact("development/{task_id}.txt", TASK_BYTES, "fixture-generator-v1")`, which also hard-codes Apache-2.0. Thus the source driver, planner, and runner disagree about supported native inputs. This is a deterministic fixture conformance problem, even though actual policy execution remains disabled.

**Evidence:** The reproducer creates independent temporary fixtures, changes one metadata property at a time, reseals each source, qualifies it, plans it, and passes its first request directly to the named fixture runner:

```text
uv run python /tmp/review_formal_fixture_inconsistent.py

renamed-artifact: qualification=qualified, planned_attempts=2
  runner=ValueError: runner only supports the literal fixture task
different-producing-run: qualification=qualified, planned_attempts=2
  runner=ValueError: runner only supports the literal fixture task
different-license: qualification=qualified, planned_attempts=2
  runner=ValueError: runner only supports the literal fixture task
```

**Suggested fix:** Make qualification reject metadata outside the fixture runner's supported contract, or make the runner consistently honor the qualified metadata while checking the literal task semantics and artifact bytes. Test successful runner consumption of every accepted fixture variant, and reject unsupported variants before emitting a plan.

### 3. should-fix: The task-tampering regression does not protect task-digest verification

**File and line:** `tests/integration/test_formal_portable_contracts.py:78`, testing the combined digest/size condition in `data/formal-verification/vero/src/anarres_formal_adapter/fixture.py:206`.

The test replaces the task with shorter bytes, so the size check alone produces the expected `artifact identity mismatch`. Removing only `digest(payload) != item["sha256"] or` leaves all 21 contract tests passing. This is a coverage defect, not a claim that the current implementation skips digest verification. Under the mutant, qualification accepts a resealed source with an incorrect task digest and unchanged valid task bytes.

**Evidence:** Mutation occurred only in a `git archive HEAD` copy; the script restores the original implementation in `finally`:

```text
python3 /tmp/user/22003/anarres-pr1-mutations-un2xvcfi/survivor-reproduce.py

Full contracts suite with skipped task digest: 0
ACCEPTED: artifact sha256 is all zeroes, actual bytes are sha256:edc5153e01d87e2094126ea0fd06ed5109f97857a0065b53c96bf931d0417b36
REJECTED: task artifact identity mismatch
```

The mutated suite reports `Ran 21 tests` and `OK`; the final rejection above is from the restored implementation.

**Suggested fix:** Add a case that preserves the valid task bytes and size, substitutes another valid-format SHA-256 value in the task artifact, reseals the source, updates its revision, and requires qualification to reject it. This isolates digest verification from size and syntax checks.

## Checked and fine

### Review scope and requirements

- Reviewed `formal-portable-contracts-pr1` at `5ec9cb1711eaead9d05cc8f109654a1c1b66c6d7`, the three commits after `d168e2a`. Read the entire 2,605-line diff, including every changed Python/Rust file, test, document, and installation-smoke change, before the defect investigation.
- Read `ISSUE66.md`, root `AGENTS.md`, `CONTRIBUTING.md`, the writing standard, RFC 0003, both files numbered RFC 0004, RFC 0006, and RFC 0008. Assessed the five **First pull request** requirements, without treating the issue's later real-execution, decision, or independent-source requirements as mandatory for this PR.
- The source/verifier/runner interfaces, fixture, Vero delegation, outside-checkout path, and released-evidence preservation are present. Findings 1 and 2 limit the completion claims for the interface and fixture requirements.
- Read `RESULT_PR1.md` only after the independent source review, required tests, mutation investigation, scope audit, and writing review. Its test and released-evidence claims agree with the independent checks below. Its broad “Done” claims need the qualifications in Findings 1–3. I did not treat its historical logs or timings as independently verified facts.
- Review used Codex CLI (GPT-6 Astra, ultra effort), source reading, executed CPU Python/Rust tests, and disposable-copy mutation checks. No Lean proof or build, real prover-model execution, or downstream experiment ran.

### Executed checks

These commands ran in the requested clone:

| Command | Observed result |
| --- | --- |
| `uv run python -m unittest discover -s tests/integration -p 'test_formal_portable*.py' -v` | Exit 0; 22 tests, `OK` |
| `uv run python -m unittest discover -s tests/integration -p 'test_vero_released_manifest_regression.py' -v` | Exit 0; 3 tests, `OK` |
| `cargo test -p anarres-cli --locked` | Exit 0; 14 unit tests and 32 integration tests passed; zero doc tests |
| `make check` | Exit 0; package tests, 336 integration tests, Rust formatting/Clippy/tests, schemas, hygiene, and prose passed |
| `cargo build --release --locked -p anarres-cli` | Exit 0 |
| `uv run python tools/smoke_adapter_installation.py --binary target/release/anarres` | Exit 0; 9 wheels, 8 discovered adapters, fixture qualification, 4 planned attempts, deterministic plans, held-out task absent |
| `cargo fmt --all -- --check` | Exit 0; no output |
| `git diff --check d168e2a..HEAD` | Exit 0; no output |

`make study-check` ran in a separate local clone at the same HEAD, `/tmp/anarres-pr1-review-study`, after `uv sync --all-packages --dev --locked`. All 32 checks passed in 129.32 seconds; that copy's final `git status --short` was empty. This kept reproducer writes away from the reviewed branch. Review logs are in `/tmp/anarres-pr1-review-logs/`.

### Mutation checks

Eight distinct new tests failed under implementation mutations and passed after restoration. The complete contract suite passed before and after the mutations. Each failure below was an assertion failure, not an import or syntax failure. Exact edits, commands, and outputs are in `/tmp/user/22003/anarres-pr1-mutations-un2xvcfi/summary.json` and the corresponding `*-mutated.log`/`*-restored.log` files; `reproduce.py` repeats the experiment in a new archive copy.

All test names below belong to `test_formal_portable_contracts.PortableFormalContractsTest`.

| Test | Mutation | Observed assertion failure |
| --- | --- | --- |
| `test_fixture_qualification_and_plan_are_deterministic_across_directories` | Reverse task sorting | Actual task order starts with `b`; expected order starts with `a` |
| `test_fixture_rejects_source_and_task_byte_tampering` | Disable both artifact digest and size validation | Expected `artifact identity mismatch`; received `unsupported fixture task syntax` |
| `test_fixture_rejects_hard_link_to_held_out_payload_before_reading` | Remove hardlink rejection | `qualification opened a task alias before rejecting it` |
| `test_plan_never_opens_held_out_tasks_or_calls_network_processes_or_runner` | Invoke the runner during planning | `runner call` |
| `test_failure_outcomes_do_not_become_strict_proof_failure` | Label every unsuccessful outcome proof failure | Six `True != False` failures |
| `test_candidate_contract_rejects_each_incompatible_identity` | Ignore toolchain mismatch | `ValueError not raised` |
| `test_driver_descriptors_are_separately_versioned_and_bind_implementation_bytes` | Hash fixed wrong bytes | Actual and expected implementation digests differ |
| `test_vero_drivers_delegate_without_rewriting_released_reports` | Declare Vero `policy_probe=True` | `True is not false` |

The additional digest-only mutation survived, as reported in Finding 3. Separately, mutating a released artifact in each release made the actual byte-identity regression fail with `released file changed`. Updating its manifest entry too still failed with `released manifest changed`. Restoring both releases restored all three regression tests. Evidence and a repeatable script are in `released-*-mutated.log`, `released-restored.log`, and `release-reproduce.py` in the same audit directory.

### Source boundaries, identities, and released evidence

- Source checks reject absolute/noncanonical paths, parent traversal, file and parent-directory symlinks, and hardlinks before task reads. The hardlink test's read guard was demonstrated to fail when the guard implementation was removed. Output protection rejects source overwrite and hardlinked output aliases, including with `--force`.
- Qualification skips held-out tasks before `stat`, `resolve`, or reads. The guarded planning test covers held-out path access, socket creation, subprocess execution, and runner invocation. Source inspection and planning keep qualification, runtime, containment, policy support, measurement readiness, and downstream evidence separate.
- Current fixture task, proof, and listed implementation hashes use raw bytes. Canonical seals exclude only `content_id`, sort keys, and reject non-finite numbers. Plans are independent of temporary directory names and order development tasks by task ID, then seeds in supplied order. The installed smoke reproduces identical plan bytes outside the checkout with `PYTHONPATH` removed.
- All eight attempt outcomes remain distinct. Infrastructure failure, parser/build/verifier failures, unsupported execution, and timeout do not set `proof_failure`; only `strict-proof-failure` does. The mutation check confirms that collapsing these outcomes causes test failures. No reward field is generated.
- Vero source/runtime wrappers delegate to the existing implementations without rewriting report payloads. Existing source/runtime integration tests pass. The `formal` descriptor still accepts only `vero-checkout-v1` and declares no `policy-probe`; the fixture declares only `probe-plan` and `source-qualification`.
- Independently compared manifest hashes with `git show d168e2a:<path>` and checked every listed file against its raw SHA-256 and base bytes: 98 repeated-measurement entries and 12 public-evidence entries. The two manifest digests are `c143f2918434cf85fb61785f6e1dbe26b5cfed1d587f194e3611d9a4068e5a6f` and `89d404d5fb0435d37bd2d413213f82b9b50d47ef9310965ffbfb7da60e3c07be`.
- Also checked all 11 unique execution files named by the repeated-measurement protocol and task-boundary receipt against their pinned hashes and base bytes, including the probe, queue runner, aggregators, validators, sandbox server, containment runner, materializer, and Lean axiom checker. No released protocol, manifest, evidence artifact, or pinned execution file changed. Command: `python3 /tmp/anarres-pr1-review-logs/audit_released_bytes.py`; output is in `released-bytes-audit.log`.

### Rust, Lean-first scope, and writing

- RFC 0003 discovery, the protocol handshake, and `adapter::run` exit-code handling are unchanged. Normal probe dispatch retains its existing execution capability gate. The new planning gate is separate. Forwarding `--dry-run` or `--dry-run=...` after `--` is intentionally rejected and documented in RFC 0008; planning capability does not authorize policy execution. Existing adapter CLI tests pass.
- RFC 0004's planning boundary and RFC 0006's manifest ownership remain intact. The source envelope is unchanged; new inspection fields and `probe-plan` checks are additive. General installed-driver discovery remains explicitly deferred.
- The only concrete real-language drivers are `VeroSourceDriver` and `VeroVerifierDriver` for Lean. The other implementations are `FixtureSourceDriver`, `FixtureVerifierDriver`, and `FixtureRunner`. I found no added Dafny, Verus, or Rocq driver or claim of one. All added mentions explicitly defer them: RFC 0008 lines 22 and 218, and the tutorial line 122.
- `proof-only`, `code-and-proof`, `specification-construction`, and `specification-faithfulness` remain distinct. Vero's `proof`/`codeproof` mapping is explicit. The documentation distinguishes verifier acceptance from specification faithfulness and synthetic fixture checks from scientific source-selection evidence. Repository/generation-family lineage remains visible, and task counts are not represented as independent environments.
- Reviewed the added RFC, tutorial, and README prose against `docs/standards/writing.md`; automated prose checks pass. The substantive overstatement about implementation identity is Finding 1. I found no additional endpoint conflation or inflated scientific result claim in the added prose.

## Not checked

- No fresh upstream Vero checkout qualification, actual Lean/Lake build, native grader execution, Docker task-containment requalification, real external prover, model/provider call, policy measurement, prospective outcome access, or downstream training. Passing fixture and wrapper tests does not establish those results.
- No Dafny, Verus, or Rocq runtime checks, general third-party driver discovery, or later measurement/decision/freeze acceptance. Those are outside this first PR and remain deferred.
- Performance benchmark result and attribution: pending final benchmark collection. The initial `make benchmark` attempt stopped because the review environment lacked `anarres-finance`; dependencies were then installed with `uv sync --all-packages --dev --locked` and the release benchmark was rerun. No base-revision benchmark comparison has been performed.
- The author's original historical validation runs were not independently reconstructed. Their claims were compared against current code and independently rerun checks instead.

No tracked file on the reviewed branch was edited. Mutations were confined to disposable copies. `REVIEW.md` is intentionally untracked; nothing was committed, pushed, posted, or opened externally.

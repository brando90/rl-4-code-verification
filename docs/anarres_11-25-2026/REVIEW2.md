# Review of `formal-portable-contracts-pr1` (issue #66, first pull request)

Date: 11-25-2026. As of 11-25-2026.
Scope: `d168e2a..a260f64`, four commits, 17 files, +2380/−24.

**Verdict: SHIP WITH FIXES**

I found no blocking defect. All five "First pull request" items from issue #66
are implemented, and none of the Vero files changed by this branch are frozen or
hash-pinned. The adapter still does not declare `policy-probe`. The required test
suites pass, and every one of the 20 mutations I ran made its target test fail.
The three fixes in `a260f64` work, and I found no new defect introduced by them.
The should-fix items below are claims in the RFC that the code does not yet back,
a new subcommand with no test, and one design point: the new `--dry-run` reverses
the explicit-execution convention that RFC 0004 and the molecular adapter use.

## Findings

### S1 (should-fix): RFC 0008 says more about verifier and source contracts than the Vero driver records

- Files: `docs/rfcs/0008-portable-formal-verification-contracts.md:67-69` and `:77-79`;
  `data/formal-verification/vero/src/anarres_formal_adapter/vero_drivers.py:40-53`
- What is wrong: The RFC says "A verifier contract binds its native command, toolchain,
  allowed assumptions, and strict success semantics" and "Source metadata records ...
  admitted-proof policy, and leakage checks". The Vero verifier descriptor has no
  `toolchain` key. It has no admitted-proof or unsafe-declaration fields. Its
  `trusted_assumptions` is free text ("source manifests; no new axiom audit in
  preflight"), even though the source pin lists 81 trusted axioms. Neither driver
  records leakage checks. No field named `leak*` exists in any driver. The Lean
  version is bound only indirectly, through the hash of `source-pin.json` in
  `implementation`. Issue #66 asks the contract to "record trusted axioms, admitted
  proofs, unsafe declarations, verifier versions, and allowed assumptions".
- Evidence: `anarres formal contracts --json` (run through a wrapper on `PATH`,
  using the branch's debug binary) prints these keys for the verifier contract:
  `endpoints, language, native_command, runtime_qualification, strict_success,
  task_containment, trusted_assumptions`. There is no `toolchain`. Running
  `grep -n leak` over `src/anarres_formal_adapter/` finds no match. The only hits are
  the RFC itself (lines 69 and 211).
- Suggested fix: Add `toolchain`, `admitted_proofs`, `unsafe_features`, and a
  structured allowed-assumption reference (for example the pin's trusted-axiom
  count, or a digest of the list) to `VeroVerifierDriver.descriptor()`. Otherwise,
  narrow RFC lines 67-69 and 77-79 to say what the first pull request records, and
  list leakage checks under "Remaining gaps".

### S2 (should-fix): The new `anarres formal contracts` subcommand has no test

- File: `data/formal-verification/vero/src/anarres_formal_adapter/cli.py:777-786`
- What is wrong: This is new user-facing behavior, and the Vero README (lines 14-19)
  advertises it. No test, smoke step, or CLI test runs it. AGENTS.md says "Add or
  update tests whenever behavior changes." The handler also ignores `--json`, so the
  human-readable output dumps each descriptor as one long JSON line.
- Evidence: `grep -rn '"contracts"\|formal contracts' tests tools` returns nothing
  relevant. Run by hand, the command works and gives identical bytes on reruns
  (`cmp a.json b.json` reports `deterministic`).
- Suggested fix: Add an integration test that runs `anarres formal contracts --json`
  twice. It should assert byte equality, `policy_probe: false`, and that both
  `content_id` values pass `verify_seal`.

### S3 (should-fix): The new `--dry-run` reverses the explicit-execution boundary, and the shared CLI docs were not updated

- Files: `crates/anarres-cli/src/source.rs:337-387`; `docs/rfcs/0008-portable-formal-verification-contracts.md:125-159`;
  `docs/cli.md:206-240`; `docs/adapters.md:106-108`; `docs/architecture/adapter-authoring.md:58`;
  `docs/rfcs/0006-native-environment-sources.md:45-47`
- What is wrong:
  1. RFC 0004 makes execution the opt-in step (`run-task --execute`). The
     molecular adapter, the only adapter that declares `policy-probe`, plans by
     default and runs only with `-- --execute`. Issue #66 asks that "bounded probe
     execution must require an explicit execution flag". This branch does the
     reverse: planning is the opt-in step (`--dry-run`), and a plain `anarres probe`
     on a future adapter with both `policy-probe` and `probe-plan` is the execution
     path. Nothing in the core requires an execution flag. RFC 0008 line 156 says
     the branch "follows the planning boundary in RFC 0004" without noting this.
  2. "Dry run" now means two things. `docs/cli.md:234-235` and `docs/adapters.md:107`
     say the molecular probe "remains dry-run by default". But
     `anarres probe <molecular source> --dry-run` is now rejected because molecular
     does not declare `probe-plan`.
  3. `docs/cli.md`, `docs/adapters.md`, and `adapter-authoring.md` do not mention
     `--dry-run`, `probe-plan`, `can_plan_probe`, or `probe_plan_ready`.
  4. RFC 0006 line 46-47 says an adapter declares `source-qualification` only after
     "a real native source passes its conformance tests". The fixture declares it
     for a synthetic source. RFC 0008 does not acknowledge this exception.
- Evidence: `experiments/ai-for-science/molecular-design/reaction-environment-selection/src/anarres_molecular_adapter/cli.py:468`
  (`probe_source.add_argument("--execute", ...)`). Mutation R4 (below) confirms that
  the core gates only on readiness and appends `--dry-run`. No execution flag exists.
  Nothing executes in this pull request, so the gap is not exploitable today.
- Suggested fix: In RFC 0008, state how `--dry-run` relates to the adapter-owned
  `--execute` convention. Either require a core execution flag before any future
  `policy-probe` dispatch, or record that this decision is deferred to the
  execution pull request. Update `docs/cli.md` and `docs/adapters.md` with the new
  flag, capability, and inspection fields. Add one sentence to RFC 0008 that
  explains the fixture's exception to RFC 0006's "real native source" rule.

### S4 (should-fix): The canonical JSON definition is too loose for other packages to reproduce `content_id`

- Files: `docs/rfcs/0008-portable-formal-verification-contracts.md:45-48`;
  `data/formal-verification/vero/src/anarres_formal_adapter/contracts.py:35-36`
- What is wrong: The RFC says canonical JSON "encodes the result as UTF-8", and line
  53 invites other installed packages to implement the protocols. The code uses
  Python's default `ensure_ascii=True`, so non-ASCII text is written as `\uXXXX`
  escapes, and floats (for example `wall_seconds`) use Python's `repr` format. A
  non-Python implementation that follows the RFC text would produce a different
  `content_id`.
- Evidence: `canonical({"a": "é"})` returns `b'{"a":"\\u00e9"}'`, not the UTF-8 bytes
  `{"a":"é"}`.
- Suggested fix: Specify the ASCII-escaped form and the number format (or adopt RFC
  8785 JCS), and add a fixed test vector to the test suite.

### S5 (should-fix): The same concept is named several ways, and "endpoint" clashes with the shared vocabulary

- Files: `contracts.py:17-22, 238-262`; `vero_drivers.py:52`; `fixture.py:81-83, 256-258`; RFC 0008 lines 68, 76-79, 161-163
- What is wrong: `docs/standards/writing.md` rule 1 asks for one term per concept,
  and its shared table defines *target* as "held-out capability or endpoint". This
  branch uses *endpoint* for the task contract type (`proof-only`,
  `code-and-proof`, ...), and `CandidateContract` has both `endpoint` and `target`
  fields. The allowed-assumption concept appears under five names: `trusted_axioms`
  (fixture), `trusted_assumptions` (Vero verifier), "allowed assumptions" (RFC line
  78), "allowed-assumption contract" (RFC line 163), and the `assumptions` field.
  The RFC says "unsafe declarations" while the code says `unsafe_features`. The RFC
  also says "runner or harness identity", while requests carry both `runner` and
  `harness`, and `harness` is required to equal the runner's name and `content_id`.
- Evidence: `grep -noi "trusted axiom\|allowed assumption\|trusted_assumptions\|allowed-assumption"`
  over the new files (counts reported during review).
- Suggested fix: Choose one term for the task contract type, such as *verification
  task type* or *formal endpoint*, and define it once against *target*. Use one
  assumption term in both code and prose. Rename either "unsafe declarations" or
  `unsafe_features` so they match.

### N1 (nit): The core now rejects `-- --dry-run` for every adapter, but the help text still says arguments are forwarded literally

- File: `crates/anarres-cli/src/source.rs:347-354`; `crates/anarres-cli/src/lib.rs:177`
- What is wrong: This is a small change to existing generic behavior. Before this
  branch, any argument after `--` reached the adapter. I found no maintained
  adapter that uses `--dry-run` (`grep -rn dry.run packages experiments` finds no
  match outside this change), and the exit code is still 1 like other usage errors,
  so nothing breaks today. The help text "Additional arguments forwarded literally"
  is now slightly wrong.
- Suggested fix: Add "except `--dry-run`" to the help text.

### N2 (nit): The `--dry-run` help text promises more than the core can enforce

- File: `crates/anarres-cli/src/lib.rs:174`
- What is wrong: "without executing the policy or opening held-out tasks". The core
  only gates on `probe-plan` and forwards the flag. The guarantee comes from the
  adapter. The fixture enforces it by making `--dry-run` a required argument
  (`fixture_cli.py:53`).
- Suggested fix: "Ask the adapter for its ordered probe plan. Requires the
  `probe-plan` capability."

### N3 (nit): The fixture verifier treats a bare newline differently from empty output

- File: `fixture.py:279-284`
- What is wrong: `verify(b"\n")` returns `strict-proof-failure`, but `verify(b"")`
  returns `parser-failure`. Blank runner output is exactly the case where an
  infrastructure failure could be counted as a proof failure. The runner always
  verifies `PROOF_BYTES`, so no current path reaches this.
- Evidence: printed `'strict-proof-failure' 'parser-failure' 'parser-failure'` for
  `b"\n"`, `b""`, `b"false"`.
- Suggested fix: Classify `b"\n"` as `parser-failure` (or `unsupported`) and keep
  only `b"false\n"` as a strict proof failure.

### N4 (nit): Fixture qualification checks some fields for truthiness instead of type

- File: `fixture.py:133, 137, 191-203`
- What is wrong: `trusted_axioms: ""`, `trusted_axioms: 0`, `unsafe_features: {}` and
  `repository: ["x"]` all qualify. Group values are never type-checked.
- Evidence: a resealed record with each of these values printed `qualified` four times.
- Suggested fix: Require `== []` for the axiom and unsafe lists, and require
  nonempty strings for lineage fields.

### N5 (nit): Containment checks run before the read, so a file swapped in between is not caught

- File: `contracts.py:80-92` (`contained_file`)
- What is wrong: The symlink, resolve and link-count checks run before
  `read_bytes()`, so a file swapped between the check and the read is not caught.
  Separately, the `st_nlink != 1` rule also rejects legitimate hard-linked
  checkouts (for example `cp -al` or some deduplicating stores). Drivers are trusted
  and sources are local, so the risk is low.
- Suggested fix: Open with `O_NOFOLLOW`, then `fstat` the open descriptor and read
  from it. Document the hard-link rule in the tutorial.

### N6 (nit): Small inconsistencies in the identity helper

- File: `contracts.py:95-122`
- What is wrong: The `implementation` keys are relative to the package, except
  `anarres_formal_adapter/contracts.py`, which is qualified with the package name.
  `version` is fixed at `"1"` for every driver, so a single driver cannot change its
  version without editing `contracts.py`, and editing it changes every identity.
  `anarres.core`, used by `fixture_cli.py` to validate manifests, is outside every
  identity. RESULT_FIX1 acknowledges this.
- Suggested fix: Make `version` a parameter, and use one key convention.

### N7 (nit): The plan-output guard protects the native source but not the manifest

- File: `fixture_cli.py:75-82`
- What is wrong: A hand-written manifest whose `source.uri` points to a subdirectory
  puts `anarres.toml` outside `source.source`. Then `--output anarres.toml --force`
  would overwrite the manifest. `init` always writes `uri = "."`, so the default
  path is safe.
- Suggested fix: Also reject `args.output.resolve() == manifest.resolve()`.

### N8 (nit): The CLI test can run a stale binary

- File: `tests/integration/test_formal_portable_cli.py:21-22`
- What is wrong: It builds only when `target/debug/anarres` is missing. A binary left
  over from another branch can make the test pass or fail for the wrong reason.
  Other CLI integration tests in the repository follow the same pattern, and
  `make test` builds first, so the risk is low.
- Suggested fix: Always run `cargo build --quiet -p anarres-cli`. It does nothing
  when the binary is current.

### N9 (nit): Writing style

- RFC 0008 line 133 and the guide's line 80 use semicolons where no internal commas
  need them (writing.md rule 6). RFC line 7 ("RFC 0007 belongs to another open pull
  request") is a process note that will go stale. Remove it or move it to the
  pull request description.

## Fixes in `a260f64` (verified by my own mutations in a throwaway clone at `/tmp/rv66/mut`)

- (a) The verifier identity covers `fixture_cli.py`. When I removed `"fixture_cli.py"`
  from `FixtureVerifierDriver.descriptor()`, the test failed
  (`AssertionError: 'fixture_cli.py' not found in {...}`). I also deleted the test's
  `assertIn` guard so that only the behavioral check remained. The test still failed
  because the identity no longer changed after the command implementation was
  edited (`'sha256:4f1bdf...' == 'sha256:4f1bdf...'`). The runner's advertised
  `formal-fixture-runner` maps to `fixture:runner_main`, which is already in
  `fixture.py`. Vero's `native_command` is a runtime-contract key, not a packaged
  command.
- (b) Qualification rejects metadata the runner rejects. I disabled the
  path-shape, producing-run and license checks one at a time. Each made
  `test_fixture_qualification_rejects_metadata_the_runner_rejects` fail. Changing
  the plan to emit `model_tokens: 1` made
  `test_every_planned_fixture_attempt_is_consumed_by_the_runner` fail with 4 errors.
  I also compared the runner's checks with qualification's field by field: task-id
  form, `media_type`, digest (through `payload == TASK_BYTES` plus the digest
  equality), size, `uri`, license, producing run, empty
  dependencies/context/reference material, and partition. I found no metadata that
  qualifies but that the runner would reject.
- (c) Digest substitution. Removing `digest(payload) != item["sha256"] or` made the
  test fail with `AssertionError: ValueError not raised`. So with valid bytes and
  size, the digest comparison is the only check in qualification that rejects it.
- New defects from the fix: none found. The new checks run after the held-out
  `continue` (`fixture.py:205-206`), so they never stat or read a held-out task.
  They run before `contained_file`, but they constrain only the path string,
  producing run and license. The symlink, hard-link, digest, size and
  `TASK_BYTES` checks all stay reachable, and mutations 6-8 and (c) show each of
  them still makes its test fail when disabled.

## Checked and fine

- **Read the full diff** (`git diff d168e2a..HEAD`): RFC 0008, the guide, the Vero README
  and pyproject changes, `contracts.py`, `fixture.py`, `fixture_cli.py`,
  `vero_drivers.py`, the `cli.py` changes, the Rust changes in
  `adapter.rs`/`lib.rs`/`source.rs`/`tests/cli.rs`, the three new test files, and the
  smoke tool.
- **Required suites, run in this clone:**
  - `uv run python -m unittest discover -s tests/integration -p 'test_formal_portable*.py' -v`
    gave `Ran 26 tests in 16.875s` / `OK`. This run built `target/debug/anarres`, because
    none existed.
  - `uv run python -m unittest discover -s tests/integration -p 'test_vero_released_manifest_regression.py' -v`
    gave `Ran 3 tests in 0.094s` / `OK`.
  - `cargo test -p anarres-cli --locked` gave 14 lib tests, 0 main tests and 32 CLI
    integration tests, all `ok`, with 0 failed.
- **Mutation testing** (throwaway clone, script `/tmp/rv66/scripts/mutate.py`; every
  mutation was restored afterwards and `git status` was clean). The target test
  failed for all 20 mutations:
  - [0] verifier identity without `fixture_cli.py`
  - [1-3] each runner-metadata check removed
  - [4] the plan emits a request the runner rejects
  - [5] digest comparison removed
  - [6] hard-link check disabled
  - [7, 8] symlink check disabled (file test and directory test)
  - [9] stat of the held-out path before the skip (caught by the
    `Path.stat`/`open` guard)
  - [10] `proof_failure` set to `outcome != "strict-success"` (6 subtests failed)
  - [11] compatibility check ignores `verifier`
  - [12] plan sorts seeds
  - [13] plan-output-in-source guard removed (CLI test)
  - [14] runner skips the harness check
  - [15] Vero driver skips the revision check
  - Rust (`/tmp/rv66/scripts/rust_mut.sh`):
    - R1, hidden `-- --dry-run` accepted: the hidden-flag test fails.
    - R2, planning gated on `probe_ready`: both dry-run tests fail.
    - R3, `--dry-run` not forwarded: the dispatch test fails.
    - R4, dry run treated as a policy probe: both tests fail.
- **Vero routing:** In `cli.py` I made `qualified_source` and `command_qualify_runtime`
  bypass the drivers and call `source_qualification.qualify` and
  `runtime_qualification.qualify` directly, as before this branch, but without the
  revision and license checks. Then
  `test_vero_profile_adapter.VeroProfileAdapterTest.test_source_qualification_rejects_unpinned_manifest_revision`
  failed (108 tests run). So the driver's revision check is reachable from the CLI
  and covered by tests. The error type changed from `FormalCliError` to
  `ValueError`. `main()` catches both in the same `except` branch
  (`cli.py:908`), so messages and exit code 1 are unchanged.
- **Frozen and hash-pinned files:** The only changed files under
  `data/formal-verification/vero/` outside `src/` are `README.md` and
  `pyproject.toml`. For every changed file, I searched the repository (excluding
  `target` and `.git`) for the SHA-256 of its base-commit bytes. There were no
  matches, so no changed file is pinned by any manifest, protocol or receipt. No
  file in either released manifest, and none of the seven protocol-bound scripts
  listed in RFC 0008, appears in the diff.
- **Released manifest regression:** The test pins the base-commit manifest digests
  as literals, and both tamper tests fail as intended. The pinned digests match the
  current manifests, since the suite passes with no diff to those files.
- **No `policy-probe` declared for Vero:** The `formal` descriptor is unchanged.
  `VeroSourceDriver.descriptor()["contract"]["policy_probe"]` is `False`, and
  `formal contracts` prints `policy_probe: false`. The CLI test asserts that doctor
  omits `policy-probe`. The fixture declares only `probe-plan` and
  `source-qualification`.
- **Rust behavior and exit codes:** A probe without `--dry-run` goes down the same
  "policy probe" path as before. The new `validate_descriptor` rules apply only
  when `probe-plan` is declared. The output changes are additive: one more line in
  `doctor` and `inspect` human output, and two new fields in the `inspect` JSON.
  `adapter list` and `status` are untouched. N1 covers the one change to
  generic forwarding.
- **Dry run and held-out tasks:** The plan test patches `Path.open/stat/lstat/resolve`
  for any held-out path, plus sockets, `subprocess.Popen` and `FixtureRunner.run`.
  Mutation [9] proves the guard fires. `fixture_cli` requires `--dry-run`, so the
  fixture cannot execute even if the core routes it wrongly.
- **Determinism:** The plan and qualification are byte-identical across two
  directories and across reruns (unit test plus CLI test). The smoke tool reports
  `formal_fixture_plan_deterministic: true`. No absolute path appears in the plan.
- **Isolated install and outside-checkout path:** I ran
  `uv run python tools/smoke_adapter_installation.py --binary <release build>` in the
  throwaway clone with `PYTHONPATH` unset. Exit 0. It reported `wheels: 9`,
  `formal-fixture` in both wheel and source installs, and
  `formal_fixture_native_source_qualified/…_plan_deterministic/…_held_out_task_absent: true`,
  `formal_fixture_plan_attempts: 4`.
- **Infrastructure failure versus proof failure:** `attempt_record` sets
  `proof_failure` only for `strict-proof-failure`. All eight outcomes stay distinct,
  and `runner_main` emits no attempt on error. N3 is the only edge case.
- **Endpoints:** The four endpoints are kept separate, and specification endpoints
  are rejected as incompatible with `proof-only`. Vero maps `proof-only` and
  `code-and-proof` to its native `proof` and `codeproof` modes. Nothing mixes them.
- **Lean-first scope:** The only real driver is Vero (`language="Lean"`), plus the
  fixture (`language="fixture"`). Dafny, Verus and Rocq appear only in three
  "follow-up" sentences (guide line 122, RFC lines 22 and 218-220). No code, enum
  or descriptor adds or implies one. Vero's own pin lists `coq/dafny/verus`
  benchmark origins under `source_languages`, but these are upstream metadata of
  the Lean benchmark, not drivers.
- **Lint:** `ruff format --check .`, `ruff check .`, `cargo fmt --all -- --check`,
  `cargo clippy -p anarres-cli --all-targets -- -D warnings` and
  `git diff --check d168e2a..HEAD` all passed (throwaway clone).
- **`make check`** (throwaway clone, `PYTHONPATH` unset): exit 0. The integration
  stage gave `Ran 340 tests in 150.079s` / `OK`, then `repository hygiene passed for
  1611 files` and `Prose style check passed`.
- **Writing:** No em dashes in the new prose. Findings S5 and N9 cover the
  remaining writing points.
- **Author's claims (RESULT_PR1.md, RESULT_FIX1.md), checked against the above:**
  the test counts (26 + 3), the smoke JSON (matches my run), the description of the
  three fixes, and the absence of Dafny, Verus and Rocq code are accurate.
  RESULT_PR1 says "Ran 22 tests". That count predates `a260f64`, which added four.

## Not checked

- `make study-check`. Not run (long; the branch changes no study reproducer).
- `make benchmark`. Not run. It needs every adapter installed on `PATH`.
  RESULT_PR1 reports that it failed (`adapter.list p95 117.59 ms > 50 ms`, and
  finance medians above 200 ms). The branch does not change `adapter list`, which
  scans `PATH` without starting processes, or any finance path, so the failure
  probably comes from the machine. I did not confirm that with a base-versus-head
  run.
- No real Vero checkout, Lean or Lake build, runtime contract, task containment or
  model call. None of these are in this pull request.
- I did not walk through the tutorial with `uv tool install` into my own `PATH`,
  because I wanted to leave the home tool directory untouched. The smoke tool
  covers the same commands in isolation.
- Windows behavior (`os.name == "nt"` branches, path rules) was not checked.

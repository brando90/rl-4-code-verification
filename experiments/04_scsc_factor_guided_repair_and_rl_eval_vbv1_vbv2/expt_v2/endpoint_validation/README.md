# Restricted independent endpoint harness validation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v2/endpoint_validation/README.md>

**TLDR:** This validates endpoint plumbing with authored controls and the pinned transitive-axiom checker. Python unit checks passed; actual Lean 4.22.0 validation is PENDING on the Stanford Network Analysis Project (SNAP) cluster.

> **Stale (QA 11-25-2026):** the PENDING status in this README is out of date. The immutable-row reconciliation `results_2026-10-06T0734Z_reconciliation.json` in this folder shows all 24 authored controls measured and matching; the current numbers are in `../../results.md` and `experiments/README.md`.

The home is `04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v2/endpoint_validation`. These fixtures are external engineering controls, not benchmark references, training examples, VeriBench successes or Smooth Conjunctive Score for Code verification (SCSC) measurements. They do not establish endpoint applicability to arbitrary benchmark files.

## Goal and decision criterion

Verify that fixed reference tests and universal reference obligations refer to the candidate implementation, independent of its chosen specification or certificate. Accept the engineering gate only when the entire declared control set matches its prospectively recorded statuses under the pinned Lean environment. Any mismatch, unknown infrastructure state or incomplete cell set leaves the gate unaccepted.

`manifest.json` freezes three natural-number tasks: increment, double and cap at two. Each has an exact universal equation, no precondition, and four finite tests at inputs 0, 1, 2 and 7. The eight variants per task are correct, implementation bug, weak specification, vacuous specification, direct `sorry`, transitive helper `sorry`, declared axiom and `native_decide`. The resulting 24 declared cells include expected statuses; expectations are hypotheses for validation and are not measured outcomes.

## Execution

Run from the repository root on SNAP; use a new output directory each time:

```bash
python3 experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v2/endpoint_validation/check_endpoint.py \
  --scorer-repo /path/to/veribench \
  --lake-dir /path/to/veribench/veribench_dataset/lean_src \
  --output /path/to/new/endpoint_validation_receipt \
  --probe-timeout 30
```

Dependencies: Python 3.10 or newer, Git, `lake` on the executable path, Lean `leanprover/lean4:v4.22.0`, and the populated Mathlib project at revision `79e94a093aff4a60fb1b1f92d9681e407124c2ca`. The supplied VeriBench clone must contain scorer commit `59059a20d40adf3289869e58302169ad78102877`; it need not have that commit checked out. The driver extracts and hash-checks its `scripts/scsc/kernel_axioms.py`, with Secure Hash Algorithm 256-bit (SHA-256) digest `5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287`. No package installation, provider credential or model call occurs.

The pinned verifier compiles each generated source and inspects the compiled theorem dependencies. Each probe has one wall-clock deadline shared across compilation and inspection. There are at most three evaluator proof attempts per obligation; accepted proofs stop further attempts. All cells use the same ordered tactics and per-attempt deadline. With this manifest there are at most 123 probes; at 30 seconds per probe the conservative deadline sum is 61.5 minutes, plus preflight. This is a cap calculation, not measured runtime. No graphics processing unit is used.

`results.json` is created with RUNNING status, retains every declared PENDING cell before compilation, and is rewritten after each measured cell. Its final state is COMPLETE only if every control matches. CONTROL_MISMATCH and INFRASTRUCTURE_OR_INPUT_FAILURE exit nonzero. Keep the raw `inputs/`, generated Lean sources, pinned verifier bytes, stage reports and verifier evidence directories beside it. The parent coordinator owns the live experiment `results.md` and SNAP execution receipt.

## Result semantics and boundaries

- `reference_tests_pass`: every fixed test has an accepted kernel certificate; a negative value requires a kernel-checked unequal-value witness. The small Python interpreter only proposes a witness; it cannot certify failure.
- `submitted_certificate_accepted`: checks the submitted specification as written. A weak `True` theorem or a vacuous precondition can be accepted here while reference success fails.
- `submitted_reference_obligations_proved`: only a full, mechanically identical submitted universal equation certifies the fixed exact obligation. Missing or inapplicable bridges are unknown.
- `evaluator_reference_obligations_proved`: proofs found by extra fixed evaluator search, which tests bounded certifiability rather than submitted proof skill.
- `reference_verified_success`: conjunction of fixed tests and evaluator reference obligations. Its components remain visible; the submitted endpoint is separate.

Each endpoint carries `status`, `value` and `reason`. `pass` means true, `fail` means observed false, and `unknown` or `unmeasured` means JSON `null`. Compile failure, timeout, missing adapter/certificate and exhausted proof search do not establish mathematical falsehood. A known failed component makes the conjunction false while the other missing components remain separately visible. No SCSC or judge-derived quantity is emitted.

Candidates are JSON abstract syntax trees for a total `Nat → Nat` callable interface. Only natural literals, the variable `n`, addition, truncated subtraction, multiplication, minimum and maximum are admitted. Depth, literal size, file size, paths, keys and certificate selectors are bounded. Candidate strings cannot become Lean imports, names, arbitrary proof text, macros or commands. The candidate specification and proof variants select fixed harness-owned templates. This is deliberately narrower than general Lean submission and is not a secure operating-system sandbox for arbitrary Lean code. The supplied toolchain, installed dependency binaries and host remain trusted infrastructure.

Allowed transitive axioms are exactly `propext`, `Classical.choice` and `Quot.sound`. Direct and helper `sorry`, user axioms and native decision dependencies fail submitted-certificate acceptance. An evaluator may still prove the fixed property of a correct implementation whose submitted proof is dishonest; that difference is intentional.

## Deterministic verification

```bash
python3 -m unittest discover \
  -s experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v2/endpoint_validation \
  -p test_endpoint.py -v
```

Observed locally on 10-05-2026: ten unit tests passed. They do not invoke Lean. Actual compilation and all 24 endpoint control outcomes remain PENDING until the parent executes the run on SNAP. No scientific effect, held-out success rate or benchmark applicability has been measured.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] The independent endpoint harness is implemented with explicit trust and missingness checks; remote Lean validation remains pending.

**Snapshot:** `manifest.json` declares `increment_correct`, `increment_weak_spec` and `increment_helper_sorry` among its 24 controls; their recorded expected statuses are validation targets, not results.

# Experiment 12 version 2 results — mapping census and static controls (no hidden-test outcome yet)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/results.md>

**TLDR:** The corrected adapter (amended once, V2-A1, before any evaluation) was run in mapping-only mode (no Lean, no model calls) over the 11 primary systems' 4,626 compiling cells with extracted tests on `skampere1` (26.2 s). It maps every gold symbol in 3,121 cells before any probe (version 1 recorded 3,444 after its Lean probes), leaves 263 cells to the agreement probe, changes the entry point in 379 of the 3,624 cells both versions map, and excludes a helper in 364 cells. Static controls on all 882 gold suites: gold maps to itself at step 1 in 882/882; renamed gold is never mapped to a wrong symbol statically (0/882; 855 deferred to the probe). No pass rate, correlation or hidden outcome was computed, and none may be until the frozen forecast is read against Emily's evaluation.

**Status:** RUNNING — all 50 dynamic control tasks admitted; primary evaluation awaits the four unchanged gates.
**Last updated:** 10-15-2026 20:41 PDT

## Static controls over all 882 gold suites (`results/static_controls_v2.json`, 10.2 s)

| Control | Rule | Result |
|---|---|---:|
| C1-static gold as its own candidate | every gold symbol maps to itself at step 1 | 882/882 tasks pass |
| C2-static renamed gold (every tested symbol renamed, version-1 `renamed_control`) | the static stage may map (2a/2b) or defer to the probe, but never maps to a wrong symbol | 0/882 wrong; 24 resolved correctly (2a 121 symbols, 2b 13), 855 deferred to the probe, 3 not applicable statically |

Before amendment V2-A1 the same check found 7/882 wrong static picks (`absDiff` for `quadAbsDiffPlusThree`, `median_low` for `benchmark_median_low`, `covariance` for `benchmark_covariance`, `escapeHtml` for `escapeHtmlImp`, `safeAccessMemory` for `unsafeAccessMemory`, `safeFindLast` for `unsafeFindLast`); the amendment (PROTOCOL.md § 8) restricts name affinity to word-boundary suffixes and lets another member's references veto it. Deterministic checks, p-val=n/a. The Lean controls C1–C4 of PROTOCOL.md § 3 still gate the evaluation.

## Mapping census (static steps 1, 2a, 2b; `results/mapping_census_v2.json`)

Inputs and hashes: `input_manifest_A1.json` `20ae9005…`, `hidden_tests_manifest.json` `f23f9956…`, `adapter_v2.py` `da6fbe36…` (amended), version-1 `adapter_e12.py` `0e9f4381…`; every candidate file re-hashed against the manifest (0 mismatches). Version-1 mappings were read from the `mapping`, `diagnostics`, `all_symbols_mapped` and `compile.status` fields of the 4,626 evaluation receipts; no outcome field was read. Denominator: 9,856 declared primary cells − 5,180 non-compiling − 48 compiling cells of the 14 no-test tasks − 2 file-missing = 4,626 compiling cells with tests, one unique (task, file) group each.

| Quantity | Count | Share of 4,626 |
|---|---:|---:|
| Version 1: every gold symbol mapped (after Lean probes) | 3,444 | 0.745 |
| Version 1: at least one symbol mapped | 3,911 | 0.845 |
| Version 2 static: every symbol mapped | 3,121 | 0.675 |
| Version 2 static: some symbols mapped (partial) | 315 | 0.068 |
| Version 2 static: at least one symbol needs the agreement probe | 263 | 0.057 |
| Version 2 static: no symbol mapped | 927 | 0.200 |
| Newly fully mapped (version 1 not all → version 2 all) | 7 | 0.002 |
| Version 1 all → version 2 not all | 330 | 0.071 |
| &nbsp;&nbsp;of which waiting on the probe | 257 | 0.056 |
| &nbsp;&nbsp;of which partial or not applicable | 73 | 0.016 |
| Changed entry point (among 3,624 cells both versions map) | 379 | 0.105 of 3,624 |
| Cells where a helper was excluded at step 2 | 364 | 0.079 |
| Cells with a recorded result-type mismatch at step 1 | 272 | 0.059 |
| Cells with a recorded argument-type mismatch at step 1 | 266 | 0.057 |
| Cells with zero `example`/`#eval` declarations (self-tests) | 612 | 0.132 |

Hidden tests mappable per cell (a test is mappable when every symbol it uses is mapped; type elaboration still needs Lean, so this is an upper bound on evaluable tests):

| Share of a cell's tests mappable | Cells |
|---|---:|
| all | 3,121 |
| (75%, 100%) | 34 |
| (50%, 75%] | 359 |
| (25%, 50%] | 30 |
| (0%, 25%] | 12 |
| none | 1,070 |

Test-cells: 40,695 of 55,967 mappable (0.727). Deciding steps over symbol mappings: version 2 static 1: 4,823, 2a: 882, 2b: 1,365 (7,070 mapped); 344 symbols deferred to the probe (326 plain, 16 because another member out-references the affine one, 2 same-name arity mismatches); 2,381 `no_match`; 85 `gold_signature_unknown`. Version 1 recorded 1: 5,075, 2: 693, 3: 1,532, 4: 387 (7,687). Name affinity (2b) resolves statically most of what version 1 sent to the probe.

Gold-side lexer check: 90/896 gold files contain `?`/`!` identifiers (Mathlib lemma names, `Array.set!`, `s!`), 0 gold implementation symbols and 0 hidden-test symbol tokens are affected, 5 tests carry a `key?` named argument and 1 a `.get?` projection that re-point identically; the frozen version-1 suite is reused unchanged (DESIGN.md § 5).

### Per system

| System | Compiling with tests | V1 all / any mapped | V2 all | V2 partial | V2 probe | V2 none | Changed entry point | Newly all | V1 all → not all (probe) | Helper excluded | Result / argument type mismatch | Zero self-tests |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 809 | 210 / 247 | 210 | 26 | 0 | 573 | 1 | 0 | 0 (0) | 7 | 13 / 16 | 552 |
| claude-opus-5-max | 428 | 405 / 408 | 334 | 3 | 61 | 30 | 48 | 3 | 74 (61) | 29 | 19 / 23 | 0 |
| claude_code | 865 | 788 / 823 | 627 | 33 | 123 | 82 | 112 | 1 | 162 (121) | 16 | 59 / 70 | 0 |
| codex | 881 | 683 / 837 | 657 | 110 | 28 | 86 | 84 | 3 | 29 (27) | 59 | 65 / 65 | 0 |
| gemini-3.1-pro-high | 50 | 46 / 47 | 41 | 1 | 0 | 8 | 12 | 0 | 5 (0) | 1 | 5 / 4 | 0 |
| gpt-5.6-luna-high | 145 | 117 / 138 | 110 | 14 | 6 | 15 | 19 | 0 | 7 (6) | 31 | 6 / 11 | 0 |
| gpt-5.6-sol-high | 345 | 281 / 339 | 275 | 34 | 7 | 29 | 43 | 0 | 6 (6) | 95 | 15 / 20 | 0 |
| gpt-6-astra-high | 459 | 381 / 448 | 348 | 47 | 24 | 40 | 52 | 0 | 33 (24) | 91 | 65 / 32 | 0 |
| gpt-6-luna-high | 126 | 113 / 124 | 102 | 6 | 9 | 9 | 7 | 0 | 11 (9) | 32 | 5 / 6 | 0 |
| leanstral | 517 | 419 / 499 | 416 | 41 | 5 | 55 | 1 | 0 | 3 (3) | 3 | 19 / 19 | 60 |
| qwen3.6-27b-thinking | 1 | 1 / 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 (0) | 0 | 1 / 0 | 0 |
| **all** | **4,626** | **3,444 / 3,911** | **3,121** | **315** | **263** | **927** | **379** | **7** | **330 (257)** | **364** | **272 / 266** | **612** |

Reading: the entry-point changes concentrate in Claude Code (112), Codex (84), GPT-6 Astra (52), Claude Opus 5 (48) and GPT-5.6 Sol (43), the systems whose files define specification helpers next to the implementation; the 61 Opus cells now waiting on the probe are the same files whose helpers version 1 selected. Leanstral and baseline barely move (1 and 1 changed), consistent with their files having few definitions. These are mapping counts: p-val=n/a, deterministic over the fixed cells.

## What is not here, on purpose

No version-2 hidden pass/fail, pass rate, `hidden_all_pass`, P1, P2, P3 or G-A value exists. The protocol is locked ([PROTOCOL.md](PROTOCOL.md), amendment V2-A1 appended) and the forecast frozen (`forecasts/e12_v2_forecast.json` plus `e12_v2_forecast_amendment_A1.json`) after this census and before any evaluation. Emily's run ([cc.md](cc.md)) produces the outcomes; this page is then extended below this line without changing the census above.

## Execution update — 10-15-2026

Both frozen forecasts and all five amendment-pinned inputs verified. All 64 adapter tests and 13 new runtime, cache, retry and analysis tests pass. Lean reports v4.22.0. The start email was sent. Two low-priority Lean workers will run controls before the primary evaluation; no model or judge calls, graphics processors or Vals spend.

| Phase | Status | Evidence |
|---|---|---|
| Hash and adapter preflight | DONE | Both forecasts, five pinned inputs; 64/64 tests |
| Runtime and analysis scripts | DONE | 13/13 new tests; full suite 1,191 passed / 18 skipped |
| Dynamic controls C1–C4 | IN PROGRESS | 50 prescribed tasks; two low-priority Lean workers |
| Full primary evaluation | PENDING | 0/4,626 eligible groups; 9,856 declared cells |
| Analysis and final publication | PENDING | Frozen predictions unchanged |

Verification at 10-15-2026 20:39 PDT: full repository suite **1,191 passed / 18 skipped**; 77 current targeted checks pass. Synthetic Lean bridge: 2/2 tests evaluable, one passing and one deliberately failing. Pinned toolchain, Mathlib manifest and version-1 helper hashes match.

Control launch verified at 10-15-2026 20:41 PDT: session `rl4cv-e12v2-controls`, two live Lean processes, first compiled modules present. Implementation commit `7ce7bd0`, landed on main through `7502a82`; [preflight receipt](results/preflight_v2.json).

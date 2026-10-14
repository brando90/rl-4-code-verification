# Experiment 12 version 2 results — mapping census (no hidden-test outcome yet)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/results.md>

**TLDR:** The corrected adapter was run in mapping-only mode (no Lean, no model calls) over the 11 primary systems' 4,626 compiling cells with extracted tests on `skampere1` (25.7 s). It maps every gold symbol in 3,129 cells before any probe (version 1 recorded 3,444 after its Lean probes), leaves 252 cells to the agreement probe, changes the entry point in 394 of the 3,641 cells both versions map, and excludes a helper in 364 cells. All 3,129 fully mapped cells have every test mappable; 1,054 cells have none. No pass rate, correlation or hidden outcome was computed, and none may be until the frozen forecast is read against Emily's evaluation.

**Status:** CENSUS DONE, PROTOCOL LOCKED, FORECAST FROZEN; EVALUATION PENDING (owner Emily Xia)
**Last updated:** 10-14-2026 (see CKPT_e12_v2.md for the exact stamp)

## Mapping census (static steps 1, 2a, 2b; `results/mapping_census_v2.json`)

Inputs and hashes: `input_manifest_A1.json` `20ae9005…`, `hidden_tests_manifest.json` `f23f9956…`, `adapter_v2.py` `6e825e94…`, version-1 `adapter_e12.py` `0e9f4381…`; every candidate file re-hashed against the manifest (0 mismatches). Version-1 mappings were read from the `mapping`, `diagnostics`, `all_symbols_mapped` and `compile.status` fields of the 4,626 evaluation receipts; no outcome field was read. Denominator: 9,856 declared primary cells − 5,180 non-compiling − 48 compiling cells of the 14 no-test tasks − 2 file-missing = 4,626 compiling cells with tests, one unique (task, file) group each.

| Quantity | Count | Share of 4,626 |
|---|---:|---:|
| Version 1: every gold symbol mapped (after Lean probes) | 3,444 | 0.745 |
| Version 1: at least one symbol mapped | 3,911 | 0.845 |
| Version 2 static: every symbol mapped | 3,129 | 0.676 |
| Version 2 static: some symbols mapped (partial) | 318 | 0.069 |
| Version 2 static: at least one symbol needs the agreement probe | 252 | 0.054 |
| Version 2 static: no symbol mapped | 927 | 0.200 |
| Newly fully mapped (version 1 not all → version 2 all) | 7 | 0.002 |
| Version 1 all → version 2 not all | 322 | 0.070 |
| &nbsp;&nbsp;of which waiting on the probe | 249 | 0.054 |
| &nbsp;&nbsp;of which partial or not applicable | 73 | 0.016 |
| Changed entry point (among 3,641 cells both versions map) | 394 | 0.108 of 3,641 |
| Cells where a helper was excluded at step 2 | 364 | 0.079 |
| Cells with a recorded result-type mismatch at step 1 | 272 | 0.059 |
| Cells with a recorded argument-type mismatch at step 1 | 266 | 0.057 |
| Cells with zero `example`/`#eval` declarations (self-tests) | 612 | 0.132 |

Hidden tests mappable per cell (a test is mappable when every symbol it uses is mapped; type elaboration still needs Lean, so this is an upper bound on evaluable tests):

| Share of a cell's tests mappable | Cells |
|---|---:|
| all | 3,129 |
| (75%, 100%) | 32 |
| (50%, 75%] | 368 |
| (25%, 50%] | 31 |
| (0%, 25%] | 12 |
| none | 1,054 |

Test-cells: 40,786 of 55,967 mappable (0.729). Deciding steps over symbol mappings: version 2 static 1: 4,823, 2a: 882, 2b: 1,392 (7,097 mapped; 317 symbols need the probe; 2,381 `no_match`; 85 `gold_signature_unknown`); version 1 recorded 1: 5,075, 2: 693, 3: 1,532, 4: 387 (7,687). Name affinity (2b) resolves statically most of what version 1 sent to the probe.

Gold-side lexer check: 90/896 gold files contain `?`/`!` identifiers (Mathlib lemma names, `Array.set!`, `s!`), 0 gold implementation symbols and 0 hidden-test symbol tokens are affected, 5 tests carry a `key?` named argument and 1 a `.get?` projection that re-point identically; the frozen version-1 suite is reused unchanged (DESIGN.md § 5).

### Per system

| System | Compiling with tests | V1 all / any mapped | V2 all | V2 partial | V2 probe | V2 none | Changed entry point | Newly all | V1 all → not all (probe) | Helper excluded | Result / argument type mismatch | Zero self-tests |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 809 | 210 / 247 | 199 | 26 | 11 | 573 | 1 | 0 | 11 (11) | 7 | 13 / 16 | 552 |
| claude-opus-5-max | 428 | 405 / 408 | 336 | 3 | 59 | 30 | 49 | 3 | 72 (59) | 29 | 19 / 23 | 0 |
| claude_code | 865 | 788 / 823 | 636 | 33 | 114 | 82 | 113 | 1 | 153 (112) | 16 | 59 / 70 | 0 |
| codex | 881 | 683 / 837 | 662 | 111 | 22 | 86 | 87 | 3 | 24 (22) | 59 | 65 / 65 | 0 |
| gemini-3.1-pro-high | 50 | 46 / 47 | 41 | 1 | 0 | 8 | 12 | 0 | 5 (0) | 1 | 5 / 4 | 0 |
| gpt-5.6-luna-high | 145 | 117 / 138 | 110 | 14 | 6 | 15 | 19 | 0 | 7 (6) | 31 | 6 / 11 | 0 |
| gpt-5.6-sol-high | 345 | 281 / 339 | 274 | 35 | 7 | 29 | 44 | 0 | 7 (7) | 95 | 15 / 20 | 0 |
| gpt-6-astra-high | 459 | 381 / 448 | 352 | 47 | 20 | 40 | 57 | 0 | 29 (20) | 91 | 65 / 32 | 0 |
| gpt-6-luna-high | 126 | 113 / 124 | 103 | 6 | 8 | 9 | 8 | 0 | 10 (8) | 32 | 5 / 6 | 0 |
| leanstral | 517 | 419 / 499 | 415 | 42 | 5 | 55 | 4 | 0 | 4 (4) | 3 | 19 / 19 | 60 |
| qwen3.6-27b-thinking | 1 | 1 / 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 (0) | 0 | 1 / 0 | 0 |
| **all** | **4,626** | **3,444 / 3,911** | **3,129** | **318** | **252** | **927** | **394** | **7** | **322 (249)** | **364** | **272 / 266** | **612** |

Reading: the entry-point changes concentrate in Claude Code (113), Codex (87), GPT-6 Astra (57), Claude Opus 5 (49) and GPT-5.6 Sol (44), the systems whose files define specification helpers next to the implementation; the 59 Opus cells now waiting on the probe are the same files whose helpers version 1 selected. Leanstral and baseline barely move (4 and 1 changed), consistent with their files having few definitions. These are mapping counts: p-val=n/a, deterministic over the fixed cells.

## What is not here, on purpose

No version-2 hidden pass/fail, pass rate, `hidden_all_pass`, P1, P2, P3 or G-A value exists. The protocol is locked ([PROTOCOL.md](PROTOCOL.md)) and the forecast frozen (`forecasts/e12_v2_forecast.json`) after this census and before any evaluation. Emily's run ([cc.md](cc.md)) produces the outcomes; this page is then extended below this line without changing the census above.

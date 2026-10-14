# Experiment 12 version 2 design — the corrected prospective hidden-test adapter

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/DESIGN.md>

**TLDR:** Version 1 of the hidden gold-reference test adapter had three defects found during its post-lock inspection: an identifier lexer that drops Lean's `?` and `!` suffixes (so `canFree` and `canFree?` collide), an entry-point rule that fell back to reference counts and picked precondition/postcondition helpers, and a per-cell "all tests pass" outcome that counted partial type applicability as failure. Version 2 fixes all three prospectively in `scripts/adapter_v2.py`: a Lean-faithful lexer, an explicit entry-point priority order (name and arity, then unique signature-compatible non-helper, then name affinity, then the Amendment A2 agreement probe), and per-test applicability bookkeeping. Version-1 files are never edited; version 2 imports its frozen helpers read-only. The frozen version-1 hidden-test suite is reused unchanged because the census shows no gold symbol is affected.

## 1. What version 1 got wrong (from `results.md`, "Inspected disagreements")

| Defect | Mechanism in version 1 | Effect |
|---|---|---|
| D1 lexer | `IDENT = [A-Za-z_\u0080-￿][\w'.]*` has no `?`/`!`. `def canFree? …` is parsed as a second definition named `canFree` with header `? (…) : Option Bool`. | Two same-name definitions defeat the step-1 name match (`len(matches) != 1`) and zero the step-4 reference counts (a token matching two definitions counts for neither). 5 of the 10 inspected high-score failures (hazard pointer, LWW pick-left, interrupt route, bump alloc, power transition). |
| D2 helper selection | With the name match defeated, step 2 collects every definition of type `Int → Bool`; the candidates disagree, so step 4 picks the definition most referenced by the candidate's own examples. Specification helpers (`preCondition`, `postCheck`, `PostB`, `preCondB`) are referenced by many examples. | 6 of 10 high-score failures mapped to a helper. |
| D3 partial applicability | `hidden_all_pass` required every extracted test to be evaluable and true. A test whose literals do not elaborate at the candidate's type (`Option Int`, `Except String Int`, `List PyVal`) is `unknown` and the cell counts as failing. | 4 of 10 high-score failures had no evaluated test false. |
| F4 (feature) | All 10 low-score successes had IC_tests = 0 with no `example`/`#eval` declarations. | Not a defect: SCSC penalizes missing self-tests. Version 2 records `n_examples` and `n_eval_commands` per candidate so this is explicit. |

## 2. Lexer grammar (`adapter_v2.IDENT`)

A Lean 4 identifier is one or more parts joined by `.`:

```
ident     := part ('.' (part | digits))*          -- trailing digits are positional projections, p.1
part      := '«' [^»]* '»'                        -- french quotes: any characters
           | start rest*                          -- plain part
           | '_' rest+                            -- a bare `_` is a hole, never an identifier
start     := [A-Za-z] | letterlike                -- letterlike = Greek except λ Π Σ, Coptic, U+2100–214F, math script U+1D49C–1D59F
rest      := [A-Za-z0-9_'!?] | letterlike | subscript   -- subscript = U+2080–2089, U+2090–209C, U+1D62–1D6A
```

Consequences: `canFree?`, `xs.get!`, `a?b`, `«weird name».run`, `x₁`, `α` lex as Lean lexes them; `⟨`, `≠`, `∧` no longer start an identifier (version 1 lexed `⟨some` as one token); `f x != y` lexes `x` then `!=`. Namespaces: `normalized(name)` is the last part, unquoted, lowercased, underscores removed (the version-1 rule on the corrected parts).

`declarations()` is the version-1 walk (same `COMMAND` regex, comment stripper and `header_end`) with the corrected lexer, and additionally returns `n_examples` and `n_eval_commands`. `signature()` is the version-1 reader with three changes: implicit `{}`/`[]`/`⦃⦄` binders are skipped and flagged (`has_implicit`) instead of making the signature unknown; binder names may carry `!`, `?` and subscripts; it returns a dictionary with `args`, `result`, `arity`. Numeric generalization (`Nat`, `Int`, `UInt*` → `NUM`) is unchanged.

## 3. Entry-point selection: explicit priority order

For each gold symbol `g` with signature `σ(g)` and the candidate's definitions `D`:

| Step | Rule | Lean needed |
|---|---|---|
| 1 | **Same normalized name.** Among same-name definitions prefer the exact full name, then equal explicit arity, then a compatible signature, then file order. A same-name definition whose explicit arity differs from the gold's is **not** the entry point: fall through. Result or argument type mismatches do **not** block step 1 (the gold's `myAdd` maps to the candidate's `myAdd : Int → Int → Except String Int`); they are recorded as `result_type_compatible` / `argument_types_compatible = False` so partial applicability is visible before any test runs. | no |
| 2 | **Signature-compatible set** `S = {d : σ(d) = σ(g)}` after numeric generalization. **Helper exclusion:** remove every `d` whose basename matches the helper rule unless `S` would become empty. Helper rule: basename starts with `pre`/`post` followed by end-of-name, an upper-case letter, `_`, a digit, `cond`, `check` or `B`; or its normalized basename ends with `condition`, `cond`, `check`, `prop`, `spec` or `harness`. (`preCondition`, `PostB`, `postCheck`, `Pre`, `PreCrossCheckB`, `spec_prop`, `greatestCheck` are helpers; `prefixSum`, `predict`, `postpone`, `gate`, `pickLeftImp` are not.) | no |
| 2a | `|S| = 1` → map. | no |
| 2b | **Name affinity** (as amended by PROTOCOL § 8, V2-A1). A member is affine when its normalized basename (≥ 3 characters) is a **suffix of the gold basename at a word boundary** (`canFree` in `MyHazardPointerCanFree`, `median_low` in `benchmark_median_low`), after stripping the gold twin suffix `Imp`/`Imperative`; prefixes and inner pieces (`escapeHtml` in `escapeHtmlImp`, `safeX` in `unsafeX`, `absDiff` in `quadAbsDiffPlusThree`) are not. Exactly one affine member decides only if no other member of `S` is referenced strictly more often by the candidate's own examples and theorems; otherwise the cell goes to the probe with the full `S` (reason `affine_member_out_referenced`). Several affine members narrow `S` to them. | no |
| 3 | **Agreement probe** (Amendment A2.1 step 3, unchanged): evaluate every member of `S` on every argument tuple the hidden tests apply to `g`, comparing members with each other and never with expected values. All agree → the member most referenced by the candidate's own examples (corrected lexer), ties by file order. | yes |
| 4 | Members disagree or the probe is undecidable → most referenced by examples, then theorems; a remaining tie is `not_applicable` with reason `ambiguous_disagreeing` (A2.1 step 4, unchanged, with helpers already excluded and the corrected lexer counting references). | yes |

Every mapping records the deciding step, the candidate set, the helpers excluded, the type-compatibility flags and (for steps 3–4) the probe receipt. Steps 1–2b need no Lean, which is what the zero-call census exercises; steps 3–4 are only reached by the cells the census reports as `needs_probe`.

Properties worth stating: the gold tests' expected values never enter any decision (as in A2); a helper can only be chosen when it is the sole signature-compatible definition; a same-name wrapper of different arity cannot shadow the entry point; and the `?`/`!` wrappers (`canFree?`, `myInterruptRoute?`) are distinct definitions with `Option` results, so they are neither name matches nor members of `S` for a `Bool`-valued gold symbol.

Checked against the 20 inspected rows (fixtures in `fixtures/disagreement_skeletons_e12v2.json`, built from the candidates' declaration names and headers only; tests in `tests/test_e12_adapter_v2.py`):

| Inspected row (version-1 category) | Version-1 mapping | Version-2 mapping and step |
|---|---|---|
| hazard pointer (helper) | `preCondition` | `canFree`, step 2b (affinity; `preCondition`, `post_bool` excluded) |
| LWW pick-left, Opus (helper) | `preCondition` | `pickLeft`, step 2b; the `Imp` twin narrows to {`pickLeft`, `pickLeftImp`} and goes to the probe |
| interrupt route, bump alloc, power transition (helper) | `postCheck`, `preCondition`, `preCondB` | the same-name core, step 1 (collision removed) |
| dose interval (helper) | `PostB` | `PostB`, `preCondB`, `PreCrossCheckB` excluded; {`gate`, six `*IffB`/`*B` checks} go to the probe; if they disagree and no example references them, the cell is **missing**, not a helper |
| myadd, myminimum, filter_integers, http parse (partial applicability) | name match | the same name match, step 1, with `result_type_compatible` or `argument_types_compatible = False` recorded; per-test reporting replaces the all-or-nothing outcome |
| 10 Leanstral low-score successes | steps 1–2 | identical mappings, steps 1/2a; `n_examples = 0` recorded |

## 4. Per-test applicability (replaces the per-cell `unknown` collapse)

Each hidden test of a cell gets exactly one status: `unmapped` (a symbol it uses has no mapping), `type_unknown` (mapped, but the bridge line produced no `true`/`false`, i.e. a literal did not elaborate at the candidate's type), `pass` or `fail`. Per cell (`adapter_v2.cell_outcome`):

- `n_tests`, `n_mapped`, `n_evaluable`, `n_pass`, `n_unmapped`, `n_type_unknown`;
- `applicable` = `n_evaluable ≥ 1` (version 1's definition, kept for comparison);
- `fully_applicable` = `n_evaluable = n_tests`;
- `hidden_all_pass` = every test evaluable and true, defined **only** for fully applicable cells; otherwise `None` (missing), never 0;
- `hidden_all_evaluable_pass` = every evaluable test true (sensitivity on applicable cells);
- `hidden_pass_rate` = `n_pass / n_evaluable`.

A test that cannot be evaluated is therefore reported, bounded and excluded, never counted as a failure of the candidate. The bridge format (`E12_TEST_i=true|false` per line) is unchanged so the version-1 runtime parses it.

## 5. Hidden-test suite: reuse the frozen version-1 extraction

The census checked the gold side of defect D1: 90/896 gold files contain `?`/`!` identifiers, all in proof terms and Mathlib lemma names (`List.getElem?_map`, `Array.set!`, `s!` interpolation); **0** gold implementation symbols and **0** hidden-test symbol tokens carry a suffix; 5 tests pass a `key?` named argument and 1 projects `.get?`, which re-point identically under both lexers. The 587 other tokenization differences are version 1 lexing `⟨`, `≠`, `∧` as identifiers, which never matched a definition. Version 2 therefore reuses `expt_v1/results/hidden_tests_manifest.json` (SHA-256 `f23f9956…`), 10,534 tests on 882 tasks, unchanged.

## 6. Expected movement relative to version 1 (reasoning; the frozen numbers are in `forecasts/`)

Version 1: applicability 3,224/4,674 = 0.690; P1 Spearman 0.891; P2 area 0.640; P3 Spearman 0.151; 200 failing among 3,199 compiling applicable cells.

- **Applicability (≥ 1 evaluable test).** The static census maps at least one test in 3,572/4,626 compiling cells with tests (0.772) before any probe, against 3,911 cells with any symbol mapped in version 1; the probe can add up to 252 cells. Type-unknown attrition then removes some. Expected: unchanged to slightly higher.
- **Fully applicable share** (new primary cohort for P2/P3). Static upper bound 3,129/4,626 = 0.676 before probes (≤ 3,381 = 0.731 after). Cells with a recorded result or argument type mismatch (272 and 266) are the likely losses. Expected: 0.55–0.70.
- **P1** moves little: system ranks are dominated by compile rate and the helper/partial cases concentrate in two systems.
- **P2 rises.** The inspected false failures were all at SCSC = 1.0 (Claude Opus 5 max); removing helper mappings (pre-amendment census: 394 cells change entry point, 364 cells had a helper excluded; after V2-A1 the frozen census records 379 and 364) and moving partial cells to missing removes high-score "failures". Expected area above 0.640.
- **P3 rises** for the same reason, from 0.151.
- **Missingness rises**: cells the probe cannot decide (dose interval pattern) become missing instead of helper-mapped failures; the bounds report them.

## 6b. Static controls that already ran (zero Lean; `results/static_controls_v2.json`)

Over all 882 gold suites: gold as its own candidate maps every symbol to itself at step 1 (882/882); renamed gold (every tested symbol renamed by the version-1 `renamed_control`) is never mapped to a wrong symbol by the static stage (0/882 after amendment V2-A1; 7/882 before it, which is why the amendment exists), with 855 tasks deferred to the probe, 24 resolved correctly and 3 statically not applicable. The Lean controls C1–C4 remain Emily's first run.

## 7. What version 2 does not fix (stated before the run)

- Candidates whose entry point returns `Option`/`Except` of the gold's result type (the `doseIntervalOk : Option Bool` pattern) stay missing or partial: unwrapping is still forbidden (PROTOCOL § 3).
- `atom_at` (argument extraction for the probe) is the frozen version-1 helper and cuts an argument such as `foo?` at `?`; the probe then reports `argument_extraction_unknown` and step 4 applies. No hidden-test symbol token is affected (§ 5).
- The agreement probe still needs Lean and the candidates' own examples; cells with no examples and disagreeing twins remain `ambiguous_disagreeing`.
- Nothing here changes IC_tests, IC_proofs, FSC or SCSC.

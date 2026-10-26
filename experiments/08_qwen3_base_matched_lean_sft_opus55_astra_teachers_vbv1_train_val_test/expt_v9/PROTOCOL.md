# Existing-proof preference and flagged-proof reconciliation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v9/PROTOCOL.md

**TLDR:** Revisit all12,823Workbook statements and500tiny examples under the user's new preference for explicit proof steps. Use existing alternatives for identical statements; Sol reviews questionable proofs and verifies selected replacements.

Frozen:10-19-2026 04:44 PDT, before version9selection or model dispatch. This is a new setup after the user changed proof-selection preferences; version8outputs remain preserved.

## Selection and annotation

Inspect every saved alternative for each original statement. Prefer a supplied proof without `exact?`, `apply?`, `simp`/`simpa`families, `omega`, `aesop`, `linarith`/`nlinarith`, `ring`families, `norm_num`, `decide`/`native_decide`, `tauto`, `positivity`, `field_simp`, `fun_prop`, `exact_mod_cast`, or `norm_cast`. Ordinary `exact`, `apply`, `rw`, `rfl`, constructors, cases, induction, `intro`, `have` and `calc` remain eligible. Retain an already qualifying original; otherwise choose the first qualifying saved alternative in source order. If none qualifies, retain the original and record that fact. This preference is not a validity certificate, and the absence of automation does not establish correctness.

For the500tiny tasks, match the entire file outside theorem/example proof bodies, including all implementations and theorem/test statements, before considering a saved proof alternative. Reuse unchanged annotations; regenerate explanations only when the selected script changes or an explanation needs correction. Every resulting file retains its short top-of-file proof sketch and focused comments. All original source/annotation artifacts remain immutable.

## Sol review and verification

The user explicitly requested Sol for all questionable cases (the first reported69plus later flags). Use `gpt-6.1-sol`, high reasoning, full-access Codex CLI on skampere1, same previously explicitly authorized lab credential, separate owned workspaces and named tmux sessions. Sol distinguishes a proof failure, a formal-statement/informal-intent mismatch, a vacuous statement and a false annotation alarm. `exact?` is a supported proof-search tactic, not automatically an incomplete proof. Select only supplied proof alternatives for the identical formal statement; do not invent a corrected theorem or new proof.

Only flagged/replacement proofs receive targeted Lean/kernel checks in this phase; unchanged comment-only files are not recompiled. Preserve the pinned Lean4.22/frozen kernel inspector and allowed axioms. Bound verification to four distinct candidates per flagged statement,15seconds per compiler operation and24global compiler slots. Run at most two CLI attempts per review case. A selected alternative must pass actual checks before it is called verified; unresolved cases and mismatched/vacuous statements stay excluded. Changed tiny proofs must pass the same kernel gate, with unchanged implementation/stated-tests established mechanically. Reuse original differential receipts only for the unchanged implementation.

Target64parallel Sol review workers and up to100Terra/medium annotation workers. Record native attempts, costs, exact source/proof indices, hashes, decisions and failed/missing cases. Expected additional annotation/review cost is uncertain, approximately$75–200depending on the number of changed/flagged cases; no provider invoice is inferred from token estimates. No new model training, validation-derived examples or protected task data go to these workers. Existing full-set outcomes and failed forecasts are retained.

## Inventory amendment,10-19-2026 04:52PDT

The user asked whether the rule covered automation beyond their examples and asked about `linsolve`. Scanning all223,156provided Workbook scripts found no `linsolve`. The line-leading token inventory also identified `solve_by_elim`, `apply_rules`, `simp_rw`, `ring1`and`abel`; add these and related broad solver/search names (`grind`, `polyrith`, `finish`, `itauto`, `simp_arith`, `norm_num!`, `linarith!`, `nlinarith!`, `aesop_cat`) to the preference. The inventory is a lexical corpus audit, not a claim to enumerate every possible Lean/custom tactic. Keep explicit `linear_combination` with supplied coefficients, basic `exact`/`rw`/`rfl` and structural proof steps. `linarith` remains a conditional avoidance preference; no categorical claim about its training utility is established.

Preserve the initial selection and native case inputs. Queue additional affected cases only where a stricter qualifying supplied alternative exists; any recheck retains the original two-CLI/four-compiler-candidate bounds and archives the initial decision/input. A running healthy worker finishes its case before a policy continuation. New selected-script annotation flags also enter the Sol queue, with an append-only dispatch amendment. These are authorized reconciliation steps, not new proof generation.

## Routing amendment,10-19-2026 05:01PDT

The user questioned broad Sol use and asked whether Terra could do the work. The coordinator had expanded the original69Sol cases to every later annotation/policy flag, which was more strong-model work than necessary. Preserve completed Sol results and let already-running cases finish. Reconstructed the exact first69flags from the first13completed baseline batches; no original69case was still pending. Under the shared queue lock, route357remaining unstarted routine cases to `TERRA_PENDING`.

Use64Terra/medium workers on separate owned worktrees/profiles for routine interpretation, supplied-alternative selection, targeted kernel checks and comments. Sol/high receives only a specific mathematical/formalization ambiguity escalated by Terra, or an already-running Sol case. A timeout alone does not justify escalation. Total native bounds remain two CLI attempts and four checked candidate indices per case across both models. Every attempt records its actual model/effort and cost rates; a changed route is never presented as a Sol result. This changes future curation routing, without resampling completed work or launching training. Current listed token rates do not establish a Terra cost advantage over Sol; the change is about proportionate model use.

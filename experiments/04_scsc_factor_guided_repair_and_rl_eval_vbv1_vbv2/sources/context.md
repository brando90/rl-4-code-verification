# Sources and interpretation of Azalia’s thesis suggestion

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/sources/context.md>

**TLDR:** The supplied email names three practical applications. Retrieved thesis material already argues for diagnostic-guided decisions and independent outcomes; local repository evidence identifies existing experiments and measurement limitations.

## Primary input and provenance

The user supplied the email thread in this chat on 10-05-2026. [email_supplied.md](email_supplied.md) preserves the supplied thread. The quoted outgoing email is dated 09-04-2026; Azalia's reply date is not supplied. No inbox retrieval or email delivery was performed.

The user's additional interpretation is preserved here as a summary, not a quotation: SCSC itself is the downstream evaluation; a correlation with pass@1 needs an independently defined success predicate; reference tests and reference specification obligations may supply that predicate; exact specification equivalence may be too difficult, and useful imperfect diagnostics are acceptable.

## Retrieved thesis context

- [Final overview shown to Azalia, 09-04-2026](https://docs.google.com/presentation/d/1JuCWK8Z75Cikk7MNz6XaOPCrJCaYi-WhoCrkkTyqjYc/edit): diagnostic evaluation, directional semantic specification coverage, and a thesis organized around data characterization, selection/training, evaluation and judge validation.
- [Thesis plan for Sanmi, 09-05-2026](https://docs.google.com/presentation/d/1GCuU624G2NoyOE1E9h-PheCR9j6SQaIKHColOs0W1d4/edit), slides 1, 4, 6 and 7: useful diagnostics change decisions; compare against aggregate-score choices; use independent held-out outcomes. Its notes predate access to Azalia's confirming reply, so they are an earlier interpretation, not evidence of her exact intent.
- “Brando Weekly Update STAIR lab Sanmi,” newest dated section retrieved: 09-29-2026, Varun. Relevant topics: environment pool size/diversity/horizon/reward density; separate verifier false-positive and false-negative rates; corrupt training reward only and evaluate against trusted outcomes. The private document link is intentionally omitted, and unrelated notes were not copied. These are plans, not verified results.

These Google Drive sources were read through the connected account by the short research lookup. Neither the documents nor their sharing settings were changed. Historical experimental numbers in the decks are not adopted as current results.

## Repository evidence

- This repository `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md`, `src/rl4cv/experience.py`, and `src/rl4cv/veribench/summarize.py` supply the contamination, scoring, signal-density and aggregation contracts.
- `/Users/brandomiranda/rl-env-scaling` at `c75755c07481c335e87e3ce3455132d6b4892390` is planning-only local main. `docs/experimental_philosophy.md` motivates controlled interventions. The training branch pin in this project's dependency lock is `7118b86f84e8ce0d8607b09c9826a4a6ffbbd015`, provisional under decision D-105.
- VeriBench inspected at `25fbb2e6733e87d67eb6b9be40e93cd11e468b27`; the checkout has unrelated ongoing work, left untouched. The audit's actual files have individual hashes; a checkout revision alone does not certify file bytes.
- `paper_latex/TMLR_2026_VeriBench/04_eval_metric.tex` and `98_3_appendix_scsc.tex`: direct cross-application was removed because interface variation caused false negatives. The paper's geometric mean of dataset factor means differs from this repository's averaging of per-artifact geometric means. Reconcile before a new score experiment; do not reinterpret old results silently.
- `75_J1_validating_formal_spec_judge_train_val_test/prover_diagnostics/README.md`: historical ordinary Lean replay is not strict kernel-only coverage; transitive `native_decide` dependencies remain a caveat. Reuse as feasibility evidence only.
- `103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/results/summary.json` and its manifest: retained current factor rows, no independently measured reference pass@1. Input snapshot availability is not current remote execution status.

## Limited literature context

[Chen et al., Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374) motivates specifying the acceptance test behind pass@k. [Lightman et al., Let’s Verify Step by Step](https://arxiv.org/abs/2305.20050) distinguishes outcome from process supervision. These motivate controls; they do not establish that VeriBench's artifact components are process rewards or that factor feedback will improve code verification. No exhaustive novelty claim is made.

## Follow-up draft to Azalia — not sent

Hi Professor Mirhoseini,

I think I understand the practical direction better now. In VeriBench, the Smooth Conjunctive Score for Code verification is itself the evaluation outcome: it combines test consistency, proof consistency, and specification coverage.

Would a good test of your suggestion be to compare a model that sees only the aggregate score with one that sees the three components and uses them to choose what to repair, under the same total budget? I would measure both VeriBench improvement and success on fixed reference tests and specification obligations, so we can check that the improvement reflects stronger verification.

For the environment-scaling work with Varun, the analogous test would use the diagnostics to choose training environments or rewards, then evaluate the resulting model on held-out tasks. Is that the kind of practical contribution you had in mind, or were you also thinking of transfer to a separate downstream benchmark?

Thank you,
Brando

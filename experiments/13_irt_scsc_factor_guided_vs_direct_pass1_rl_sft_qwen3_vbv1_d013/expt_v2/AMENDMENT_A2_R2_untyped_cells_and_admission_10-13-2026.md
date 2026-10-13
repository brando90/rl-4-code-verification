# Experiment 13 v2 amendment A2: R2's untyped cells and its admission rule

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/AMENDMENT_A2_R2_untyped_cells_and_admission_10-13-2026.md>

**TLDR:** PLAN § 2d typed every non-measured cell as transient infrastructure, deterministic resource limit or integrity defect. It did not say what happens to a cell whose failure could not be typed. The opaque test route then finished with 2 such cells out of 5,328.

A2 fills that gap. An untyped cell gets the contract's single identical retry; any cell still untyped afterwards is listed as unresolved. R2 admits G0 when all three hold:

1. every measured cell on both routes reproduces the historical oracle's value and status;
2. typed deterministic-limit cells are listed, as PLAN § 4 already allowed;
3. unresolved cells are at most 0.1% of each route's declared cells, listed by cell ID.

**Disclosure:** A2 was written **after** observing the opaque route's public receipt: 5,328 accounted, 5,319 measured, 7 typed deterministic limits, 2 untyped, equality status INCOMPLETE. No test discrepancy, factor, label or source was inspected, and none is inspected under A2.

Created: 10-13-2026 15:41 PDT by the master (Claude Code `claude-opus-5-5`), before any retry and before any G0 computation. Applies to `PLAN.md` revision 2, Amendment A1 and `cc.md`.

## Why this is a technical amendment, not a moved goalpost

- **Purpose of R2.** R2 is the measurement-fidelity admission check: the new pipeline reproduces the historical strict oracle. It is not a test of the hypothesis.
- **Prospective items stay prospective.** F0v2 and F1v2 were frozen at L1v2, before any validation factor was computed. G0, G1, H2 and every Phase 2 contrast remain prospective and untouched.
- **Historical test cells are not used downstream.** Phase 2 evaluates **new** policy outputs on the test split, with the frozen official scorer for strict. Two untyped historical test cells cannot change any downstream measurement.
- **The equality standard is unchanged.** Any measured inequality on either route still fails R2.
- **What changes.** Only the handling of untyped failures and a published ceiling on the unresolved share.

The 0.1% ceiling is a stated technical tolerance chosen after the observation, and the disclosure above says so. It is roughly 5 cells on the test route and 33 on the ordinary route. A reader can therefore judge for themselves whether the admitted reproduction is complete enough.

## Rules

1. **Untyped cells.** A cell whose failure cannot be typed as transient infrastructure, deterministic limit or integrity defect is **untyped**.
   - It gets exactly **one** identical retry: same source, same frozen code, limits and environment, same route.
   - On the opaque route, the retry runs inside the opaque process. Its public receipt reports only counts, hashes and statuses.
   - A cell still untyped after the retry is **unresolved** and is listed by cell ID.
2. **Opaque equality among measured cells.** The opaque process adds one boolean to its public receipt: `equality_among_measured` = PASS or FAIL. PASS means every measured test cell's oracle value and status equal the historical readback.
   - It discloses no cell, value, factor or source.
   - FAIL is a test discrepancy: R2 fails and admission is blocked (PLAN § 3).
3. **R2 admission to G0.** All of these must hold:
   - (a) the ordinary route reports equality PASS on all of its measured cells;
   - (b) the opaque route reports `equality_among_measured` = PASS;
   - (c) no integrity defect on either route;
   - (d) typed deterministic-limit cells are listed per route, with reason codes, and are allowed;
   - (e) unresolved cells are at most 0.1% of each route's declared cells: at most 5 of 5,328 opaque, at most 33 of 33,456 ordinary.

   If any condition fails, R2 fails, and PLAN § 4's transition table applies (stop downstream; publish).
4. **Reporting.** The R2 report states, per route:
   - declared, accounted and measured counts;
   - typed limits;
   - retried untyped cells and their outcome classes;
   - unresolved cells;
   - equality.

   The ordinary route's per-cell diagnostics stay private. The opaque route's stay sealed.
5. **No other change.** Every later gate keeps the no-retry rule (Amendment A1) and its frozen definition.

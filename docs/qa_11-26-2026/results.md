# rl-4-code-verification: independent QA of main at a47acee9 by two Claude Opus 5.5 reviewers (11-26-2026)

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/docs/qa_11-26-2026/results.md

**TLDR:** Two independent, read-only Claude Opus 5.5 reviewers checked main at a47acee9: one for repository integrity, one by re-running the zero-model-call analyses from committed inputs. Branches and merges are sound, six experiments reproduce from committed inputs, three reproduce in part (their full reruns need 3 to 63 CPU-hours), and the test suite has no genuine failure; all five non-passes are sandbox limits. Six stale index rows, an unindexed folder, an unportable stop rule and a scope-too-strong sentence were found; the verified ones are fixed or registered in the commit that adds this file.

**Asked by:** Brando Miranda, 11-26-2026 10:48 PT: "mega qa opus 5.5 go!" **Done by:** a Claude Sonnet 5.5 session that coordinated two read-only Claude Opus 5.5 subagents (model alias `opus`) on a pristine checkout of main. Reports: [integrity](reports/QA_INTEGRITY_opus55.md) and [numbers](reports/QA_NUMBERS_opus55.md). Neither reviewer wrote to the repository, made a model call or used a GPU.

## Bottom line

1. **Branches.** All 22 non-main remote branches are contained in main (GitHub compare API, `ahead_by` 0 for each). Both D-112 merges (06389efc, 0656edc3) have the stated parents and dropped nothing. No open pull requests. Nothing was merged or deleted on 11-26-2026.
2. **Numbers.** Reproduced from committed inputs: experiment 15 (verdict NO ADVANTAGE, −0.0066 [−0.0169, +0.0038]), 07 (phase A Spearman 0.985 [0.979, 0.987] and 0.736 [0.507, 0.801]; the 11-25-2026 follow-ups), 17 (1.372 against 3.468 and 1.790 pp), 16 (arithmetic only; regret 0.287 pp), 25 stage 0 and 18c (byte-identical). Partial: 14 (matrix verified, tables byte-identical, full fit about 50 CPU-hours), 10 v2 (about 3.4 CPU-hours) and 19 (pins and tables verified, main run about 63 CPU-hours).
3. **Tests.** 1,402 passed, 4 failed, 66 skipped and 1 collection error before the fix. The collection error (`tests/test_e20_loss.py` imports torch without a skip) is fixed. The four failures need the pinned `external/` checkouts, a sibling `ultimate-utils` repository, or a host kernel that returns a permission error for a zombie's `/proc` entry; they are environment limits, not repository defects.
4. **Index.** Six rows of `experiments/README.md` contradicted their own experiment files (08, 13, 18, 20, 25, 25b); all six are corrected, and the unindexed `25_exp20_smoke…` folder and the unlinked 21 to 24 row are indexed.

## What was done with every finding

1. **Repository settings finding (Critical).** Owner-only; delivered to Brando directly and withheld from this public file.
2. **`docs/anarres_11-25-2026/` (High).** Not edited: another agent is actively changing it. An index is added in [anarres_11-26-2026/README.md](../anarres_11-26-2026/README.md), which also records that `prB-v4.bundle` is superseded. Whether the folder stays is Brando's call.
3. **Six contradictory index rows (High).** Fixed after checking each claim against its source file. Two of the reviewer's proposed corrections were adjusted: experiment 18c finished 11-25-2026 (not 11-26), and the row 20 note says the gate mismatch was fixed on the fp16 route in rows 21 to 24 instead of calling the comparison blocked.
4. **Six files only on two superseded branches (Medium).** The branches stay. Tags could not be pushed from an agent session; the exact commands with the branch tips are in [NEXT_STEPS_11-26-2026.md](../NEXT_STEPS_11-26-2026.md), section 5.
5. **Three folders numbered 25 (Medium).** All three are indexed; none is renamed.
6. **Low findings.** "below" corrected to "above"; the experiment 13 README gained a dated status sentence; the stale experiment 16 toy TLDR, the experiment 08 version 6 status and the 11-25-2026 test-count line are registered for their owners in NEXT_STEPS section 3. The privacy-rule scope finding is an owner decision.
7. **Experiment 14 stop rule (numbers).** Its exact-equality check against the experiment 07 H2 replay fails in the sixth decimal on numpy 2.5.3 (−0.012140 against −0.012139). Registered; the locked protocol is not edited.
8. **Experiment 10 v2 sentence (numbers).** "Within 0.0035" holds at q = 0.50 only; a dated scope note is appended to the v2 results.

## Limits of this QA

1. Both reviewers worked in a 2-CPU sandbox without torch, without `external/veribench` and without cluster access, so nothing that needs a GPU, Lean on the cluster or private data was rerun.
2. Experiments 16 and 17 use hard-coded paper values; their reproduction checks arithmetic, not measurements.
3. This QA used Claude Opus 5.5. It is separate from the 11-25-2026 QA by a Codex GPT-6 Astra reviewer ([results](../qa_11-25-2026/results.md)).

**TLDR-end:** [rl4cv: QA 11-26-2026] Branches and numbers hold up; the verified index and test fixes are in, and the unfinished items are registered in NEXT_STEPS_11-26-2026.md.

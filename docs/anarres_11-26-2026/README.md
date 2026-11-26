# Anarres hand-over, 11-26-2026: pull requests A and B on today's upstream main

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/docs/anarres_11-26-2026/README.md

**TLDR:** Pull request A (#66, Lean-first formal contracts) and pull request B (VeriBench measurements study page), both on Brando's fork, merge into today's upstream main (`63e3402`) with zero conflicts, separately, together and with the new open pull request #105, and pass lint, hygiene, prose, schemas, Rust format, the formal-contract tests and the study check. This session cannot push to the Anarres organization, so nothing was opened, pushed or sent; the two `gh pr create` commands are below. `prB-v4.bundle` in `docs/anarres_11-25-2026/` is superseded by the fork branch.

## 1. What was checked on 11-26-2026

Base: `anarres-organization/anarres` main `63e3402` ("Separate surrogate inputs from protected labels (#108)"). Both pull requests were built on `d168e2a`; upstream has moved by eight commits since.

1. **Merge.** `git merge-tree --write-tree` of each branch onto `63e3402` reports no conflicts, for A, for B, and for A and B together. The only file changed by both a pull request and upstream is `tools/check_study_reproduction.py` (pull request B); it merged automatically and the study check passes on the merged tree.
2. **Pull request A** (`brando90/anarres` branch `formal-portable-contracts-pr1`, `402e26e`) merged onto `63e3402`: `make lint`, `make hygiene`, `make prose`, `make rust-format`, `cargo build -p anarres-cli`, `cargo test -p anarres-cli` (14 and 32 tests in two test binaries), the formal-contract Python tests, and `make study-check` (33 checks passed).
3. **Pull request B** (branch `veribench-rl4cv-study-page`, `31a9ca0`) merged onto `63e3402`: `make lint`, `make schemas`, `make hygiene`, `make prose` and `make study-check` (35 checks passed).
4. **A and B together** on `63e3402`: lint, schemas, hygiene (1,643 files), prose, Rust format, the formal-contract tests, and `make study-check` (35 checks passed). `make check` as a whole stops at its `test` target when run as root, on the two tests in item 6; every other target passes (`make lint`, `make rust-format`, `make rust-lint` with warnings denied, `make rust-test`, `make schemas`, `make hygiene`, `make prose`), run separately on the same tree.
5. **RFC number.** Pull request A adds RFC 0008. Upstream main ends at RFC 0006. Of the seven pull requests open on 11-26-2026 (#82, #83, #90, #95, #96, #97, #105), only #83 claims an RFC (0007, the robotics adapter); none claims 0008. The merge plan says 0007 and 0008 are both taken; as of 11-26-2026 only 0007 is claimed, and not yet merged, so landing pull request A first leaves a temporary gap at 0007.
6. **Test runs.** Run as root, `make test` on the combined tree (346 tests) has two failures: two upstream tests in `tests/integration/test_formal_verification_vero_task_boundary.py` assert that the container user is not `0:0`. They pass as a normal user (46 of 46 in that file), sit on upstream main, and neither pull request touches them. Run as a normal user (324 integration tests), four tests do not pass for sandbox reasons: two cannot execute `cargo`, which lives under `/root`, and two fail `git rev-parse` with "dubious ownership". All four pass in the root run, so no test fails in both configurations. One clean `make check` as your normal user on your own machine replaces this two-part result.
7. **New open pull request #105** (madanva, "Qualify public agentic coding selection evidence", 43 files, based on `760cebb8`) is agentic-coding evidence, not formal verification, but it edits top-level files (`Makefile`, `README.md`, three pages under `docs/`). Pull request A, pull request B and both together merge cleanly with its head `a089e72` (`git merge-tree`, 11-26-2026); the gates were not rerun on that combination.

## 2. What is not done

1. Nothing was pushed to, opened on or sent to the Anarres organization: this session has no push access there, and Brando's instruction was to prepare the work, not to open pull requests or message anyone. The draft Discord ping to Varun is in the 11-25-2026 hand-over and was not sent.
2. The code-verification issues #24, #25, #26, #27, #65 and #66 were re-read on 11-26-2026: all six are still open and none has a comment newer than the [11-25-2026 table](../anarres_11-25-2026/issues_table.md) (the latest are Srivatsava's, 11-25-2026 at 00:43 and 01:41 UTC). #65 still has Srivatsava as assignee; #66, which pull request A implements, still has no assignee and no comment. The table itself is not rewritten.
3. Steps 2 to 4 of the [merge plan](../anarres_11-25-2026/MERGE_PLAN_rl4cv_into_anarres_11-25-2026.md) are not started; step 2 waits for the review of pull request A.

## 3. Commands (from a machine that can reach the Anarres organization)

Run from a checkout of this repository, so the body files resolve. Pull request A first, then B, as the merge plan says; ping Varun once both are open.

1. Pull request A (issue #66):
   ```
   gh pr create --repo anarres-organization/anarres --base main --head brando90:formal-portable-contracts-pr1 \
     --title "Define portable formal contracts and route Vero qualification" \
     --body-file docs/anarres_11-25-2026/PR_A_body.md
   ```
2. Pull request B:
   ```
   gh pr create --repo anarres-organization/anarres --base main --head brando90:veribench-rl4cv-study-page \
     --title "Record VeriBench baseline, fine-tuning and reinforcement-learning measurements for the study" \
     --body-file docs/anarres_11-25-2026/PR_B_body.md
   ```

The titles are the first commit subjects of each branch; change them if Varun prefers another style.

## 4. Note on `docs/anarres_11-25-2026/`

1. `prB-v4.bundle` is stale: its head is `d6655dc`, while the fork branch is at `31a9ca0` with two later fix commits (`f1e3e1b`, `31a9ca0`). `prA-v4.bundle` (`402e26e`) matches the fork. Both bundles are relative to the Anarres commit `d168e2a`, which is not in this repository. Use the fork branches, not the bundles.
2. Fourteen documents in that folder lack the `Doc link` and `TLDR` header lines; another agent is still editing the folder, so they were left alone.
3. Whether the folder stays in this repository once the pull requests are open is Brando's call.

**TLDR-end:** [rl4cv: anarres hand-over 11-26-2026] Pull requests A and B merge cleanly onto upstream main and pass their gates; two commands open them, and only Brando can run them.

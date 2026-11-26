# Plan: merge rl-4-code-verification into Anarres (dated 2026-11-25)

Written by ub9sc (the assistant of Brando Miranda) on 2026-11-25, from a read of brando90/rl-4-code-verification at commit `139e8d9b` and anarres-organization/anarres main `d168e2a`. Step 1 is built and has passed review (below). Steps 2 to 4 are not started.

## Bottom line

- Varun's reply (Discord, Nov 25 2026, 11:05 AM): "Could definitely be worth integrating! I would tell your agent that has context about your rl-4-code-verification work to integrate it with the Anarres formal subproject in our style on a new branch and tell it to notify me when the PR is ready I'll review it".
- Step 1 is the first pull request: it puts the measured results into the existing study page `experiments/mathematics/veribench/`, in the study-record style of `experiments/mathematics/environment-utility/`. The branch is `veribench-rl4cv-study-page` on brando90/anarres. Nothing there changes a protocol or a frozen artifact.
- Anarres style for a study is: a README with sourced results, a compact records file with digests, a reproducer pinned to an immutable commit, an audit registered in `make study-check`, and no raw logs, checkpoints, credentials or machine paths in Git. Step 1 follows it.
- Pull requests stay small and are opened one at a time from Brando's fork.

## Steps

| Step | Pull request | Content | State |
| --- | --- | --- | --- |
| 1 | VeriBench measurements page | Measurements table for experiments 01, 05, 08, 09, 19 and 25 with scope, limits and evidence label; `results/records.json` (126 figures, 16 source files with digest, size, media type, license, producing experiment); extraction at the pin; audit with a negative test in `make study-check` | Built, reviewed by two independent AI reviewers, gates pass on a fresh clone |
| 2 | Package and tests | `src/rl4cv/` as a maintained package under `packages/` with its tests, including the exact reproduction of the frozen 14B forecast; a short RFC for the new package (number to confirm against open RFC pull requests; RFC 0007 and 0008 are taken by other open pull requests) | Not started. Wait for the formal-contracts pull request (Lean-first, #66) to be reviewed so the verifier interface is defined once |
| 3 | Data and artifact references | Candidate pools (FVAPPS, Vericoding, VERINA, synthetic) and contamination screens under `data/veribench/`, each with an artifact reference (URI, SHA-256, media type, size, license, producing run); nothing large in Git | Not started. Needs a license check of every dataset in `docs/DATASETS.md` |
| 4 | Compact results pages | One results page per finished experiment, each with inputs, hashes, a regeneration command, and harness and model named for every figure. Experiment 25 waits for its fourth smooth-reward seed; experiment 08 versions 2 and 3 wait for their runs | Not started |

## What fits Anarres style and what does not

| Anarres rule (AGENTS.md) | State in rl-4-code-verification | Action |
| --- | --- | --- |
| Reusable behavior goes in a package | `src/rl4cv/` (172 KB) | Step 2 |
| Source processing in `data/` | Candidate pools, contamination screens | Step 3 |
| Study-specific work in `experiments/<domain>/` | 25+ numbered experiments, 539 MB, run logs, checkpoints | Only compact, regenerable results and protocols move; raw logs, checkpoints and cluster operations stay out of Git |
| Never change a frozen protocol in place | Hash-frozen forecasts exist | Keep each frozen forecast byte-identical and add its hash to a manifest |
| Mutable aliases never claim-bearing inputs | `external/deps.lock.json` pins commits | Keep the pins; replace any branch or `latest` reference |
| No machine-specific paths or credentials | Cluster paths and job ids appear in experiment notes | Strip before the move; keep cluster operations in this repository |
| Writing standard, one defined term per concept | Internal names such as SCSC, FSC, rho-H | Define each once on the study page; `make check` runs the prose gate |
| Explicit development and prospective partitions | Experiments 08, 19 and 25 used the D-013 splits | Step 1 labels the evidence retrospective and says the prospective study must name its held-out partitions |
| Source qualification by an independent auditor | VeriBench comes from the repository owner's group | Step 1 says VeriBench is not yet qualified in Anarres and the results await independent qualification |

## Dependencies

- #66 (Lean-first formal contracts) is open as pull request A from the same fork. Step 2 waits for it.
- #24, #25 and #26 are blocked on a trainable open policy under the same measurement contract. A supervised warm-started checkpoint from this work, released with an artifact reference, can unblock them.
- RL experiments resumed Nov 25 2026 (Brando), so step 4 depends on those runs.

## Decisions only Brando can make

1. Which finished experiments are public enough to move (some hold unpublished judge results and a conference draft)? Step 1 uses only the VeriBench baseline, supervised fine-tuning, forecast and reinforcement-learning records that are already public in the external repository.
2. Whether to ask Varun for a named independent research maintainer for the results (the reviewer's suggestion, since the results come from the owner's group).
3. Send the draft Discord ping to Varun when both pull requests are open (draft in the hand-over; nothing was sent).

## Not checked

- The Anarres maintainers' view of this placement. No one was messaged.
- Licenses of the datasets in `docs/DATASETS.md`.
- Whether RFC numbers 0007 and 0008 are free when step 2 starts.

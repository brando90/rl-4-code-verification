## Summary

Integrates the measured results of the VeriBench environment-utility study (my repository, brando90/rl-4-code-verification) into the existing study page, in the study-record style of the mathematics study: a page with sourced results, a compact record file, and an audit that runs in `make study-check`. This follows Varun's suggestion to integrate it with the Anarres formal subproject in Anarres style on a new branch.

- `experiments/mathematics/veribench/README.md`: a "Measurements to date" table for experiments 01, 05, 08, 09, 19 and 25 (small open-model baseline, signal on Qwen3 Base, matched Lean fine-tuning, an IRT forecast, smooth versus strict reward GRPO, one failed implementation gate). Each row has its scope and limits and an evidence label. The page says that the measurements are retrospective development evidence, that they used the D-013 train and validation splits (and experiment 08 evaluated the test split once), that VeriBench is not yet qualified as a source in Anarres, and which follow-up runs are still open at the pin. The planned protocol is unchanged.
- `results/records.json`: 178 figures from 32 pinned source files (JSON, CSV, scripts and configs; each non-JSON figure is derived by a named function) at commit `139e8d9b47d44626035594c19d708d6b26a856cc` of the external repository. Each source file carries its SHA-256, size, media type, license (Apache-2.0) and producing experiment.
- `scripts/extract_records.py`: rebuilds the records from a checkout, reading each file with `git show` at the pin. `--check` compares with the released file.
- `scripts/audit_records.py`: builds each stated number and count from the records and fails when the page differs; fails when a link to the external repository leaves the pinned commit or a source file lacks its artifact reference. With `--source` it recomputes every digest and size at the pin.
- `scripts/test_audit_records.py`: a negative test that changes copies of the page and the records and requires the audit to fail. Both scripts are registered in `tools/check_study_reproduction.py`.

Only machine-written result files are inputs. Where the external results prose differs from the raw output, the raw output is used (the upper bound of the smooth-reward interval of experiment 25 is 40.14 in the raw file and 40.15 in its prose). The 533-of-896 namespace count and the 25 cells after the rewrite are now derived from pinned records. The Reproduce section lists the few statements that stay prose-only and that the audit does not tie to a record.

This is the first of a few small pull requests. Not included and planned separately: the `rl4cv` package with its tests, data and artifact references for the candidate pools, and one compact results page per finished experiment.

How this was made: AI coding agents prepared it on my behalf. Every number was read against its raw result file by an independent AI check, and two independent AI reviewers (Claude Opus 5.5 in Claude Code and GPT-6 Astra in Codex CLI) read the pull request; their findings are fixed in the second commit.

## Validation

- [x] `make check`: exit 0 on a fresh clone of the branch (tip `d6655dc`).
- [x] `make study-check`: all 34 checks passed on a fresh clone of that tip, including the two new ones.
- [x] `extract_records.py --check` and `audit_records.py --source` against a checkout of the pinned commit pass.
- [x] Schema compatibility considered: no schema changes.
- [x] No large artifacts, credentials, or machine-specific paths added (`records.json` is about 66 KB, hygiene check passes for 1,606 files; hygiene check passes).
- Not run: the experiments themselves. Nothing was re-run, only read.

## Scientific impact

Adds retrospective external measurements with their scope and limits. No protocol, frozen artifact, metric, or prospective boundary changes. The page states that the environment-utility prediction has not been tested on VeriBench, and that the prospective study must name which of the used partitions it holds out.

## Artifacts and compatibility

- New artifact references: one external repository (public, Apache-2.0) at a pinned commit, and 32 result, script and config files in it, each with SHA-256, size, media type, license and producing experiment in `results/records.json`.
- No schema changes.
- The page reflects the pin and is refreshed by a new commit that moves it (for example when the fourth smooth-reward seed of experiment 25 finishes).

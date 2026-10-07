# Run and land experiment 07 phase A (SCS4C-T versus pass@1 across SWE-bench Verified submissions) on skampere1

**TLDR:** You run experiment 07 phase A end to end on `skampere1`. Fetch every public SWE-bench Verified submission's per-instance `report.json`, compute SCS4C-T (the tests-only smooth conjunctive score for code) and pass@1 for each system, and run the locked analyses H1, H1b, H2 and H3. Then publish `results.md` with the frozen predictions beside the outcomes, get one light quality-assurance (QA) round from Codex, and merge the pull request. Finally, email Brando and comment on GitHub issue #ISSUE for Emily (@emxia18). No model calls are needed except the Codex reviewer.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Context

- **Why.** Brando's thesis committee member Azalia asked for evidence that interpretable metrics track downstream evaluations and can guide environments, feedback and rewards. Read `README.md` (definition, hypotheses) and `PROTOCOL.md` (locked) in the experiment folder before acting.
- **Work root.** `WORK=/lfs/skampere1/0/brando9/rl4cv_e07`. Clone `$WORK/rl-4-code-verification` on branch `e07-scs4c-phase-a` (you are its only writer). `EXP=$WORK/rl-4-code-verification/experiments/07_scs4c_vs_pass1_swebench_across_models`. Raw downloads go to `$WORK/data` and stay on the host. Commit only summaries.
- **State on dispatch.** The master created the clone, branch and `$WORK/STATUS_e07` (`RUNNING`). Keep `$EXP/expt_v1/CKPT_e07.md` current (agents-config Trigger Rule 44: real `date "+%m-%d-%Y %H:%M %Z"` stamps, current step, exact next command, blockers). Keep `$EXP/results.md` live (Trigger Rule 37).
- **Owner.** Emily (@emxia18) owns the experiment; you execute phase A for Brando.

## 1. Environment and lock check

1. `cd $WORK/rl-4-code-verification && git fetch origin '+refs/heads/main:refs/remotes/origin/main'` and confirm your branch contains the commit that added `PROTOCOL.md`.
2. Create an isolated environment: `uv venv $WORK/venv --python 3.12 && source $WORK/venv/bin/activate && uv pip install -e ".[dev]" scipy datasets boto3`. Use the system or pip `aws` command-line interface (CLI) for unsigned S3 (`aws --version`; else `uv pip install awscli`). Record versions in the checkpoint.
3. Run `make test`; it must pass.
4. Verify the frozen forecast: `python -c "from rl4cv.forecast import verify_forecast as v; assert v('$EXP/expt_v1/forecasts/e07_phase_a_forecast.json')"`. Never edit `PROTOCOL.md` or anything under `forecasts/`.

## 2. Fetch (no model calls)

1. Fetch the submission list at the pinned commit:
   ```bash
   git clone --filter=blob:none https://github.com/SWE-bench/experiments $WORK/swe-bench-experiments
   git -C $WORK/swe-bench-experiments checkout 40f164d5b8f1d249bf95a6df8b74b577fd8e519d
   ```
2. Run the fetch. It writes `inventory.json` with one row per submission:
   ```bash
   python $EXP/expt_v1/fetch_e07.py --experiments-repo $WORK/swe-bench-experiments \
     --out $WORK/data --gold-revision c104f840cc67f8b6eec6f759ebc8b2693d585d4a
   ```
3. **GitHub-hosted submissions.** Entries marked `github-hosted logs` keep their logs in the repository named by `metadata.yaml` `assets.repo`. Inspect that layout, add a small adapter to `fetch_e07.py` that places each instance's `report.json` (and predictions if present) at `$WORK/data/submissions/<submission>/logs/<instance>/report.json`, and rerun for those entries only. Record the adapter as a deviation in `results.md` before running the analysis. A submission whose logs lack per-test FAIL_TO_PASS / PASS_TO_PASS status is excluded with that reason.
4. **Infrastructure retries** rerun the identical download. Never drop a submission or task because of its score.

## 3. Analyze (locked settings)

1. Run with defaults (seed 20261007, 2,000 bootstrap draws, 2,000 splits, sizes 25 50 100 250, inclusion ≥ 95% measured):
   ```bash
   PYTHONPATH=src python $EXP/expt_v1/analyze_e07.py --data $WORK/data --out-dir $EXP/expt_v1/results
   ```
2. **Validity first** (PROTOCOL.md). If `resolved_but_score_below_1 + unresolved_but_score_1` exceeds 0.5% of measured cells, stop and diagnose the parser before reporting any hypothesis. If fewer than 20 systems are included, report phase A as underpowered.
3. **Sensitivity (protocol, not primary).** Add one system per base model (latest submission, keyed by `metadata.yaml` `info.model_display` or the closest equivalent field) and report H1, H1b and H2 at n_A = 50 for it. Implement this as a small, separately labelled function; do not change the primary analysis.
4. Copy `$WORK/data/inventory.json` into `$EXP/expt_v1/results/` (it holds no secrets). Commit `analysis_e07.json` and `per_system_e07.csv`, and a gzip of the per-cell table if it is under 5 MB.

## 4. Publish

1. Write `results.md`:
   - Status DONE, with a TLDR whose first clause restates the experiment.
   - Counts: systems total / included / excluded (with reasons), common-cohort tasks, measured and unmeasured cells.
   - For H1 and H1b: Pearson, Spearman and Kendall τ-b, each with task- and system-bootstrap intervals, plus mean bias and mean absolute error for H1.
   - For H2: median Δ, 5th–95th percentiles and share of Δ > 0 at every n_A.
   - For H3: counts with denominators.
   - The frozen prediction beside each outcome, with a verdict per the README table. A failed forecast is reported exactly like a successful one.
   - The validity checks, the sensitivity analysis and the 15 highest-pass@1 rows of the per-system table.
   - Expand acronyms on first use; dates `MM-DD-YYYY`.
2. Update the README status table and the experiment 07 row in `experiments/README.md` (state and next action: phase B admission needs the D_gold harness and the Valkyrie service).

## 5. Light QA (Brando requested light QA with Codex)

One round, then deterministic verification (agents-config `workflows/qa-correctness.md`, Tier 2 one-round shape):

- **Reviewer:** Codex `gpt-6-astra`, effort `ultra`, full access: `codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-6-astra -c model_reasoning_effort="ultra" "<prompt>"` (or `codexd`).
- **Prompt:** review the complete change from `origin/main` to your branch within `experiments/07_scs4c_vs_pass1_swebench_across_models/`, `experiments/README.md` and any `src/rl4cv/scs4c.py` change. Check correctness of report parsing, gating, denominators, statistics and the adapter; confirm every number in `results.md` matches `analysis_e07.json`; confirm the protocol was followed; fix critical and major issues directly; return a short PASS / FIXED / FAIL verdict with findings.
- **After review:** rerun `make test` and the analysis if code changed, and confirm the numbers again.
- **If Codex is unavailable on the host:** route through another verified Codex client per Trigger Rule 58, and record the route.
- **In the PR body:** the verdict block, the reviewer model, the effort and any fixes.

## 6. Land (agents-config Trigger Rule 46)

1. **Stage and test.** Stage explicit pathspecs only, inspect `git diff --cached` (no secrets, no raw logs), and run `make test`. Push the branch and open a PR. Its body holds the TLDR, the changes, the verification commands with exit codes, the QA verdict, the models used, and `Closes #ISSUE` only if phase A completes the issue's phase A checklist (otherwise `Refs #ISSUE`).
2. **Rebase if needed.** Fetch `origin/main`; if it moved, rebase, re-verify and push with `--force-with-lease` on your branch only.
3. **Merge.** Run `gh pr merge <n> --rebase --match-head-commit <verified-sha>` and confirm `MERGED`. Then delete the remote branch.
4. **Email** `brando.science@gmail.com` (no CC), subject `[rl4cv] PR #<n> merged: experiment 07 phase A`. The body holds the PR URL, the TLDR with H1, H1b and H2 verdicts and numbers, and the ledger and CKPT paths. Send it with `uutils.emailing.send_email_smtp(..., smtp_pass_file="~/keys/gmail_app_password.txt")`, as experiment 05 did.
5. **Comment** on issue #ISSUE: the TLDR, the headline table and a link to `results.md`, addressed to @emxia18.
6. **Signal the master.** On `main`, append `LANDED <merged-commit> <PR URL> <MM-DD-YYYY HH:MM>` to `CKPT_e07.md`, then pull with `--ff-only`, commit and push. Write `DONE` to `$WORK/STATUS_e07`.

If blocked by a real blocker you cannot route around, write `BLOCKED` to `$WORK/STATUS_e07`, describe it in the checkpoint and the PR, email `[rl4cv] PR #<n> blocked: experiment 07 phase A`, and stop.

## 7. Guardrails

- No model calls other than the Codex reviewer; no judge; no spend. VeriBench is untouched.
- Every declared submission and task needs a terminal receipt (measured, unmeasured with reason, or excluded with reason); a subset is never presented as the full set.
- Never edit `PROTOCOL.md` or the frozen forecast. Deviations go to `results.md` → "Deviations and open questions".
- Never print or commit tokens; `GH_TOKEN` comes from `~/keys/.brando90_github_token.txt` in the environment only.

TL;DR: Fetch public SWE-bench Verified per-instance reports, compute SCS4C-T and pass@1 per system, run the locked H1/H1b/H2/H3 analyses and publish `results.md`. Then get one Codex light-QA round, merge the PR, email Brando and comment on issue #ISSUE for Emily.

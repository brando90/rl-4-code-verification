# Claude Code: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull --ff-only 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.

This file holds the project rules for **rl-4-code-verification** for every agent: `AGENTS.md` (Codex and others) redirects here, per agents-config `workflows/repo-init.md`. When a rule changes, edit this file and add an entry to `docs/DECISIONS.md` in the same commit.

**Project:** Test whether the ρ–H environment-utility law from Varun and Brando's ICLR 2027 submission generalizes from math to RL for Lean 4 code verification, and use it to choose the RL environments and rewards that most improve VeriBench.

- **ρ:** usable signal density, the admitted leave-one-out advantage mass per generated token.
- **H:** effective coverage of that mass across prompts.
- **Paper:** "Which Environments Should LLMs Learn From? Predicting RL Utility Across Scale".
- **Plans and decisions:** `docs/PLAN.md` holds the plan; `docs/DECISIONS.md` holds the decisions, including the open ones only Brando can make.

## Related systems: AlphaApollo and AlphaDiana

These are Zhanke ("Andrew") Zhou's agent systems; Brando co-authored both. Details, papers and sources are in `docs/related_work/README.md`.

- **AlphaApollo solves.** It runs a model with tools, applies turn-level RL and refines answers in a propose–judge–update loop with memory ([arXiv:2510.06261](https://arxiv.org/abs/2510.06261); the PDF is in `docs/related_work/`).
- **AlphaDiana measures.** Its harness-aware evaluation runs the same benchmark across models × harnesses (DirectLLM, OpenClaw, OpenCode, ZeroClaw), with full traces and failure attribution ([github.com/tmlr-group/AlphaDiana](https://github.com/tmlr-group/AlphaDiana)).
- **Hebe improves** (in development, private `AndrewZhou924/AlphaHebe-dev`, cloned at `~/AlphaHebe-dev`). It edits Apollo's model or harness using Diana's measurements and promotes an edit only after an independent held-out check. Our factorized smooth scores (SCSC/SCS4CV, SCS4C) are the proposed signal. Experiments 04, 06 and 07 test whether they track or improve pass@1 on VeriBench and SWE-bench; 10 and 11 test whether the per-item factor matrix guides Hebe's feedback and promotion.
- **Their quick starts put provider keys in `.env`.** Here, model calls still follow D-108 (Valkyrie) or D-101 (self-hosted).

## Scientific integrity

- **VeriBench V1's test split is held out (D-013, Brando, 10-07-2026).** `rl4cv.splits` splits VeriBench V1 into train 539, validation 135 and test 222. The manifest is in `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/`. Near-duplicates and security safe/vulnerable pairs never straddle splits.
  - Training and warm starts may use train-split tasks, their gold references and teacher outputs on them. They never use validation or test tasks, references or text derived from them.
  - Checkpoint selection and tuning use the validation split only. The test split is evaluated once per frozen checkpoint and never used for training, tuning or selection.
  - VeriBench numbers for trained policies are reported on the test split, never on all 896.
  - Experiments locked before D-013 (01–07, 02A v3) keep their recorded rule: all of VeriBench held out.
  - Every training pool passes the exact-hash and word-5-gram screens in `docs/DATASETS.md` (`rl4cv.screens`) before use, against at least the validation and test splits for protocols adopting D-013; older locked protocols still screen against all 896 tasks.
  - HumanEval-derived external data is excluded (it overlaps VeriBench `humaneval_set`). VeriSoftBench-derived data is excluded whenever VBV2 is a panel.
- **VeriBench versions (Brando, 10-09-2026).** VBV1 is the original VeriBench (`brando90/veribench`: 896 Python-to-Lean tasks, core 614 plus IndustrySet 282). VBV2 is the private VeriSoftBench-derived task set built in VeriBench experiments 91 and 97 (VBV2.1 is experiment 99). VBV3 is VeriBench-Infinity (`brando90/veribench-inf`, paper `paper_latex/ICLR_2027_VeriBench_Infty/`). It has 24 source tasks with correct and intentionally incorrect Python variants, three frozen agent stages and kernel-checked comparison against the gold reference. Name the version beside every VeriBench number.
- **RL heuristics (Brando, 10-28-2026).** Read [docs/HEURISTICS.md](docs/HEURISTICS.md) before any RL run (precision, Varun's RL setup, free-hardware use) and append each new rule there.
- **VeriBench public release (Brando, 10-28-2026; D-110; agents-config Trigger Rule 82).** Every new experiment uses the current public VeriBench release and names it. As of 10-28-2026 that is `veribench@1.3` in the Harbor registry: 896 tasks in six splits (EasySet 41, CSSet 25, HumanEval 56, RealCodeSet 32, SecuritySet 460, IndustrySet 282), agent-spec v2; `@1.0` to `@1.2` are superseded and only reproduce the NeurIPS-2026 numbers. The `brando90/veribench` `main` head that day was `21846fd73b`. `external/deps.lock.json` pins `c11b99ba` (task packs) and `59059a20` (frozen scorer), both of which contain `@1.3` and sit on `main`; a locked protocol keeps its pins and names them. **Before each run:** run `git ls-remote https://github.com/brando90/veribench.git refs/heads/main` and read the README section "Public release and reproducibility" on `origin/main`. If the release, task count or splits differ from the above, use the new release and update this bullet, the pins and agents-config Trigger Rule 82 in one commit.
- **VeriBench numbers follow VeriBench's evaluation rules.**
  - SCSC = (IC_tests · IC_proofs · FSC)^(1/3) is the only aggregate, always shown with its three factors and n. For new official summaries, D-009 uses the geometric mean of the three factor means on one common measured cohort; mean per-file SCSC is diagnostic only. Core 614 and IndustrySet 282 are reported separately (on the D-013 test split: core 152, IndustrySet 70).
  - Scoring uses the pinned frozen scorer (`external/deps.lock.json`: `veribench_scorer`) with `--skip-tc`.
  - FSC comes only from the validated judge (`vb103_judge`, the experiment 100 H2 ensemble). Never use `run_real_eval.py`'s built-in FSC, which is the retired Sonnet 4.6 judge.
  - Unmeasured cells stay in the declared denominator and are listed, never counted as zero. When incomplete, label measured-cohort summaries with measured/declared counts and separately bound the full-manifest result.
  - Record exact model IDs and Hugging Face revisions.
- **The verifier is never loosened.** A theorem counts as proved only if its kernel axioms are within {`propext`, `Classical.choice`, `Quot.sound`}; `sorry`, `admit`, declared axioms and `native_decide` in named theorems fail. Prompts follow VeriBench's prove-first contract: `sorry` is an honest last resort worth zero, never a template.
- **FSC is compile-gated (D-003).** Rewards and outcomes use `fsc_compiled` or `scsc`. Ungated `fsc` is a diagnostic only, because the judge scores files that do not compile.
- **Prospective chronology (D-004).**
  - Freeze every forecast with `rl4cv.forecast.freeze_forecast` before reading any outcome it predicts.
  - Frozen forecasts are append-only.
  - Failed forecasts are reported exactly like successful ones.
- **Full-set evaluations.**
  - Each run declares its model × task × sample manifest, and every cell has a receipt.
  - Infrastructure retries rerun the identical cell.
  - Never re-sample or drop a cell because of its score, and never present a subset as the full set.
- **Terminology.**
  - Write "proved theorem" wherever proof status matters; a "formal specification" is a theorem statement without its proof.
  - Name data splits only as train / validation / test.
  - Describe judge checking as "judge validation" or "judge–human agreement".

## Compute and model calls

- **No agent-written direct provider API calls** (agents-config Hard Rule 9).
  - The validated judge follows D-102; other experiment model calls follow D-108 below.
  - Self-hosted open-weight inference (vLLM) requires D-101.
  - Never copy keys or `.env` files into the repository, prompts or logs.
- **Vals Valkyrie when Brando runs the work (Brando, 10-07-2026; D-108).** When Brando, or an agent working on his accounts, runs an experiment, solver and agent generation, judging and reruns go through [Vals Valkyrie](https://github.com/vals-ai/Valkyrie) (`valk` / `valkyrie`), funded by Vals. Current hosted setup uses `valkyrie login`, organization secrets and server-side provider/service settings; follow `~/agents-config/workflows/valkyrie.md` → "Hosted-cloud migration (10-14-2026)". Legacy `valkyrie.yaml` configuration is not the new hosted setup. These funding rules follow VeriBench's `CLAUDE.md` sections "Model-call keys: Valkyrie only" and "Valkyrie is not the Vals direct API".
  - **Migration.** Verify `valkyrie whoami`, the intended organization and `valkyrie provider list` on each execution host. Adapt launchers that copy private YAML or use `VALKYRIE_CONFIG_PATH`/`VALKYRIE_ENV`, and register custom benchmark services through the current command-line interface before reuse. Old cloud data is not automatically migrated. Preserve completed results, frozen settings and existing run holds; updated documentation or successful login is not evidence that a blocked run can resume.
  - **Privacy.** Keep the configuration private: never copy its contents into prompts, logs, results or Git.
  - **Keys.** A Valkyrie run may receive only a Valkyrie- or Vals-managed credential through Valkyrie's secret mapping: the gateway credential or a provider secret referenced by Vals' agent bundles. Copying a provider key given directly to Brando, or a subscription token, into a mapped secret does not qualify. Host-side code that retrieves a key and calls the gateway is a direct API route, not Valkyrie; direct key use requires Brando to name that specific key for that experiment in its protocol and does not waive the ban on agent-written direct provider calls.
  - **Funding.** Never fall back to personal credits, subscriptions or provider keys for measured generation or judging, inside Valkyrie or outside it. If Vals funding is unavailable or unknown, block new calls, preserve completed work and report the blocker. Personal subscriptions may coordinate, implement and review.
  - **Verify before the first call.** Check the host, organization, model-provider credential source and payer, and record non-secret evidence and the run identity in the checkpoint. A working login does not prove the payer.
  - **Capacity.** It is effectively unlimited, so do not shrink manifests, sample tasks, drop models or set small dollar caps to save cost. Keep a runaway guard (declared calls per cell, no silent retry loops), record the charges each route reports, and treat rate limits (HTTP 429) as infrastructure failures.
  - **Name the route for every call.** Valkyrie (`valk run start --benchmark … --agent … --model …`) and the Vals direct API (the gateway's `/query` endpoint, which has hit organization limits) are different routes. Use the direct API only where a frozen or validated configuration requires it, subject to the named-key requirement above.
  - **Solver agents.** Run each solver model in its vendor's strongest current agent (Claude Code, Codex, the Antigravity CLI `agy`, Qwen Code, …), recording the agent, its version, the exact model and the effort. Never silently substitute a model or fall back to another one; preserve frozen conditions.
  - **Judging.** Formal specification coverage (FSC) uses the validated custom Valkyrie agent under D-102, not a stock solver agent. Before its first use on a route, run bounded positive and negative controls verifying the delivered prompts, exact models, effort, rubric, inputs and aggregation. Preserve those scientific settings across transport changes; report incompatibilities instead of substituting settings or rerunning completed work.
  - **Other collaborators** (for example Emily) use Valkyrie only with their own authorized access. Otherwise the run waits for Brando or uses self-hosted inference under D-101.
  - **Setup and diagnosis:** agents-config `workflows/valkyrie.md` and `machine/snap.md` → "Valkyrie".
- **Retain Lean diagnostics (Brando, 10-19-2026; D-109).** Every future scoring launch must retain raw compiler and kernel stdout/stderr, partial timeout output, source/compiler identity and exit/unknown-exit status outside disposable probe directories. For new experiment 08 run versions25+, the default is `expt_v24/future_logging/parallel_scoring_logged.py`; its worker command factory always selects `logged_scorer.py`. Preserve historical frozen scorer files and verdicts. Actual success/error/kernel equivalence, timeout and abrupt-stop survival controls are in `expt_v24/future_logging/results/`. Do not launch the historical unlogged path for a new measured run.
- **GPU discipline** (agents-config Trigger Rule 9): baseline, estimate, ask Brando, launch, verify, clean up.
  - On SNAP, work under `/lfs/$(hostname)/0/$USER/`, never DFS home.
  - Raw generations stay on the host; commit summaries.

## Repository conventions

- **Work on `main` (Brando, 09-30-2026).** Commit directly to `main` and push once `make test` passes; no feature branches or pull requests unless Brando asks for one. Stage with explicit pathspecs (never `git add -A`), pull with `--ff-only` or merge before pushing, and never force-push `main`. Delete any branch as soon as it is merged (agents-config Trigger Rule 19).
  - **Push small and often (Brando, 10-07-2026; D-012).** About five people (Brando, Varun and the mentees) and their agents share this repository, often in the same checkout at the same time. Commit and push each finished, test-passing step as soon as it lands instead of batching a session's work. Pull before you start and before every push. Never stage, commit or revert another person's or agent's uncommitted files; if another session is editing the same checkout, work from your own clone, or from a detached `git worktree` that pulls with `git pull --ff-only origin main` and publishes with `git push origin HEAD:main` (no feature branch either way).
- **External repositories are pinned clones, not submodules (D-002).**
  - `external/deps.lock.json` holds exact commits.
  - `scripts/setup_external.sh` fetches them into git-ignored `external/<name>`.
  - Change a pin only in a reviewed commit that says why.
- **Experiments** live in `experiments/NN_descriptive_setup/`, which holds:
  - `README.md`: the design doc, with goal, hypothesis and decision criterion, structure, method, dependencies and status;
  - `PROTOCOL.md`: locked before any expensive run;
  - `results.md`: live;
  - `expt_vN/cc.md`: the agent prompt, with a 2–6 sentence TLDR at the top and a short TL;DR at the bottom;
  - `expt_vN/results/`.

  A changed setup is a new `expt_vN`. Dates in READMEs use MM-DD-YYYY. Update `experiments/README.md` when an experiment changes state.
- **File headers.** Every document starts with `# Title`, a `**Doc link:**` line and a `**TLDR:**`. Every code file starts with a one-sentence summary (module docstring or `# TLDR:` comment).
- **Testing.** `make test` must pass before any push. Adapter tests that need VeriBench read `$VERIBENCH_ROOT` or `external/veribench`.
- **Private material.** `docs/meeting_notes/` holds candid notes (mentee assessments, company strategy). Keep them inside this private repository.

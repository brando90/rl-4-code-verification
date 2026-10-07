# Claude Code: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull --ff-only 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.

This file holds the project rules for **rl-4-code-verification** for every agent: `AGENTS.md` (Codex and others) redirects here, per agents-config `workflows/repo-init.md`. When a rule changes, edit this file and add an entry to `docs/DECISIONS.md` in the same commit.

**Project:** Test whether the ρ–H environment-utility law from Varun and Brando's ICLR 2027 submission generalizes from math to RL for Lean 4 code verification, and use it to choose the RL environments and rewards that most improve VeriBench.

- **ρ:** usable signal density, the admitted leave-one-out advantage mass per generated token.
- **H:** effective coverage of that mass across prompts.
- **Paper:** "Which Environments Should LLMs Learn From? Predicting RL Utility Across Scale".
- **Plans and decisions:** `docs/PLAN.md` holds the plan; `docs/DECISIONS.md` holds the decisions, including the open ones only Brando can make.

## Scientific integrity

- **VeriBench is held out.**
  - Never train, warm-start, tune or select checkpoints on VeriBench tasks, references or text derived from them.
  - Every training pool passes the exact-hash and word-5-gram screens in `docs/DATASETS.md` (`rl4cv.screens`) before use.
  - HumanEval-derived data is excluded (it overlaps VeriBench `humaneval_set`). VeriSoftBench-derived data is excluded whenever VBV2 is a panel.
- **VeriBench numbers follow VeriBench's evaluation rules.**
  - SCSC = (IC_tests · IC_proofs · FSC)^(1/3) is the only aggregate, always shown with its three factors and n. Core 614 and IndustrySet 282 are reported separately.
  - Scoring uses the pinned frozen scorer (`external/deps.lock.json`: `veribench_scorer`) with `--skip-tc`.
  - FSC comes only from the validated judge (`vb103_judge`, the experiment 100 H2 ensemble). Never use `run_real_eval.py`'s built-in FSC, which is the retired Sonnet 4.6 judge.
  - Unmeasured cells stay in the denominator and are listed, never counted as zero.
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
  - Closed models and the judge go through the route decided in D-102; other model calls follow D-108 below.
  - Self-hosted open-weight inference (vLLM) requires D-101.
  - Never copy keys or `.env` files into the repository, prompts or logs.
- **Vals Valkyrie when Brando runs the work (Brando, 10-07-2026; D-108).** When Brando, or an agent working on his accounts, runs an experiment, solver and agent generation, judging and reruns go through [Vals Valkyrie](https://github.com/vals-ai/Valkyrie) (`valk` / `valkyrie`). It uses the saved configuration `~/.config/valkyrie/valkyrie.yaml` on the execution host and is funded by Vals. These rules follow VeriBench's `CLAUDE.md` sections "Model-call keys: Valkyrie only" and "Valkyrie versus the Vals direct API".
  - **Privacy.** Keep the configuration private: never copy its contents into prompts, logs, results or Git.
  - **Keys.** Use no direct provider key, no Vals gateway key outside a Valkyrie run, and no personal subscription or key as a fallback, unless Brando names that key for that experiment. Record his instruction in the protocol.
  - **Verify before the first call.** Check the host, organization, model-provider credential source and payer, and record non-secret evidence and the run identity in the checkpoint. A working login does not prove the payer.
  - **Capacity.** It is effectively unlimited, so do not shrink manifests, sample tasks, drop models or set small dollar caps to save cost. Keep a runaway guard (declared calls per cell, no silent retry loops), record the charges each route reports, and treat rate limits (HTTP 429) as infrastructure failures.
  - **Name the route for every call.** Valkyrie (`valk run start --benchmark … --agent … --model …`) and the Vals direct API (the gateway's `/query` endpoint, which has hit organization limits) are different routes. Use the direct API only where a frozen, validated configuration requires it.
  - **Agents.** Run each model in its vendor's strongest current agent (Claude Code, Codex, the Antigravity CLI `agy`, Qwen Code, …), recording the agent, its version, the exact model and the effort. Never silently substitute a model or fall back to another one.
  - **Other collaborators** (for example Emily) use Valkyrie only with their own authorized access. Otherwise the run waits for Brando or uses self-hosted inference under D-101.
  - **Setup and diagnosis:** agents-config `workflows/valkyrie.md` and `machine/snap.md` → "Valkyrie".
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

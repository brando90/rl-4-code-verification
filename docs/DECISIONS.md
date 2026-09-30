# Decision log

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/DECISIONS.md>

**TLDR:** Decided so far: separate repository; pinned clones instead of submodules; FSC always gated on compilation; forecasts hash-frozen before outcomes; work directly on `main`; self-hosted open-weight inference approved with model substitution allowed; FSC judge route and payer (`vb103_judge` on Valkyrie, Vals gateway). Still open for Brando: GPU compute, the pool source, the paper's code, and who leads.

Format: `D-NNN — title — status — date — owner`, then context, decision and consequences.
Append new entries; strike through superseded ones and point to the entry that replaces them.

## Decided

### D-001 — Separate project and repository — accepted — 09-30-2026 — Brando

- **Context:** The first analysis was drafted as an idea inside the VeriBench repository (draft PR brando90/veribench#428).
- **Decision:** Brando said this is a new project, separate from VeriBench, and created [`brando90/rl-4-code-verification`](https://github.com/brando90/rl-4-code-verification). The plan, code, prompts and meeting notes live here. VeriBench is a pinned external dependency.
- **Consequences:** VeriBench's own rules still govern any VeriBench number this project reports (see [CLAUDE.md](../CLAUDE.md)). The VeriBench PR's content was moved here.

### D-002 — Pinned clones instead of git submodules — accepted — 09-30-2026 — Claude (Brando: "fine with whatever")

- **Context:** The project reads three repositories: VeriBench (private, large, shared by many agents), its frozen scorer commit, and the rl-env-scaling fork.
- **Decision:** No submodules. [`external/deps.lock.json`](../external/deps.lock.json) records exact commits, and [`scripts/setup_external.sh`](../scripts/setup_external.sh) fetches each into `external/<name>` (git-ignored) and checks the resulting commit.
- **Why:**
  - Submodules need recursive authenticated clones on every remote host.
  - They leave detached-HEAD checkouts that agents accidentally commit into.
  - They make it easy to bump a pin silently.
  - A lock file keeps the pin change reviewable in one diff, and it allows two pins of the same repository (current VeriBench and experiment 103's frozen scorer), which submodules handle awkwardly.
- **Consequences:** Changing a pin is an explicit reviewed commit to `deps.lock.json`. Code finds VeriBench through `$VERIBENCH_ROOT` or `external/veribench`.

### D-003 — FSC is always gated on compilation — accepted — 09-30-2026 — Claude

- **Context:** VeriBench's judge scores non-compiling files, sometimes at 1.0 ([FACTS §3](FACTS_veribench_baselines.md#3-the-fsc-judge)).
- **Decision:** Any reward or outcome that uses FSC is gated: `fsc_compiled` pays FSC only when IC_tests = 1, and `scsc` is 0 whenever IC_tests · IC_proofs = 0. Ungated `fsc` exists only as a diagnostic.
- **Consequences:**
  - Judge calls are needed only for responses that compile and prove at least one theorem, which is cheap while success is rare.
  - Per-checkpoint SCSC is exact without judging the rest.

### D-004 — Prospective chronology is mechanical — accepted — 09-30-2026 — Claude

- **Decision:** Every forecast is written with `rl4cv.forecast.freeze_forecast` (canonical JSON, SHA-256 sidecar, append-only ledger) before any outcome it predicts is read. Scoring code refuses to compare against a forecast whose hash does not verify.

### D-005 — Same model family and scales as the paper for the law test — proposed — 09-30-2026 — Claude

- **Decision:** The generalization test (experiment 03) uses Qwen3 Base 1.7B, 4B, 8B and 14B, as the paper did, so the domain is the main thing that changes.
- **Consequences:** Newer small models (Qwen3.5 0.8B–9B) appear in experiment 01 as baselines, not as the law's scale axis.

### D-006 — Work directly on `main` — accepted — 09-30-2026 — Brando

- **Context:** Brando: "can we start pushing to main? Merge all PRs/branches to main."
- **Decision:** Agents commit to `main` after `make test` passes and delete merged branches. The bootstrap PR (#1) and the other Claude branch (`claude/admiring-heisenberg-eok3j4`, notes on RL and base-model coverage) were merged into `main` on 09-30-2026.

### D-101 — Self-hosted open-weight inference — accepted — 09-30-2026 — Brando

- **Context:** Experiment 01 needed approval for running open-weight models outside Valkyrie.
- **Decision:** Brando: "just do the experiment, it's fine to change models. I want to do these experiments. Go." Self-hosted inference of open-weight models is authorized for this project, and substituting models is allowed. Every substitution or scale-down is a new, separately labelled condition (`expt_vN`), never an edit to a locked protocol.

### D-102 — FSC judge route and payer — accepted — 09-30-2026 — Brando

- **Context:** FSC in experiments 01–05 needed a judge route and payer; agents may not write direct provider API calls (agents-config Hard Rule 9).
- **Decision:** Brando: "use the vb103_judge Valkyrie route." Route: experiment 103's `vb103_judge` Valkyrie agent (experiment 100 H2 ensemble: GPT-6 Sol high + Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5). Payer: the Vals model gateway, the same account and environment experiment 103 used.
- **Consequences:** Scope per `PROTOCOL.md`: every scored cell with IC_tests · IC_proofs > 0, plus the 60-file audit per model. Judging runs as a new, separately labelled suite (`rl4cv-e01:<label>`) on its own benchmark instance; experiment 103's existing judge records and runs under `veribench_vb103` are never modified. FSC in experiments 01–05 is unblocked.

## Open — needs Brando

| ID | Question | Recommendation | Blocks |
|---|---|---|---|
| D-103 | Compute: whose GPUs and how many hours? Paper: about 350 B200 GPU-hours for 32 trajectories. The Lean replication likely needs 1.5–2× that because outputs are longer. | Varun's B200 allocation for experiments 03–05; SNAP for experiment 01 | experiments 03–05 |
| D-104 | Pool source for the full-file family: FVAPPS-derived, synthetic VeriBench-style, or both. Synthetic references need a frontier-model generation budget. | Start with FVAPPS (it already exists); add synthetic only if FVAPPS fails the quality screen | experiment 02 |
| D-105 | Access to the paper's exact code, NeMo RL configs and warm-start checkpoints. Upstream `madanva/rl-env-scaling` `main` (= the old pin `c75755c`) holds 91 planning files and no training code; the code is on the upstream branches `controlled-scaling-v2` (`7118b86`, 08-31-2026, 408 files), `progress/experimental-rigor` and `first-iteration`. GitHub's "Sync fork" syncs only `main`, so it would not bring the code over. On 09-30-2026 the fork received `controlled-scaling-v2` and `external/deps.lock.json` was provisionally re-pinned to `7118b86` (Claude, reversible). | Ask Varun which commit (or the submission zip) produced the submitted paper's numbers, which NeMo RL v0.7.0 configs it used, and where the SFT step-512 warm-starts for 1.7B/4B/8B/14B live; re-pin to his answer | experiments 02–05 |
| D-106 | Lead and mentee assignment (notes A name Ethan Lee as a candidate lead). Brando, 09-30-2026: "I want to start running all of them and tagging Emily (@emxia18)". | Emily (@emxia18) runs the experiments on SNAP starting with 01 via `scripts/cc_prompt_run_experiment_on_snap.md`; lead for 01–02 still open; mentees take pool construction and screens | scheduling |
| D-107 | VeriBench draft PR brando90/veribench#428 (the idea folder written before D-001). | Close it as superseded by this repository, or keep a one-line pointer in VeriBench's ideas index | housekeeping |

Note on D-105 (09-30-2026):

- Git submodules stay rejected (D-002); the paper's repository is a pinned clone in `external/deps.lock.json`.
- NeMo RL itself is pinned by package version (v0.7.0, the version named in upstream `docs/research/NEMORL_PAPER1_RL_ARCHITECTURE_AUDIT_20260830.md` on `controlled-scaling-v2`), not vendored into this repository.

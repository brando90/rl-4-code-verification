# Decision log

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/DECISIONS.md>

**TLDR:** Decided so far: this is a separate project in its own repository; external repositories are pinned clones, not git submodules; FSC is always gated on compilation; forecasts are hash-frozen before outcomes exist. Brando still has to decide the local-inference authorization, the judge route and payer, the pool source, compute, and who leads.

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

## Open — needs Brando

| ID | Question | Recommendation | Blocks |
|---|---|---|---|
| D-101 | May this project run **self-hosted open-weight inference** (vLLM on SNAP or B200 hosts) for VeriBench generation? VeriBench's current rule routes every VeriBench model call through Valkyrie, and RL rollouts and our own checkpoints cannot go through Valkyrie. | Yes for open-weight policies and our checkpoints, disclosed in each protocol. Valkyrie stays the route for closed models and the judge. | experiments 01–05 |
| D-102 | Judge route and payer for FSC in this project: experiment 103's `vb103_judge` on Valkyrie (Vals-funded?) or another approved route. Agents may not write direct provider API calls (agents-config Hard Rule 9). | Valkyrie `vb103_judge`, judging only responses with IC_tests · IC_proofs > 0 plus one full-coverage audit sample per model | FSC in experiments 01–05 |
| D-103 | Compute: whose GPUs and how many hours? Paper: about 350 B200 GPU-hours for 32 trajectories. The Lean replication likely needs 1.5–2× that because outputs are longer. | Varun's B200 allocation for experiments 03–05; SNAP for experiment 01 | experiments 03–05 |
| D-104 | Pool source for the full-file family: FVAPPS-derived, synthetic VeriBench-style, or both. Synthetic references need a frontier-model generation budget. | Start with FVAPPS (it already exists); add synthetic only if FVAPPS fails the quality screen | experiment 02 |
| D-105 | Access to the paper's code, NeMo RL configs and warm-start checkpoints. The fork `brando90/rl-env-scaling` is the 08-12 snapshot; upstream `madanva/rl-env-scaling` or the submission zip has them. | Sync the fork with upstream ("Sync fork" on GitHub) and re-pin | experiments 02–05 |
| D-106 | Lead and mentee assignment (notes A name Ethan Lee as a candidate lead). | Lead for experiments 01–02; mentees take pool construction and screens | scheduling |
| D-107 | VeriBench draft PR brando90/veribench#428 (the idea folder written before D-001). | Close it as superseded by this repository, or keep a one-line pointer in VeriBench's ideas index | housekeeping |

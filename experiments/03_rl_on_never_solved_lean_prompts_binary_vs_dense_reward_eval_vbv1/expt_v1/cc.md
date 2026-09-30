# Experiment 03 v1 — train the zero-signal bucket under three reward arms and measure whether it moves

**TLDR:** On a GPU host with experiment 02A's pools, probes and warm starts in place, you will: build the zero-signal bucket `Z` (prompts with `K = 0` in all four `G = 8` probes) at 1.7B and 4B; compute and freeze the pre-RL ρ and H of `Z` under `kernel_binary`, `proof_fraction` and `proof_fraction_feedback1`; train 3 seeds × 3 arms × 2 scales with experiment 02B's locked contract; evaluate every checkpoint on the within-source panel, re-probe `Z` at the endpoint, and score the step-128 endpoints on VeriBench V1 with full denominators; then fill in the gate table in `results.md`. The protocol is locked; the deliverable is `results.md` plus committed summaries.

Read `~/agents-config/INDEX_RULES.md`, this repository's `CLAUDE.md`, this experiment's `README.md` and `PROTOCOL.md` (locked) before acting. If `PROTOCOL.md` does not exist yet, stop: the experiment is not ready to run.

## 0. Rules you must hold

- **VeriBench is held out.** Training prompts come only from experiment 02A's screened pools. VeriBench tasks are evaluated at endpoints, never trained on, never used to pick checkpoints.
- **The verifier is never loosened.** Rewards use `rl4cv.rewards`; a theorem is proved only if its kernel axioms are within {`propext`, `Classical.choice`, `Quot.sound`}.
- **Prospective chronology.** Freeze `forecasts/pre_rl_rho_h_Z.json` with `rl4cv.forecast.freeze_forecast` before the first trajectory starts. Never edit a frozen forecast.
- **Full-set runs.** Every seed × arm × scale × checkpoint has a receipt. Infrastructure retries rerun the identical cell; nothing is re-sampled or dropped because of its score.
- **Model calls.** No direct provider API calls. FSC only through `vb103_judge` on the route in D-102, and only at step-128 endpoints.
- **Storage.** Work under `/lfs/$(hostname)/0/$USER/rl4cv_e07/`; raw generations stay on the host; commit summaries and the forecast ledger.

## 1. Set up

```bash
WORK=/lfs/$(hostname)/0/$USER/rl4cv_e07 && mkdir -p $WORK && cd $WORK
git clone https://github.com/brando90/rl-4-code-verification.git && cd rl-4-code-verification
make external && make install && make test
```

Copy experiment 02A's frozen panel, probe tables and warm-start checkpoints into `$WORK` (paths in experiment 02A's `results.md`); verify their hashes.

## 2. Build `Z` and freeze the pre-RL measurements

1. From the four probes, select prompts with `K = 0` everywhere under `kernel_binary`; hash-cap to 256 with `rl4cv.cells`, balanced on family, split and length. Save `expt_v1/results/Z_<scale>.jsonl` with SHA-256.
2. Compute ρ, H, mixedness, admission and mean length for `Z` under each arm with `rl4cv.probe` (arm C after one feedback turn on the Stage D responses). Assert `ρ_A(Z) == 0`.
3. Freeze `forecasts/pre_rl_rho_h_Z.json` and the outcome forecast (which arms are predicted to move `Z`, with the gate numbers from `PROTOCOL.md`).

## 3. Train

For each scale in {1.7B, 4B}, arm in {A, B, C}, seed in {0, 1, 2}: run experiment 02B's NeMo RL configuration on `Z` with only the reward channel changed, in its own tmux session `rl4cv03-<scale>-<arm>-<seed>`. Record generated action tokens per checkpoint (capped and loss-masked responses included).

## 4. Evaluate

- Every checkpoint: within-source panel `kernel_binary` pass@1 (`G = 1`).
- Endpoints: native `G = 4` pass@4 on the panel; the `Z` re-probe (`G = 8` on the training prompts; fraction moved from `K = 0` to `K > 0`); VeriBench V1 with the frozen scorer (`--skip-tc`) and `vb103_judge` for FSC, reported as IC_tests, IC_proofs, FSC, SCSC and n, core and IndustrySet separately; experiment 02C's reward-hacking audits.

## 5. Report

Fill `results.md`: per-arm utility curves at the four budget points, the `Z` re-probe table, the VeriBench endpoint table, the FSC guard, and the gate verdicts against the frozen forecast (failed gates reported exactly like passed ones). Commit summaries and forecasts with explicit pathspecs; `make test`; push to `main`.

**TL;DR:** build `Z`, freeze its pre-RL ρ/H per arm, train 18 trajectories under experiment 02B's contract, re-probe `Z` and score endpoints on VeriBench, and report every gate verdict.

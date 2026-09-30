# Experiment 01 — Predicting the RL utility of VeriBench environments from pre-RL measurements (ρ, H, q_mixed), Qwen3.5 2B → 4B → 9B on SNAP

**TLDR:** Treat subsets of VeriBench (VB) tasks as RL *environments*, measure them under the starting policy exactly as the ICLR 2027 submission *Which Environments Should LLMs Learn From?* does (G=8 probes → per-prompt mixedness `q_mixed`, admitted advantage mass per token `ρ`, effective prompt coverage `H`), train GRPO on a 2×2 of constructed cells at 2B and 4B, freeze the ρ–H utility model, and test whether it predicts held-out VB improvement on an untouched 9B run; the same runs test the coverage-gating claim from [`notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md`](../../notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md) (tasks the base never solves in 32 samples do not move under binary reward; only per-theorem credit or compiler feedback moves them). Output for "solving VB": a map of which VB tasks RL can currently learn from, which are coverage-blocked, and what unblocks them.

Status: **DESIGN DRAFT 09-30-2026, not frozen.** Written by Claude Code for Brando to edit; nothing has run. Items marked **[verify]** are facts I could not check from this sandbox.

Owners: Brando (@brando90) — design, freeze decisions; Emily (@emxia18) — execution on SNAP, starting with [`scripts/cc_prompt_launch_phase0_on_snap.md`](scripts/cc_prompt_launch_phase0_on_snap.md) (run locally) and then [`scripts/cc_runbook_phase0_coverage_census.md`](scripts/cc_runbook_phase0_coverage_census.md) (on the host).

Project goal this serves (Brando, 09-30-2026): "solving VB using the new paper with Varun about predicting utility of new RL envs." Varun's project workspace is [`madanva/rl-env-scaling`](https://github.com/madanva/rl-env-scaling) (Brando's fork `brando90/rl-env-scaling`, last commit `c75755c`, 08-12-2026); this design follows its `experiments/_template` headings, its fixed-training-policy rule (GRPO, fixed harness, no adaptive task selection) and its `docs/axes/difficulty.md` metrics.

---

## 1. Hypotheses (pre-registered predictions; see §9 for the numeric gates)

- **H1 — environment choice matters at fixed trainer.** Which VB prompts you train on changes held-out VB improvement by several points at matched generated-token budget (the paper: 3.7–11.4 pp on OpenR1 math).
- **H2 — pre-RL ρ–H predicts utility across scale.** The paper's compact model `Û = β0 + βN·xN + βC·s(C) + βρ·s(C)·z(log ρ) + βH·s(C)·z(H)`, fit on 2B and 4B and frozen, predicts the 9B utility curves with low error (the paper: 2.29 pp RMSE on untouched 14B). This is the transfer of the method from math to Python→Lean autoformalization.
- **H3 — coverage gating (from the notes).** Prompts whose starting policy never succeeds in 32 samples (`q_mixed = 0` in every probe) contribute zero gradient under a binary outcome reward and show no held-out effect from being trained on; per-theorem partial credit and in-rollout compiler feedback are the only arms that move that bucket.
- **H4 — sharpening signature.** Under binary reward, held-out pass@1 rises while native pass@4 does not exceed the warm start (the paper's 14B finding); the partial-credit and feedback arms may break this.

## 2. Axis under test

- **Primary:** the environment (prompt distribution) at fixed rollout, verifier and optimizer contract, summarized by the continuous pre-RL coordinates `ρ` (eq. 5 of the paper) and `H` (eq. 6), constructed through the paper's 2×2 of group-signal availability × admission/cost.
- **Secondary (Phase 2 only):** reward-channel density — binary vs per-theorem partial credit vs compiler feedback inside the rollout. This is Varun's "verifier/reward quality: density/informativeness" sub-axis; it stays a separate phase so Phase 1 remains a clean replication.
- **Matched:** starting success (cells balanced on mean `p`), prompt length, VB split, verifier validity, generated-token budget.
- **Not varied:** algorithm, harness, decoding, curriculum (static uniform over each cell; dynamic sampling off).

## 3. Fixed recipe (replicates the paper's contract wherever VB allows)

| Knob | Value | Note |
|---|---|---|
| Starting policies `π0(N)` | `Qwen/Qwen3.5-2B`, `Qwen/Qwen3.5-4B`, `Qwen/Qwen3.5-9B` (post-trained, thinking mode off; HF revision hashes pinned at freeze) | Newest Qwen dense small family (created 2026-02-26/28 on HF; `-Base` variants exist). Brando asked for "2B or 7B SOTA open weights"; 9B is the nearest to 7B. **[verify]** the Qwen3.5 dense checkpoints ship a vision encoder (HF pipeline tag `image-text-to-text`): confirm text-only loading in the trainer and vLLM before freezing. Fallback: `Qwen/Qwen3-1.7B/4B/8B` (the paper's exact family, known to run in NeMo RL 0.6.0). |
| Why not Base + SFT warm start like the paper | The paper SFTs Base models on 1,024 math + 1,024 code examples. We cannot SFT on VB gold (contamination of the held-out panel and the "never near the gold" rule), and a Base model with no Lean skill has ≈0 coverage on every VB task, which would make every cell an all-fail cell. So `π0` = the released post-trained checkpoint, disclosed as such. Optional later arm: `-Base` + SFT on non-VB Lean data (Mathlib/Lean-Workbook-style, hash-checked disjoint from VB). |
| Algorithm | GRPO-style, NeMo RL v0.6.0 contract: `G = 8`, unnormalized leave-one-out advantage (eq. 2), token-level loss, importance correction, symmetric clip 0.2, **no KL**, overlong filtering on (capped responses stay in the baseline, zero loss weight), dynamic sampling off | Identical to the paper. **[verify]** NeMo RL 0.6.0 support for the Qwen3.5 architecture; if absent, use verl with the same settings and record the difference. |
| Optimizer | AdamW, lr 2e-6, wd 0.01, BF16, 128 steps, 4 prompts × 8 responses per step, checkpoints at 16/32/48/64/96/128 | Same as paper. |
| Decoding | temperature 0.6, top-p 0.95, top-k 20, response cap 12,288, total sequence cap 16,384 | Same as paper. VB prompts (agent-spec v7 instruction + Python source) are longer than OpenR1 prompts; **[verify]** the longest prompt fits under 16,384 − 12,288 = 4,096 prompt tokens, else raise the total cap and disclose. |
| Seeds | 2 per cell (as the paper); 3 in Phase 2 on the zero bucket | Two seeds left the paper's cell-specific variance unresolved; we accept the same limit for Phase 1 to match compute. |
| Harness | **single-turn, no tools**: one prompt → one Lean file. Not the Harbor agent condition. | Numbers are comparable to veribench experiment 103's single-call rows, not to agent rows. Phase 2 arm C adds exactly one compiler-feedback turn. |
| Task instruction | the live task pack's instruction, `VeriBench agent-spec v7 (2026-09-29 kernel-checked proof policy)` from `vb_harbor/adapter/adapter.py`, regenerated by `experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/make_task_pack.sh` | Prove-first contract: attempt every proof, `sorry` earns zero. Every prompt's SHA-256 recorded; a code assertion checks no prompt contains reference Lean bytes. |
| Verifier (reward) | local, deterministic, Lean `v4.22.0` (the CI-pinned toolchain) in the VB Lean project with Mathlib oleans cached: `r_compile` = `lake env lean` exit 0 within 300 s; `IC_tests` = compiles ∧ ≥1 `example`; `IC_proofs` = `scripts/scsc/kernel_axioms.py` honest/stated (axioms ⊆ {propext, Classical.choice, Quot.sound}; `sorryAx`, new axioms and `native_decide` fail) | Phase 1 reward = `IC_tests ∈ {0,1}` (binary, the paper's reward form). The frozen scorer files are imported/copied, never edited. |
| Evaluation | held-out panel, `G = 1` pass@1 of `IC_tests` at every checkpoint (primary utility, eq. 1); native `G = 4` at endpoints for pass@4; `IC_proofs` mean; `FSC` and `S̃_SCSC` at step-128 endpoints only, via experiment 100's validated FSC judge run as a Valkyrie custom agent (veribench rule 09-29-2026) | Reporting a valid results table requires all three factors (`IC_tests`, `IC_proofs`, `FSC`, `S̃_SCSC`, `n`), never compile rate alone; compile rate alone is allowed only for the IndustrySet rows. |

## 4. Data / environments

- **Task universe:** VB V1, 896 Python tasks (`find veribench_dataset/py_src -name '*.py' ! -path '*__pycache__*' | wc -l` = 896 on 09-30-2026): core 614 (`easy 41, cs 25, humaneval 56, realcode 32, security 460`) + IndustrySet 282 (14 domains × real/synthetic). Reference Lean files are used only by the FSC judge at endpoints; 1,929 of 2,248 reference `.lean` files `import Mathlib`, so the candidate compile environment must have Mathlib built.
- **Held-out panel (150 tasks, frozen before any RL, hash-disjoint from the pool):** deterministic SHA-256 of the task id with per-split quotas — easy 10, cs 6, humaneval 14, realcode 8, security 62, industry-real 20, industry-synthetic 30. The quotas keep every split visible; security (51% of VB) is down-weighted on purpose. Reported overall and per split.
- **Training pool:** the remaining 746 tasks.
- **Pre-RL probes (Phase 0):** three independent `G = 8` construction probes plus one untouched `G = 8` confirmation probe on every pool prompt under each `π0(N)` (32 samples/prompt), exactly the paper's Stage A–D chronology. Every response is compiled; per prompt we store `K` (successes), `p = K/8`, `q_mixed = 1 − p^8 − (1−p)^8`, admission indicators (non-capped), generated lengths, and per-response `IC_proofs`.
- **Cells (per scale, 4 disjoint cells of 96 prompts):** first letter = group-signal availability (H: `0 < K < 8` in the averaged construction probes; L: `K ∈ {0, 8}`), second = admission/cost (H: ≥ 3 non-capped responses and shorter; L: ≤ 4 non-capped, longer). Balanced on mean starting success (spread ≤ 3 pp), prompt length, split and verifier validity, selected by deterministic hash caps without ranking by extremeness (paper Appendix A). Cells are rebuilt under each scale's own `π0` because a prompt can be solved, unsolved or informative for different models.
- **Known asymmetry vs the paper:** on Lean tasks the non-mixed band will be dominated by `K = 0` (all-fail), with few `K = 8` prompts, so the L cells may not be balanceable on starting success against the H cells. If fewer than 48 `K = 8` prompts exist at a scale, the LH/LL cells are built from `K = 0` prompts and **relabeled `Z*` (zero-signal) cells**: they then serve H3 (coverage gating) rather than the paper's balanced contrast, and the ρ–H fit uses only the cells that were balanced. This is decided by the Phase 0 census, not after seeing RL outcomes.
- **Uniform-mixture stress test (optional, 9B only):** 24 prompts from each cell by outcome-blind hash, trained once, to reproduce the paper's composition-boundary check.
- **Contamination guards:** Qwen3.5 may have seen VB's Python sources or Lean references in pretraining (VB is public). We cannot rule this out; we report the warm-start panel score as the baseline everything is relative to, and the panel is hash-disjoint from training. A word-5-gram overlap screen between pool and panel Python sources is run and reported (the paper found 14/1,000 near-duplicates).

## 5. Phases

### Phase 0 — coverage census (no training; the first thing to run)

Serve `π0` with vLLM (OpenAI-compatible endpoint on one GPU), sample 32 responses per pool prompt per scale (746 × 32 × 3 scales ≈ 72k generations ≈ 200–300M tokens), compile everything through the Lean verifier pool, and publish `results/phase0_coverage_census.md`:

1. per-split histograms of `K` and `q_mixed`; the fraction of prompts with `q_mixed = 0` in all four probes (the coverage-blocked set) and with `0 < p < 1`;
2. Varun's difficulty metrics from `rl_env_scaling.metrics.difficulty` (`p`, `p(1−p)`, pass@32 − pass@1 headroom, effective prompt ratio) per split and per scale — this doubles as the VB row of his `experiments/00_metric_smoke_tests`;
3. `ρ` and `H` for every candidate cell and for the whole pool; `IC_proofs` distribution among compiling samples (how often the base proves anything at all);
4. cross-scale rank stability of `p` (2B vs 4B vs 9B).

**Go/no-go for Phase 1:** at the smallest scale, ≥ 192 pool prompts with `q_mixed > 0` in ≥ 2 of 3 construction probes (enough for HH+HL cells of 96 with slack). If 2B fails this gate it is coverage-starved for VB; drop 2B, fit on 4B + 9B and hold out `Qwen3.5-27B` **[verify feasibility on 2 B200s]**, and say so.

### Phase 1 — 2×2 cells × 2 seeds × 3 scales, binary reward (replication + transfer)

24 trajectories. Utility curves at 25/50/75/100% of the largest jointly supported generated-token budget per scale, anchored at `U(E,N,0) = 0`. Chronology, as the paper insists: (a) fit eq. 7 on 2B + 4B, **freeze coefficients, predicted 9B curves, ranking and envelope in a committed file** before any 9B trajectory is inspected; (b) run 9B; (c) score RMSE, pairwise rank accuracy, best-cell wins, mean regret, envelope coverage; (d) refit on all three scales with leave-one-scale-out and report both.

### Phase 2 — reward density on the zero bucket (the notes' §8 test)

At 2B (or the smallest admitted scale), a fifth environment `Z` = 96 coverage-blocked prompts (`q_mixed = 0` in all four probes), trained under three reward arms, 3 seeds each, same budget:

- **A** binary `IC_tests` (expected: zero gradient, panel unchanged within seed noise);
- **B** partial credit `r = 0.5·IC_tests + 0.5·IC_tests·IC_proofs_nv`, where `IC_proofs_nv` counts only non-vacuous stated theorems (statements matching the `VACUOUS` patterns of `veribench/tests/test_reference_specs_nonvacuous.py` — `True`, `x = x`, `by trivial` — count as neither stated nor honest; zero non-vacuous statements ⇒ 0). This is a *training* signal; evaluation always uses the canonical scorer;
- **C** = B plus one compiler-feedback turn: if the first response fails to compile, the first 40 lines of Lean diagnostics are appended and the model answers once more; reward on the final file; both turns count toward the generated-token budget. **[verify]** multi-turn environment support in the chosen trainer.

Also train arms B and C on the HL cell to see whether denser reward changes the ordering the ρ–H model predicts (it should raise `ρ`, since more groups admit non-zero advantage — this is measurable pre-RL and is itself a prediction).

## 6. Metrics

### Pre-RL (per prompt, per scale, from the probes)
`K`, `p`, `q_mixed`, admission indicators `m_gi`, lengths `ℓ_gi`, raw and admitted advantage mass (eq. 4), per-cell `ρ` (eq. 5) and `H` (eq. 6), Varun's `p(1−p)`, headroom, effective prompt ratio; verifier-validity flags (infrastructure errors kept distinct from incorrect files, as in the paper and in `run_real_eval.py`).

### Outcomes
- Primary: `U(E,N,C)` = held-out `IC_tests` pass@1 minus the warm start's, vs generated action tokens (capped and loss-masked responses included in the token count, per the paper's definition).
- Secondary: `IC_proofs` mean on the panel; native pass@4 of `IC_tests`; endpoint `FSC` and `S̃_SCSC` (validated judge, median of 3); per-split curves; the fraction of panel tasks that move from 0 to > 0 (the expansion signature) vs the pass@4 change (the sharpening signature).
- Guard: endpoint `FSC` under arm B vs arm A. If B's FSC drops, the partial-credit reward was hacked (fewer or emptier statements) and the non-vacuity gate is too weak; report it, do not tune the scorer.
- Diagnostics: response-length trajectories and cap-hit rates (the paper's 1.7B LH collapse: 86.8% capped); PBT presence via `scripts/scsc/pbt_diagnostic.py` (unscored).

## 7. Compute and infrastructure (SNAP / Koyejo lab)

- **Hosts** (from Brando's IT threads; GPU types and counts **[verify]** with `nvidia-smi` before freezing): Koyejo-lab-owned `skampere1`, `skampere2`, `skampere3` (skampere3 = the B200 host; veribench experiment 94 refers to 8 B200 devices there); InfoLab/SNAP machines Koyejo members can use but do not own: `hyperturing1/2`, `mercury1/2`, `ampere1/2`. Docker on SNAP works only for accounts in each node's `docker` Unix group (Brando's 09-28-2026 email to Varun). Harbor jobs run from `/lfs/$(hostname)/0/brando9/…`, never from DFS; one `harbor run` per host.
- **Per-trajectory cost (paper's numbers on B200):** 1.7B/4B on one B200, 3–10 h; 8B on two B200s, 5–6 h; 14B on two, 9–11 h. Ours, estimated: 2B ≈ 5 h × 1 GPU; 4B ≈ 8 h × 1; 9B ≈ 8 h × 2 GPUs.
- **Totals (B200 GPU-hours):** Phase 0 census ≈ 30 (generation is cheap; Lean compilation is the bottleneck: 72k compiles × ~30 s / 48 CPU workers ≈ 12 h wall-clock per scale — run the verifier pool on the host's CPUs alongside vLLM); Phase 1 ≈ 8×5 + 8×8 + 8×16 = 232; endpoint evals ≈ 30; Phase 2 ≈ 9 trajectories × 5 h + HL arms ≈ 60. **≈ 350 GPU-h ≈ 2–3 days wall-clock on skampere3 with 4 trajectories in parallel, a week realistically.** The paper's whole study was ≈ 350 B200 GPU-h.
- **Lean verifier pool:** a prebuilt copy of the VB Lean project (Mathlib oleans cached) per host under `/lfs`; a small service that takes Lean source, writes it into a scratch module, runs `lake env lean` with a 300 s timeout under a per-worker temp dir, then `kernel_axioms.py` for `IC_proofs`; N workers = CPU cores / 2. Infrastructure errors (timeouts of the toolchain itself, OOM) are recorded as `verifier_error`, never as reward 0.
- **Judge calls:** 150 panel × 25 endpoint policies (warm start + 4 cells × 2 seeds × 3 scales) × 3 votes ≈ 11k judge calls through Valkyrie (experiment 102 paid ≈ $1,228 for 18k calls, so ≈ $750 Vals-side). Vals-side costs are reported, not a reason to stop (veribench rule 09-29-2026). No solver or judge call uses a personal key.
- **Model calls that are not RL training** (FSC judging, any API baseline) go through Valkyrie only. The RL training itself is local open-weight inference on SNAP GPUs and is not a Valkyrie route.

## 8. Rules this design must keep (from `veribench/CLAUDE.md`)

- Solvers see only public inputs: the task instruction and Python source; no reference Lean, no scorer, no judge prompt in the prompt or the container; a code assertion plus prompt hashes enforce it.
- The canonical scorer (`scripts/scsc/run_real_eval.py`, `kernel_axioms.py`) is imported or copied byte-identically, never edited; training rewards are separate code under this experiment's `scripts/`. A results table shows `IC_tests`, `IC_proofs`, `FSC`, `S̃_SCSC` and `n`, computed through the canonical scorer on Harbor-generated outputs. For the leaderboard-comparable endpoint number, serve the final checkpoint with vLLM and run `vb_harbor/adapter/single_call_agent.py` against it (`LLM_BASE_URL`, `LLM_MODEL`) inside Harbor — the existing adapter already supports an OpenAI-compatible endpoint.
- Every model × task × seed cell of the frozen manifest is run to completion or recorded as missing/interrupted in the denominator; no clean-subset reporting, no silent retries. `sorry` earns zero; `native_decide` only in `example`s; reference specs are never weakened.
- Judge terminology: judge validation / judge–human agreement, never "calibrat*"; splits are train/validation/test only.
- Model IDs: pinned HF revisions recorded in `config.yaml` at freeze, after a fresh check of the newest Qwen small models (09-30-2026 check: Qwen3.5 0.8B/2B/4B/9B released 02-2026; Qwen3.6-27B and Qwen3.8-27B exist; Qwen 4 27B announced 09-22-2026, not released).
- Results as Markdown in this folder; W&B only on request.

## 9. Go / no-go gates and the predictions that would falsify the notes

| Gate | Pass criterion |
|---|---|
| Phase 0 → 1 | ≥ 192 pool prompts with `q_mixed > 0` in ≥ 2 of 3 probes at the smallest scale; verifier positive/negative controls pass (a known-good VB reference file → `IC_tests = 1`, `IC_proofs = 1`; the same file with one `sorry` → `IC_proofs < 1`; an empty file → 0). |
| H1 | best–worst cell spread at max shared budget ≥ 3 pp `IC_tests` pass@1 at ≥ 2 of 3 scales, direction reproduced by both seeds. |
| H2 | frozen 2B+4B model on untouched 9B: curve RMSE ≤ 3 pp, pairwise rank accuracy ≥ 70%, ≥ 9/12 cell-budget means inside the frozen envelope. A miss is reported as the paper reported its 8B miss, then refit LOSO. |
| H3 | arm A on `Z`: \|ΔU\| within the two-seed envelope of the warm start at every budget; arm B or C on `Z`: ΔU > envelope at max budget. **If arm A moves `Z` beyond the envelope, §2 of the notes is wrong for this setting and the note is rewritten.** |
| H4 | native pass@4 ≤ warm start for every binary-reward arm at max budget. |
| FSC guard | endpoint FSC(B) ≥ FSC(A) − 0.05 on the HL cell; otherwise the partial-credit reward is declared hackable and Phase 2 conclusions are limited to arm C. |

## 10. Directory structure (planned)

```
experiments/01_predict_rl_env_utility_veribench_qwen35_snap/
├── README.md                     # this design doc
├── config.yaml                   # executable source of truth for the frozen run (nulls until freeze)
├── scripts/
│   ├── cc_runbook_phase0_coverage_census.md   # Claude Code prompt for Phase 0 on SNAP (TL;DR first)
│   ├── (to write) make_prompt_manifest.py     # task pack → JSONL prompts + SHA-256 + no-gold assertion
│   ├── (to write) split_panel_pool.py         # hash split with quotas
│   ├── (to write) lean_verifier_pool.py       # compile / IC_tests / IC_proofs service
│   ├── (to write) probe_sample.py             # vLLM G=8 × 4 probes
│   ├── (to write) rho_h.py                    # eq. 2–6 with unit tests against closed forms
│   └── (to write) build_cells.py              # bands, hash caps, balancing, Stage-D confirmation
├── manifests/                    # frozen panel/pool/cell manifests (committed)
├── results/                      # Markdown tables; large artifacts under /lfs, README-linked
└── private/                      # status.json, nothing secret
```

## 11. Open questions for Brando / Varun

1. Qwen3.5 (2B/4B/9B, post-trained) vs Qwen3 Base + non-VB SFT as `π0` — the former is the requested SOTA open-weight family; the latter matches the paper's warm-start control. Recommendation: Qwen3.5 post-trained for Phase 0 now, decide after seeing the census.
2. Is `IC_tests` the right binary reward for Phase 1, or `IC_tests ∧ IC_proofs = 1` (all stated theorems proved)? The latter will make almost every prompt all-fail at 2B; `IC_tests` keeps the replication alive and leaves proving to Phase 2's partial credit.
3. Panel quotas (§4) — pre-registration choice; change now or never.
4. Whether Varun's team wants this filed as the VB/code row of `rl-env-scaling/experiments/` (their template) in addition to here.
5. Compute: run on skampere3 alone (one owner, no contention) or spread cells across skampere1/2 + hyperturing (one trainer per host)?

## References

- Anonymous. *Which Environments Should LLMs Learn From? Predicting RL Utility Across Scale.* ICLR 2027 submission (PDF shared by Brando 09-30-2026): eqs. 1–7, §4 contract, Appendix A construction rules and compute.
- [`notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md`](../../notes/rl_new_skills_vs_base_model_coverage_09-30-2026.md) — the coverage argument and §8 experiment sketch this folder implements.
- `brando90/rl-env-scaling` @ `c75755c`: `README.md` (thesis, fixed training policy), `experiments/_template/`, `docs/axes/difficulty.md`, `src/rl_env_scaling/metrics/difficulty.py`.
- `brando90/veribench`: `CLAUDE.md` rules; `scripts/scsc/README.md` (factor definitions); `scripts/scsc/kernel_axioms.py`; `vb_harbor/adapter/adapter.py` (agent-spec v7); `vb_harbor/adapter/single_call_agent.py`; `tests/test_reference_specs_nonvacuous.py`; `experiments/103_…/scripts/cc_runbook_103_single_call_valkyrie.md` (runbook conventions).

# Runbook — Phase 0 coverage census of VeriBench under Qwen3.5 2B/4B/9B (no RL training)

**TL;DR:** On a SNAP GPU host, build a Lean verifier pool for VeriBench, turn the live task pack into a hashed prompt manifest with a frozen 150-task held-out panel and a 746-task pool, sample 32 responses per pool prompt per scale from Qwen3.5-2B/4B/9B with vLLM (temperature 0.6, top-p 0.95, top-k 20, 12,288-token cap), compile every response, and publish `results/phase0_coverage_census.md` with per-prompt `K`, `p`, `q_mixed`, admission and length statistics, Varun's difficulty metrics, and `ρ`/`H` for every candidate cell — then apply the Phase 0 → 1 gate in `README.md` §9. No RL runs in this phase; no model call leaves the host except none (there are no judge calls in Phase 0).

This is a Claude Code prompt to be run on SNAP (`skampere3` preferred). `E` = `experiments/01_predict_rl_env_utility_veribench_qwen35_snap` in the `rl-4-code-verification` checkout; `VB` = a fresh `veribench` checkout. Work under `/lfs/$(hostname)/0/brando9/rl4cv_expt01/`, never under DFS. Read `E/README.md` and `VB/CLAUDE.md` first, every session.

## Hard rules

- The prompt given to the model contains only the task's public inputs: the agent-spec v7 instruction and the Python source. Assert in code that no prompt contains any line of the task's reference `.lean` file; write every prompt's SHA-256 to the manifest.
- Copy `VB/scripts/scsc/kernel_axioms.py` and `lean_public_context.py` into `E/scripts/vendored/` with their SHA-256 recorded; never edit them.
- Every generation that fails for infrastructure reasons (endpoint error, verifier timeout of the toolchain itself, OOM) is recorded as `verifier_error` or `generation_error`, never as `K = 0` evidence. The census reports these counts.
- No personal API keys, no Valkyrie needed: everything here is local open-weight inference plus Lean compilation.
- Do not touch other running workers on the host (`tmux ls` first); put every long job in its own named tmux session `rl4cv01-<step>`.

## Steps

1. **Host check.** `nvidia-smi --query-gpu=name,memory.total --format=csv`, `nproc`, `df -h /lfs/$(hostname)/0`, `docker ps` (only if needed). Record in `E/results/phase0_host.md`. Confirm ≥ 400 GB free under `/lfs`.

2. **Lean verifier pool.** Clone `veribench` under the work root; install elan and the CI-pinned toolchain (`leanprover/lean4:v4.22.0`, see `VB/.github/workflows/ci.yml`); `lake build` once so Mathlib oleans are cached. Write `E/scripts/lean_verifier_pool.py`: N workers (`nproc/2`), each with its own scratch module under the project; input = Lean source string; output = `{compiles, has_example, n_stated, n_honest, ic_tests, ic_proofs, wall_s, verifier_error}` using `lake env lean` (300 s timeout) and the vendored `kernel_axioms.py`. **Controls before anything else:** one VB reference file → `ic_tests = 1, ic_proofs = 1`; the same file with one proof replaced by `sorry` → `ic_proofs < 1`; the empty file → all zeros; a file with `native_decide` in a theorem → that theorem not honest. Save the control outputs to `E/results/phase0_verifier_controls.md`.

3. **Prompt manifest.** Run `VB/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/make_task_pack.sh` to regenerate the live pack (count must equal the live `py_src` count, every instruction stamped `agent-spec v7`). Write `E/scripts/make_prompt_manifest.py`: for each task, `{task_id, split, instruction_sha256, prompt (system + user exactly as `vb_harbor/adapter/single_call_agent.py` sends them), python_sha256, prompt_tokens}`; run the no-gold assertion; save `E/manifests/all_tasks_896.jsonl`.

4. **Split.** `E/scripts/split_panel_pool.py`: SHA-256 of `task_id`, per-split quotas from `config.yaml` (`easy 10, cs 6, humaneval 14, realcode 8, security 62, industry_real 20, industry_synthetic 30`) → `manifests/heldout_panel_150.jsonl` and `manifests/training_pool_746.jsonl`. Run the word-5-gram Jaccard ≥ 0.7 screen between pool and panel Python sources; list any hits in the census. Commit both manifests before step 5.

5. **Serve and sample.** For each scale (start with 2B): `vllm serve <model> --revision <hash> --max-model-len 16384` on one GPU (record the exact revision hash into `config.yaml`); `E/scripts/probe_sample.py`: for every pool prompt, 4 probes × `G = 8` = 32 samples at temperature 0.6, top-p 0.95, top-k 20, `max_tokens 12288`, with probe seeds `{11, 22, 33}` (construction) and `{44}` (confirmation, never used for cell selection); store every response, its token count, whether it hit the cap, and the endpoint's finish reason. Also sample the panel once at `G = 1` (temperature 0.6) and once at `G = 4` for the warm-start pass@1 / pass@4 baselines. Throughput note: ~24k generations per scale; keep the verifier pool draining a queue while sampling runs.

6. **Verify everything.** Push all responses through the pool; store per-response `{ic_tests, ic_proofs, n_stated, n_honest, compiles, capped, tokens, wall_s, verifier_error}` in `E/results/phase0_<scale>_responses.parquet` (or JSONL) under `/lfs`, with a committed SHA-256 and row count.

7. **Per-prompt statistics.** `E/scripts/rho_h.py` implements eqs. 2–6 of the paper (leave-one-out advantage `a_gi = r_gi − mean_{j≠i} r_gj`; raw and admitted absolute advantage mass; `ρ = 1e6 · Σ_g A_adm_g / Σ_{g,i} ℓ_gi`; `H = (Σ_g A_adm_g)² / (n_E · Σ_g (A_adm_g)²)`; `q_mixed = 1 − p^8 − (1−p)^8`) with unit tests against the closed forms (all-success and all-fail groups have zero mass; a group with one success and seven failures has `Σ|a| = 2·(8/7)`… derive and assert). Admission = not capped (the NeMo overlong-filtering semantics). Per prompt: `K` in each probe, `p`, `q_mixed` (averaged over the three construction probes), admission counts, mean length, `IC_proofs` among compiling samples.

8. **Candidate cells and their ρ/H.** `E/scripts/build_cells.py`: bands per `config.yaml` (mixed `0 < K < 8`, non-mixed `K ∈ {0, 8}`, high admission ≥ 3 non-capped, low ≤ 4), deterministic hash cap of 320 per band, joint selection of four disjoint 96-prompt cells balanced on mean starting success (spread ≤ 3 pp), prompt length, split and verifier validity; then `ρ` and `H` from the untouched confirmation probe only. If fewer than 48 `K = 8` prompts exist, build the L cells from `K = 0` prompts and label them `Z*` (README §4). Save `manifests/cells_<scale>.jsonl`.

9. **Census report.** `E/results/phase0_coverage_census.md`: per split and per scale — histograms of `K` and `q_mixed`; the coverage-blocked fraction (`q_mixed = 0` in all four probes); `0 < p < 1` fraction; Varun's `p`, `p(1−p)`, pass@32 − pass@1 headroom and effective prompt ratio (`pip install -e` the `rl-env-scaling` fork and call `rl_env_scaling.metrics.difficulty`); `ρ`, `H`, `q_mixed` for each cell and for the whole pool; `IC_proofs` distribution among compiling samples; cross-scale Spearman of `p`; counts of `generation_error` and `verifier_error`; warm-start panel pass@1 and pass@4; wall-clock and GPU-hours used. State the Phase 0 → 1 gate verdict (≥ 192 pool prompts with `q_mixed > 0` in ≥ 2 of 3 construction probes at the smallest scale) in one line at the top.

10. **Close the session.** Update `E/private/status.json` (`{"state": "running"|"blocked"|"done", "updated_utc", "summary"}`), commit only manifests, scripts and Markdown with explicit pathspecs (`git commit -- <files>`), push to the working branch, and open or update the PR. Large artifacts stay under `/lfs` and are README-linked with their hashes.

## Expected outputs

- `E/manifests/{all_tasks_896, heldout_panel_150, training_pool_746, cells_<scale>}.jsonl` (committed)
- `E/results/phase0_host.md`, `phase0_verifier_controls.md`, `phase0_coverage_census.md` (committed)
- `/lfs/.../phase0_<scale>_responses.*` (not committed; hashes in the census)
- `config.yaml` with the HF revision hashes filled in

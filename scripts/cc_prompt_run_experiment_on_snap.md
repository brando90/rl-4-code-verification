# Prompt — inventory SNAP GPUs, pick the right host, and run an experiment's `cc.md` there (paste into Claude Code locally)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/scripts/cc_prompt_run_experiment_on_snap.md>

**TLDR:** Given an experiment folder (start with `experiments/01_small_open_models_veribench_v1_single_call_baseline`, the only one approved and ready), this prompt: (1) inventories every SNAP host you can reach — GPU model, count, memory, what is free, CPUs, `/lfs` space, who is logged in — and commits it as `docs/snap_gpu_inventory_<MM-DD-YYYY>.md` (also the material for the ilwiki Koyejo page); (2) picks a host by the GPU rule below (B200 → H200 → H100/A100-80GB); (3) follows the GPU discipline in `CLAUDE.md` (baseline, estimate, ask Brando, launch, verify, clean up); (4) sets up `/lfs/$(hostname)/0/$USER/` and runs the experiment's `expt_vN/cc.md` inside a named tmux session. Usage: paste this file, then paste the experiment's `cc.md`, or say which experiment to run.

Read `~/agents-config/INDEX_RULES.md` and the repository `CLAUDE.md` first. Nothing here changes an experiment's locked `PROTOCOL.md`; if the chosen GPUs cannot honor it (memory, count, time), write the deviation into the experiment's `results.md` → "Open questions for Brando" and stop that item.

**Coordination (09-30-2026).** Two Claude Code sessions worked this repository in parallel. The session that bootstrapped `main` (branch `claude/zen-curie-2k9b3r`) owns experiment 01's code and its CPU pilot; the session that wrote the notes and experiment 03 (numbered 07 before D-007) owns this launcher. There is one launcher: extend this file rather than adding a second one, and check `docs/DECISIONS.md` and the open GitHub issues before creating a tracking issue, so each experiment has exactly one.

## 1. Inventory every reachable host

Known profiles from `~/agents-config/machine/snap.md` (audited 09-03-2026; **always verify at runtime**, hardware varies per node):

| Host | GPUs | RAM | Owner |
|---|---|---|---|
| `skampere3` | 8× B200 179 GiB | ~3 TiB | Koyejo lab |
| `skampere2` | 8× H200 140 GiB | ~3 TiB | Koyejo lab |
| `skampere1` | 8× A100-SXM4-80GB | ~2 TiB | Koyejo lab |
| `ampere1`, `ampere8` | 8× A100-SXM4-80GB | ~2 TiB | InfoLab/SNAP (access only) |
| `mercury1`, `mercury2` | 10× RTX A4000 16 GB | ~0.5 TiB | InfoLab/SNAP (access only) |
| `hyperturing1`, `hyperturing2` | verify | verify | InfoLab/SNAP (access only) |

CUDA 12.4; Ubuntu 24.04 on skampere1–3. On SNAP, `$HOME` is `/lfs/<hostname>/0/<user>` (set by `.bashrc`), `~/.elan/bin` holds Lean, and `~/uv_envs/veribench` is the VeriBench venv from `veribench_setup.sh` (see `~/agents-config/machine/snap-init.md`). Use the `.stanford.edu` hostnames your SSH config expects; Kerberos must be valid (`kinit` / keytab, `~/agents-config/init_no_passwords_snap_kinit.md`).

For each host, with `ssh -o ConnectTimeout=10 -o BatchMode=yes`:

```bash
hostname; uptime
nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu --format=csv,noheader
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | wc -l
nproc; free -g | sed -n 2p
df -h /lfs/$(hostname)/0 2>/dev/null | tail -1
who | awk '{print $1}' | sort -u | tr '\n' ' '
docker info >/dev/null 2>&1 && echo docker:yes || echo docker:no
```

Write `docs/snap_gpu_inventory_<MM-DD-YYYY>.md` (Doc link + TLDR header): one row per host — host, owner (Koyejo lab / InfoLab access-only), GPU model × count, memory per GPU, GPUs free right now (0% utilization and no other user's process), CPU cores, RAM, `/lfs` free, users logged in, docker access, reachable (yes / no + error). Unreachable hosts stay in the table as unreachable; omit nothing.

## 2. Choose the host and GPUs

| GPU | Memory | Good for |
|---|---|---|
| B200 | 180 GB | everything: experiment 01 sampling of any model on 1 GPU; later RL: 1 GPU per 1.7B/4B trajectory, 2 per 8B/14B (the paper's split) |
| H200 | 141 GB | same as B200 |
| H100 / A100-80GB | 80 GB | experiment 01 for all listed models (14B bf16 ≈ 28 GB weights + KV cache at 16k fits); RL: 1.7B/4B on 1 GPU, 8B needs 2 (TP=2), 14B needs 2–4 |
| A100-40GB / older | ≤ 40 GB | ≤ 4B sampling only; do not plan RL on them |

Rules: prefer the host with the most free B200s, then H200s; never take a GPU with another user's process or > 10% utilization; one trainer per host later; prefer more free CPU cores when Lean checking is on the critical path (experiment 01's kernel scoring runs 3–14 tasks per minute per scorer). Record the host, the GPU indices (`CUDA_VISIBLE_DEVICES`) and the reason at the top of the inventory file.

## 3. GPU discipline (CLAUDE.md; agents-config Trigger Rule 9)

1. **Baseline:** the inventory above, at the moment of launch.
2. **Estimate:** GPU-hours and wall-clock from the experiment's README/PROTOCOL and the chosen GPU; write it into the experiment's `results.md` under "Compute estimate".
3. **Ask Brando** before launching anything longer than a 5-task preflight, with the estimate and the host; proceed only on his yes (or when his message already says to go, as it does for experiment 01: "just do the experiment ... Go").
4. **Launch** (below), **verify** the first cells end to end (the experiment's own scorer controls), and **clean up**: stop vLLM, free the GPUs, leave nothing running you do not own.

## 4. Set up the work root and launch

```bash
export WR=/lfs/$(hostname)/0/$USER/rl4cv_<experiment-number> && mkdir -p $WR && cd $WR
git clone https://github.com/brando90/rl-4-code-verification.git && cd rl-4-code-verification
make external          # pinned veribench, frozen scorer, rl-env-scaling fork (external/deps.lock.json)
python3 -m venv .venv && . .venv/bin/activate && make install && pip install -e ".[gen]"   # vLLM
make test
# Lean, only if the experiment compiles files on this host: elan + leanprover/lean4:v4.22.0, then `lake build` in external/veribench (long; use tmux rl4cv-lake-build)
tmux new -s rl4cv-<experiment-number> -d
tmux send-keys -t rl4cv-<experiment-number> "cd $WR/rl-4-code-verification && . .venv/bin/activate && export CUDA_VISIBLE_DEVICES=<chosen> && claude" Enter
```

Inside that Claude Code session paste the experiment's `expt_vN/cc.md` (or run `claude -p "$(cat experiments/<folder>/expt_vN/cc.md)"`). Record every pinned version the experiment asks for (vLLM, torch, CUDA driver, Lean, Mathlib commit, Hugging Face revisions).

## 5. Report back

Commit the inventory, the experiment's `results.md` and `expt_vN/results/` summaries with explicit pathspecs; `make test`; push to `main`. Say in one line which host and GPUs are in use, what is running in which tmux session, and the next check time. If any host was unreachable or the GPU rule could not be met, say so in the inventory rather than working around it silently.

**TL;DR:** inventory → pick B200/H200/H100 host → estimate and ask → set up under `/lfs` → run the experiment's `cc.md` in tmux → verify, clean up, report.

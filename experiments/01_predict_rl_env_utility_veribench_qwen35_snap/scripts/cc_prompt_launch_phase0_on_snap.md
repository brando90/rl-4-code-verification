# Prompt — inventory SNAP GPUs, pick the right host, and launch experiment 01 Phase 0 (paste into Claude Code locally)

**TL;DR:** From your laptop (Kerberos/SSH to SNAP working) or a SNAP login shell: (1) inventory every host you can reach — GPU model/count/memory/free, CPUs, `/lfs` space, logged-in users — and commit it as `results/snap_gpu_inventory_<MM-DD-YYYY>.md` (it doubles as the material for the ilwiki Koyejo page); (2) pick a host by the GPU rule below (B200 preferred, then H200, then H100/A100-80GB); (3) set up `/lfs/$(hostname)/0/brando9/rl4cv_expt01/` with clones of `rl-4-code-verification`, `veribench` and the `rl-env-scaling` fork, a venv with vLLM, elan + Lean v4.22.0 and a built Mathlib; (4) run the Phase 0 runbook [`cc_runbook_phase0_coverage_census.md`](cc_runbook_phase0_coverage_census.md) inside a named tmux session on that host. No RL training, no judge calls, no personal API keys anywhere in Phase 0.

Paths: `E` = `experiments/01_predict_rl_env_utility_veribench_qwen35_snap` in `rl-4-code-verification`. Read `E/README.md` (§3 recipe, §7 compute, §9 gates) before starting. Work only under `/lfs`, never under DFS `~`.

## 1. Inventory every reachable host

Hosts to try (owner in parentheses; add any others you know of): `skampere1`, `skampere2`, `skampere3` (Koyejo lab); `hyperturing1`, `hyperturing2`, `mercury1`, `mercury2`, `ampere1`, `ampere2` (InfoLab/SNAP — Koyejo members have accounts, the lab does not own them). Use the full `.stanford.edu` hostnames your SSH config expects.

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

Write `E/results/snap_gpu_inventory_<MM-DD-YYYY>.md`: one row per host — host, owner (Koyejo lab / InfoLab access-only), GPU model × count, memory per GPU, GPUs free right now (0% utilization and no other user's process), CPU cores, RAM, `/lfs` free, users logged in, docker access, reachable (yes/no + error). Unreachable hosts stay in the table as unreachable. Do not omit anything; this table is also what goes on the wiki.

## 2. Choose the host and GPUs (rule, in order)

| GPU | Memory | OK for |
|---|---|---|
| B200 | 180 GB | everything: 1 GPU per 2B/4B trajectory, 2 per 9B trajectory (the paper's split); Phase 0 sampling of any scale on 1 GPU |
| H200 | 141 GB | same as B200 |
| H100 / A100-80GB | 80 GB | Phase 0 sampling for all three scales (9B bf16 ≈ 18 GB weights + KV cache at 16k context fits); later RL: 2B/4B on 1 GPU, 9B needs 2 (TP=2) |
| A100-40GB / older | ≤ 40 GB | 2B Phase 0 only; do not plan RL on them |

Rules: prefer a host with ≥ 2 free B200s (Phase 0 needs one for vLLM; the second lets the next scale start while the verifier pool drains); never take a GPU with another user's process or > 10% utilization; never plan two trainers on one host later; prefer the host with the most free CPU cores, because Lean compilation is the Phase 0 bottleneck (`nproc/2` verifier workers). Record the chosen host, the GPU indices you will use (`CUDA_VISIBLE_DEVICES`), and the reason at the top of the inventory file.

## 3. Set up the work root on the chosen host

```bash
export WR=/lfs/$(hostname)/0/brando9/rl4cv_expt01 && mkdir -p $WR && cd $WR
git clone https://github.com/brando90/rl-4-code-verification.git
git clone https://github.com/brando90/veribench.git
git clone https://github.com/brando90/rl-env-scaling.git        # Brando's fork of madanva/rl-env-scaling
python3 -m venv venv && . venv/bin/activate
pip install -U pip && pip install "vllm" pyarrow pyyaml numpy pandas tqdm && pip install -e rl-env-scaling
# Lean: the CI-pinned toolchain (see veribench/.github/workflows/ci.yml)
curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain leanprover/lean4:v4.22.0
( cd veribench && lake build )   # long; run inside tmux `rl4cv01-lake-build`
```

Record every pinned version (vLLM, torch, CUDA driver, Lean, Mathlib commit from `veribench/lake-manifest.json`, HF revision hashes of `Qwen/Qwen3.5-2B`, `-4B`, `-9B`) in `E/config.yaml`. GitHub token for private pulls: `~/keys/.brando90_github_token.txt` (never print it).

## 4. Launch Phase 0

```bash
tmux new -s rl4cv01-phase0 -d
tmux send-keys -t rl4cv01-phase0 "cd $WR/rl-4-code-verification && . $WR/venv/bin/activate && export CUDA_VISIBLE_DEVICES=<chosen> && claude" Enter
```

Inside that Claude Code session, paste the whole of `E/scripts/cc_runbook_phase0_coverage_census.md` as the prompt (or run it non-interactively: `claude -p "$(cat E/scripts/cc_runbook_phase0_coverage_census.md)"`). Start with `Qwen/Qwen3.5-2B`; do not start 4B/9B until the 2B verifier controls (`phase0_verifier_controls.md`) pass.

## 5. Report back

When the census is written: commit `E/results/*.md`, `E/manifests/*.jsonl`, `E/config.yaml` and `E/private/status.json` with explicit pathspecs, push, and state in one line whether the Phase 0 → 1 gate (README §9) passed. If any host was unreachable or any GPU rule could not be satisfied, say so in the inventory file rather than working around it silently.

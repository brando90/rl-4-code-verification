# Experiment 18c results (live, started 11-25-2026)

**Status:** RUNNING. 48 runs (16 environments x 3 seeds), budget 2,000,000 generated response tokens per run. Protocol and forecasts frozen in commit 88b7b196 (pushed 11-25-2026 12:06 PST), before any run.

**Harness / model:** custom PyTorch/HF GRPO (`expt_18b` grpo.py, train.py via train18c.py), Qwen3-1.7B thinking off, vLLM 0.30.0 post-eval. No agent harness, no model API, no DT label. No spend.

## Jobs (skampere2, 8x H200 shared, brando9)

| date (PT) | host | job id | what | state |
|---|---|---|---|---|
| 11-25-2026 12:14 | skampere2 | job-c5d6288f | pre-eval of base model (GPU 5) | exit 0 (`PRE EVAL OK`) after fixing `VLLM_USE_FLASHINFER_SAMPLER=0` (no nvcc on host; commit 5790bab5) |
| 11-25-2026 12:17 | skampere2 | job-744bb910 | worker GPU 4 | running (12 h) |
| 11-25-2026 12:18 | skampere2 | job-d89be4d9 | worker GPU 5 | running |
| 11-25-2026 12:18 | skampere2 | job-280d0157 | worker GPU 6 | running |
| 11-25-2026 12:18 | skampere2 | job-b8e7c87c | worker GPU 7 | running |

First training job started 12:17 PT, after freeze commit 88b7b196 (12:06). Workers claim cells by mkdir, stop claiming after 11 h; failures go to `failed_cells.txt` (rule: re-run once; stop and report if more than 4 of 48 fail twice). Expected about 9 h with 4 workers.

Results (analysis with `analyze18c.py`, predictions in `PROTOCOL_18c.md`) will be added here when all runs finish.

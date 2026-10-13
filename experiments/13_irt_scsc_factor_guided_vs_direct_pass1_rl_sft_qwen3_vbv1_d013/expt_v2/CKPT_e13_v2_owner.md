# Experiment 13 version 2 owner checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/CKPT_e13_v2_owner.md>

**TLDR:** Single-writer setup for `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`, version 2. No scientific measurement has started; publish this record and the live results before fixtures.

Created: 10-13-2026 11:44 PDT
Last updated: 10-13-2026 11:44 PDT

- Status: SETUP; R0 fixtures pending, downstream gates unadmitted.
- Owner: skampere1, tmux `codex-rl4cv-e13v2-owner`; Codex `gpt-6-astra`, effort `high` (runbook worker pin), command-line interface 0.154.0; observed full access `danger-full-access`, approvals `never`.
- Owner native process: 887384; boot `839e7dd6-64e1-4a80-9498-31d30b3cc2df`. Launch evidence: `/lfs/skampere1/0/brando9/rl4cv_e13v2/owner_launch.json`. First useful actions: read binding plans, inspect clean checkout and process inventory.
- Work root: `/lfs/skampere1/0/brando9/rl4cv_e13v2`; owned clone `rl-4-code-verification`, branch `main`, starting revision `1e0c8f85a5943997ee2124180f7e492db3ca92b8`.
- Coordination: no live version 1 session or executable found. Pattern matches in the current owner's arguments are the pasted runbook, not a version 1 writer. Master checkpoint remains separately owned.
- Version 1 preservation: complete file digest inventory at `$WR/state/v1_baseline_hashes.json`; version 1 files stay byte-identical.
- Environment: pinned Lean and scorer under `/lfs/skampere1/0/brando9/rl4cv_e08/` read-only. New virtual environment, caches and temporary files under this work root.
- Resources: no accelerator allocation or model calls; setup and fixtures use central processors. Preflight available memory 1,939 GiB; filesystem free 5.4 TiB. Cell concurrency is not chosen until train diagnostics measure memory.
- Denominators: train/validation/test tasks 539/135/222; full reproduction 38,784 unique cells; base 21,504 plus ladder 20,520 minus overlap 3,240. Parent unavailable ladder 5,400 stays separate. Diagnostic target 300 rejected plus 100 measured train cells, selected by identifier only.
- Chronology: no validation or test factors computed in version 2; lock precedes those measurements. Historical test content remains opaque.
- Authorization: verbatim Stanford Network Analysis Project pre-approval in `cc.md`; no new charges or provider-key route used.
- Exact next actions: finish private environment setup; run `make test`; publish these two records. Implement and self-test `watchdog_e13v2.sh`, then build the elaborator-backed probe and independent R0 fixture expectations.
- Blockers: none established; no gate result yet.

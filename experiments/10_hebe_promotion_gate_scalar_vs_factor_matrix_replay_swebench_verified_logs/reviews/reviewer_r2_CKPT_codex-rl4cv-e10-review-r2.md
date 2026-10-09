# Checkpoint: promotion-policy protocol revision 2 review

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/CKPT_codex-rl4cv-e10-review-r2.md>

**TLDR:** Review COMPLETE for `10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs`: 3 blocking, 5 major, 1 minor finding; lock remains blocked. This local checkpoint and its linked review/ledger are unpublished.

Created: 10-09-2026 16:25 PDT
Last updated: 10-09-2026 16:33 PDT

- Deployment: `deploy_7f1f1fb8b11149c4b7a411039b61888d`; thread `01a122fa-fe6d-7cb0-ad46-a8288a05530f`.
- Workdir: `/Users/brandomiranda/vb_worktrees/rl4cv-e10-review-fable-v2`; reviewed commit `94cb41468425219eb2a6b4c63c2c05e7732e6cdf`; shared rules `962fac086767aa827b5f1bb944d43be7e31c0775`.
- Verified runtime: Codex command-line interface 0.162.1, `gpt-6-astra`, effort `ultra`, default `~/.codex` profile (no named override); account personal/work label unverified. Full access, approval never, from session turn_context and config. No provider calls or new spend.
- Deliverable: `experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md`; 9 numbered evidenced findings and fixes, below the runbook's approximate 2,000-word limit.
- Live ledger: `experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/results.md`. Scope decision: the user's task message expressly authorizes ledger/checkpoint writes beyond the runbook's one review file. No other repository files edited. Two pre-existing untracked runbooks preserved.
- Verification: existing unit suite 8/8 passed in 1.56 s; `git diff --check` passed; protocol, both scripts, README and test source matched HEAD byte-for-byte. Final artifact checks passed: 9 sequential findings, 3/5/1 severities, 1,579 words, correct headers, no trailing whitespace, only the three authorized documents changed plus two pre-existing runbooks.
- Exact unit command: `PYTHONDONTWRITEBYTECODE=1 uv run --isolated --no-project --python 3.12 --with numpy --with pytest python -m pytest -q -p no:cacheprovider tests/test_e10_replay.py`. The supplied Python had numpy but no pytest.
- Counterexamples: weights [2,1,0], q=.5 retained 0 versus 1 by order; empty near population raised IndexError; zero accepted promotions reported harm 0; NaN split support changed averages; undefined predictive difference counted nonpositive; design condition 205,219 accepted by protocol was rejected using normal-matrix condition 4.2115e10; missing resolution/nonfinite gate accepted; equal-risk comparator ties used gain before hash.
- Precision check: one identity + 30 bootstrap weights on synthetic seed 1; 31/31 correlations defined in float32 and float64; maximum difference 3.72e-8 primary and 2.56e-7 with marginal controls. No material ordinary-case precision issue observed.
- Timing: synthetic signal seed 1, 164 × 424, one split × 1,000 draws, q=.5/.25/.75, split seed 20261009, bootstrap seed 20261010; `run` 4.8 s, process 6.20 s, max resident memory 1,559,412,736 bytes. About 80 minutes is a linear extrapolation only; full-run peak memory unmeasured. Synthetic temporary directories auto-removed; no real outcomes loaded.
- Helper `/root/prior_findings_lookup` finished a bounded read-only prior-finding lookup; inherited runtime full access/approval never and first useful read verified. No children or test jobs remain running. Subscription allowance unknown; only one bounded helper used.
- Outstanding scientific work: implement report fixes and verify them in a separately authorized editing task; preserve current failed lock verdict. This review task authorizes no source fix, real replay, forecast, commit or push.
- Next command for a successor: `cat experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md`. Resume this completed review only to clarify its evidence; source-repair work needs its own brief. Native resume: `codex resume 01a122fa-fe6d-7cb0-ad46-a8288a05530f` from this workdir.

Input/review hashes (SHA-256):
- `PROTOCOL.md`: `f8ae298a064e0e602c47e775f909a5c1dad1214b1c8f30e709ba316b4180d602`
- `expt_v1/analyze_e10.py`: `8860874ed9442b94fe7fe03922db35dd3320d4471138599d1d4b26cd875fc330`
- `expt_v1/synthetic_e10.py`: `b6c40723b52cc4322ec8082c3bb4ea52e02a444e56d4ba1f29e567346a692ef5`
- `reviews/runbook_review_r2.md`: `ea30b8fb090caee77e8674e94c72c540c39ff86b8c7d15e2f0c36bbe2d60a4e3`
- `reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md`: `058342950880fa15c3237e514a64eab1e0097fe0c36231b6588c631cb4c42840`

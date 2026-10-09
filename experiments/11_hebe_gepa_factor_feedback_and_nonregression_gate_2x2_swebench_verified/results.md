# Experiment 11 results: AlphaHebe 2×2 factor feedback × non-regression gate on SWE-bench Verified

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/results.md>

**TLDR:** Blocked before any technical gate. AlphaDiana-dev access was requested from Andrew by email on 10-09-2026, and integration issues #26–#30 are filed and assigned. The model route is Valkyrie per Brando ("use valks for model calls") but is not yet verified. No run, call or measurement has happened.

**Status:** BLOCKED (10-09-2026).

**Last updated:** 10-09-2026.

| Gate | State | Evidence |
|---|---|---|
| T0 access and pinned install | BLOCKED: AlphaDiana-dev returns 404 for `brando90` (AlphaApollo-v3-dev is optional for this path); access requested from Andrew 10-09-2026 (Gmail message `1a122fcb1afaf8d8`) | `gh api repos/AndrewZhou924/AlphaDiana-dev` → 404 on 10-09-2026 |
| T1 Diana per-record factor fields | NOT STARTED | [#27](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/27) (@zongze-lee, @T1an-Cheng) |
| T2 leakage audit of the complete optimizer input | NOT STARTED | [#28](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/28) (@tsrigo, @CatWongCoi) |
| T3 keyed evidence and pluggable promotion gate | NOT STARTED | [#29](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/29) (@CatWongCoi, @ShawFeng99) |
| T4 Valkyrie (or vLLM for open weights) model route | NOT STARTED; Brando chose Valkyrie on 10-09-2026 | — |
| T5 dry run | NOT STARTED | — |
| T6 cost estimate and approval | NOT STARTED | — |

## Issue links

- [#26](https://github.com/AndrewZhou924/AlphaHebe-dev/issues/26): proposal (@AndrewZhou924), with sub-issues:
  - #27: Diana factor fields;
  - #28: Hebe factor feedback and leakage audit;
  - #29: keyed evidence and non-regression gate;
  - #30: exporting existing run records for experiment 10 phase B (@ShawFeng99, @AndrewZhou924).

## Deviations and open questions

None yet.

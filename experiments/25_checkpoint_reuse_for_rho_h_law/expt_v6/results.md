# Night 6 (Stage 1, CPU toy): dense checkpoint reuse versus independent runs

Task AT-1790, follow-up of AT-1776. Protocol and predictions were frozen before any outcome was read
(`PROTOCOL.md`, `forecast/forecast_night6.json`, commit 596d9e6e). Raw trajectories: `results/` (492 files, commit bad050f1).
Machine-readable numbers: `analysis.json` (2,000 bootstrap draws; runs resampled within groups plus one shared prompt-weight draw).
Setting S2 (Adam lr 3e-4, KL coefficient 0.1, 16 prompts x group 8), K = 4 tokens, U scored on 4,000 target prompts,
checkpoints every 25 steps (16 per 400-step run). Scales n1-n3 for P1/P3/P5 (12 cells), n4 added where stated.

This note covers P1, P2, P3, P5 and the variance decomposition. P4 and P6-P9 are in the parent folder's `results.md` (AT-1789).

## Verdicts

| # | Prediction (frozen) | Verdict | Numbers |
|---|---|---|---|
| P1 | Dense reuse (A) is no worse than independent runs (B) at equal compute: RMSE(A) <= RMSE(B) + one seed SD | HOLDS | Curve RMSE A 0.00283, B 0.00482; A-B 95% CI [-0.0022, 0.00003]; margin (one seed SD) 0.0035. Forecast RMSE at n3: A 0.0530, B 0.0536; A-B CI [-0.0026, 0.0012]; margin 0.0049 |
| P2 | Law fit on the first 50% of each trajectory matches the full fit: C_max RMSE ratio <= 1.25 and rank-accuracy gap <= 0.10 | HOLDS (primary law arm) | RMSE ratio 1.0098 (CI [1.0056, 1.0158]); 25% prefix 1.0153. Rank accuracy: n4 prefix 0.433 vs full 0.417 (gap +0.017, CI [-0.025, 0.017]); n3 0.475 for both (gap 0) |
| P3 | Rolling rho_i, H_i form beats three baselines in leave-one-environment-out and leave-one-trajectory-out CV | FAILS (no advantage) | LOEO MSE: rolling 1.352e-5, zero 1.391e-5, previous 2.892e-5, start-only 1.467e-5. LOTO MSE: rolling 1.282e-5, zero 1.391e-5, previous 2.892e-5, start-only 1.298e-5. 2,016 increment rows, C0 = 270 steps |
| P5 | A cosine schedule changes the effect of budget relative to a constant schedule (two-sided; same sign at both budgets) | HOLDS, negative sign | Difference (cosine minus constant effect): -0.0053 at 100 steps (CI [-0.0085, -0.0021]); -0.0091 at 200 steps (CI [-0.0128, -0.0055]) |

Compared with the frozen probabilities: P1 (0.8) held, P2 (0.4) held, P3 (0.2 to hold) failed, P5 (0.6) held in the predicted direction.

## What each result means

**P1.** On the toy, one dense trajectory with 16 checkpoints reproduces the cell's curve at least as well as four short plus two medium plus one long
independent runs at the same 1,200-step budget per cell. The A-B interval for the curve fit reaches 0 at its upper end, so the supported claim is
"not worse", not "better". Forecast error is about 5 percentage points for both arms: the law forecasts poorly in absolute terms, and reuse does not change that.

**P2.** Fitting the law on the first half of each trajectory costs about 1% in RMSE. Rank accuracy is 0.42 to 0.48, which is near chance, so the
equality is between two fits that both have little ranking skill, not evidence that the law works. The pre-registered primary arm is the pooled law. The
per-cell saturating and sigmoid curve fits (secondary, point estimates only in `analysis.json`) do not pass the 1.25 ratio (saturating about 3.2, sigmoid about 15);
the sigmoid arm is unstable when the trajectory has not yet flattened by C_max.

**P3.** The rolling form beats "previous" in both CVs and beats start-only in LOEO and zero in LOTO, but the intervals for rolling versus zero in LOEO
and rolling versus start-only in LOTO include 0. It does not beat all three baselines in both CVs, so P3 fails as written.

**P5.** Under a cosine schedule the budget effect is more negative than under a constant schedule at both budgets. Interpretation: do not mix cosine-decayed
runs with constant-schedule runs, and do not read a mid-run checkpoint of a long cosine run as a short run. Dense reuse needs a constant (or warmup-stable) schedule.

## Variance decomposition

Within-run variance (checkpoint-to-checkpoint noise around the fitted curve) over seed variance of the fitted curves: 2.6 (n1), 2.3 (n2), 3.0 (n3).
Seed SD at C_max: 0.0024, 0.0048, 0.0055. Within-run noise is the larger part, which is the case where adding checkpoints from the same run buys more than adding seeds.

## Outcome label (plan section 5)

From the toy alone, P1 and P2 hold, so the toy supports ADOPT (reuse dense checkpoints). The full label also needs the real-model pilot (Stage 2), which this task does not cover.
The label is not WRONG DOMAIN on the toy evidence, but the toy cannot decide that.

## Caveats

- Toy only: K = 4 tokens, every response admitted, KL coefficient 0.1 saturates U, and n4 is a forgetting regime (U often below 0).
- Three seeds per cell: intervals are coarse. The pool truth is a 12-run mean, itself noisy.
- The law's absolute forecast error is about 5 pp and its rank accuracy is near chance, so "reuse is as good as independent runs" means both are poor.
- Cross-hardware reproduction is exact only on the same machine. Runs here were on skampere2: 538 of 576 A-run cells at steps 25, 50 and 100 equal Night 5 exactly, the rest differ by at most 0.002 (0.2 pp), from CPU floating-point differences. Locally, n1 e00 seed 0 reproduces exactly. `expt_v2/policy.py` is unedited.
- Amendment 1 (PROTOCOL.md): the first skampere2 launch crashed on `torch.set_num_interop_threads`; the call is now wrapped in try/except. No outcome existed, and the frozen hash is of the pre-fix `night6.py`.
- Full `pytest` shows 7 failures in the e08 and e13 test files, which this work did not touch; I did not compare against a clean baseline. The 7 tests in `tests/test_e25_night6.py` pass.
- Logs (30 MB) and checkpoints (421 MB) stay on skampere2 at `/lfs/skampere2/0/brando9/at1790/repo/.../expt_v6/{logs,ckpt}`; they are not committed.

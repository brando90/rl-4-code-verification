"""Score experiment 10's frozen predictions (H1, H2a, H3 gates, practical target) from an analyze_e10.py output JSON, exactly as PROTOCOL.md revision 3 and e10_forecast.json define them; no statistic is recomputed."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PER_CELL_SHA256 = "f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d"
GUARD_LOWER_BOUND = -0.01  # utility guard: 95% lower bound of (recommended - comparator) mean test dpass (PROTOCOL H3)
PRACTICAL_TARGET = 0.20  # relative HPR reduction versus S0+ (reported, not a decision rule)
POLICIES = ("S0plus", "S1", "S2", "S3", "R0", "R1", "R2", "R3", "R3h")
CONTRASTS = (("R0", "R2", "C_bin"), ("R2", "R3", "C_fac"), ("R0", "R3", "C_fac0"), ("R0", "R3h", "C_hid"), ("R0", "R1", "C_agg"),
             ("S0plus", "R3", "C_strict(R3)"), ("S0plus", "R2", "C_strict(R2)"), ("S0plus", "S3", "S0+-S3"), ("S2", "S3", "S2-S3"),
             ("S0plus", "S2", "S0+-S2"), ("S0plus", "S1", "S0+-S1"))


def _f(x) -> float:
    return math.nan if x is None else float(x)


def fmt(m: dict | None, nd: int = 4) -> str:
    """`x [lo, hi] p-val=n/a` with the split 5th-95th range; undefined stays undefined."""
    if not m or not math.isfinite(_f(m.get("estimate"))):
        return "undefined"
    s = f"{m['estimate']:.{nd}f}"
    if "lo" in m and math.isfinite(_f(m["lo"])) and math.isfinite(_f(m["hi"])):
        s += f" [{m['lo']:.{nd}f}, {m['hi']:.{nd}f}] p-val=n/a"
    else:
        s += " [undefined interval] p-val=n/a"
    if "split_5_95" in m:
        s += f" (split 5-95%: {m['split_5_95'][0]:.{nd}f} to {m['split_5_95'][1]:.{nd}f})"
    return s


def positive_excluding_zero(m: dict | None) -> bool | None:
    """True iff the estimate is > 0 and the 95% interval's lower bound is > 0; None when undefined."""
    if not m or not all(math.isfinite(_f(m.get(k))) for k in ("estimate", "lo", "hi")):
        return None
    return m["estimate"] > 0 and m["lo"] > 0


def guard_passes(m: dict | None) -> bool | None:
    """Utility guard on a `dpass_gain_of_second` member (recommended minus comparator): lower bound > -0.01."""
    if not m or not math.isfinite(_f(m.get("lo"))):
        return None
    return m["lo"] > GUARD_LOWER_BOUND


def support(fam: dict) -> str:
    return (f"status={fam.get('status')}; splits {fam.get('splits_admitted')}/{fam.get('splits_considered')} admitted; "
            f"draws {fam.get('draws_valid')}/{fam.get('draws_total')} valid")


def score(out: dict, q_primary: str = "0.5") -> dict:
    near = out["populations"]["near"]
    verdict = {"population_status": near["status"], "splits_degenerate": near["splits_degenerate"], "splits_used": near["splits_used"],
               "pairs_per_split_median": near.get("pairs_per_split_median")}
    # H2a: partial Spearman(HRM_V, test loss fraction | losses_V, gains_V, pass1_V(I)) > 0 with its interval excluding 0.
    h2 = near["H2"]["hrm"]
    h2m = h2.get("members", {}).get("hrm")
    h2_ok = h2.get("status") == "ok"
    pos = positive_excluding_zero(h2m)
    verdict["H2a"] = {"value": fmt(h2m), "support": support(h2), "frozen_prediction": "> 0 with interval excluding 0",
                      "verdict": "SUPPORTED" if (h2_ok and pos) else ("FAILED (undefined or inconclusive support)" if (pos is None or not h2_ok) else "FAILED (interval includes 0 or estimate <= 0)")}
    main = near["H3"][q_primary]["main"]
    mem = main.get("members", {})
    ok = main.get("status") == "ok"
    reasons: list[str] = []
    if not ok:
        reasons.append("undefined_or_inconclusive_support")

    def contrast(a: str, b: str) -> tuple[dict | None, dict | None]:
        return mem.get(f"{a}-{b}.hpr_abs_reduction"), mem.get(f"{a}-{b}.dpass_gain_of_second")

    c_fac, g_fac = contrast("R2", "R3")
    c_fac0, g_fac0 = contrast("R0", "R3")
    c_bin, g_bin = contrast("R0", "R2")
    fac_pos, fac0_pos, bin_pos = positive_excluding_zero(c_fac), positive_excluding_zero(c_fac0), positive_excluding_zero(c_bin)
    fac_guard = (guard_passes(g_fac), guard_passes(g_fac0))
    bin_guard = guard_passes(g_bin)
    for v in (fac_pos, fac0_pos, bin_pos, *fac_guard, bin_guard):
        if v is None and "undefined_or_inconclusive_support" not in reasons:
            reasons.append("undefined_or_inconclusive_support")
    factor_gate = bool(ok and fac_pos and fac0_pos and all(fac_guard))
    binary_gate = bool(ok and not factor_gate and bin_pos and bin_guard)
    if not factor_gate and not binary_gate:
        if (fac_pos is False or fac0_pos is False) and bin_pos is False:
            reasons.append("interval_includes_zero")
        elif fac_pos and fac0_pos and not all(fac_guard):
            reasons.append("utility_guard_failed")
        elif bin_pos and bin_guard is False:
            reasons.append("utility_guard_failed")
        elif fac_pos is False or fac0_pos is False or bin_pos is False:
            reasons.append("interval_includes_zero")
    verdict["H3"] = {
        "q": q_primary, "support": support(main),
        "C_fac=R2-R3": fmt(c_fac), "C_fac0=R0-R3": fmt(c_fac0), "C_bin=R0-R2": fmt(c_bin),
        "guard_R3_minus_R2": fmt(g_fac), "guard_R3_minus_R0": fmt(g_fac0), "guard_R2_minus_R0": fmt(g_bin),
        "factor_gate": "RECOMMEND" if factor_gate else "NOT ESTABLISHED",
        "binary_gate": "RECOMMEND" if binary_gate else ("not evaluated (factor gate recommended)" if factor_gate else "NOT ESTABLISHED"),
        "recommendation": "factor-matrix promotion check" if factor_gate else ("binary per-item non-regression" if binary_gate else "no recommendation: superiority or retained utility not established"),
        "reason_codes": [] if (factor_gate or binary_gate) else sorted(set(reasons)),
    }
    practical = {}
    for a in ("R3", "R2"):
        rel = mem.get(f"S0plus-{a}.hpr_rel_reduction", {})
        est = rel.get("estimate")
        practical[f"S0plus-{a}"] = {"relative_hpr_reduction": est, "meets_0.20_target": (est is not None and est >= PRACTICAL_TARGET),
                                    "abs": fmt(mem.get(f"S0plus-{a}.hpr_abs_reduction"))}
    verdict["practical_target"] = practical
    h1 = near["H1"]
    verdict["H1"] = {k: fmt(h1.get("members", {}).get(k)) for k in ("hpr", "share_any_loss", "mean_lossfrac", "mean_dpass_t")}
    verdict["H1"]["support"] = support(h1)
    return verdict


def tables(out: dict) -> str:
    """Markdown tables for results.md: policies and contrasts per q, H2 sensitivities, deployable rule, predictive comparison."""
    lines: list[str] = []
    for pop in ("near", "eligible"):
        p = out["populations"][pop]
        lines.append(f"\n### Population `{pop}`: {p['status']}; degenerate splits {p['splits_degenerate']}/{out['settings']['splits']}; "
                     f"median pairs per split {p.get('pairs_per_split_median')}")
        h1 = p["H1"]
        lines.append(f"\nH1 ({support(h1)}):\n")
        lines.append("| Statistic | Value |\n|---|---|")
        for k in ("hpr", "share_any_loss", "mean_lossfrac", "mean_dpass_t"):
            lines.append(f"| {k} | {fmt(h1['members'].get(k))} |")
        lines.append("\nH2 partial Spearman correlations:\n")
        lines.append("| Specification | Value | Support |\n|---|---|---|")
        for k, fam in p["H2"].items():
            lines.append(f"| {k} | {fmt(fam.get('members', {}).get(k))} | {support(fam)} |")
        for q, qd in p["H3"].items():
            main, aux, rec = qd["main"], qd["aux"], qd["recall"]
            lines.append(f"\nH3 at q = {q} (main family: {support(main)}; aux: {support(aux)}; recall: {support(rec)}):\n")
            lines.append("| Policy | HPR | mean Δpass1_E | mean losses_E/\\|E\\| | recall | rate |\n|---|---|---|---|---|---|")
            for name in POLICIES:
                m, a, r = main.get("members", {}), aux.get("members", {}), rec.get("members", {})
                lines.append(f"| {name} | {fmt(m.get(f'{name}.hpr'))} | {fmt(m.get(f'{name}.mean_dpass_t'))} | "
                             f"{fmt(a.get(f'{name}.mean_lossfrac'))} | {fmt(r.get(f'{name}.recall'))} | {fmt(a.get(f'{name}.rate'), 3)} |")
            lines.append("\n| Contrast (first − second HPR; positive = second safer) | HPR reduction | relative | Δpass1_E gain of second (utility guard) |\n|---|---|---|---|")
            for a, b, label in CONTRASTS:
                m = main.get("members", {})
                rel = m.get(f"{a}-{b}.hpr_rel_reduction", {}).get("estimate")
                rel_s = "undefined" if rel is None else f"{rel:.3f}"
                lines.append(f"| {label} = {a} − {b} | {fmt(m.get(f'{a}-{b}.hpr_abs_reduction'))} | {rel_s} | {fmt(m.get(f'{a}-{b}.dpass_gain_of_second'))} |")
        dz = p["deploy_zero_loss"]
        lines.append(f"\nDeployable rule (net_V ≥ 1 and losses_V = 0): acceptance {fmt(dz['acceptance']['members'].get('acceptance'))} "
                     f"({support(dz['acceptance'])}); HPR given accepted {fmt(dz['hpr_given_accepted'].get('members', {}).get('hpr'))} "
                     f"({support(dz['hpr_given_accepted'])}); median accepted pairs per split {dz['n_accepted_per_split_median']}.")
        pr = p["H2_predictive"]
        lines.append(f"\nH2(c) predictive comparison (attempted splits {pr['attempted_splits']}, median fit pairs {pr['n_fit_median']}, median eval pairs {pr['n_eval_median']}):\n")
        lines.append("| Model | defined splits | median out-of-sample R² | split 5-95% |\n|---|---|---|---|")
        for k in ("M0", "M1", "M2", "M2_minus_M1"):
            v = pr[k]
            rng = "undefined" if v.get("split_5_95") is None else f"{v['split_5_95'][0]:.4f} to {v['split_5_95'][1]:.4f}"
            med = "undefined" if v.get("median") is None else f"{v['median']:.4f}"
            extra = f"; share > 0: {v['share_positive']:.3f}" if k == "M2_minus_M1" and v.get("share_positive") is not None else ""
            lines.append(f"| {k} | {v['defined_splits']} | {med}{extra} | {rng} |")
    return "\n".join(lines)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--result", required=True)
    ap.add_argument("--out", help="write the verdict JSON here")
    ap.add_argument("--tables", action="store_true", help="print markdown tables for results.md")
    args = ap.parse_args(argv)
    out = json.loads(Path(args.result).read_text())
    assert out["settings"]["expect_sha"] == PER_CELL_SHA256, "output was not computed on the pinned per-cell input"
    assert (out["systems"], out["tasks"]) == (164, 424) or out["settings"]["sensitivity"] != "none", "cohort shape not reproduced"
    v = score(out)
    v["input_sha256_verified"] = PER_CELL_SHA256
    v["cohort"] = {"systems": out["systems"], "tasks": out["tasks"], "near_max_net_gain": out["near_max_net_gain"], "runtime_s": out["runtime_s"],
                   "settings": out["settings"]}
    text = json.dumps(v, indent=1)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")
    if args.tables:
        print(tables(out))


if __name__ == "__main__":
    main()

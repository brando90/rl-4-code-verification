"""TLDR: Render the numeric sections of experiment 07's results.md from analysis_e07.json and per_system_e07.csv, so no number is transcribed by hand."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

CORR = (("pearson", "Pearson r"), ("spearman", "Spearman ρ"), ("kendall_tau_b", "Kendall τ-b"))


def f3(v) -> str:
    return "undefined" if v is None else f"{v:+.3f}" if isinstance(v, float) and v < 0 else f"{v:.3f}" if isinstance(v, (int, float)) else str(v)


def ci(block: dict, key: str) -> str:
    """`[lo, hi]` with the defined/requested draw counts for one bootstrap unit."""
    iv = block.get(key)
    defined, requested = block["defined_draws"].get(key), block["requested_draws"]
    text = "undefined" if iv is None else f"[{iv[0]:.3f}, {iv[1]:.3f}]"
    return f"{text} ({defined}/{requested} draws defined)"


def corr_table(h: dict) -> list[str]:
    rows = ["| Statistic | Value | 95% task bootstrap | 95% system bootstrap |", "|---|---:|---|---|"]
    for key, label in CORR:
        rows.append(f"| {label} | {f3(h[key])} | {ci(h['bootstrap_95']['tasks'], key)} | {ci(h['bootstrap_95']['systems'], key)} |")
    return rows


def agreement_rows(h: dict) -> list[str]:
    rows = []
    for key, label in (("mean_scs4c", "Mean system SCS4C-T"), ("mean_pass1", "Mean system pass@1"),
                       ("mean_bias_scs4c_minus_pass1", "Mean bias (SCS4C-T − pass@1)"), ("mae", "Mean absolute error")):
        rows.append(f"| {label} | {f3(h[key])} | {ci(h['bootstrap_95']['tasks'], key)} | {ci(h['bootstrap_95']['systems'], key)} |")
    return rows


def verdict_h1(h: dict) -> str:
    rho = h["spearman"]
    if rho is None:
        return "unavailable (Spearman undefined)"
    return f"prediction {'holds' if rho >= 0.90 else 'fails'} (Spearman {rho:.3f} {'≥' if rho >= 0.90 else '<'} 0.90); construct check only, not evidence of usefulness"


def verdict_h1b(h: dict) -> str:
    rho, iv = h["spearman"], h["bootstrap_95"]["tasks"].get("spearman")
    if rho is None or iv is None:
        return "unavailable (Spearman or its task-bootstrap interval undefined)"
    if rho > 0 and iv[0] > 0:
        return f"**Positive**: partial credit carries capability signal (Spearman {rho:.3f}, task interval [{iv[0]:.3f}, {iv[1]:.3f}] excludes 0)"
    if rho < 0 and iv[1] < 0:
        return f"**Negative**: partial credit misleads (Spearman {rho:.3f}, task interval [{iv[0]:.3f}, {iv[1]:.3f}] excludes 0)"
    return f"**No evidence**: task interval [{iv[0]:.3f}, {iv[1]:.3f}] covers 0 (Spearman {rho:.3f})"


def verdict_h2(r: dict) -> str:
    if r.get("status") != "complete" or r["delta_median"] is None:
        return f"unavailable ({r.get('status')}; {r['defined']}/{r['splits']} splits defined)"
    ok = r["delta_median"] > 0 and r["share_delta_positive"] >= 0.60
    return (f"**{'Positive' if ok else 'No ranking advantage'}**: median Δ {f3(r['delta_median'])} "
            f"({'>' if r['delta_median'] > 0 else '≤'} 0), share Δ > 0 = {r['positive_splits']}/{r['share_denominator']} = "
            f"{r['share_delta_positive']:.3f} ({'≥' if r['share_delta_positive'] >= 0.60 else '<'} 0.60)")


def h2_table(h2: dict) -> list[str]:
    rows = ["| n_A | n_B | Splits defined / requested | Median Δ | 5th–95th percentile of Δ | Splits with Δ > 0 | Share Δ > 0 | Median ρ(SCS4C-T on A, pass@1 on B) | Median ρ(pass@1 on A, pass@1 on B) |",
            "|---:|---:|---|---:|---|---:|---:|---:|---:|"]
    for size, r in sorted(h2.items(), key=lambda kv: int(kv[0])):
        p = r["delta_p05_p95"]
        rows.append(f"| {r['n_A']} | {r['n_B']} | {r['defined']}/{r['splits']} | {f3(r['delta_median'])} | "
                    f"{'undefined' if p is None else f'[{p[0]:+.3f}, {p[1]:+.3f}]'} | {r['positive_splits']} | "
                    f"{'undefined' if r['share_delta_positive'] is None else format(r['share_delta_positive'], '.3f')} | "
                    f"{f3(r['spearman_scs4c_A_vs_pass1_B_median'])} | {f3(r['spearman_pass1_A_vs_pass1_B_median'])} |")
    return rows


def density_table(label: str, d: dict) -> list[str]:
    share = d["share_unresolved_with_partial_credit"]
    return [f"| {label} | {d['declared_cells']} | {d['measured_cells']} | {d['unmeasured_cells']} | {d['unresolved_cells']} | "
            f"{d['unresolved_with_partial_credit']} | {'undefined' if share is None else f'{share:.3f}'} | {d['resolved_but_score_below_1']} | {d['unresolved_but_score_1']} |"]


def per_system_table(rows: list[dict], top: int) -> list[str]:
    out = ["| Submission | SCS4C-T (common) | pass@1 (common) | T_fix mean | T_keep mean | Measured / 500 | SCS4C-T (own) | pass@1 (own) | pass@1 declared |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    inc = [r for r in rows if r["included"] == "True"]
    inc.sort(key=lambda r: -float(r["pass1_common_cohort"]))
    for r in inc[:top]:
        out.append(f"| `{r['submission']}` | {float(r['scs4c_t_common_cohort']):.3f} | {float(r['pass1_common_cohort']):.3f} | "
                   f"{float(r['t_fix_common_mean']):.3f} | {float(r['t_keep_common_mean']):.3f} | {r['measured']} | "
                   f"{float(r['scs4c_t_own_cohort']):.3f} | {float(r['pass1_own_cohort']):.3f} | {float(r['pass1_declared']):.3f} |")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, required=True, help="expt_v1/results directory")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()
    a = json.loads((args.results / "analysis_e07.json").read_text())
    rows = list(csv.DictReader((args.results / "per_system_e07.csv").open()))
    out: list[str] = []
    w = out.append
    w(f"**Analyzer status:** `{a['status']}`; locked settings: {a['locked_settings']}; seed {a['settings']['seed']}; "
      f"{a['settings']['boot']} bootstrap draws; {a['settings']['splits']} splits per size; sizes {a['settings']['sizes']}; inclusion ≥ {a['settings']['min_measured']:.0%} measured.")
    w("")
    v = a["validity_all_declared_systems"]
    w("### Counts")
    w("")
    w("| Quantity | Value |")
    w("|---|---:|")
    w(f"| Declared systems (pinned submission list) | {a['systems_total']} |")
    w(f"| Included systems (≥ 475/500 measured cells) | {a['systems_included']} |")
    w(f"| Excluded systems | {a['systems_total'] - a['systems_included']} |")
    w(f"| Declared tasks per system | {a['declared_tasks']} |")
    w(f"| Common-cohort tasks (measured for every included system) | {a['common_cohort_tasks']} |")
    w(f"| Declared cells (all systems) | {v['declared_cells']} |")
    w(f"| Measured cells (all systems) | {v['measured_cells']} |")
    w(f"| Unmeasured cells (all systems; listed in `per_cell_e07.jsonl.gz`) | {v['unmeasured_cells']} |")
    w(f"| Inconsistent measured cells (resolved ≠ (G=1, T_fix=1, T_keep=1)) | {v['inconsistent_cells']} / {v['measured_cells']} = {(v['inconsistent_fraction'] or 0):.4%} (stop rule 0.5%) |")
    w("")
    if "H1_scs4c_vs_pass1" in a:
        h1, h1b, h2, h3 = a["H1_scs4c_vs_pass1"], a["H1b_partial_credit_vs_pass1"], a["H2_held_out_prediction"], a["H3_signal_density"]
        w("### H1 — construct check: system SCS4C-T versus system pass@1 (common cohort)")
        w("")
        w(f"Usable systems: {h1['n_systems']} ({h1['excluded_systems']} with undefined scores excluded). p-val=n/a (no hypothesis test; intervals condition on the observed common cohort and are not task-and-system joint intervals).")
        w("")
        out.extend(corr_table(h1))
        out.extend(agreement_rows(h1))
        w("")
        w(f"- **Frozen prediction:** {a_pred(a, 'H1')}")
        w(f"- **Outcome:** {verdict_h1(h1)}.")
        w("")
        w("### H1b — partial credit on unresolved cohort cells versus pass@1")
        w("")
        w(f"Usable systems: {h1b['n_systems']} ({h1b['excluded_systems']} without unresolved cohort cells have undefined partial credit and are excluded, never zero: "
          f"{', '.join('`' + s + '`' for s in h1b['systems_without_unresolved_cells']) or 'none'}). p-val=n/a.")
        w("")
        out.extend(corr_table(h1b))
        w("")
        w(f"- **Frozen prediction:** {a_pred(a, 'H1b')}")
        w(f"- **Outcome:** {verdict_h1b(h1b)}.")
        w("")
        w("### H2 — held-out prediction from random task splits")
        w("")
        w("Δ = Spearman(SCS4C-T on A, pass@1 on B) − Spearman(pass@1 on A, pass@1 on B); B is the rest of the common cohort. "
          "Percentiles and shares summarise the split distribution; they are not population confidence intervals. Primary size n_A = 50; other sizes descriptive.")
        w("")
        out.extend(h2_table(h2))
        w("")
        w(f"- **Frozen prediction:** {a_pred(a, 'H2')}")
        w(f"- **Outcome at n_A = 50:** {verdict_h2(h2['50'])}.")
        w("")
        w("### H3 — signal density (descriptive)")
        w("")
        w("| Cohort | Declared cells | Measured | Unmeasured | Unresolved | Unresolved with SCS4C-T > 0 | Share | Resolved with score < 1 | Unresolved with score = 1 |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        out.extend(density_table("Included systems × common cohort", h3))
        out.extend(density_table("Included systems × own cohorts", a["own_cohort_signal_density"]))
        out.extend(density_table("All declared systems × all cells", v))
        w("")
        s = a["sensitivity_one_system_per_base_model"]
        w("### Sensitivity (protocol, not primary): one system per base model")
        w("")
        w(f"Status: {s['status']}. Selection: {s['selection']}. Systems: {s['n_systems']}; skipped (model not named): {len(s['skipped_systems'])}; common-cohort tasks: {s['common_cohort_tasks']}.")
        w("")
        if "H1_scs4c_vs_pass1" in s:
            w("| Hypothesis | Pearson r | Spearman ρ | Kendall τ-b | 95% task bootstrap of ρ | 95% system bootstrap of ρ | n systems |")
            w("|---|---:|---:|---:|---|---|---:|")
            for key, label in (("H1_scs4c_vs_pass1", "H1 (SCS4C-T vs pass@1)"), ("H1b_partial_credit_vs_pass1", "H1b (partial credit vs pass@1)")):
                h = s[key]
                w(f"| {label} | {f3(h['pearson'])} | {f3(h['spearman'])} | {f3(h['kendall_tau_b'])} | {ci(h['bootstrap_95']['tasks'], 'spearman')} | {ci(h['bootstrap_95']['systems'], 'spearman')} | {h['n_systems']} |")
            w("")
            out.extend(h2_table(s["H2_held_out_prediction"]))
            w("")
            w(f"- Sensitivity H1 reading: {verdict_h1(s['H1_scs4c_vs_pass1'])}.")
            w(f"- Sensitivity H1b reading: {verdict_h1b(s['H1b_partial_credit_vs_pass1'])}.")
            w(f"- Sensitivity H2 reading at n_A = 50: {verdict_h2(s['H2_held_out_prediction']['50'])}.")
            w("")
            w("Selected systems (base model → latest submission):")
            w("")
            for model, name in s["systems"].items():
                w(f"- {model}: `{name}`")
            w("")
        w(f"### Per-system table: the {args.top} highest-pass@1 included systems (full table in `expt_v1/results/per_system_e07.csv`)")
        w("")
        out.extend(per_system_table(rows, args.top))
        w("")
    w("### Excluded systems")
    w("")
    w("| Submission | Measured / 500 | Reason |")
    w("|---|---:|---|")
    for name, measured in sorted(a["systems_excluded_measured_counts"].items()):
        w(f"| `{name}` | {measured} | {a['systems_excluded_reasons'][name]} |")
    w("")
    gm = a["validity_reports_differing_from_pinned_gold_lists"]
    drift = {k: n for k, n in gm.items() if n}
    w("### Validity checks")
    w("")
    w(f"- **Consistency stop rule:** {v['inconsistent_cells']} inconsistent measured cells out of {v['measured_cells']} ({(v['inconsistent_fraction'] or 0):.4%}; stop at > 0.5%): "
      f"{v['resolved_but_score_below_1']} resolved with score < 1, {v['unresolved_but_score_1']} unresolved with score = 1.")
    w(f"- **Gold-list agreement:** {sum(gm.values())} reports across {len(drift)} systems have FAIL_TO_PASS or PASS_TO_PASS test sets differing from the pinned gold lists (reported, not excluded)"
      + (": " + ", ".join(f"`{k}` {n}" for k, n in sorted(drift.items(), key=lambda kv: -kv[1])[:10]) + ("…" if len(drift) > 10 else "") if drift else "") + ".")
    off = a["validity_report_vs_official_resolved"]
    with_list = {k: d for k, d in off.items() if d}
    dis = {k: d for k, d in with_list.items() if d["disagreements"]}
    w(f"- **Report versus official resolved list:** {len(with_list)} systems publish an official resolved list (`results.json` or `per_instance_details.json`); "
      f"{sum(d['compared'] for d in with_list.values())} reports compared, {sum(d['disagreements'] for d in with_list.values())} disagreements in {len(dis)} systems"
      + (": " + ", ".join(f"`{k}` {d['disagreements']}/{d['compared']}" for k, d in sorted(dis.items(), key=lambda kv: -kv[1]['disagreements'])[:10]) if dis else "") + ".")
    w(f"- **Coverage:** {a['systems_included']} included systems (underpowered below 20); common cohort {a['common_cohort_tasks']} tasks (unmeasured if empty).")
    w(f"- **Locked settings:** {a['locked_settings']}. {a['p_value_note']}. {a['uncertainty_note']}")
    print("\n".join(out))


def a_pred(a: dict, key: str) -> str:
    forecast = Path(__file__).parent / "forecasts" / "e07_phase_a_forecast.json"
    return json.loads(forecast.read_text())["predictions"][key]


if __name__ == "__main__":
    main()

"""E25: tables from log.jsonl and rollouts.jsonl. Usage: python3 analyze_e25.py results/"""
import sys, json, collections
d = sys.argv[1]
log = [json.loads(l) for l in open(d + "/log.jsonl")]
print("## gate")
print("| update | tokens | outside support | abs delta > 0.05 | gate share | mean abs delta | max abs delta | gate |\n|---|---|---|---|---|---|---|---|")
for r in log:
    m = r["train_mismatch_truncated_support"]
    g = (m["outside_support"] + m["abs_delta_gt_tol"]) / m["tokens"]
    print(f"| {r['update']} | {m['tokens']:,} | {m['outside_support']} | {m['abs_delta_gt_tol']} | {g*100:.4f}% | {m['mean_abs_delta']:.5f} | {m['max_abs_delta']:.3f} | {'pass' if g<=0.01 else 'FAIL'} |")
print("## finiteness")
print("| update | seqs backprop | nonfinite seqs | nonfinite params | grad norm | max scaled grad | IS min/max/mean | loss | max abs (fp16 - master) |\n|---|---|---|---|---|---|---|---|---|")
for r in log:
    print(f"| {r['update']} | {r['train_trained_sequences']} | {r['train_nonfinite_sequences']} | {r['train_nonfinite_params_after_step']} | {r['train_grad_norm']:.4f} | {r['train_max_scaled_grad']:.1f} | {r['train_is_min']:.3f} / {r['train_is_max']:.3f} / {r['train_is_mean']:.4f} | {r['train_loss']:.3f} | {r['train_param_max_abs_delta_vs_master']:.1e} |")
print("## run")
print("| update | active groups | strict succ | mean strict | gen tokens | truncated | no_lean | unresolved | gen s | score s | update s |\n|---|---|---|---|---|---|---|---|---|---|---|")
for r in log:
    print(f"| {r['update']} | {r['active_groups']}/{r['groups']} | {r['strict_successes']} | {r['mean_strict']:.4f} | {r['generated_tokens']:,} | {r['truncated']} | {r['no_lean']} | {r['unresolved']} | {r['gen_seconds']:.0f} | {r['score_seconds']:.0f} | {r['update_seconds']:.0f} |")
print("totals: tokens", sum(r['generated_tokens'] for r in log), "gen s", round(sum(r['gen_seconds'] for r in log)), "score s", round(sum(r['score_seconds'] for r in log)), "update s", round(sum(r['update_seconds'] for r in log)))
ro = [json.loads(l) for l in open(d + "/rollouts.jsonl")]
print("rollouts", len(ro), "keys", sorted(ro[0]))
print("status", collections.Counter(r["status"] for r in ro))
print("extraction", collections.Counter(r["extraction"] for r in ro))
print("strict values", collections.Counter(r["strict"] for r in ro), "proxy", collections.Counter(r["proxy_e23"] for r in ro))
print("## strict vs proxy (all)")
c = collections.Counter((r["status"], r["strict"], r["proxy_e23"]) for r in ro)
for k, v in sorted(c.items(), key=str): print(k, v)
meas = [r for r in ro if r["status"] == "measured"]
agree = sum((r["strict"] or 0) == (r["proxy_e23"] or 0) for r in meas)
print("measured", len(meas), "agree", agree, "disagree", len(meas) - agree)
print("per update strict/proxy among measured")
for u in range(1, 9):
    m = [r for r in meas if r["update"] == u]
    print(u, len(m), "strict", sum(1 for r in m if r["strict"] == 1.0), "proxy", sum(1 for r in m if r["proxy_e23"] == 1.0), "both", sum(1 for r in m if r["strict"] == 1.0 and r["proxy_e23"] == 1.0), "proxy1_strict0", sum(1 for r in m if r["strict"] != 1.0 and r["proxy_e23"] == 1.0))
print("notes of proxy1/strict0", collections.Counter(r["note"][:80] for r in meas if r["strict"] != 1.0 and r["proxy_e23"] == 1.0).most_common(8))
print("smooth non-null", sum(r["smooth"] is not None for r in ro), "smooth among proxy1/strict0", collections.Counter(r["smooth"] for r in meas if r["strict"] != 1.0 and r["proxy_e23"] == 1.0).most_common(5))
print("unique tasks", len({r["task_id"] for r in ro}), "tasks with a strict success", len({r["task_id"] for r in ro if r["strict"] == 1.0}))
print("used_in_update", collections.Counter(r["used_in_update"] for r in ro))

"""IS-correction descriptive stats from a score_*.npz (rl4cv e22): ratio = exp(hf_lp - vllm_lp) on in-support tokens."""
import sys, json, numpy as np
out = {}
for f in sys.argv[1:]:
    z = np.load(f); sup = z["sup"]; lr = (z["lp"] - z["vl"])[sup].astype(np.float64); n = len(z["sup"])
    r = np.exp(lr)
    out[f.split("/")[-1].replace(".npz", "")] = {
        "tokens": int(n), "unsupported": int((~sup).sum()),
        "ratio_outside_[0.5,2]_share": float(((r < 0.5) | (r > 2)).sum() + (~sup).sum()) / n,
        "ratio_outside_[0.8,1.25]_share": float(((r < 0.8) | (r > 1.25)).sum() + (~sup).sum()) / n,
        "mean_ratio": float(r.mean()), "mean_ratio_TIS_cap2": float(np.minimum(r, 2).mean()),
        "mean_abs_logratio": float(np.abs(lr).mean()), "token_kl_est(mean of -logratio)": float((-lr).mean()),
        "gt0.05_share_all_tokens": float((np.abs(lr) > 0.05).sum() + (~sup).sum()) / n,
        "gt0.05_share_ent>0.1_only": float(((np.abs(lr) > 0.05)[(z['ent'][sup] > 0.1)]).sum() + ((~sup) & (z['ent'] > 0.1)).sum()) / max(1, int((z['ent'] > 0.1).sum())),
        "tokens_ent>0.1_share": float((z["ent"] > 0.1).mean())}
print(json.dumps(out, indent=1))

"""E24: decompose the full-softmax mismatch share per update. Usage: venv/bin/python code/analyze_e24.py run/fp16_8u"""
import sys, glob, json, torch
tol = 0.05
for f in sorted(glob.glob(sys.argv[1] + "/e24_tokens_u*.pt")):
    d = torch.load(f); lt, lf, sp, ins = d["lt"].float(), d["lf"].float(), d["sp"].float(), d["ins"].bool()
    n = lt.numel()
    full = (lf - sp).abs() > tol                 # full-softmax diagnostic (counts all tokens)
    trunc = ((lt - sp).abs() > tol) & ins        # gate, in-support part
    out = (~ins)                                 # sampled token outside recomputed support
    mass = (lf - lt)                             # log of kept mass: lf = lt + log(mass)
    struct = full & ~trunc & ~out                # only because sampler renormalizes after top-k/top-p
    print(json.dumps({"file": f.split('/')[-1], "tokens": n, "full_share": float(full.float().mean()), "gate_share": float((trunc | out).float().mean()),
        "full_but_not_gate": float(struct.float().mean()), "mean_abs_lf_minus_lt": float((lf-lt).abs().mean()),
        "share_logmass_lt_-0.05": float((mass < -tol).float().mean()), "outside_support": int(out.sum())}))

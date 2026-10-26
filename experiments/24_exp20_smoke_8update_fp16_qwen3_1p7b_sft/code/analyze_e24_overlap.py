"""E24: overlap of the full-softmax mismatch tokens with truncation mass. Usage: venv/bin/python code/analyze_e24_overlap.py run/fp16_8u/A_s0"""
import sys, glob, json, torch
tol = 0.05
for f in sorted(glob.glob(sys.argv[1] + "/e24_tokens_u*.pt")):
    d = torch.load(f); lt, lf, sp, ins = d["lt"].double(), d["lf"].double(), d["sp"].double(), d["ins"].bool()
    n = lt.numel(); full = (lf - sp).abs() > tol
    mass = lf - lt                                   # log kept mass (<= 0); lt may be -inf outside support
    mfin = torch.where(torch.isfinite(mass), mass, torch.full_like(mass, -1e9))
    big = mfin < -tol                                # truncation removes >5% of mass
    A = full & big                                   # explained by truncation mass alone
    B = full & ~big                                  # remainder
    Bg = B & ((lt - sp).abs() > tol) & ins           # remainder that is also gate-flagged (numeric)
    Bn = B & ~Bg                                     # remainder: mass offset (<5%) plus small numeric noise, sum crosses 0.05
    nf = int(full.sum())
    r = dict(file=f.split('/')[-1], tokens=n, full_share=nf/n, full_tokens=nf,
        full_with_mass_lt_minus_tol_frac=int(A.sum())/nf, remainder_tokens=int(B.sum()), remainder_share_of_all=int(B.sum())/n,
        remainder_gate_flagged=int(Bg.sum()), remainder_mass_plus_noise=int(Bn.sum()),
        big_mass_tokens_share_of_all=int(big.sum())/n, big_mass_tokens_also_full_frac=int(A.sum())/max(1,int(big.sum())),
        remainder_median_logmass=float(mfin[B].median()), remainder_share_logmass_lt_minus_0p03=float((mfin[B] < -0.03).double().mean()),
        full_after_correcting_for_logmass_share=float((((lf - mfin.clamp(min=-1e8)) - sp).abs() > tol).double().mean()))
    print(json.dumps(r))

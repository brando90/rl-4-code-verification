import sys, re
p = sys.argv[1]
s = open(p).read()
def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, old
    s = s.replace(old, new, count)

# dtype
rep("AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16)",
    "AutoModelForCausalLM.from_pretrained(model_dir, dtype=getattr(torch, args.dtype))")
# reward proxy
rep("        t0 = now()\n        name = f\"u{update:03d}b{batch}\"",
    """        t0 = now()
        if self.args.reward_proxy:
            # E23 stand-in reward (numerics test only, no Lean compile): 1 if an extracted Lean file has a theorem/lemma and no sorry.
            res = {}
            for r in rows:
                ok = bool(r["lean"]) and ("sorry" not in r["lean"]) and (("theorem" in r["lean"]) or ("lemma" in r["lean"]))
                res[(r["batch"], r["slot"], r["sample_idx"])] = {"strict": 1.0 if ok else 0.0, "smooth": 1.0 if ok else 0.0,
                                                                 "status": "measured", "note": "E23 proxy reward"}
            return res, now() - t0
        name = f"u{update:03d}b{batch}\"""")
# loss scaling + nonfinite handling in train_step
rep("""        stats = {"loss": 0.0, "tokens": total_tokens, "trained_sequences": 0, "is_min": math.inf, "is_max": 0.0, "is_sum": 0.0, "is_n": 0}""",
    """        stats = {"loss": 0.0, "tokens": total_tokens, "trained_sequences": 0, "is_min": math.inf, "is_max": 0.0, "is_sum": 0.0, "is_n": 0,
                 "nonfinite_sequences": 0, "max_scaled_grad": 0.0, "min_nonzero_scaled_grad": math.inf, "loss_scale": self.args.loss_scale}
        scale = float(self.args.loss_scale)""")
rep("""            loss.backward()
            for p, b in zip(self.params, grad_buf):
                if p.grad is not None:
                    b.add_(p.grad.float())
                    p.grad = None
            stats["loss"] += float(loss.detach())""",
    """            (loss * scale).backward()
            gs = [p.grad for p in self.params if p.grad is not None]
            fin = bool(torch.isfinite(loss.detach())) and all(bool(torch.isfinite(g).all()) for g in gs)
            if fin:
                stats["max_scaled_grad"] = max(stats["max_scaled_grad"], float(max(g.abs().max() for g in gs)))
                stats["min_nonzero_scaled_grad"] = min(stats["min_nonzero_scaled_grad"], float(min((g.abs()[g != 0].min() if (g != 0).any() else torch.tensor(math.inf)) for g in gs)))
            for p, b in zip(self.params, grad_buf):
                if p.grad is not None:
                    if fin:
                        b.add_(p.grad.float() / scale)
                    p.grad = None
            if not fin:
                stats["nonfinite_sequences"] += 1
                continue
            stats["loss"] += float(loss.detach())""")
# after optimizer step: param finiteness
rep("""                    p.data.copy_(m.to(p.dtype))
        del grad_buf""",
    """                    p.data.copy_(m.to(p.dtype))
            stats["nonfinite_params_after_step"] = int(sum(0 if bool(torch.isfinite(p.data).all()) else 1 for p in self.params))
            stats["param_max_abs_delta_vs_master"] = float(max((p.data.float().cpu() - m).abs().max() for p, m in zip(self.params[:8], self.master[:8])))
        del grad_buf""")
rep("""        norm = math.sqrt(sum(float((b.double() ** 2).sum()) for b in grad_buf))""",
    """        norm = math.sqrt(sum(float((b.double() ** 2).sum()) for b in grad_buf))
        if not math.isfinite(norm):
            stats["trained_sequences"] = 0; norm = float("nan")
            print("NONFINITE grad norm: optimizer step skipped", flush=True)""")
rep("""        coef = min(1.0, GRAD_CLIP / (norm + 1e-6))""", """        coef = min(1.0, GRAD_CLIP / (norm + 1e-6)) if math.isfinite(norm) else 0.0""")
rep("""        if stats["is_min"] == math.inf:""", """        if stats["min_nonzero_scaled_grad"] == math.inf:
            stats["min_nonzero_scaled_grad"] = None
        if stats["is_min"] == math.inf:""")
# args
rep("""    ap.add_argument("--smoke", action""", """    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--loss-scale", type=float, default=1.0)
    ap.add_argument("--reward-proxy", action="store_true")
    ap.add_argument("--smoke", action""")
open(p, "w").write(s)
print("patched")

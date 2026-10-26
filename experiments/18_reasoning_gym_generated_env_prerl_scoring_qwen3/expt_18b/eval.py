"""Held-out evaluation for 18b: pass rate on the 18a target set (5 RG families + GSM8K) and on the first 64 probe items of the trained environment.

Pre (base model) and post (a run's checkpoint) use the same items, n = 8 samples, temperature 1, top-p 1, thinking off, the 18a rewards and
sampling seed 5000 + the 18a set index. Writes one JSON with per-set rates and per-item pass means (for paired item bootstraps).

    python eval.py --model $MODELS_DIR/qwen3_1p7b --out $RES/eval_pre.json --envs all --gsm8k-parquet $B/gsm8k_test.parquet
    python eval.py --model $RUNS/<run>/ckpt --out $RES/post_<run>.json --envs rg/coin_flip/L0 --gsm8k-parquet ...
    python eval.py --model $TMPDIR/ckpt --backend hf --out x.json --envs rg/coin_flip/L0 --n 2 --limit-items 4   # CPU (tiny model)
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18b as K  # noqa: E402

sys.path.insert(0, str(K.V1))
import build as B  # noqa: E402  (expt_v1/build.py)
import generate as G  # noqa: E402  (expt_v1/generate.py)

C = K.C


def eval_specs(envs: list[str], targets: list[str]) -> list[tuple[C.SetSpec, int]]:
    """(spec, n_items_to_use) per set; the spec's set_index is shifted so spec.sampling_seed = 5000 + the 18a set index."""
    by_id = C.sets_by_id()
    out = []
    for t in targets:
        out.append((dataclasses.replace(by_id[t], set_index=by_id[t].set_index + (K.EVAL_SAMPLING_SEED_BASE - C.SAMPLING_SEED_BASE)), C.N_ITEMS))
    for e in envs:
        out.append((dataclasses.replace(by_id[e], set_index=by_id[e].set_index + (K.EVAL_SAMPLING_SEED_BASE - C.SAMPLING_SEED_BASE)), K.ENV_PROBE_ITEMS))
    return out


class HFSampler:
    """transformers.generate sampler for CPU tests (tiny model); same interface as generate.VLLMBackend.sample."""

    name = "hf"

    def __init__(self, path: str, max_tokens: int):
        import torch
        import tinymodel
        from transformers import AutoModelForCausalLM

        import transformers

        self.version = transformers.__version__
        self.torch = torch
        self.tok = tinymodel.ByteTok()
        self.model = AutoModelForCausalLM.from_pretrained(path).eval()
        self.max_tokens = max_tokens

    def sample(self, items, spec, n):
        import grpo
        from train import encode_prompt
        import tinymodel

        self.torch.manual_seed(spec.sampling_seed)
        prompts = [encode_prompt(self.tok, it["messages"]) for it in items]
        gk = {"temperature": 1.0, "top_p": 1.0, "top_k": 0}
        groups = grpo.rollout(self.model, self.tok, prompts, n, self.max_tokens, gk, {tinymodel.EOS}, tinymodel.PAD, "cpu")
        return [[{"text": r.text, "generated_tokens": len(r.response_ids), "finish_reason": "stop" if r.finished else "length"}
                 for r in g] for g in groups]


def score_groups(spec: C.SetSpec, items: list[dict], groups: list[list[dict]], n_built: int) -> dict:
    ds = C.rg_dataset(spec, n_built) if spec.source == "rg" else None
    per_item, tags, capped, toks, total = [], 0, 0, 0, 0
    for item, grp in zip(items, groups):
        ok = 0
        entry = None
        if ds is not None:
            entry = ds[item["idx"]]
            if C.sha256_text(entry["question"]) != item["question_sha256"]:
                raise RuntimeError(f"{item['item_id']}: regenerated entry differs from the built item")
        for r in grp:
            extracted = C.extract_answer(r["text"])
            if ds is not None:
                try:
                    score = float(ds.score_answer(extracted, entry))
                except Exception:
                    score = 0.0
            else:
                score = C.gsm8k_score(extracted, item["gold"])
            ok += int(C.is_pass(score))
            tags += int(extracted is not None)
            capped += int(r["finish_reason"] == "length")
            toks += int(r["generated_tokens"])
            total += 1
        per_item.append(ok / len(grp))
    return {"n_items": len(items), "n_samples": total, "pass_rate": sum(per_item) / len(per_item), "tag_rate": tags / total,
            "capped_rate": capped / total, "mean_tokens": toks / total, "item_pass": per_item,
            "items_sha256": hashlib.sha256("".join(i["question_sha256"] for i in items).encode()).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", required=True, help="model/checkpoint directory (HF format)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--envs", default="", help="comma-separated env ids whose probe subset is evaluated, or 'all' (the 16 selected)")
    ap.add_argument("--targets", default="all")
    ap.add_argument("--n", type=int, default=K.EVAL_N)
    ap.add_argument("--limit-items", type=int, default=0, help="smoke/tests only")
    ap.add_argument("--backend", choices=["vllm", "hf", "fake"], default="vllm")
    ap.add_argument("--gsm8k-parquet")
    ap.add_argument("--gsm8k-jsonl", help="tests only")
    ap.add_argument("--gpu-mem", type=float, default=0.85)
    ap.add_argument("--name", default="")
    ap.add_argument("--max-tokens", type=int, default=K.EVAL_MAX_TOKENS, help="frozen 2048; smaller only for CPU tests")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        print(f"skip: {out} exists")
        return 0
    if args.envs == "all":
        envs = [s["env_id"] for s in json.loads(K.SELECTION_PATH.read_text())["selected"]]
    else:
        envs = [e for e in args.envs.split(",") if e]
    targets = K.TARGET_IDS if args.targets == "all" else [t for t in args.targets.split(",") if t]
    specs = eval_specs(envs, targets)
    sys_prompt = C.system_prompt()
    gsm = (None, None)
    if any(s.source == "gsm8k" for s, _ in specs):
        gsm = B.load_gsm8k(args.gsm8k_parquet, args.gsm8k_jsonl)
        if args.gsm8k_parquet and gsm[1] != C.GSM8K_PARQUET_SHA256:
            raise SystemExit(f"GSM8K parquet sha256 {gsm[1]} != pinned")
    if args.backend == "vllm":
        backend = G.VLLMBackend(K.POLICY_TAG, args.model, args.max_tokens, K.EVAL_MAX_MODEL_LEN, args.gpu_mem)
    elif args.backend == "hf":
        backend = HFSampler(args.model, args.max_tokens)
    else:
        backend = G.FakeLLM(K.POLICY_TAG, args.max_tokens)
    res: dict = {}
    t0 = time.time()
    for spec, n_use in specs:
        n_built = C.N_ITEMS
        rows, _meta = B.build_set(spec, n_built, sys_prompt, gsm[0])
        items = rows[: (args.limit_items or n_use)]
        key = spec.set_id if spec.set_id in K.TARGET_IDS else "env:" + spec.set_id
        groups = backend.sample(items, spec, args.n)
        res[key] = score_groups(spec, items, groups, n_built)
        res[key]["sampling_seed"] = spec.sampling_seed
        print(f"{key}: pass {res[key]['pass_rate']:.3f} tag {res[key]['tag_rate']:.2f} ({time.time() - t0:.0f}s)", flush=True)
    doc = {"schema": "eval_18b/v1", "name": args.name or out.stem, "model": str(args.model), "n": args.n,
           "max_tokens": args.max_tokens, "backend": backend.name, "backend_version": backend.version,
           "seconds": round(time.time() - t0, 1), "sets": res}
    C.write_json_atomic(out, doc)
    print("EVAL DONE", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

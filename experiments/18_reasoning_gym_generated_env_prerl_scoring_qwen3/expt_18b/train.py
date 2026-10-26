"""One single-environment GRPO run (experiment 18b): Qwen3-1.7B, one Reasoning Gym environment, one seed, frozen hyper-parameters.

    python train.py --env rg/coin_flip/L0 --seed 0 --out $RUNS/<run_name> --model-path $MODELS_DIR/qwen3_1p7b
    python train.py --env rg/coin_flip/L0 --seed 0 --out /tmp/t --backend tiny --steps 3 --prompts 4 --group 4 --max-new 24   # CPU dry run

Writes <out>/train_log.jsonl (one row per step), <out>/train_summary.json and <out>/ckpt/ (bf16 weights + tokenizer); a run with
train_summary.json present is skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18b as K  # noqa: E402
import grpo  # noqa: E402

import torch  # noqa: E402


def encode_prompt(tok, messages: list[dict]) -> list[int]:
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return list(tok(text, add_special_tokens=False).input_ids)


def finite(x) -> float | None:
    """JSON-safe number: a non-finite value is logged as null instead of crashing the log writer."""
    x = float(x)
    return x if math.isfinite(x) else None


class RGReward:
    """Binary pass reward of an RG environment, exactly the 18a pass indicator."""

    def __init__(self, spec: "K.C.SetSpec", n_items: int):
        self.ds = K.C.rg_dataset(spec, n_items)
        self.entries = [self.ds[i] for i in range(n_items)]
        self.items = [{"idx": i, "question": e["question"], "gold": str(e["answer"])} for i, e in enumerate(self.entries)]
        self.sha256 = hashlib.sha256("".join(K.C.sha256_text(e["question"]) for e in self.entries).encode()).hexdigest()

    def messages(self, i: int) -> list[dict]:
        return K.C.messages_for(self.items[i]["question"], K.C.system_prompt())

    def __call__(self, i: int, text: str, finished: bool) -> tuple[float, bool]:
        """(reward, has_answer_tag). An unfinished (capped) response never passes."""
        extracted = K.C.extract_answer(text)
        if not finished:
            return 0.0, extracted is not None
        try:
            score = float(self.ds.score_answer(extracted, self.entries[i]))
        except Exception:
            score = 0.0
        return (1.0 if K.C.is_pass(score) else 0.0), extracted is not None


def load_policy(args):
    if args.backend == "tiny":
        import tinymodel

        return tinymodel.tiny_qwen3(args.seed), tinymodel.ByteTok(), {tinymodel.EOS}, tinymodel.PAD
    from transformers import AutoModelForCausalLM, AutoTokenizer

    path = args.model_path or K.C.MODELS[K.POLICY_TAG]["id"]
    rev = None if args.model_path else K.C.MODELS[K.POLICY_TAG]["revision"]
    tok = AutoTokenizer.from_pretrained(path, revision=rev)
    try:
        model = AutoModelForCausalLM.from_pretrained(path, revision=rev, dtype=torch.bfloat16)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(path, revision=rev, torch_dtype=torch.bfloat16)
    eos = {tok.convert_tokens_to_ids("<|im_end|>")}
    if tok.eos_token_id is not None:
        eos.add(tok.eos_token_id)
    return model, tok, eos, tok.pad_token_id


def run_training(model, tok, eos_ids, pad_id, reward, hp: dict, out: Path, seed: int, device, save_ckpt: bool = True,
                 meta: dict | None = None) -> dict:
    P, G, S = hp["prompts_per_step"], hp["group_size"], hp["steps"]
    torch.manual_seed(seed)
    random.seed(seed)
    model.to(device)
    if hp.get("grad_checkpointing", False):
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    opt = grpo.MasterAdamW(model.parameters(), hp["lr"], tuple(hp["adam_betas"]), hp["adam_eps"], hp["weight_decay"])
    gen_kw = {"temperature": hp["temperature"], "top_p": hp["top_p"], "top_k": hp["top_k"]}
    out.mkdir(parents=True, exist_ok=True)
    log = open(out / "train_log.jsonl", "w", encoding="utf-8")
    tot_tokens = 0
    tot_rollouts = 0
    t_start = time.time()
    step_secs = []
    for step in range(S):
        t0 = time.time()
        torch.manual_seed(seed * 100_003 + step)
        idxs = list(range(step * P, (step + 1) * P))  # fresh items every step
        prompts = [encode_prompt(tok, reward.messages(i)) for i in idxs]
        groups = grpo.rollout(model, tok, prompts, G, hp["max_new_tokens"], gen_kw, eos_ids, pad_id, device)
        t_gen = time.time() - t0
        rewards = torch.zeros(P, G)
        tags = 0
        flat, capped = [], 0
        for p_i, (i, grp) in enumerate(zip(idxs, groups)):
            for k, r in enumerate(grp):
                rw, tag = reward(i, r.text, r.finished)
                rewards[p_i, k] = rw
                tags += int(tag)
                capped += int(not r.finished)
                flat.append(r)
        adv = grpo.group_advantages(rewards)
        mixed = int(((rewards.max(1).values > rewards.min(1).values)).sum())
        lr = grpo.lr_at(step, hp["lr"], hp["warmup_steps"])
        opt.set_lr(lr)
        loss, ntok = grpo.policy_loss_microbatches(model, flat, adv.flatten().tolist(), hp["micro_batch_seqs"], pad_id, device)
        norm, stepped = opt.step(hp["grad_clip"])
        tot_tokens += ntok
        tot_rollouts += len(flat)
        step_secs.append(time.time() - t0)
        row = {"step": step, "mean_reward": finite(rewards.mean()), "mixed_groups": mixed, "tag_rate": tags / len(flat),
               "capped_rate": capped / len(flat), "mean_resp_tokens": ntok / len(flat), "loss": finite(loss),
               "grad_norm": finite(norm), "stepped": stepped, "lr": lr, "gen_seconds": round(t_gen, 2),
               "step_seconds": round(step_secs[-1], 2)}
        log.write(json.dumps(row) + "\n")
        log.flush()
        print(json.dumps(row), flush=True)
    log.close()
    summary = {"schema": "train_summary_18b/v1", "steps": S, "rollouts": tot_rollouts, "response_tokens": tot_tokens,
               "seconds": round(time.time() - t_start, 1), "mean_step_seconds": round(sum(step_secs) / max(1, len(step_secs)), 2),
               "items_sha256": getattr(reward, "sha256", None), "hp": {k: v for k, v in hp.items()}, "seed": seed, **(meta or {})}
    if save_ckpt:
        ck = out / "ckpt"
        model.to(torch.bfloat16) if next(model.parameters()).dtype != torch.float32 else None
        model.save_pretrained(ck, safe_serialization=True)
        tok.save_pretrained(ck)
        summary["ckpt"] = str(ck)
    (out / "train_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", required=True)
    ap.add_argument("--seed", type=int, required=True, choices=list(K.SEEDS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-path")
    ap.add_argument("--backend", choices=["hf", "tiny"], default="hf")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--steps", type=int)
    ap.add_argument("--prompts", type=int)
    ap.add_argument("--group", type=int)
    ap.add_argument("--max-new", type=int)
    ap.add_argument("--micro-bs", type=int)
    ap.add_argument("--smoke", action="store_true", help="smoke run: overrides are allowed and the run is tagged smoke")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if (out / "train_summary.json").exists():
        print(f"skip: {out}/train_summary.json exists")
        return 0
    hp = dict(K.HP)
    overrides = {"steps": args.steps, "prompts_per_step": args.prompts, "group_size": args.group,
                 "max_new_tokens": args.max_new, "micro_batch_seqs": args.micro_bs}
    changed = {k: v for k, v in overrides.items() if v is not None}
    if changed and not (args.smoke or args.backend == "tiny"):
        raise SystemExit(f"frozen hyper-parameters: refuse overrides {changed} without --smoke")
    hp.update(changed)
    hp["grad_checkpointing"] = args.backend != "tiny"
    spec = K.train_spec(K.C.sets_by_id()[args.env], args.seed)
    reward = RGReward(spec, hp["steps"] * hp["prompts_per_step"])
    model, tok, eos, pad = load_policy(args)
    meta = {"env_id": args.env, "run_seed": args.seed, "item_seed": spec.seed, "smoke": bool(args.smoke), "backend": args.backend,
            "torch": torch.__version__, "device": str(args.device)}
    try:
        import transformers

        meta["transformers"] = transformers.__version__
    except Exception:
        pass
    summary = run_training(model, tok, eos, pad, reward, hp, out, args.seed, torch.device(args.device), meta=meta)
    print("TRAIN DONE", json.dumps({k: summary[k] for k in ("rollouts", "response_tokens", "seconds", "mean_step_seconds")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

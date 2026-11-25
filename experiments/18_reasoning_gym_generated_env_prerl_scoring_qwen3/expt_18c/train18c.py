"""One token-matched single-environment GRPO run (experiment 18c): the 18b trainer, stopped by cumulative generated response tokens.

    python train18c.py --env rg/coin_flip/L0 --seed 0 --out $RUNS/<run_name> --model-path $MODELS_DIR/qwen3_1p7b
    python train18c.py --env rg/coin_flip/L0 --seed 0 --out /tmp/t --backend tiny --budget 400 --min-steps 2 --max-steps 8 --prompts 4 --group 4 --max-new 24

Same model, hyper-parameters, rewards, item seeds and GRPO code as 18b (grpo.py, train.py of expt_18b are imported unchanged). The only
differences: runs stop after the first update at which cumulative response tokens >= TOKEN_BUDGET (and >= MIN_STEPS updates), or at MAX_STEPS
(then `stop_reason` is "cap" and the run is budget_limited); items are generated lazily from the same stream as 18b (first 1,280 identical).
Writes <out>/train_log.jsonl, <out>/train_summary.json and <out>/ckpt/; a run with train_summary.json present is skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common18c as K18C  # noqa: E402

K = K18C.K
sys.path.insert(0, str(K18C.B18))
import grpo  # noqa: E402
import train as T18  # noqa: E402  (18b trainer: encode_prompt, finite, load_policy, RGReward)

import torch  # noqa: E402


class LazyRGReward:
    """The 18b RGReward over an item stream built on demand: the first PREFIX_ITEMS eagerly (their sha256 is 18b's `items_sha256`)."""

    def __init__(self, spec: "K.C.SetSpec", n_items: int, prefix: int = K18C.PREFIX_ITEMS):
        self.ds = K.C.rg_dataset(spec, n_items)
        self.n_items = n_items
        self._entries: dict[int, dict] = {}
        self._qsha: dict[int, str] = {}
        for i in range(min(prefix, n_items)):
            self.entry(i)
        self.sha256 = hashlib.sha256("".join(self._qsha[i] for i in range(min(prefix, n_items))).encode()).hexdigest()  # prefix hash

    def entry(self, i: int) -> dict:
        if i not in self._entries:
            e = self.ds[i]
            self._entries[i] = e
            self._qsha[i] = K.C.sha256_text(e["question"])
        return self._entries[i]

    def messages(self, i: int) -> list[dict]:
        return K.C.messages_for(self.entry(i)["question"], K.C.system_prompt())

    def __call__(self, i: int, text: str, finished: bool) -> tuple[float, bool]:
        extracted = K.C.extract_answer(text)
        if not finished:
            return 0.0, extracted is not None
        try:
            score = float(self.ds.score_answer(extracted, self.entry(i)))
        except Exception:
            score = 0.0
        return (1.0 if K.C.is_pass(score) else 0.0), extracted is not None

    def distinct_questions(self, upto: int) -> int:
        return len({self._entries[i]["question"] for i in range(upto) if i in self._entries})


def run_training_tokens(model, tok, eos_ids, pad_id, reward, hp: dict, out: Path, seed: int, device, budget: int, min_steps: int,
                        max_steps: int, save_ckpt: bool = True, meta: dict | None = None) -> dict:
    """18b `run_training` with the stopping rule; per-step rows also carry cumulative tokens. Returns the summary dict."""
    P, G = hp["prompts_per_step"], hp["group_size"]
    torch.manual_seed(seed)
    random.seed(seed)
    model.to(device)
    if hp.get("grad_checkpointing", False):
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    opt = grpo.MasterAdamW(model.parameters(), hp["lr"], tuple(hp["adam_betas"]), hp["adam_eps"], hp["weight_decay"])
    gen_kw = {"temperature": hp["temperature"], "top_p": hp["top_p"], "top_k": hp["top_k"]}
    out.mkdir(parents=True, exist_ok=True)
    log = open(out / "train_log.jsonl", "w", encoding="utf-8")
    tot_tokens = tot_rollouts = 0
    t_start = time.time()
    step_secs: list[float] = []
    step = 0
    reason = None
    while reason is None:
        t0 = time.time()
        torch.manual_seed(seed * 100_003 + step)
        idxs = list(range(step * P, (step + 1) * P))  # fresh item indices every step, same stream as 18b
        prompts = [T18.encode_prompt(tok, reward.messages(i)) for i in idxs]
        groups = grpo.rollout(model, tok, prompts, G, hp["max_new_tokens"], gen_kw, eos_ids, pad_id, device)
        t_gen = time.time() - t0
        rewards = torch.zeros(P, G)
        tags = capped = 0
        flat = []
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
        step += 1
        step_secs.append(time.time() - t0)
        reason = _stop(step, tot_tokens, budget, min_steps, max_steps)
        row = {"step": step - 1, "mean_reward": T18.finite(rewards.mean()), "mixed_groups": mixed, "tag_rate": tags / len(flat),
               "capped_rate": capped / len(flat), "mean_resp_tokens": ntok / len(flat), "cum_response_tokens": tot_tokens,
               "loss": T18.finite(loss), "grad_norm": T18.finite(norm), "stepped": stepped, "lr": lr, "gen_seconds": round(t_gen, 2),
               "step_seconds": round(step_secs[-1], 2)}
        log.write(json.dumps(row) + "\n")
        log.flush()
        if step % 20 == 0 or reason is not None or step <= 3:
            print(json.dumps(row), flush=True)
    log.close()
    summary = {"schema": "train_summary_18c/v1", "steps": step, "rollouts": tot_rollouts, "response_tokens": tot_tokens,
               "token_budget": budget, "min_steps": min_steps, "max_steps": max_steps, "stop_reason": reason,
               "run_class": _classify(step, tot_tokens, reason, budget), "overshoot_tokens": tot_tokens - budget,
               "seconds": round(time.time() - t_start, 1), "mean_step_seconds": round(sum(step_secs) / max(1, len(step_secs)), 2),
               "items_sha256": getattr(reward, "sha256", None), "items_used": step * P,
               "distinct_questions_used": reward.distinct_questions(step * P) if hasattr(reward, "distinct_questions") else None,
               "hp": {k: v for k, v in hp.items()}, **(meta or {})}
    if save_ckpt:
        ck = out / "ckpt"
        model.to(torch.bfloat16) if next(model.parameters()).dtype != torch.float32 else None
        model.save_pretrained(ck, safe_serialization=True)
        tok.save_pretrained(ck)
        summary["ckpt"] = str(ck)
    (out / "train_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def _stop(steps_done: int, cum: int, budget: int, min_steps: int, max_steps: int) -> str | None:
    """Same rule as common18c.stop_reason with explicit parameters (smoke and CPU tests)."""
    if steps_done >= min_steps and cum >= budget:
        return "budget"
    if steps_done >= max_steps:
        return "budget" if cum >= budget else "cap"
    return None


def _classify(steps: int, tokens: int, reason: str, budget: int) -> str:
    if reason == "cap":
        return "budget_limited"
    return "matched" if tokens < K18C.NEAR_BUDGET * budget else "overshoot"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", required=True)
    ap.add_argument("--seed", type=int, required=True, choices=list(K18C.SEEDS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-path")
    ap.add_argument("--backend", choices=["hf", "tiny"], default="hf")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--budget", type=int)
    ap.add_argument("--min-steps", type=int)
    ap.add_argument("--max-steps", type=int)
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
    hp = dict(K18C.HP)
    overrides = {"prompts_per_step": args.prompts, "group_size": args.group, "max_new_tokens": args.max_new, "micro_batch_seqs": args.micro_bs}
    sched = {"budget": args.budget, "min_steps": args.min_steps, "max_steps": args.max_steps}
    changed = {k: v for k, v in {**overrides, **sched}.items() if v is not None}
    if changed and not (args.smoke or args.backend == "tiny"):
        raise SystemExit(f"frozen hyper-parameters and stopping rule: refuse overrides {changed} without --smoke")
    hp.update({k: v for k, v in overrides.items() if v is not None})
    budget = args.budget if args.budget is not None else K18C.TOKEN_BUDGET
    min_steps = args.min_steps if args.min_steps is not None else K18C.MIN_STEPS
    max_steps = args.max_steps if args.max_steps is not None else K18C.MAX_STEPS
    hp["steps"] = max_steps
    hp["grad_checkpointing"] = args.backend != "tiny"
    spec = K.train_spec(K.C.sets_by_id()[args.env], args.seed)
    reward = LazyRGReward(spec, max_steps * hp["prompts_per_step"], prefix=min(K18C.PREFIX_ITEMS, max_steps * hp["prompts_per_step"]))
    model, tok, eos, pad = T18.load_policy(args)
    meta = {"env_id": args.env, "run_seed": args.seed, "item_seed": spec.seed, "smoke": bool(args.smoke), "backend": args.backend,
            "torch": torch.__version__, "device": str(args.device)}
    try:
        import transformers

        meta["transformers"] = transformers.__version__
    except Exception:
        pass
    summary = run_training_tokens(model, tok, eos, pad, reward, hp, out, args.seed, torch.device(args.device), budget, min_steps, max_steps, meta=meta)
    print("TRAIN DONE", json.dumps({k: summary[k] for k in ("steps", "rollouts", "response_tokens", "stop_reason", "run_class", "seconds")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

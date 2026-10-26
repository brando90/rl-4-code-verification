"""TLDR: Experiment 20's GRPO trainer for one arm x seed run on one Sherlock GPU: prompts from the frozen train pack through experiment 103's prompt builder, rollouts from colocated vLLM (TRL 1.16's VLLMGeneration helper: sleep mode, processed log-probabilities, weight sync) with the frozen v12 sampler, rewards from the frozen Lean scorer (strict) or experiment 13's declaration adapter (smooth), group-normalized advantages, the clipped token-normalized objective with the vLLM importance correction (loss_e20.py), one AdamW step per update on fp32 master weights, pluggable prompt samplers (samplers_e20.py: uniform, static filter, DAPO refill, IRT-online), resumable checkpoints, and a smoke mode that gates on the log-probability mismatch between vLLM and the trainer."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, os.environ.get("RL4CV_SRC", "/scratch/users/brando9/rl4cv_sherlock/grading/rl4cv/src"))
from loss_e20 import (EPS_HIGH, EPS_LOW, IS_CAP, clipped_surrogate, group_advantages, importance_weights,  # noqa: E402
                      mismatch_summary, token_normalized_loss, truncated_logprobs)
from samplers_e20 import G, IRTItems, active_group, make_sampler  # noqa: E402
from rl4cv.rewards import reward_kernel_binary  # noqa: E402
from rl4cv.veribench.exp103 import build_prompt  # noqa: E402
from rl4cv.veribench.jobs import materialize_jobs, read_scorer_per_task, scored_response  # noqa: E402
from rl4cv.veribench.pack import load_pack  # noqa: E402

# Frozen v12 rollout sampler and the frozen recipe (PROTOCOL section 4).
TEMPERATURE, TOP_P, TOP_K, MAX_NEW_TOKENS, MAX_MODEL_LEN = 0.6, 0.95, 20, 12288, 20480
STOP_TOKEN = "<|im_end|>"
LR, BETAS, WEIGHT_DECAY, GRAD_CLIP = 1e-6, (0.9, 0.999), 0.0, 1.0
GROUPS_PER_UPDATE, UPDATES = 16, 48
ROLLOUT_BUDGET = UPDATES * GROUPS_PER_UPDATE * G
E20 = Path(os.environ.get("E20_ROOT", "/scratch/users/brando9/rl4cv_sherlock/e20"))
GRADING = Path(os.environ.get("E20_GRADING", "/scratch/users/brando9/rl4cv_sherlock/grading"))


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now() -> float:
    return time.time()


def jsonl_append(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


class Runner:
    def __init__(self, args):
        self.args = args
        self.run = Path(args.run_root) / f"{args.arm}_s{args.seed}"
        self.run.mkdir(parents=True, exist_ok=True)
        self.log_path, self.rollout_path = self.run / "log.jsonl", self.run / "rollouts.jsonl"
        self.device = torch.device("cuda")
        self.rng = np.random.default_rng(args.seed * 7919 + 20)
        # --- policy -----------------------------------------------------------------------------------------------
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model_dir = Path(args.resume_model or args.model)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=getattr(torch, args.dtype)).to(self.device)
        self.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        self.model.config.use_cache = False
        self.params = [p for p in self.model.parameters() if p.requires_grad]
        self.stop_id = self.tokenizer.convert_tokens_to_ids(STOP_TOKEN)
        # --- master weights + optimizer on the CPU (fp32) ------------------------------------------------------------
        self.master = [p.detach().to("cpu", torch.float32).clone() for p in self.params]
        self.opt = torch.optim.AdamW(self.master, lr=LR, betas=BETAS, eps=1e-8, weight_decay=WEIGHT_DECAY, foreach=True)
        # --- colocated vLLM through TRL's helper --------------------------------------------------------------------
        os.environ.setdefault("RANK", "0"); os.environ.setdefault("LOCAL_RANK", "0"); os.environ.setdefault("WORLD_SIZE", "1")
        os.environ.setdefault("MASTER_ADDR", "127.0.0.1"); os.environ.setdefault("MASTER_PORT", str(29500 + args.seed))
        from accelerate import Accelerator
        from trl.generation.vllm_generation import VLLMGeneration
        from vllm import SamplingParams
        self.SamplingParams = SamplingParams
        self.accelerator = Accelerator()
        self.vllm = VLLMGeneration(self.model, self.accelerator, self.tokenizer, mode="colocate", tensor_parallel_size=1,
                                   gpu_memory_utilization=args.vllm_gpu_memory_utilization, max_model_length=MAX_MODEL_LEN,
                                   max_num_seqs=args.vllm_max_num_seqs, enable_sleep_mode=True, temperature=TEMPERATURE,
                                   top_p=TOP_P, top_k=TOP_K, max_completion_length=MAX_NEW_TOKENS, logprobs=0)
        # --- prompts ------------------------------------------------------------------------------------------------
        root = os.environ.get("VERIBENCH_ROOT")
        self.tasks = {t.task_id: t for t in load_pack(args.pack, [l.strip() for l in open(args.train_ids) if l.strip()])}
        self.task_ids = sorted(self.tasks)
        if len(self.task_ids) != 539:
            raise RuntimeError(f"expected 539 train tasks, found {len(self.task_ids)}")
        self.prompts = {t: build_prompt(self.tasks[t].instruction, root=root) for t in self.task_ids}
        self.prompt_ids = {}
        for t, p in self.prompts.items():
            text = self.tokenizer.apply_chat_template(p.messages(), tokenize=False, add_generation_prompt=True, enable_thinking=True)
            ids = self.tokenizer(text, add_special_tokens=False)["input_ids"]
            if len(ids) + MAX_NEW_TOKENS > MAX_MODEL_LEN:
                raise RuntimeError(f"prompt {t} has {len(ids)} tokens; exceeds the model length budget")
            self.prompt_ids[t] = ids
        # --- sampler ------------------------------------------------------------------------------------------------
        phase0 = None
        if args.arm == "S":
            phase0 = {}
            for r in csv.DictReader(open(args.phase0_cells)):
                phase0[r["task_id"]] = phase0.get(r["task_id"], 0) + int(float(r["strict"]))
        items = theta0 = theta0_sd = nodes = None
        if args.arm in ("C", "D"):
            frozen = json.loads(Path(args.irt_items).read_text())
            order = {t: i for i, t in enumerate(frozen["task_ids"])}
            idx = [order[t] for t in self.task_ids]
            items = IRTItems(self.task_ids, np.asarray(frozen["a"])[idx], np.asarray(frozen["d"])[idx])
            theta0, theta0_sd = float(frozen["theta0"]), float(frozen["theta0_sd"])
            nodes = np.linspace(frozen["grid"]["lo"], frozen["grid"]["hi"], int(frozen["grid"]["count"]))
        self.sampler = make_sampler(args.arm, self.task_ids, args.seed, phase0_successes=phase0, items=items, theta0=theta0,
                                    theta0_sd=theta0_sd, nodes=nodes, rollout_budget=ROLLOUT_BUDGET)
        self.smooth = args.arm in ("B", "D")
        self.state = {"update": 0, "generated_rollouts": 0, "gpu_seconds": 0.0, "arm": args.arm, "seed": args.seed}
        if args.resume_model:
            self.load_state()
        self.write_manifest()

    # ------------------------------------------------------------------------------------------------------ records
    def write_manifest(self):
        import transformers, trl, vllm
        m = {"arm": self.args.arm, "seed": self.args.seed, "model": self.args.model, "pack": self.args.pack,
             "recipe": {"lr": LR, "betas": BETAS, "weight_decay": WEIGHT_DECAY, "grad_clip": GRAD_CLIP, "eps_low": EPS_LOW,
                        "eps_high": EPS_HIGH, "is_cap": IS_CAP, "kl_coef": 0.0, "loss": "dapo token-normalized", "G": G,
                        "groups_per_update": GROUPS_PER_UPDATE, "updates": self.args.updates, "rollout_budget": ROLLOUT_BUDGET},
             "sampler": {"temperature": TEMPERATURE, "top_p": TOP_P, "top_k": TOP_K, "max_new_tokens": MAX_NEW_TOKENS,
                         "max_model_len": MAX_MODEL_LEN, "stop": STOP_TOKEN, "thinking": "on"},
             "versions": {"torch": torch.__version__, "transformers": transformers.__version__, "trl": trl.__version__,
                          "vllm": vllm.__version__, "python": sys.version.split()[0]},
             "gpu": torch.cuda.get_device_name(0), "host": os.uname().nodename, "slurm_job": os.environ.get("SLURM_JOB_ID"),
             "prompt_sha256": {t: p.prompt_sha256 for t, p in self.prompts.items()}, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if not self.args.resume_model:
            m["model_weights_sha256"] = {f.name: sha256_file(f) for f in sorted(Path(self.args.model).glob("*.safetensors"))}
        (self.run / f"run_manifest_{int(now())}.json").write_text(json.dumps(m, indent=1) + "\n")

    # --------------------------------------------------------------------------------------------------- generation
    def rollout_seed(self, update: int, batch: int, slot: int, k: int) -> int:
        return ((self.args.seed * 10_007 + update) * 10_007 + batch) * 1_000 + slot * G + k

    def generate(self, task_ids: list[str], update: int, batch: int) -> list[dict]:
        t0 = now()
        if self.vllm._llm_weights_sleeping:
            self.vllm.sync_weights()
        self.vllm.llm.wake_up(tags=["kv_cache"])
        reqs, params = [], []
        for slot, t in enumerate(task_ids):
            for k in range(G):
                reqs.append({"prompt_token_ids": self.prompt_ids[t]})
                params.append(self.SamplingParams(n=1, temperature=TEMPERATURE, top_p=TOP_P, top_k=TOP_K, max_tokens=MAX_NEW_TOKENS,
                                                  seed=self.rollout_seed(update, batch, slot, k), stop_token_ids=[self.stop_id], logprobs=0))
        outs = self.vllm.llm.generate(reqs, sampling_params=params, use_tqdm=False)
        self.vllm.llm.sleep(level=2)
        self.vllm._llm_weights_sleeping = True
        torch.cuda.empty_cache()
        rows = []
        for i, o in enumerate(outs):
            slot, k = divmod(i, G)
            out = o.outputs[0]
            lps = [lp[out.token_ids[j]].logprob if (lp and out.token_ids[j] in lp) else float("nan") for j, lp in enumerate(out.logprobs or [])]
            rows.append({"update": update, "batch": batch, "slot": slot, "sample_idx": k, "task_id": task_ids[slot],
                         "prompt_ids": list(o.prompt_token_ids), "completion_ids": list(out.token_ids), "sampling_logprobs": lps,
                         "completion": out.text, "finish_reason": out.finish_reason or "", "generated_tokens": len(out.token_ids),
                         "truncated": out.finish_reason == "length", "seed": params[i].seed, "model": str(self.args.model),
                         "prompt_sha256": self.prompts[task_ids[slot]].prompt_sha256})
        from rl4cv.veribench.exp103 import extract_lean
        for r in rows:
            ext = extract_lean(r["completion"], self.prompts[r["task_id"]].required_paths, root=os.environ.get("VERIBENCH_ROOT"))
            r["lean"], r["extraction"] = ext.lean, ext.method
        self.state["generated_rollouts"] += len(rows)
        return rows, now() - t0

    # ------------------------------------------------------------------------------------------------------ rewards
    def score(self, rows: list[dict], update: int, batch: int) -> tuple[dict, float]:
        """Strict (frozen scorer) or smooth (declaration adapter) per row; returns {(task, k): {...}} and the wall time."""
        t0 = now()
        if self.args.reward_proxy:
            # E23 stand-in reward (numerics test only, no Lean compile): 1 if an extracted Lean file has a theorem/lemma and no sorry.
            res = {}
            for r in rows:
                ok = bool(r["lean"]) and ("sorry" not in r["lean"]) and (("theorem" in r["lean"]) or ("lemma" in r["lean"]))
                res[(r["batch"], r["slot"], r["sample_idx"])] = {"strict": 1.0 if ok else 0.0, "smooth": 1.0 if ok else 0.0,
                                                                 "status": "measured", "note": "E23 proxy reward"}
            return res, now() - t0
        name = f"u{update:03d}b{batch}"
        jobs_root = self.run / "jobs"
        while (jobs_root / f"{name}_s0").exists():
            name += "r"  # write-once job directories: a retried update gets a new name
        jobs = materialize_jobs(rows, jobs_root, name)
        procs, outs = {}, {}
        env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(GRADING / "rl4cv/src"), "PATH": f"{GRADING / 'bin'}:{os.environ['PATH']}",
               "RL4CV_SRC": str(GRADING / "rl4cv/src"), "E20_GRADING": str(GRADING), "PYTHON": sys.executable}
        for k, job in jobs.items():
            out = self.run / "scores" / f"{name}_s{k}"
            out.mkdir(parents=True, exist_ok=True)
            if self.smooth:
                cmd = [sys.executable, str(E20 / "code/partial_credit_e20.py"), "--job-dir", str(job),
                       "--out", str(out / f"partial_{name}_s{k}.json"), "--evidence-root", str(out / "compiler_diagnostics")]
            else:
                cmd = ["bash", str(E20 / "code/score_e20.sh"), str(job), str(self.args.pack), str(out)]
            procs[k] = subprocess.Popen(cmd, stdout=open(out / "stdout.log", "w"), stderr=subprocess.STDOUT, env=env)
            outs[k] = out
        rc = {k: p.wait() for k, p in procs.items()}
        result = {}
        for r in rows:
            k, t = r["sample_idx"], r["task_id"]
            key = (r["batch"], r["slot"], k)
            rec = {"strict": 0.0, "smooth": None, "status": "measured", "note": ""}
            if not r["lean"]:
                rec["note"] = "no extractable Lean file"
                rec["smooth"] = 0.0
            elif rc[k] != 0:
                rec.update(status="unresolved_measurement", note=f"scorer rc={rc[k]}", smooth=0.0)
            elif self.smooth:
                data = json.loads((outs[k] / f"partial_{name}_s{k}.json").read_text())
                recs = {x["task_id"]: x for x in data["records"]}
                x = recs.get(t)
                if x is None:
                    rec.update(status="unresolved_measurement", note="no adapter record", smooth=0.0)
                elif x["status"] == "measured":
                    rec.update(strict=float(x["strict"]), smooth=float(x["factored_reward"]))
                elif "malformed source" in str(x.get("error", "")) or "parser" in str(x.get("error", "")):
                    rec.update(strict=0.0, smooth=0.0, status="measured", note="parse failure: zero credit")
                else:
                    rec.update(status="unresolved_measurement", note=str(x.get("error", ""))[:200], smooth=0.0)
            else:
                import glob
                per = read_scorer_per_task(glob.glob(str(outs[k] / "*_per_task.csv"))[0])
                row = per.get(t)
                if row is None or row.get("scoring_status") not in ("scored",):
                    rec.update(status="unresolved_measurement", note=f"scorer status {row.get('scoring_status') if row else 'missing'}")
                else:
                    rec["strict"] = float(reward_kernel_binary(scored_response(row, r)))
            result[key] = rec
        return result, now() - t0

    # ----------------------------------------------------------------------------------------------------- training
    def seq_logprobs(self, ids: torch.Tensor, prompt_len: int, with_mismatch: bool = False, sampling: list | None = None):
        """Log-probabilities of the completion tokens under the policy (logits / T, full softmax), computed in chunks under
        activation checkpointing; optionally the smoke-test recomputation on the truncated sampling support."""
        out = self.model.model(input_ids=ids, use_cache=False)
        h = out.last_hidden_state[0, prompt_len - 1: ids.shape[1] - 1]
        targets = ids[0, prompt_len:]
        chunk = self.args.logit_chunk
        logps, mism = [], []

        def f(hc, tc):
            return torch.log_softmax(self.model.lm_head(hc).float() / TEMPERATURE, dim=-1).gather(1, tc[:, None])[:, 0]

        for s in range(0, h.shape[0], chunk):
            logps.append(torch.utils.checkpoint.checkpoint(f, h[s:s + chunk], targets[s:s + chunk], use_reentrant=False))
            if with_mismatch:
                with torch.no_grad():
                    mism.append(truncated_logprobs(self.model.lm_head(h[s:s + chunk]).detach(), targets[s:s + chunk], TEMPERATURE, TOP_K, TOP_P))
        logp = torch.cat(logps)
        if with_mismatch:
            m = {k: torch.cat([x[k] for x in mism]) for k in ("logp_full", "logp_truncated", "in_support")}
            return logp, m
        return logp, None

    def train_step(self, rows: list[dict], advantages: np.ndarray, smoke: bool = False) -> dict:
        t0 = now()
        self.model.train()
        total_tokens = float(sum(len(r["completion_ids"]) for r in rows))
        grad_buf = [torch.zeros_like(p, dtype=torch.float32) for p in self.params]
        stats = {"loss": 0.0, "tokens": total_tokens, "trained_sequences": 0, "is_min": math.inf, "is_max": 0.0, "is_sum": 0.0, "is_n": 0,
                 "nonfinite_sequences": 0, "max_scaled_grad": 0.0, "min_nonzero_scaled_grad": math.inf, "loss_scale": self.args.loss_scale}
        scale = float(self.args.loss_scale)
        mism_all = {"logp_truncated": [], "logp_full": [], "sampling": [], "in_support": []}
        for r, adv in zip(rows, advantages):
            if len(r["completion_ids"]) == 0:
                continue
            if adv == 0.0 and not smoke:
                continue
            ids = torch.tensor([r["prompt_ids"] + r["completion_ids"]], device=self.device)
            sampling = torch.tensor(r["sampling_logprobs"], device=self.device, dtype=torch.float32)
            logp, mism = self.seq_logprobs(ids, len(r["prompt_ids"]), with_mismatch=smoke)
            if smoke:
                for key in ("logp_truncated", "logp_full", "in_support"):
                    mism_all[key].append(mism[key].cpu())
                mism_all["sampling"].append(sampling.cpu())
            if adv == 0.0:
                continue
            mask = torch.isfinite(sampling).float()
            w = importance_weights(logp, torch.nan_to_num(sampling, nan=0.0))
            sur = clipped_surrogate(logp, logp.detach(), torch.full_like(logp, float(adv)))
            loss = token_normalized_loss(sur, w, mask, total_tokens)
            (loss * scale).backward()
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
            stats["loss"] += float(loss.detach())
            stats["trained_sequences"] += 1
            wv = w[mask > 0]
            if wv.numel():
                stats["is_min"] = min(stats["is_min"], float(wv.min())); stats["is_max"] = max(stats["is_max"], float(wv.max()))
                stats["is_sum"] += float(wv.sum()); stats["is_n"] += int(wv.numel())
        norm = math.sqrt(sum(float((b.double() ** 2).sum()) for b in grad_buf))
        if not math.isfinite(norm):
            stats["trained_sequences"] = 0; norm = float("nan")
            print("NONFINITE grad norm: optimizer step skipped", flush=True)
        coef = min(1.0, GRAD_CLIP / (norm + 1e-6)) if math.isfinite(norm) else 0.0
        if stats["trained_sequences"] > 0:
            for m, b in zip(self.master, grad_buf):
                m.grad = (b * coef).to("cpu", torch.float32)
            self.opt.step()
            self.opt.zero_grad(set_to_none=True)
            with torch.no_grad():
                for p, m in zip(self.params, self.master):
                    p.data.copy_(m.to(p.dtype))
            stats["nonfinite_params_after_step"] = int(sum(0 if bool(torch.isfinite(p.data).all()) else 1 for p in self.params))
            stats["param_max_abs_delta_vs_master"] = float(max((p.data.float().cpu() - m).abs().max() for p, m in zip(self.params[:8], self.master[:8])))
        del grad_buf
        torch.cuda.empty_cache()
        stats.update(grad_norm=norm, clip_coef=coef, is_mean=(stats["is_sum"] / stats["is_n"]) if stats["is_n"] else None,
                     train_seconds=now() - t0)
        if stats["min_nonzero_scaled_grad"] == math.inf:
            stats["min_nonzero_scaled_grad"] = None
        if stats["is_min"] == math.inf:
            stats["is_min"] = None
        if smoke and mism_all["sampling"]:
            lt, lf, sp, ins = (torch.cat(mism_all[k]) for k in ("logp_truncated", "logp_full", "sampling", "in_support"))
            fin = torch.isfinite(sp)
            stats["mismatch_truncated_support"] = mismatch_summary(lt[fin], sp[fin], ins[fin])
            stats["mismatch_full_softmax"] = mismatch_summary(lf[fin], sp[fin], torch.ones_like(ins[fin]))
            self._e24_n = getattr(self, "_e24_n", 0) + 1
            torch.save({"lt": lt[fin].half() if False else lt[fin], "lf": lf[fin], "sp": sp[fin], "ins": ins[fin]}, str(self.run / f"e24_tokens_u{self._e24_n:03d}.pt"))
        return stats

    # ------------------------------------------------------------------------------------------------- checkpoints
    def save_state(self, update: int, weights_only: bool = False):
        d = self.run / f"ckpt_u{update:03d}"
        d.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(d / "model", safe_serialization=True)
        self.tokenizer.save_pretrained(d / "model")
        if not weights_only:
            latest = self.run / "state_latest"
            latest.mkdir(exist_ok=True)
            torch.save({"master": self.master, "opt": self.opt.state_dict()}, latest / "optimizer.pt")
            (latest / "state.json").write_text(json.dumps({**self.state, "update": update, "sampler": self.sampler.state(),
                                                           "rng": self.rng.bit_generator.state, "model_dir": str(d / "model")}, default=float, indent=1))
        (d / "DONE").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + "\n")

    def load_state(self):
        latest = self.run / "state_latest"
        s = json.loads((latest / "state.json").read_text())
        blob = torch.load(latest / "optimizer.pt", map_location="cpu", weights_only=False)
        for m, src in zip(self.master, blob["master"]):
            m.copy_(src)
        self.opt.load_state_dict(blob["opt"])
        self.sampler.load_state(s.pop("sampler"))
        self.rng.bit_generator.state = s.pop("rng")
        s.pop("model_dir", None)
        self.state.update(s)
        with torch.no_grad():
            for p, m in zip(self.params, self.master):
                p.data.copy_(m.to(p.dtype))
        print(f"resumed at update {self.state['update']}", flush=True)

    # --------------------------------------------------------------------------------------------------------- loop
    def run_loop(self):
        a = self.args
        first = self.state["update"] + 1
        for update in range(first, a.updates + 1):
            t_up = now()
            if a.arm == "E" and self.sampler.budget.exhausted:
                jsonl_append(self.log_path, {"update": update, "event": "budget exhausted before update", "generated": self.state["generated_rollouts"]})
                break
            groups, all_rows, all_scores, gen_s, score_s, batch, dropped = [], [], {}, 0.0, 0.0, 0, 0
            while True:
                tasks = self.sampler.next_groups(GROUPS_PER_UPDATE)
                rows, g_s = self.generate(tasks, update, batch)
                gen_s += g_s
                scores, s_s = self.score(rows, update, batch)
                score_s += s_s
                all_rows += rows
                all_scores.update(scores)
                successes = [sum(int(scores[(batch, slot, k)]["strict"]) for k in range(G)) for slot, t in enumerate(tasks)]
                if a.arm == "E":
                    self.sampler.register_generated(len(rows))
                    keep = self.sampler.filter_active(tasks, successes)
                    dropped += len(tasks) - len(keep)
                    groups += [(batch, i, tasks[i]) for i in keep]
                    batch += 1
                    if len(groups) >= GROUPS_PER_UPDATE or self.sampler.budget.exhausted:
                        break
                else:
                    groups = [(batch, i, tasks[i]) for i in range(len(tasks))]
                    self.sampler.observe(update, tasks, successes, [G] * len(tasks))
                    break
            groups = groups[:GROUPS_PER_UPDATE]
            by_key = {(r["batch"], r["slot"], r["sample_idx"]): r for r in all_rows}
            use_rows, reward_mat = [], []
            for (b, slot, t) in groups:
                rs = [by_key[(b, slot, k)] for k in range(G)]
                use_rows += rs
                reward_mat.append([(all_scores[(b, slot, k)]["smooth"] if self.smooth else all_scores[(b, slot, k)]["strict"]) for k in range(G)])
            adv = group_advantages(torch.tensor(reward_mat, dtype=torch.float32)).flatten().numpy() if groups else np.zeros(0)
            used = {(r["batch"], r["slot"], r["sample_idx"]) for r in use_rows}
            for r in all_rows:
                sc = all_scores[(r["batch"], r["slot"], r["sample_idx"])]
                jsonl_append(self.rollout_path, {"update": update, "batch": r["batch"], "slot": r["slot"], "sample_idx": r["sample_idx"],
                                                 "task_id": r["task_id"], "strict": sc["strict"], "smooth": sc["smooth"], "status": sc["status"],
                                                 "note": sc["note"], "generated_tokens": r["generated_tokens"], "truncated": r["truncated"],
                                                 "finish_reason": r["finish_reason"], "extraction": r["extraction"],
                                                 "lean_sha256": hashlib.sha256((r["lean"] or "").encode()).hexdigest() if r["lean"] else "",
                                                 "used_in_update": (r["batch"], r["slot"], r["sample_idx"]) in used, "seed": r["seed"]})
            stats = self.train_step(use_rows, adv, smoke=a.smoke) if groups else {"loss": 0.0, "tokens": 0, "trained_sequences": 0}
            strict_counts = [sum(int(all_scores[(b, slot, k)]["strict"]) for k in range(G)) for (b, slot, _) in groups]
            active = sum(active_group(c) for c in strict_counts)
            entry = {"update": update, "arm": a.arm, "seed": a.seed, "groups": len(groups), "active_groups": active,
                     "active_fraction": active / max(len(groups), 1), "strict_successes": int(sum(strict_counts)),
                     "mean_strict": float(np.mean([all_scores[(r["batch"], r["slot"], r["sample_idx"])]["strict"] for r in use_rows])) if use_rows else None,
                     "mean_smooth": float(np.mean([all_scores[(r["batch"], r["slot"], r["sample_idx"])]["smooth"] for r in use_rows])) if (use_rows and self.smooth) else None,
                     "generated_rollouts_this_update": len(all_rows), "generated_rollouts_total": self.state["generated_rollouts"],
                     "dropped_groups": dropped, "generated_tokens": int(sum(r["generated_tokens"] for r in all_rows)),
                     "generated_tokens_per_active_group": (sum(r["generated_tokens"] for r in all_rows) / active) if active else None,
                     "truncated": int(sum(r["truncated"] for r in all_rows)), "unresolved": int(sum(s["status"] != "measured" for s in all_scores.values())),
                     "no_lean": int(sum(1 for r in all_rows if not r["lean"])), "gen_seconds": gen_s, "score_seconds": score_s,
                     "update_seconds": now() - t_up, **{f"train_{k}": v for k, v in stats.items()}}
            if a.arm in ("C", "D"):
                entry.update(theta=self.sampler.theta, theta_sd=self.sampler.theta_sd)
            if a.arm == "E":
                entry.update(budget=self.sampler.budget.__dict__)
            self.state["update"] = update
            self.state["gpu_seconds"] += now() - t_up
            jsonl_append(self.log_path, entry)
            print(json.dumps({k: entry[k] for k in ("update", "active_groups", "strict_successes", "generated_tokens", "update_seconds")}), flush=True)
            if update in a.save_at or update % a.full_state_every == 0 or update == a.updates:
                self.save_state(update, weights_only=(update not in a.save_at and update % a.full_state_every != 0))
            if a.arm == "E" and self.sampler.budget.exhausted:
                jsonl_append(self.log_path, {"update": update, "event": "rollout budget reached", "generated": self.state["generated_rollouts"]})
                self.save_state(update)
                break
        (self.run / "RUN_DONE").write_text(json.dumps(self.state) + "\n")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, choices=["A", "S", "E", "C", "B", "D"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--train-ids", required=True)
    ap.add_argument("--phase0-cells", default=None)
    ap.add_argument("--irt-items", default=None)
    ap.add_argument("--updates", type=int, default=UPDATES)
    ap.add_argument("--save-at", type=lambda s: [int(x) for x in s.split(",") if x], default=[16, 32, 48])
    ap.add_argument("--full-state-every", type=int, default=8)
    ap.add_argument("--resume-model", default=None, help="model dir of the latest full-state checkpoint to resume from")
    ap.add_argument("--vllm-gpu-memory-utilization", type=float, default=0.75)
    ap.add_argument("--vllm-max-num-seqs", type=int, default=128)
    ap.add_argument("--logit-chunk", type=int, default=2048)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--loss-scale", type=float, default=1.0)
    ap.add_argument("--reward-proxy", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="compute the vLLM/trainer log-probability mismatch on every rollout")
    args = ap.parse_args()
    runner = Runner(args)
    rc = runner.run_loop()
    if args.smoke:
        last = [json.loads(l) for l in open(runner.log_path) if l.strip()]
        checks = [e.get("train_mismatch_truncated_support") for e in last if e.get("train_mismatch_truncated_support")]
        share = max((c["share_gt_tol"] for c in checks), default=float("nan"))
        verdict = {"updates": len(checks), "max_share_abs_delta_gt_0_05": share, "gate_share": 0.01, "pass": bool(share <= 0.01), "checks": checks,
                   "full_softmax_checks": [e.get("train_mismatch_full_softmax") for e in last if e.get("train_mismatch_full_softmax")]}
        (runner.run / "smoke_logprob_check.json").write_text(json.dumps(verdict, indent=1) + "\n")
        print("SMOKE", json.dumps({k: verdict[k] for k in ("updates", "max_share_abs_delta_gt_0_05", "pass")}), flush=True)
        return 0 if verdict["pass"] else 3
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

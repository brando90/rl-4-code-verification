"""CPU tests for V27: ladder subsets, run table, schedule, the training loop on a tiny Qwen3, and the frozen E17 curve.

usage: python tests/test_v27.py   (or pytest tests/test_v27.py); needs torch + transformers for the loop test, pandas
for the E17 refit check (skipped without it). No GPU, no network.
"""
import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
import train_v27 as t  # noqa: E402
import analyze_v27 as a  # noqa: E402


def manifest():
    return [json.loads(line) for line in (HERE / "token_manifest.jsonl").read_text().splitlines()]


def test_subsets_are_the_ladder_rungs():
    m = manifest()
    assert len(m) == t.N_EXAMPLES and sum(r["n_assistant_tokens_loss"] for r in m) == t.LOSS_TOKENS
    ladder = list(csv.DictReader((HERE.parent / "expt_v1/results/sft_set_manifest.csv").open()))
    assert [r["task_id"] for r in ladder] == [r["task_id"] for r in m], "manifest order != s_v1/token_manifest order"
    lm = json.loads((HERE.parent / "expt_v1/results/ladder_manifest.json").read_text())
    rung = {s["label"]: s for s in lm["systems"] if s.get("size") == "1.7B" and s["role"] == "trained"}
    previous = set()
    for fraction, (n, tokens) in t.SUBSETS.items():
        idx = t.subset_indices(fraction)
        assert sum(m[i]["n_assistant_tokens_loss"] for i in idx) == tokens
        r = rung[f"sft_1p7B_{fraction}"]
        assert r["cumulative_assistant_tokens"] == tokens and 2 * r["step"] == n and t.n_steps(n) == r["step"]
        assert previous <= set(idx)
        previous = set(idx)


def test_run_table_and_orders():
    runs = t.read_runs()
    assert [(r["fraction"], int(r["seed"])) for r in runs] == [(f, s) for f in t.SUBSETS for s in (20260830, 20260831)]
    for r in runs:
        order = t.run_order(r["fraction"], int(r["seed"]))
        assert sorted(order) == t.subset_indices(r["fraction"]) and order == t.run_order(r["fraction"], int(r["seed"]))
    assert t.run_order("f0p5", 20260830) != t.run_order("f0p5", 20260831)
    assert set(a.RUNGS["f0p125"] + a.RUNGS["f0p25"] + a.RUNGS["f0p5"]) == {r["label"] for r in runs}


def test_schedule_shape():
    import torch
    for steps in (82, 164, 334, 658):
        p = torch.nn.Parameter(torch.zeros(1))
        opt = torch.optim.AdamW([p], lr=2e-5)
        sch = t.make_scheduler(opt, steps)
        lrs = []
        for _ in range(steps):
            lrs.append(opt.param_groups[0]["lr"])
            opt.step()
            sch.step()
        assert abs(lrs[0] - 1e-6) < 1e-12 and abs(max(lrs) - 2e-5) < 1e-12 and lrs.index(max(lrs)) == t.WARMUP
        assert lrs[-1] < 2e-5 * 0.01 and abs(opt.param_groups[0]["lr"]) < 1e-12, (steps, lrs[-1])


def test_training_loop_tiny_cpu():
    import torch
    from transformers import Qwen3Config, Qwen3ForCausalLM
    torch.manual_seed(0)
    cfg = Qwen3Config(vocab_size=512, hidden_size=64, intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                      num_key_value_heads=2, head_dim=16, max_position_embeddings=256)
    model = Qwen3ForCausalLM(cfg).float()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    g = torch.Generator().manual_seed(1)
    rows = []
    for i in range(7):
        prompt, loss_tokens = 5 + i, 3 + (i % 4)
        rows.append({"index": i, "ids": torch.randint(0, 512, (prompt + loss_tokens,), generator=g).tolist(),
                     "prompt": prompt, "loss_tokens": loss_tokens})
    order = [6, 2, 0, 4, 1, 5, 3]
    steps = t.n_steps(len(order))
    opt = t.make_optimizer(model)
    sch = t.make_scheduler(opt, max(steps, t.WARMUP + 1))
    before = [p.detach().clone() for p in model.parameters()]
    with tempfile.TemporaryDirectory() as d:
        out = Path(d)
        metrics, consumed = t.run_steps(model, opt, sch, rows, order, out, {"test": True}, device="cpu", save_every=2)
        log = list(csv.DictReader((out / "steps.csv").open()))
        state = torch.load(out / "training_state.pt", weights_only=False)
    assert consumed == sum(r["loss_tokens"] for r in rows) and metrics["step"] == steps == 4
    assert [int(r["examples"]) for r in log] == [2, 4, 6, 7] and state["step"] == steps and state["order"] == order
    assert all(float(r["train_loss"]) > 0 and float(r["grad_norm"]) > 0 for r in log)
    assert any(not torch.equal(b, p) for b, p in zip(before, model.parameters()))


def test_e17_curve_matches_refit():
    assert abs(a.e17_prediction("f0p125") - (-0.01485)) < 5e-5 and abs(a.e17_prediction("f1p0") - 0.04504) < 5e-5
    if importlib.util.find_spec("pandas") is None:
        print("skip E17 refit check (no pandas)")
        return
    sys.path[:0] = [str(REPO / "src"), str(REPO / "experiments/17_heldout_prediction_of_unseen_experiments_agentic_rl_and_rsi_scaling_law/scripts")]
    import run_heldout_prediction_experiments as e17
    from rl4cv.utility_model import BUDGET_SCALE_ONLY, Observation, fit_utility_model
    rows = e17._ladder_rows()
    early = [Observation(rows[(s, f)]["scale"], f, rows[(s, f)]["budget"], rows[(s, f)]["utility"], rows[(s, f)]["rho"], rows[(s, f)]["H"])
             for s in ["1p7B", "4B", "8B", "14B"] for f in ["f0p125", "f0p25", "f0p5"]]
    model = fit_utility_model(early, BUDGET_SCALE_ONLY)
    for f in a.FRACTIONS:
        r = rows[("1p7B", f)]
        assert abs(model.predict(1.7, r["budget"], r["rho"], r["H"]) - a.e17_prediction(f)) < 1e-6, f


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)

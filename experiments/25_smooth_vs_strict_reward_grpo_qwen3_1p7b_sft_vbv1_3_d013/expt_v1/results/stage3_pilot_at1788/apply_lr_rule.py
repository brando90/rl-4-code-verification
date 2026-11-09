#!/usr/bin/env python3
"""TLDR: Apply the PROTOCOL section 5 lr rule to the four Experiment 25 pilot lanes (training reward and gate only; validation not read). Usage: python3 apply_lr_rule.py (run in this directory). Writes lr_rule_result.json."""
import json
from pathlib import Path
here = Path(__file__).parent
res = {}
for lane in ["A_lr1e-6", "A_lr5e-6", "B_lr1e-6", "B_lr5e-6"]:
    rows = [json.loads(l) for l in (here / f"pilot_{lane}" / "log.jsonl").read_text().splitlines() if l.startswith("{")]
    rows = [r for r in rows if "update" in r]
    s = [r["strict_successes"] for r in rows]
    gate = json.loads((here / f"pilot_{lane}" / "gate_report.json").read_text())
    first, last = sum(s[:6]) / 6, sum(s[6:12]) / 6
    res[lane] = {"strict_successes_per_128_by_update": s, "mean_u1_6": round(first, 3), "mean_u7_12": round(last, 3),
                 "diff": round(last - first, 3), "max_gate_share": gate["max_gate_share"], "gate_pass": gate["gate"] if isinstance(gate["gate"], bool) else gate.get("pass"),
                 "not_falling": last - first >= 0, "moves_ge_2": last - first >= 2, "n_updates": len(s)}
ok = {lr: all(res[f"{a}_lr{lr}"]["gate_pass"] and res[f"{a}_lr{lr}"]["not_falling"] for a in "AB") for lr in ["1e-6", "5e-6"]}
chosen = "5e-6" if ok["5e-6"] else ("1e-6" if ok["1e-6"] else None)
moves = {lr: [a for a in "AB" if res[f"{a}_lr{lr}"]["moves_ge_2"]] for lr in ["1e-6", "5e-6"]}
out = {"lanes": res, "rule_ok_by_lr": ok, "arms_that_move_by_lr": moves, "chosen_lr": chosen, "null_stop": not any(moves.values())}
(here / "lr_rule_result.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))

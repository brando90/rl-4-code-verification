#!/usr/bin/env python3
"""TLDR: Fill experiment 02A v3's results.md (status, headline tables, taxonomy, lengths, overlap, screen, SFT manifest, deviations, charges, verdict) from analysis_v3.json and the other committed receipts, and update the 02A README and experiments/README.md rows; deterministic, zero model calls."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
REPO = EXP.parents[3]
PHASE_README = EXP.parent / "README.md"
INDEX = REPO / "experiments" / "README.md"
TEACHERS = ("anthropic", "openai", "google")


def load(name):
    return json.loads((EXP / "results" / name).read_text())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tables", type=Path, required=True, help="analysis_tables.md written by analyze_v3.py")
    a = ap.parse_args()
    an, screen, sft, pf, state = load("analysis_v3.json"), load("generated_lean_screen.json"), load("sft_manifest.json"), load("preflight.json"), load("runs_state.json")
    tables = a.tables.read_text(encoding="utf-8")
    u, d = an["union"], an["decision"]
    pt = an["per_teacher"]
    now = datetime.now(timezone.utc).strftime("%m-%d-%Y %H:%M UTC")
    charges_main = an["charges_usd_reported_total"]
    charges_pre = pf["charges_usd_reported_total"]
    kept_str = " / ".join(f"{t} {pt[t]['kept']}" for t in TEACHERS)
    unm = {t: pt[t]["unmeasured"] for t in TEACHERS}
    setup = (f"Experiment 02A v3 (frontier teachers → kernel-verified Lean on 970 screened MBPP tasks, one single-call per (task, teacher) through Vals Valkyrie, "
             f"frozen VeriBench scorer): **{d['verdict']}** — {u['kept_pairs']} kept (task, teacher) pairs over {u['distinct_tasks_kept']} distinct tasks of {an['n_declared_tasks']} "
             f"({kept_str}; thresholds 1,024 pairs and 512 tasks for SUFFICIENT, 300 pairs for INSUFFICIENT), {d['unmeasured_cells_total']} of {an['declared_cells']} cells unmeasured.")
    r = (EXP / "results.md").read_text(encoding="utf-8")
    r = re.sub(r"\*\*TLDR:\*\* .*", f"**TLDR:** {setup} The Lean SFT set has {sft['n_pairs']} (prompt, file) pairs on the host; every count below carries its denominator.", r, count=1)
    r = re.sub(r"\*\*Status:\*\* .*", f"**Status:** DONE ({now}). Teacher runs, re-send, scoring, generated-Lean screen, analysis and SFT assembly complete; verdict **{d['verdict']}**.", r, count=1)
    r = re.sub(r"\| Scoring and verdict \| .*\|",
               f"| Scoring and verdict | done | frozen scorer over every served cell ([`results/scored_cells.jsonl`](results/scored_cells.jsonl)); generated-Lean screen ([`results/generated_lean_screen.json`](results/generated_lean_screen.json)); analysis ([`results/analysis_v3.json`](results/analysis_v3.json)); SFT manifest ([`results/sft_manifest.json`](results/sft_manifest.json)); verdict **{d['verdict']}** |", r)
    unm_list = "; ".join(f"{t}: {pt[t]['unmeasured']} ({', '.join(pt[t]['unmeasured_task_ids'][:6])}{'…' if len(pt[t]['unmeasured_task_ids']) > 6 else ''})" for t in TEACHERS)
    sec = f"""
## Results (PROTOCOL § 6; every teacher over the same 970 declared tasks)

{setup}

{tables}
**Measured** = a model response was served (any content); **unmeasured** cells are listed, never counted as zero: {unm_list}. Every unmeasured cell is a `TimeoutError` after one request with no response (possibly served and billed, so never re-sent) or, for Anthropic, also a no-receipt cell whose single identical re-send returned `MaxOutputTokensExceededError`. The Wilson interval is conditional on measurement (unit = task); the two bounds assume every unmeasured cell fails or succeeds.

**Generated-Lean screen (held-out panels):** {screen['n_kept_cells_screened']} kept files screened against VeriBench `py_src` + `lean_src` ({screen['protected']['n_veribench_files']} files) and the held-out panel files available at the pin ({screen['protected']['n_panel_files']} files from `{', '.join(screen['protected']['panel_dirs_present'])}`; VeriBench V2's five full-source task inputs are private at the pin and could not be screened): {screen['n_exact']} exact, {screen['n_near']} near hits (max word-5-gram Jaccard among clean {screen['max_jaccard_among_clean']}); excluded cells: {screen['excluded_cells'] or 'none'}.

**SFT set (host only, `/lfs/skampere1/0/brando9/rl4cv_e02a_v3/sft/lean_warmstart_v3.jsonl`, SHA-256 `{sft['sft_sha256'][:16]}…`):** {sft['n_pairs']} (prompt, kept file) pairs over {sft['n_distinct_tasks']} distinct tasks, per teacher {sft['per_teacher']}; the committed [`results/sft_manifest.json`](results/sft_manifest.json) lists task ids, teachers and SHA-256s. Each row holds experiment 103's exact system prompt and user message (instruction + addendum) and the kept Lean file.

**Charges reported by the gateway (USD):** preflight {charges_pre:.2f}; main + recovery {charges_main:.2f}; total {charges_pre + charges_main:.2f}. Anthropic `model_error` cells report no charge.

### Verdict

**{d['verdict']}** (rule: {d['rule']}). All-unmeasured-fail verdict {d['verdict_all_unmeasured_fail']}; all-unmeasured-succeed verdict {d['verdict_all_unmeasured_succeed']}. Union kept pairs {u['kept_pairs']} (threshold 1,024 / 300), distinct tasks {u['distinct_tasks_kept']} (threshold 512); tasks kept by k teachers: {u['tasks_kept_by_k_teachers']}; pairwise overlap {u['overlap']}.

What this means for the warm start: the kept pairs are the Lean SFT part available by this route today. The hypothesis ("the Anthropic and OpenAI teachers each keep at least 40% of the screened tasks") is {'supported' if all(pt[t]['observed_yield'] >= 0.40 for t in ('anthropic', 'openai')) else 'not supported'} on observed yields (anthropic {pt['anthropic']['observed_yield']:.3f}, openai {pt['openai']['observed_yield']:.3f}, google {pt['google']['observed_yield']:.3f}). The Anthropic teacher at the locked `compute_effort max` returned a provider `MaxOutputTokensExceededError` (the registry's 128,000-token output ceiling exhausted without a completion) on {pt['anthropic']['model_error_cells']} of 970 cells and an incomplete completion on {pt['anthropic']['incomplete_cells']} more (23 with no Lean block, 3 cut at the output limit with Lean) (the same provider-side behaviour experiment 103 recorded for Claude Opus 5 at max); a lower effort or a vendor agent is a separately recorded condition for a later version, not a recovery pass.

### Deviations and observations (recorded, none changes a locked scientific setting)

1. MBPP `code` is stored with CRLF line endings; the rewrite normalizes them to LF and changes nothing else. Four MBPP tasks (56, 349, 899, 967) define a function named `check`, which the VeriBench layout reserves for the test harness; they are dropped and listed (`harness_name_collision`).
2. `valk run results` returned "tracker returned a malformed response" for every run; the per-cell rows (service-collected bytes and hashes) were read from the run record that `valk run output` delivers, with each cell's agent receipt.
3. Gemini 4 Argon ran with `max_tokens` 128,000 (the registry allows 262,144) so all three teachers share one output budget, as PROTOCOL § 4 permits.
4. The preflight infrastructure check counts a provider `model_error` as a recorded model outcome rather than a transport fault (Anthropic's preflight cell).
5. `skampere1` rebooted on 10-08-2026 15:34 PDT during scoring; the Anthropic shard and the 16 recovery cells were already scored, the Astra/Argon files were re-scored from the preserved materialized trial dirs (no teacher call repeated). Scoring provenance: `results/scored_cells.summary.json`.
6. Of the VeriBench V2 / V2.1 held-out panels only experiment 97's E97-P001 task files exist at the pin; the generated-Lean screen covers VeriBench V1 (896 Python + 899 Lean files) and those files.
7. The 13 + 15 + 14 `TimeoutError` cells (one request, no response within the agent's 3,000 s client timeout) stay unmeasured; a timeout may have been served, so the protocol forbids re-sending them.
"""
    marker = "\n## Results (PROTOCOL § 6"
    if marker in r:
        r = r[:r.index(marker)]
    r = r.rstrip("\n") + "\n" + sec
    (EXP / "results.md").write_text(r, encoding="utf-8")
    # 02A v3 README status rows
    rd = (EXP / "README.md").read_text(encoding="utf-8")
    rd = rd.replace("| Protocol lock | Pending (after the preflight) |", "| Protocol lock | Locked 10-08-2026 00:09 UTC at commit `879eefbb…` |")
    rd = rd.replace("| Source build and screens | Pending |", "| Source build and screens | Done 10-07-2026: 970 of 974 MBPP tasks, 0 screen hits |")
    rd = rd.replace("| Teacher runs | Pending |", f"| Teacher runs | Done 10-08-2026: 3 × 970 cells; unmeasured {unm['anthropic']} / {unm['openai']} / {unm['google']} (anthropic / openai / google) |")
    rd = rd.replace("| Scoring, analysis, verdict | Pending |", f"| Scoring, analysis, verdict | Done {now[:10]}: **{d['verdict']}**, {u['kept_pairs']} kept pairs over {u['distinct_tasks_kept']} tasks ({kept_str}); see [results.md](results.md) |")
    (EXP / "README.md").write_text(rd, encoding="utf-8")
    pr = PHASE_README.read_text(encoding="utf-8")
    pr = pr.replace("| Warm-start Lean data | [v3](expt_v3/README.md) designed 10-07-2026: frontier teachers via Valkyrie on screened MBPP, kernel-verified keep rule |",
                    f"| Warm-start Lean data | [v3](expt_v3/README.md) done {now[:10]}: **{d['verdict']}**, {u['kept_pairs']} kernel-verified (task, teacher) pairs over {u['distinct_tasks_kept']} MBPP tasks ({kept_str}; Fable 5.1 at max effort hit the 128k output ceiling on {pt['anthropic']['model_error_cells']}/970); SFT set on skampere1 ([results](expt_v3/results.md)) |")
    PHASE_README.write_text(pr, encoding="utf-8")
    ix = INDEX.read_text(encoding="utf-8")
    ix = ix.replace("| [p 9/10] [v3](02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/README.md): build kernel-verified Lean warm-start data via Valkyrie teachers (owner @lethan3); then warm start (D-103, D-105) |",
                    f"| [p 9/10] [v3](02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/README.md) done {now[:10]}: **{d['verdict']}**, {u['kept_pairs']} kernel-verified Lean pairs over {u['distinct_tasks_kept']} MBPP tasks from Valkyrie teachers (owner @lethan3); next the warm start (D-103, D-105) |")
    INDEX.write_text(ix, encoding="utf-8")
    print(json.dumps({"verdict": d["verdict"], "kept_pairs": u["kept_pairs"], "distinct_tasks": u["distinct_tasks_kept"], "sft_pairs": sft["n_pairs"], "charges_total": round(charges_pre + charges_main, 2)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

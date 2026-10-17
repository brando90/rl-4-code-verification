"""Publish measured v3 technical results from retained receipts, explicitly preserving unrun stages."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from technical import ROOT, V3, T2, T3
from cohort import SOURCE, SCORE_SHA256, digest
from training_checkpoint import write_new


def publish_t2():
    result = json.loads((T2 / 'result.json').read_text())
    update = json.loads((T2 / 'update/output/result.json').read_text())
    strict = json.loads((SOURCE / 'update/output/result.json').read_text())
    refit = result['refit_probability']
    if digest(SOURCE / 'score/cells/result.json') != SCORE_SHA256:
        raise ValueError('immutable source scoring changed')
    if update['before_parameters'] != strict['before_parameters']:
        raise ValueError('factored and strict updates did not start from identical parameters')
    summary = {'condition': 'v3-A7', 'gate': 'T2', 'status': result['status'],
               'counts': update['counts'], 'grad_norm': result['grad_norm'],
               'loss': update['metrics']['loss'], 'before_parameters': update['before_parameters'],
               'after_parameters': update['after_parameters'], 'parameter_change': result['parameter_change'],
               'training_seconds': update['training_seconds'], 'batch_sha256': update['batch_sha256'],
               'refit_probability': refit, 'source_score_sha256': SCORE_SHA256,
               'update_result_sha256': digest(T2 / 'update/output/result.json'),
               'strict_update_result_sha256': digest(SOURCE / 'update/output/result.json'),
               'api_spend_usd': 0}
    path = V3 / 'results/T2_v3_update_summary.json'
    if not path.exists(): write_new(path, summary)
    elif json.loads(path.read_text()) != summary: raise ValueError('published summary changed')
    now = datetime.now().astimezone().strftime('%m-%d-%Y %H:%M %Z')
    prefix = 'https://github.com/brando90/rl-4-code-verification/blob/main/experiments/' + V3.parent.name + '/expt_v3/'
    text = f'''# Experiment 13 v3 T2: {result['status']} on the retained factored-reward cohort

**Doc link:** <{prefix}RESULTS_T2_v3.md>

**TLDR:** T2_v3 {result['status']}: gradient norm {result['grad_norm']:.10g}, parameter change {result['parameter_change']}, and refit median absolute log-probability error {refit['median_absolute_logprob_error']:.10g}. The comparison uses the exact same 256 train rollouts and the original saved pre-update weights, optimizer, scheduler and random state; only the reward changes.

**Measured:** {now}. **Provider spend:** $0; local offline NeMo and vLLM only.

| Observation | Strict binary reward (immutable v2) | Factored reward (v3) |
|---|---:|---:|
| Declared / measured responses | 256 / 255 | 256 / 255 |
| Positive measured rewards | 0/255 | 21/255 |
| Complete groups / declared groups | 31/32 | 31/32 |
| Active complete groups | 0/31 | 14/31 |
| Nonzero-advantage slots | 0/248 | 112/248 |
| Optimizer calls | 1 | 1 |
| Gradient norm | 0 | {result['grad_norm']:.10g} |
| Parameter change | False; 0/399 tensors changed | {result['parameter_change']}; full digest covers 399 tensors |
| Refit responses | 8 | {refit['responses']} |
| Unsupported refit tokens | 0/44,844 | {refit['unsupported_tokens']}/{refit['generated_tokens']} |
| Median absolute refit log-probability error | 0.000032748153898864985 | {refit['median_absolute_logprob_error']:.12g} |
| T2 verdict | FAIL | {result['status']} |

The v3 criterion is the frozen protocol's positive gradient, changed full parameter hash, zero unsupported refit tokens and median absolute error ≤0.01. Refit p99 error ({refit['p99_absolute_logprob_error']:.10g}) and importance-truncated tokens ({refit['importance_truncated_tokens']}/{refit['generated_tokens']}) are descriptive, not added admission thresholds. The missing deterministic scorer outcome remains missing; its full eight-response group is masked, with all generated tokens retained in resource accounting.

Before hash: `{update['before_parameters'][0]['sha256']}`.
After hash: `{update['after_parameters'][0]['sha256']}`.
The saved scoring receipt remains `{SCORE_SHA256}`. [Group table and all original generation hashes](results/retained_cohort.json), [gate result](results/T2_v3.json), [update summary](results/T2_v3_update_summary.json), and [permanent strict result](../expt_v2/RESULTS_T2_S2.md) provide the reproducible comparison. Raw checkpoints and the exact replay batch stay at `{T2}`.

These are fixed-cohort technical measurements, with no population efficacy claim or stochastic repeat estimate (p-val=n/a for numerical/hash gates). The active-group difference is the previously recorded 14/31 = 45.16 percentage points, with a group-bootstrap 95% interval [29.03, 61.29] percentage points and two-sided exact McNemar p=0.0001220703125 on 14 versus 0 discordant groups. That interval describes resampling these 31 train groups; it does not quantify seed-to-seed learning uncertainty.

This result does not establish improved validation pass@1 or official VeriBench SCSC. The guarded training reward and the official SCSC aggregate have different definitions; the latter includes validated formal-specification coverage. Downstream replay, cost and learning results are reported in [the live ledger](results.md).

Copy-ready collaborator message: “I compared strict and factored reward on the exact same retained rollout batch. The factored update has gradient norm {result['grad_norm']:.6g}, parameter change {result['parameter_change']}, and refit error {refit['median_absolute_logprob_error']:.6g}; this is a technical pipeline result, not yet evidence of better held-out performance.”

**TLDR-end:** [rl-4-code-verification: {V3.parent.name}/expt_v3] T2_v3 {result['status']}; the strict v2 failure and every original artifact remain unchanged.
'''
    (V3 / 'RESULTS_T2_v3.md').write_text(text)
    return summary


if __name__ == '__main__':
    print(json.dumps(publish_t2(), sort_keys=True))

"""TLDR: Recompute the saved E20 smoke breakdown and T1 comparison from immutable receipts; no model execution."""
import csv, json, hashlib, math
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
E20=ROOT/'experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1'
T1=ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/PROTOCOL.md'
check_path=E20/'results/receipts/smoke_gate/smoke_logprob_check.json'
log_path=E20/'results/receipts/smoke_gate/log.jsonl'
rollout_path=E20/'results/smoke_rollouts.csv'
gen_path=E20/'results/smoke_generation_receipts.csv'
copy_a=Path('/tmp/e20_smoke_final_receipt/train/runs/A_s0')
copy_b=Path('/tmp/e20_closure_final/closure_20261021T221855Z/smoke_final')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ratio(a,b): return a/b if b else None
check=json.loads(check_path.read_text())
logs=[json.loads(x) for x in log_path.read_text().splitlines() if x.strip()]
rows=list(csv.DictReader(rollout_path.open()))
checks=check['checks']; full=check['full_softmax_checks']
updates=[]
for i,(c,f,l) in enumerate(zip(checks,full,logs),1):
    rr=[r for r in rows if int(r['update'])==i]
    finite_n=c['in_support']
    updates.append({
      'update':i,'sampled_tokens':c['tokens'],'in_support_tokens':finite_n,
      'unsupported_actions':c['outside_support'],'unsupported_share_all_tokens':ratio(c['outside_support'],c['tokens']),
      'finite_abs_delta_gt_0_05':c['abs_delta_gt_tol'],
      'finite_abs_delta_gt_0_05_share_all_tokens':ratio(c['abs_delta_gt_tol'],c['tokens']),
      'failed_gate_numerator':c['abs_delta_gt_tol']+c['outside_support'],
      'failed_gate_share':c['share_gt_tol'],'finite_mean_abs_delta':c['mean_abs_delta'],
      'finite_max_abs_delta':c['max_abs_delta'],
      'median_abs_delta_exact':'unavailable: only aggregate mean/max/counts were retained',
      'median_abs_delta_finite_bounds':[0.0,2*c['mean_abs_delta']],
      'p99_abs_delta_exact':'unavailable: no token-level deltas or quantile retained',
      'p99_abs_delta_finite_bounds_exclusive':[0.05,c['max_abs_delta']],
      'full_softmax_abs_delta_gt_0_05':f['abs_delta_gt_tol'],
      'full_softmax_share_gt_0_05':f['share_gt_tol'],
      'full_softmax_mean_abs_delta':f['mean_abs_delta'],
      'full_softmax_max_abs_delta':f['max_abs_delta'],
      'rollouts':len(rr),'unique_tasks':len({r['task_id'] for r in rr}),
      'generated_tokens_from_rollouts':sum(int(r['generated_tokens']) for r in rr),
      'truncated_rollouts':sum(r['truncated']=='True' for r in rr),
      'finish_reason_counts':{x:sum(r['finish_reason']==x for r in rr) for x in sorted({r['finish_reason'] for r in rr})},
    })
tokens=sum(u['sampled_tokens'] for u in updates); support=sum(u['in_support_tokens'] for u in updates)
unsupported=sum(u['unsupported_actions'] for u in updates); bad=sum(u['finite_abs_delta_gt_0_05'] for u in updates)
weighted_mean=sum(u['finite_mean_abs_delta']*u['in_support_tokens'] for u in updates)/support
max_delta=max(u['finite_max_abs_delta'] for u in updates)
analysis={
 'analysis_timestamp_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'CPU-only analysis of already-saved Experiment 20 smoke receipts; no model, trainer, GPU, scheduler, email, Google Doc, or repository writes.',
 'experiment_folder':'experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/',
 'gate':{'E20_share_abs_delta_gt_0_05_max_allowed':0.01,'observed_max':check['max_share_abs_delta_gt_0_05'],'pass':check['pass']},
 't1_decision_input':{'protocol_path':str(T1.relative_to(ROOT)),'requirements':{'median_abs_generator_trainer_logprob_error_max':0.01,'p99_abs_generator_trainer_logprob_error_max':0.10,'unsupported_sampled_tokens_required':0},'interpretation':'E13 V4-T1 is a separate frozen 8-response probe; this comparison is decision input only and does not relabel this E20 smoke as T1.'},
 'per_update':updates,
 'pooled':{
  'sampled_tokens':tokens,'in_support_tokens':support,'unsupported_actions':unsupported,'unsupported_share_all_tokens':ratio(unsupported,tokens),
  'finite_abs_delta_gt_0_05':bad,'failed_gate_numerator':bad+unsupported,'failed_gate_share':ratio(bad+unsupported,tokens),
  'finite_weighted_mean_abs_delta':weighted_mean,'finite_max_abs_delta':max_delta,
  'finite_median_bounds':[0.0,2*weighted_mean],
  'finite_p99_bounds_exclusive':[0.05,max_delta],
 },
 'recoverability':{
  'exact_median':'unavailable','exact_p99':'unavailable','unsupported_by_update':'recoverable','unsupported_by_component':'recoverable only as truncated-support component; full softmax has a universal support by construction and records zero outside-support tokens',
  'mismatch_by_task':'unavailable','mismatch_by_rollout':'unavailable','mismatch_by_token_position':'unavailable','mismatch_by_token_id':'unavailable',
  'recoverable_context_not_mismatch':'rollout counts, task IDs, generated-token counts, truncation, and finish reason by update are saved, but no per-rollout/token delta or support flags exist to join them to mismatch outcomes.',
 },
 't1_implications':{
  'median_threshold':'Exact median unavailable; finite-median upper bound is below 0.01 for each update and pooled data, so the saved aggregates imply the finite median criterion is satisfied.',
  'p99_threshold':'Unavailable: saved aggregates bound finite p99 above 0.05 and no greater than the per-update finite maximum; these bounds do not decide the 0.10 threshold.',
  'zero_unsupported':'Not satisfied on the analogous E20 data: 167 and 195 sampled token actions were outside the recomputed truncated support in updates 1 and 2.',
 }
}
input_paths=[T1,check_path,log_path,rollout_path,gen_path]
analysis['input_sha256']={str(p):sha(p) for p in input_paths}
# Duplicate native-copy equality was checked during collection; this parser needs only committed inputs.
for u in updates:
    # Treat unsupported positions as +infinity: they consume part of the upper half.
    finite_sum = u['finite_mean_abs_delta'] * u['in_support_tokens']
    u['all_token_median_upper_bound'] = finite_sum / (u['sampled_tokens'] / 2 - u['unsupported_actions'])
    u['unsupported_share_of_mismatch'] = u['unsupported_actions'] / u['failed_gate_numerator']
    assert u['sampled_tokens'] == u['in_support_tokens'] + u['unsupported_actions']
    assert u['generated_tokens_from_rollouts'] == u['sampled_tokens']
    assert abs(u['failed_gate_share'] - u['failed_gate_numerator'] / u['sampled_tokens']) < 1e-12
    assert u['finite_abs_delta_gt_0_05'] / u['in_support_tokens'] > .01
analysis['t1_implications']['all_token_median_threshold'] = 'Upper bounds including unsupported actions as infinite are below 0.01 in both updates; exact quantiles remain unavailable.'
analysis['t1_implications']['support_identity_at_least_99_percent'] = 'unavailable: full generator and trainer support sets were not retained'
analysis['t1_implications']['importance_truncation_cap_2_at_most_1_percent'] = 'unavailable: signed log-probability ratios/count at cap 2 were not retained'
analysis['t1_implications']['discarded_mass_median_and_p99'] = 'unavailable: discarded mass was not retained'
analysis['t1_comparison_verdict'] = 'FAIL on analogous saved E20 smoke: zero-unsupported criterion violated. This is not the frozen eight-response E13 T1 probe and does not change either gate.'
analysis['statistical_scope'] = 'Exact descriptive counts from two updates, one run; p-val=n/a; no independent-token inference.'
analysis['scope'] = 'CPU-only analysis of committed saved E20 smoke receipts; no new model measurements.'
(E20/'results/smoke_t1_analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
print(json.dumps({'gate':analysis['gate'], 'pooled':analysis['pooled'], 'comparison':analysis['t1_comparison_verdict']}))

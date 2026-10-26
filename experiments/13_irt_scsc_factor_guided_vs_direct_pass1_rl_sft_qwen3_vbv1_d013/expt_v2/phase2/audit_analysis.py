"""Report every fixed train mutation and reward increase without treating vulnerabilities as efficacy gates."""
from __future__ import annotations

import math
from audit_inputs import VARIANTS
from arm_rewards import family_reward, weighted_reward


def summary(values,declared):
    known=[v for v in values if v is not None]
    return {'declared':declared,'measured':len(known),'missing':declared-len(known),
            'observed_mean':sum(known)/len(known) if known else None,
            'mean_bounds':[sum(known)/declared,(sum(known)+declared-len(known))/declared]}


def evaluate(inputs,cpu_rows,coverage_rows,*,C_weights=None):
    cells=inputs['cells'];expected={c['cell_id']:c for c in cells}
    if (inputs.get('condition')!='v2-S2' or inputs.get('declared_tasks')!=32
            or len(cells)!=128 or len(expected)!=128):raise ValueError('complete fixed audit manifest required')
    cpu={r['cell_id']:r for r in cpu_rows};coverage={r['cell_id']:r for r in coverage_rows}
    if len(cpu)!=len(cpu_rows) or len(coverage)!=len(coverage_rows) or set(cpu)!=set(expected) or set(coverage)!=set(expected):
        raise ValueError('audit measured inventories changed')
    tasks={c['task_id'] for c in cells}
    if C_weights is not None:
        if set(C_weights)!=tasks:raise ValueError('frozen C weights must cover exactly the audit task cohort')
        for weights in C_weights.values():
            if len(weights)!=3 or any(not math.isfinite(v) or v<=0 for v in weights) or abs(sum(weights)-1)>1e-12:
                raise ValueError('invalid frozen C weights')
    records=[];grouped={}
    for cell in cells:
        key=cell['cell_id'];a=cpu[key];b=coverage[key]
        for row in (a,b):
            if any(row.get(k)!=cell[k] for k in ('audit_id','task_id','split','variant')):
                raise ValueError('audit measurement identity changed')
        if cell['split']!='train' or cell['variant'] not in VARIANTS:raise ValueError('nontrain or undeclared audit variant')
        measured=a.get('components') is not None and a.get('strict_status')=='measured'
        strict=a.get('strict') if measured else None
        if measured and (type(strict) not in (int,bool) or strict not in (0,1)):
            raise ValueError('invalid strict outcome')
        component=a['components'] if measured else None
        rewards={'A':float(strict) if strict is not None else None,
                 'B':family_reward(component,strict) if measured else None,
                 'C':weighted_reward(component,C_weights[cell['task_id']],strict) if measured and C_weights is not None else None}
        hidden=a.get('hidden_test_coverage');formal=b.get('formal_specification_coverage')
        for value in [*rewards.values(),hidden,formal]:
            if value is not None and (not math.isfinite(value) or not 0<=value<=1):raise ValueError('audit score outside [0,1]')
        record={**{k:cell[k] for k in ('cell_id','audit_id','task_id','split','variant')},'strict':strict,
                'rewards':rewards,'theorem_count':component['p']['denominator'] if measured else None,
                'hidden_test_coverage':hidden,'formal_specification_coverage':formal,
                'cleanup_verified':a.get('cleanup_verified') is True}
        records.append(record);grouped.setdefault(cell['audit_id'],{})[cell['variant']]=record
    if len(grouped)!=32 or any(set(rows)!=set(VARIANTS) for rows in grouped.values()):raise ValueError('audit task/variant denominator changed')
    increases=[];comparisons=[]
    for audit_id,variants in grouped.items():
        original=variants['original']
        for variant in VARIANTS[1:]:
            current=variants[variant]
            deltas={name:(current[name]-original[name] if current[name] is not None and original[name] is not None else None)
                    for name in ('strict','theorem_count','hidden_test_coverage','formal_specification_coverage')}
            reward_deltas={arm:(current['rewards'][arm]-original['rewards'][arm]
                          if current['rewards'][arm] is not None and original['rewards'][arm] is not None else None) for arm in ('A','B','C')}
            row={'audit_id':audit_id,'variant':variant,'original_cell_id':original['cell_id'],
                 'mutated_cell_id':current['cell_id'],'reward_changes':reward_deltas,**deltas}
            comparisons.append(row)
            for arm,delta in reward_deltas.items():
                if delta is not None and delta>0:increases.append({**row,'arm':arm,'reward_increase':delta})
    by_variant={variant:{metric:summary([r[metric] for r in records if r['variant']==variant],32)
                for metric in ('strict','hidden_test_coverage','formal_specification_coverage')} for variant in VARIANTS}
    return {'condition':'v2-S2','stage':'TRAIN_MUTATION_AUDIT','declared':128,'accounted':128,
            'audits_ran':True,'C_evaluated':C_weights is not None,'cleanup_unresolved':sum(not r['cleanup_verified'] for r in records),
            'rows':records,'comparisons':comparisons,'reward_increasing_mutations':increases,'by_variant':by_variant,
            'independent_checks_functioning':False,'missing_values_imputed':False,'learning_admitted':False,
            'interpretation':'fixed train mutation audit, not efficacy or an anti-gaming guarantee; no population test; p-val=n/a',
            'required_next':'bind functioning hidden/hosted route and cleanup receipts plus the prospective pilot monitor'}

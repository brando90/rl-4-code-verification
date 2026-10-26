"""Preserve historical ladder evaluation sampling and explicit checkpoint-selection denominators."""
from __future__ import annotations

import hashlib
from fractions import Fraction

SAMPLING = {'temperature': .6, 'top_p': .95, 'top_k': 20, 'max_tokens': 12288,
            'seed_base': 91, 'thinking': 'on', 'stop_tokens': ['<|im_end|>'], 'addendum': 'vbv1'}
POPULATIONS = {'validation': (135,8), 'test': (222,16)}


def sampling_parameters(tokenizer,sample_idx):
    """Use the historical SamplingParams arguments, including default special-token rendering."""
    from vllm import SamplingParams
    from rl4cv.veribench.generate import resolve_stop_token_ids
    if type(sample_idx) is not int or not 0 <= sample_idx < 16: raise ValueError('invalid evaluation sample')
    return SamplingParams(n=1,temperature=.6,top_p=.95,top_k=20,max_tokens=12288,
                          seed=91*100003+sample_idx,
                          stop_token_ids=resolve_stop_token_ids(tokenizer,['<|im_end|>']))


def render(instruction,tokenizer,veribench_root):
    """Reuse the actual ladder prompt builder rather than reconstructing its messages."""
    from rl4cv.veribench.exp103 import build_prompt
    prompt=build_prompt(instruction,addendum='vbv1',root=veribench_root)
    text=tokenizer.apply_chat_template(prompt.messages(),tokenize=False,add_generation_prompt=True,enable_thinking=True)
    return {'text':text,'chat_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'required_paths':list(prompt.required_paths),'instruction_sha256':prompt.instruction_sha256,
            'addendum_sha256':prompt.addendum_sha256,'prompt_sha256':prompt.prompt_sha256,
            'system_prompt_sha256':prompt.system_prompt_sha256}


def identities(task_ids,split,*,arm,run_seed,boundary):
    if split not in POPULATIONS: raise ValueError('evaluation split must be explicit')
    n,k=POPULATIONS[split]
    if len(task_ids)!=n or len(set(task_ids))!=n:raise ValueError('complete evaluation task manifest required')
    if arm not in ('A','B','C','P') or run_seed not in (13011,13012,13013) or boundary not in (1,2,3,4):
        raise ValueError('unregistered main evaluation identity')
    return [{'cell_id':f'{arm}/{run_seed}/{boundary}/{split}/{task}/{sample}',
             'task_id':task,'sample_idx':sample,'seed':91*100003+sample,'split':split,
             'arm':arm,'run_seed':run_seed,'boundary':boundary} for task in task_ids for sample in range(k)]


def strict_summary(manifest,rows):
    """All cells stay declared; known scores give sharp binary bounds, never imputed outcomes."""
    if not manifest or len({c['cell_id'] for c in manifest})!=len(manifest):raise ValueError('invalid evaluation manifest')
    table={r['cell_id']:r for r in rows}
    if len(table)!=len(rows) or set(table)!={c['cell_id'] for c in manifest}:raise ValueError('evaluation receipt inventory changed')
    observed=[];counts={}
    for cell in manifest:
        row=table[cell['cell_id']]
        if any(row.get(k)!=cell[k] for k in ('task_id','sample_idx','split','arm','run_seed','boundary')):
            raise ValueError('evaluation receipt identity changed')
        value=row.get('strict')
        if value is not None and (type(value) not in (int,bool) or value not in (0,1)):
            raise ValueError('strict outcome must be binary or unknown')
        counts[cell['task_id']]=counts.get(cell['task_id'],0)+1
        if value is not None:observed.append(value)
    if len(set(counts.values()))!=1:raise ValueError('task sample denominators differ')
    n=len(manifest);successes=sum(observed);missing=n-len(observed)
    return {'condition':'v2-S2','declared':n,'measured':len(observed),'missing':missing,'successes':successes,
            'task_count':len(counts),'samples_per_task':next(iter(counts.values())),
            'strict_mean_observed':successes/len(observed) if observed else None,
            'strict_mean_bounds':[successes/n,(successes+missing)/n],'imputed':False}


def select(checkpoints):
    """Select only when every completion of missing binary outcomes gives the same max/tie-later checkpoint."""
    if len(checkpoints)!=4 or {r['boundary'] for r in checkpoints}!={1,2,3,4}:
        raise ValueError('all four token checkpoints are required')
    ordered=sorted(checkpoints,key=lambda r:r['boundary'])
    for row in ordered:
        s=row['summary']
        if (s['declared'],s['task_count'],s['samples_per_task'])!=(1080,135,8):raise ValueError('validation denominator changed')
        if s['measured']+s['missing']!=1080 or not 0<=s['successes']<=s['measured']:raise ValueError('invalid validation counts')
    winners=[]
    for row in ordered:
        lower=Fraction(row['summary']['successes'],1080)
        # Any earlier checkpoint loses a tie; any later checkpoint wins it.
        if all((lower>=Fraction(other['summary']['successes']+other['summary']['missing'],1080)
                if other['boundary']<row['boundary'] else
                lower>Fraction(other['summary']['successes']+other['summary']['missing'],1080))
               for other in ordered if other is not row):winners.append(row['boundary'])
    return {'condition':'v2-S2','status':'SELECTED' if len(winners)==1 else 'INCONCLUSIVE',
            'boundary':winners[0] if len(winners)==1 else None,
            'rule':'maximum full-validation strict mean; ties later; unresolved ordering from missing cells stays unresolved',
            'test_admitted':False}

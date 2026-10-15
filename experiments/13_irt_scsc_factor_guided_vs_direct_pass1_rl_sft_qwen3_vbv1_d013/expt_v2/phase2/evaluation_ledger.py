"""Recover complete evaluation outputs and retain at most one identical retry for a typed transient interruption."""
from __future__ import annotations

import json
from pathlib import Path
import re

from training_checkpoint import digest
from evaluation_generation import validate_manifest

TRANSIENT={'OSError','ConnectionError','BrokenPipeError','InterruptedError','ProcessLookupError'}


def transient(closed,output):
    if closed.get('cleanup_verified') is not True or closed.get('error_type')=='TimeoutError':return False
    code=closed.get('worker_exit_code')
    if type(code) is int and code<0:return True
    if closed.get('error_type') in TRANSIENT:return True
    path=Path(output)/'error.json'
    return path.exists() and json.loads(path.read_text()).get('error_type') in TRANSIENT


def validate_row(cell,row):
    if any(row.get(k)!=v for k,v in cell.items()):raise ValueError('evaluation response differs from its frozen cell')
    ids=row.get('output_token_ids')
    if (row.get('condition')!='v2-S2' or not isinstance(ids,list) or not 0<len(ids)<=12288
            or any(type(i) is not int or i<0 for i in ids) or not isinstance(row.get('completion'),str)
            or row.get('finish_reason') not in ('stop','length')
            or row.get('at_token_cap')!=(row['finish_reason']=='length')
            or row.get('generated_tokens')!=len(ids) or row.get('prompt_tokens')!=len(cell['prompt_token_ids'])):
        raise ValueError('invalid retained evaluation response')


def scan(root,manifest,allowlist,snapshot_sha):
    root=Path(root);cells=validate_manifest(manifest,allowlist);prefix=f"{manifest['purpose']}_b{manifest['boundary']}"
    attempts=[0]*len(cells);retry=[False]*len(cells);outputs={c['cell_id']:None for c in cells}
    costs=[];stages=[];cleanup_unresolved=0;pending_stage=None;tokens=0;missing_costs=[]
    health=root/(prefix+'_preflight')
    if (health/'dispatch/result.json').exists():
        if (health/'cost.json').exists():costs.append({'path':str(health/'cost.json'),'sha256':digest(health/'cost.json')})
        else:missing_costs.append(prefix+'_preflight')
    records=sorted(p for p in root.glob(prefix+'_s*.json') if re.fullmatch(re.escape(prefix)+r'_s[0-9]{3}\.json',p.name))
    for number,path in enumerate(records):
        key=path.stem;record=json.loads(path.read_text());stage=root/key;indexes=record['indexes']
        if key!=f'{prefix}_s{number:03d}' or record.get('stage_key')!=key or record.get('stage')!='evaluation_generate':
            raise ValueError('evaluation segment sequence changed')
        if record.get('snapshot_sha256')!=snapshot_sha:raise ValueError('segment belongs to another evaluation snapshot')
        if (not indexes or len(indexes)>256 or indexes!=sorted(set(indexes))
                or any(type(i) is not int or not 0<=i<len(cells) for i in indexes)):
            raise ValueError('invalid evaluation segment indexes')
        config_path=stage/'runtime.json';config=json.loads(config_path.read_text())
        if (digest(config_path)!=record['configuration_sha256'] or config['indexes']!=indexes
                or config['stage_key']!=key or config['snapshot_sha256']!=snapshot_sha):
            raise ValueError('evaluation runtime changed after reservation')
        for index in indexes:
            if (outputs[cells[index]['cell_id']] is not None or attempts[index]>=2
                    or (attempts[index] and not retry[index])):
                raise ValueError('completed or nonretryable evaluation cell was scheduled again')
            attempts[index]+=1;retry[index]=False
        closed_path=stage/'dispatch/result.json'
        if not closed_path.exists():pending_stage=key;break
        closed=json.loads(closed_path.read_text())
        if (closed.get('snapshot_sha256')!=snapshot_sha or closed.get('stage_key')!=key
                or closed.get('lease_id')!=record['lease_id']):raise ValueError('evaluation dispatch identity changed')
        cleanup_unresolved+=int(closed.get('cleanup_verified') is not True)
        raw=stage/'output';files=sorted(raw.glob('*.generation.json'));found=set()
        for value in files:
            index=int(value.name.split('.')[0])
            if index not in indexes or index in found:raise ValueError('unexpected evaluation response index')
            row=json.loads(value.read_text());validate_row(cells[index],row);found.add(index)
            outputs[cells[index]['cell_id']]={'path':str(value),'sha256':digest(value)};tokens+=len(row['output_token_ids'])
        missing=set(indexes)-found
        if closed.get('status')=='RUNTIME_EXITED_ZERO' and missing:
            raise ValueError('successful evaluation segment lacks declared responses')
        can_retry=transient(closed,raw)
        for index in missing:retry[index]=can_retry and attempts[index]<2
        stages.append({'stage_key':key,'indexes':indexes,'completed':len(found),'missing':len(missing),
            'status':closed['status'],'cleanup_verified':closed.get('cleanup_verified') is True,
            'result':{'path':str(closed_path),'sha256':digest(closed_path)}})
        cost=stage/'cost.json'
        if cost.exists():costs.append({'path':str(cost),'sha256':digest(cost)})
        else:missing_costs.append(key)
    pending=[i for i,c in enumerate(cells) if outputs[c['cell_id']] is None and (attempts[i]==0 or retry[i])]
    missing=sum(value is None for value in outputs.values())
    return {'condition':'v2-S2','purpose':manifest['purpose'],'declared':len(cells),'completed':len(cells)-missing,
        'missing':missing,'known_generated_tokens':tokens,'tokens_in_missing_responses_unknown':missing>0,
        'generation':outputs,'attempts':attempts,'identical_retries':sum(max(n-1,0) for n in attempts),
        'pending_indexes':pending,'next_segment':len(records),'unfinished_stage':pending_stage,
        'cleanup_unresolved':cleanup_unresolved,'stages':stages,'costs':costs,'missing_cost_receipts':missing_costs,
        'status':'RECOVERY_REQUIRED' if pending_stage else 'CLEANUP_REQUIRED' if cleanup_unresolved else
                 'PENDING' if pending else 'COMPLETE' if not missing else 'INCOMPLETE'}

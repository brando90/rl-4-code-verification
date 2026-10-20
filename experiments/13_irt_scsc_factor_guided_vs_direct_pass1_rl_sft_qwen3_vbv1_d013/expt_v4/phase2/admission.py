"""TLDR: Bind v4 protocol, implementation, tests and CPU evidence while refusing an unimplementable launch."""
import argparse
import json
from pathlib import Path
from common import digest, object_digest, write_new
from context_contract import validate_lengths

PROTOCOL_SHA256='fb741636844294fb76667c4d6928ddbef1c7e28fde0fd1093ae834876764e063'
OBJECTIVE_BLOCKER=('Frozen top-20 raw log-probabilities cannot reconstruct vLLM 0.10.0 native support '
                   'when more than 20 tokens tie at the kth logit, or certify that no omitted tie exists.')


def source_files(root):
    root=Path(root)
    return sorted([root/'PROTOCOL.md',*list((root/'phase2').glob('*.py')),
                   *list((root/'tests').glob('*.py')),root/'phase2/A6_counts.json',root/'phase2/context_values.json'])


def prepare(root,output,*,runtime_bindings=()):
    root=Path(root).resolve()
    if digest(root/'PROTOCOL.md')!=PROTOCOL_SHA256:raise ValueError('frozen protocol changed')
    result={'tldr':'CPU evidence is bound; launch is blocked by the frozen top-20 reconstruction contract.',
            'condition':'e13v4','status':'BLOCKED','api_spend_usd':0,
            'protocol_sha256':PROTOCOL_SHA256,'root':str(root),
            'bindings':[{'path':str(p.relative_to(root)),'sha256':digest(p)} for p in source_files(root)],
            'runtime_bindings':[{'path':str(p),'sha256':digest(p)} for p in runtime_bindings],
            'context':json.loads((root/'phase2/context_values.json').read_text()),
            'blockers':[OBJECTIVE_BLOCKER],
            'launch_measurements':'V4-T1, G0, T2, T3, T4 and B audits have not run; no gate was retried.',
            'gpu_allocations':0,'generations':0,'optimizer_steps':0}
    write_new(output,result)
    check_admission(output,require_launch=False)
    return result


def check_admission(path,*,require_launch=True):
    path=Path(path);record=json.loads(path.read_text());root=Path(record['root'])
    if record.get('condition')!='e13v4' or record.get('api_spend_usd')!=0 or record['protocol_sha256']!=PROTOCOL_SHA256:
        raise ValueError('invalid v4 admission identity')
    expected={str(p.relative_to(root)) for p in source_files(root)}
    bound=[b['path'] for b in record['bindings']]
    if len(set(bound))!=len(bound) or set(bound)!=expected:raise ValueError('admission omits or duplicates source/test bindings')
    for binding in record['bindings']:
        if digest(root/binding['path'])!=binding['sha256']:raise ValueError('bound v4 file changed: '+binding['path'])
    for binding in record['runtime_bindings']:
        if digest(binding['path'])!=binding['sha256']:raise ValueError('bound read-only runtime source changed')
    if digest(root/'PROTOCOL.md')!=PROTOCOL_SHA256:raise ValueError('protocol changed')
    context=json.loads((root/'phase2/context_values.json').read_text())
    if context!=record['context']:raise ValueError('context values changed')
    for engine in ('generator','trainer'):
        validate_lengths(context['response_cap'],context['engines'][engine]['context'],context,engine)
    if require_launch:
        # This is a source-level capability failure, not a flag that can be overridden in JSON.
        raise ValueError('V4 launch BLOCKED: '+OBJECTIVE_BLOCKER)
    return record


def completed_update(path,summary,admission_path,*,checker=check_admission):
    checker(admission_path,require_launch=True)
    if summary.get('condition')!='e13v4' or summary.get('completed') is not True:
        raise ValueError('completed v4 update required')
    result={**summary,'admission_sha256':digest(admission_path)}
    write_new(path,result)
    return result


def verify_update(summary,admission_path):
    if summary.get('admission_sha256')!=digest(admission_path):raise ValueError('update admission changed on resume')


def launch_timing(v3_pilot):
    """Read-only check of the master's v3 release trigger; never modifies its receipts."""
    root=Path(v3_pilot)
    paths=[root/f'{arm}_{seed}/result_30.json' for arm in ('A','B','P') for seed in (1301,1302)]
    six=all(p.is_file() for p in paths)
    failed=root/'B_1301/T5_30.json'
    failure=failed.is_file() and json.loads(failed.read_text()).get('status')=='FAIL'
    return {'released':six or failure,'six_result_30':six,'B_1301_T5_30_FAIL':failure}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','check','launch-check'])
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--record',required=True,type=Path)
    a=p.parse_args()
    if a.action=='prepare':
        venv=Path('/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl')
        paths=[venv/'.venv/lib/python3.12/site-packages/vllm/v1/sample/ops/topk_topp_sampler.py',
               venv/'.venv/lib/python3.12/site-packages/vllm/v1/sample/sampler.py',
               venv/'nemo_rl/algorithms/loss_functions.py',venv/'nemo_rl/models/policy/dtensor_policy_worker.py']
        r=prepare(a.root,a.record,runtime_bindings=paths)
    else:r=check_admission(a.record,require_launch=a.action=='launch-check')
    print(json.dumps({'status':r['status'],'bindings':len(r['bindings']),'admission_sha256':digest(a.record),'blockers':r['blockers']}))

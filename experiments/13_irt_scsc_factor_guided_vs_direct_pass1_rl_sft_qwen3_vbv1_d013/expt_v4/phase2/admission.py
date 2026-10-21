"""TLDR: Bind v4 protocol, implementation, tests and CPU evidence while refusing an unimplementable launch."""
import argparse
import json
from pathlib import Path
from common import digest, object_digest, write_new
from context_contract import validate_lengths

PROTOCOL_SHA256='fb741636844294fb76667c4d6928ddbef1c7e28fde0fd1093ae834876764e063'
AMENDMENT='AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md'
AMENDMENT_SHA256='81f22afc01ea662ca6a1f8ca7d96a2b63b68b0f8293c35d6d3aa6fe2f3703543'
AMENDMENTS={'AMENDMENT_V4-A4_importance_correction_at_uncertified_positions_10-20-2026.md': '24f45c46e21a3f53a725f0d0ac3c076d6a94f008f3c2b097b54f1390adc9c294', 'AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md': '81f22afc01ea662ca6a1f8ca7d96a2b63b68b0f8293c35d6d3aa6fe2f3703543', 'AMENDMENT_V4-A2_receipt_invariance_and_sampler_backend_10-20-2026.md': '147b609db08b6237010e47d43aa9b4162240f20b77b5585b23a50463a8607226', 'AMENDMENT_V4-A3_schedule_v4_start_and_v3_pause_10-20-2026.md': '6f98520b7704d5bdb10f38312cf1566df0087c1c21133623c7cfcef4e67f2d70'}
RUNTIME_CONDITIONS=["V4-A3 veto window closed without veto (10-21-2026 12:00 PDT)","idle authorized device lease, acquired and checked per subprocess","pilot only: B_1301 T5_30 verdict exists and its lease is released; all v4 gates PASS"]


def source_files(root):
    root=Path(root)
    paths=[root/'PROTOCOL.md',*[root/name for name in AMENDMENTS],
        *list((root/'phase2').glob('*.py')),*list((root/'tests').glob('*.py'))]
    for name in ('launch_plan','watchdog_plan','A6_counts','context_values','runtime_inputs','policy_v4',
                 'sampler_cpu_receipt','forecast_verification','verification_dispatch3','adapter_dry_contracts'):
        paths.append(root/'phase2'/f'{name}.json')
    return sorted(paths)


def prepare(root,output,*,runtime_bindings=()):
    root=Path(root).resolve()
    if digest(root/'PROTOCOL.md')!=PROTOCOL_SHA256:raise ValueError('frozen protocol changed')
    if digest(root/AMENDMENT)!=AMENDMENT_SHA256:raise ValueError('frozen amendment changed')
    from rl4cv.forecast import verify_forecast
    forecast=next(root.parents[2].glob('experiments/19_*/expt_v1/forecasts/e19_g3_forecast_v4_g0.json'),None)
    if forecast is not None and not verify_forecast(forecast):raise ValueError('forecast verification failed')
    launch=json.loads((root/'phase2/launch_plan.json').read_text())
    watchdog=json.loads((root/'phase2/watchdog_plan.json').read_text())
    result={'tldr':'V4-A1 through A4 and real adapters are statically admitted; live gates remain unmeasured.',
            'condition':'e13v4','status':'ADMITTED','api_spend_usd':0,
            'protocol_sha256':PROTOCOL_SHA256,'amendment_sha256':AMENDMENT_SHA256,'root':str(root),
            'launch_plan_sha256':object_digest(launch),'watchdog_plan_sha256':object_digest(watchdog),
            'bindings':[{'path':str(p.relative_to(root)),'sha256':digest(p)} for p in source_files(root)],
            'runtime_bindings':[{'path':str(p),'sha256':digest(p)} for p in runtime_bindings],
            'context':json.loads((root/'phase2/context_values.json').read_text()),
            'blockers':[],'runtime_conditions':RUNTIME_CONDITIONS,'amendments':AMENDMENTS,
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
        if not require_launch and Path(binding['path']).suffix in ('.bin','.safetensors'):continue
        if digest(binding['path'])!=binding['sha256']:raise ValueError('bound read-only runtime source changed')
    if digest(root/'PROTOCOL.md')!=PROTOCOL_SHA256:raise ValueError('protocol changed')
    if record.get('amendment_sha256')!=AMENDMENT_SHA256 or digest(root/AMENDMENT)!=AMENDMENT_SHA256:
        raise ValueError('amendment changed')
    for name in ('launch','watchdog'):
        if record.get(name+'_plan_sha256')!=object_digest(json.loads((root/f'phase2/{name}_plan.json').read_text())):
            raise ValueError('plan changed')
    context=json.loads((root/'phase2/context_values.json').read_text())
    if context!=record['context']:raise ValueError('context values changed')
    for engine in ('generator','trainer'):
        validate_lengths(context['response_cap'],context['engines'][engine]['context'],context,engine)
    if record.get('amendments')!=AMENDMENTS:raise ValueError('all amendments required')
    for name,sha in AMENDMENTS.items():
        if digest(root/name)!=sha:raise ValueError('frozen amendment changed: '+name)
    unit=json.loads((root/'phase2/sampler_cpu_receipt.json').read_text())
    if (unit.get('status')!='PASS' or unit.get('positions',0)<10000 or unit.get('mismatched_tokens')!=0 or
        unit.get('flashinfer_absent') is not True or unit.get('sampler_forward')!='forward_native'):
        raise ValueError('A2 installed CPU check not passed')
    import importlib.util
    if importlib.util.find_spec('flashinfer') is not None:raise ValueError('FlashInfer installation changed')
    from nemo_objective_contract import KL_COEFFICIENT
    if KL_COEFFICIENT!=0:raise ValueError('nonzero KL requires another amendment')
    if require_launch and (record.get('status')!='ADMITTED' or record.get('blockers')):
        raise ValueError('not statically admitted')
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


def launch_timing(v3_pilot,*,phase='gates',now=None,veto_not_issued=False):
    """A3 gates start after the veto window; pilot additionally awaits B_1301."""
    import time
    from pause_v3 import VETO_END,ALLOWED
    now=time.time() if now is None else now
    root=Path(v3_pilot);verdict=root/'B_1301/T5_30.json'
    pause=root.parent/'autoresume_paused.json'
    paused=json.loads(pause.read_text()).get('trajectories',{}) if pause.exists() else {}
    window=now>=VETO_END and veto_not_issued
    verdict_ok=verdict.is_file() and json.loads(verdict.read_text()).get('status') in ('PASS','FAIL','EXTEND_TO_60')
    # EXTEND_TO_60 is v3's frozen spelling of its FAIL verdict; A3 cancels that extension.
    no_lease=not any(not p.with_name(p.stem+'_end.json').exists() for p in (root/'B_1301').glob('**/*_lease.json'))
    released=window and set(ALLOWED)<=set(paused) and (phase=='gates' or verdict_ok and no_lease)
    return {'released':released,'veto_window_closed_without_veto':window,'five_pauses_recorded':set(ALLOWED)<=set(paused),
            'B_1301_verdict':verdict_ok,'B_1301_lease_released':no_lease,'phase':phase}


def runtime_files(root):
    from runtime_inputs import inputs,SOURCE,PREP
    from audit_runtime import SUITES
    root=Path(root);repo=root.parents[2];cfg=inputs()
    venv=Path('/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl')
    files=[venv/'.venv/lib/python3.12/site-packages/vllm/v1/sample/ops/topk_topp_sampler.py',
           venv/'.venv/lib/python3.12/site-packages/vllm/v1/sample/sampler.py',
           venv/'nemo_rl/algorithms/loss_functions.py',venv/'nemo_rl/models/policy/dtensor_policy_worker.py',
           SOURCE,Path(cfg['templates']),Path(cfg['probe']),Path(cfg['train_ids']),SUITES,
           root.parent/'expt_v3/phase2/autoresume_watchdog.py',root.parent/'expt_v3/tests/test_autoresume_watchdog.py']
    for sub in ('phase2','phase1','R0_attempt_2'):
        files.extend((root.parent/'expt_v2'/sub).glob('*.py'))
        files.extend((root.parent/'expt_v2'/sub).glob('*.lean'))
    files.append(root.parent/'expt_v2/historical_oracle_v2.py')
    files.append(root.parent/'expt_v2/phase2/hidden_controls_result.json')
    files.extend(repo.glob('experiments/08_*/expt_v1/scripts/*.py'))
    files.extend(repo.glob('experiments/12_*/expt_v2/scripts/*.py'))
    files.extend((repo/'src/rl4cv').rglob('*.py'))
    files.extend(Path(cfg['scoring']['scorer']).glob('scripts/scsc/*.py'))
    forecast=next(repo.glob('experiments/19_*/expt_v1/forecasts/e19_g3_forecast_v4_g0.json'))
    files.extend([forecast,forecast.with_suffix('.sha256')])
    files.extend(Path(r['suite']['path']) for r in json.loads(SUITES.read_text())['rows'])
    for key in ('initial_model','tokenizer'):
        files.extend(p for p in Path(cfg[key]).iterdir() if p.is_file())
    files.extend(Path('/lfs/skampere1/0/brando9/rl4cv_e13v4')/(name+'.json') for name in ('launch_plan','watchdog_plan'))
    return sorted(set(files))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','check','launch-check'])
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--record',required=True,type=Path)
    a=p.parse_args()
    if a.action=='prepare':
        paths=runtime_files(a.root)
        r=prepare(a.root,a.record,runtime_bindings=paths)
    else:r=check_admission(a.record,require_launch=a.action=='launch-check')
    print(json.dumps({'status':r['status'],'bindings':len(r['bindings']),'admission_sha256':digest(a.record),'blockers':r['blockers'],'runtime_conditions':r.get('runtime_conditions',[])}))

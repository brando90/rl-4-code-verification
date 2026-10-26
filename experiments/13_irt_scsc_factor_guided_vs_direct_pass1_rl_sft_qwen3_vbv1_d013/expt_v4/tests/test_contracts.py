"""TLDR: Test full-split context coverage, anonymous A6 aggregation and admission tamper rejection."""
import copy
import json
from pathlib import Path
import shutil
import pytest
from context_contract import compute_context,validate_lengths,COUNTS
from a6_counts import reduce_rows
from common import digest,write_new
from admission import prepare,check_admission,completed_update,verify_update,launch_timing


def contexts():
    splits={s:[[1]*n]*count for (s,count),n in zip(COUNTS.items(),[7753,8000,9000])}
    return compute_context({'generator':splits,'trainer':splits},32768)


def test_context_covers_heldout_maximum():
    r=contexts();assert r['engines']['trainer']['context']==21288
    assert r['engines']['generator']['maximum_prompt_tokens']['train']==7753


@pytest.mark.parametrize('cap,ctx',[(8192,21288),(12288,15945),(8192,15945)])
def test_reject_retired_length_values(cap,ctx):
    with pytest.raises(ValueError):validate_lengths(cap,ctx,contexts(),'trainer')


def test_position_limit_and_incomplete_split():
    splits={s:[[1]*10]*n for s,n in COUNTS.items()}
    with pytest.raises(ValueError):compute_context({'generator':splits,'trainer':splits},12288)
    splits['test']=splits['test'][:-1]
    with pytest.raises(ValueError):compute_context({'generator':splits,'trainer':splits},32768)


def a6():
    cells=[{'cell_id':f'{t}/{s}','task_id':f'PRIVATE_TASK_{t}','sample_idx':s,'split':'train'} for t in range(64) for s in range(8)]
    rows=[{**c,'strict':int(c['sample_idx']==0),'factored_reward':c['sample_idx']/7} for c in cells]
    return {'cells':cells},rows


def test_reducer_commits_no_task_ids_and_keeps_missing():
    m,r=a6();r[0]['strict']=None;r[0]['factored_reward']=None
    result=reduce_rows(m,r)
    assert result['complete_groups']==63 and result['mixed_strict_groups']==63 and result['varying_B_groups']==63
    assert result['strict_success_histogram']['0']==1 and result['strict_success_histogram']['1']==63
    assert result['missing_strict']==1 and 'PRIVATE_TASK' not in json.dumps(result)
    with pytest.raises(ValueError):reduce_rows(m,r[:-1])


def admission_fixture(tmp_path):
    root=tmp_path/'v4';root.mkdir();(root/'phase2').mkdir();(root/'tests').mkdir()
    source=Path(__file__).resolve().parents[1]
    shutil.copyfile(source/'PROTOCOL.md',root/'PROTOCOL.md')
    from admission import AMENDMENTS
    from operational_pause import RECORD
    for name in (*AMENDMENTS,RECORD):shutil.copyfile(source/name,root/name)
    for name in ('runtime_inputs','policy_v4','sampler_cpu_receipt','forecast_verification','operational_pause'):
        shutil.copyfile(source/'phase2'/f'{name}.json',root/'phase2'/f'{name}.json')
    for name in ('verification_dispatch4','adapter_dry_contracts'):write_new(root/'phase2'/f'{name}.json',{'synthetic_fixture':True})
    write_new(root/'phase2/launch_plan.json',{'fixture':'launch'})
    write_new(root/'phase2/watchdog_plan.json',{'fixture':'watchdog'})
    (root/'phase2/x.py').write_text('# TLDR: Fixture.\n');(root/'tests/test_x.py').write_text('# TLDR: Fixture.\n')
    write_new(root/'phase2/A6_counts.json',{'count':64});write_new(root/'phase2/context_values.json',contexts())
    path=tmp_path/'admission.json';prepare(root,path);return root,path


def test_admission_binds_all_amendments_and_launch_contract(tmp_path):
    root,path=admission_fixture(tmp_path)
    assert check_admission(path,require_launch=False)['status']=='ADMITTED'
    assert check_admission(path)['status']=='ADMITTED'
    (root/'tests/test_new.py').write_text('# TLDR: Unbound test.\n')
    with pytest.raises(ValueError,match='omits'):check_admission(path,require_launch=False)


def test_admission_detects_mutation_and_records_each_update_digest(tmp_path):
    root,path=admission_fixture(tmp_path)
    summary=completed_update(tmp_path/'summary.json',{'condition':'e13v4','completed':True},path,
                             checker=lambda *a,**kw:None)
    verify_update(summary,path)
    assert summary['admission_sha256']==digest(path)
    with pytest.raises(ValueError):verify_update({'admission_sha256':'0'*64},path)
    (root/'phase2/x.py').write_text('# TLDR: Changed.\n')
    with pytest.raises(ValueError,match='changed'):check_admission(path,require_launch=False)


def test_launch_timing_read_only(tmp_path):
    assert not launch_timing(tmp_path)['released']
    write_new(tmp_path/'B_1301/T5_30.json',{'status':'FAIL'})
    from pause_v3 import VETO_END
    assert not launch_timing(tmp_path,phase='pilot',now=VETO_END+1,veto_not_issued=True)['released']
    write_new(tmp_path.parent/'autoresume_paused.json',{'trajectories':{'A_1302':{'pid':123}}})
    assert launch_timing(tmp_path,phase='pilot',now=VETO_END+1,veto_not_issued=True)['released']


def test_actual_inherited_policy_migrates_without_editing_source():
    from pilot_configuration import derive,validate
    p=Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical_preparation/policy_prepared.json')
    source=json.loads(p.read_text());before=copy.deepcopy(source)
    new=derive(source,contexts());assert source==before
    assert new['generation']['max_new_tokens']==12288
    new['max_total_sequence_length']=15945
    with pytest.raises(ValueError):validate(new,contexts())


def test_tldr_json_receipts_remain_valid_when_only_summary(tmp_path):
    path=tmp_path/'receipt.json'
    write_new(path,{'tldr':'Summary only.'})
    assert json.loads(path.read_text())=={'tldr':'Summary only.'}
    assert path.read_text().startswith('{"tldr":')

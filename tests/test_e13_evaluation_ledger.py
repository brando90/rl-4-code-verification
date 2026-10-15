"""Keep every declared evaluation cell while recovering only typed, identical infrastructure attempts."""
from pathlib import Path
import hashlib,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));sys.path.insert(0,str(Path(__file__).parent))
import evaluation_ledger as m
from evaluation_contract import identities


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path


def manifest():
    ids=[f'authored_{i:03d}' for i in range(135)]
    cells=identities(ids,'validation',arm='A',run_seed=13011,boundary=1)
    for cell in cells:cell.update(prompt_text='authored',chat_text_sha256=hashlib.sha256(b'authored').hexdigest(),prompt_token_ids=[1,2],required_paths=['solution.lean'])
    return {'condition':'v2-S2','purpose':'validation','arm':'A','run_seed':13011,'boundary':1,'cells':cells},ids


def segment(root,manifest,number,indexes,completed,*,status='INCOMPLETE_INFRA',error='BrokenPipeError',closed=True):
    key=f'validation_b1_s{number:03d}';folder=root/key
    config={'indexes':indexes,'stage_key':key,'snapshot_sha256':'snapshot'}
    cp=put(folder/'runtime.json',config)
    put(root/(key+'.json'),{'stage_key':key,'stage':'evaluation_generate','indexes':indexes,'snapshot_sha256':'snapshot',
        'configuration_sha256':m.digest(cp),'lease_id':key})
    if closed:
        put(folder/'dispatch/result.json',{'snapshot_sha256':'snapshot','stage_key':key,'lease_id':key,
            'status':status,'cleanup_verified':True,'worker_exit_code':1,'error_type':error})
        put(folder/'output/error.json',{'error_type':error})
    for index in completed:
        row={**manifest['cells'][index],'condition':'v2-S2','output_token_ids':[3,4],
            'completion':'authored','finish_reason':'stop','at_token_cap':False,'generated_tokens':2,'prompt_tokens':2}
        put(folder/'output'/f'{index:05d}.generation.json',row)
    return folder


def test_transient_recovery_preserves_valid_neighbors_and_counts_every_slot(tmp_path):
    value,ids=manifest();segment(tmp_path,value,0,[0,1],[0])
    state=m.scan(tmp_path,value,ids,'snapshot')
    assert state['completed']==1 and state['missing']==1079 and state['pending_indexes'][0]==1
    segment(tmp_path,value,1,[1],[1],status='RUNTIME_EXITED_ZERO')
    state=m.scan(tmp_path,value,ids,'snapshot')
    assert state['completed']==2 and state['identical_retries']==1 and state['attempts'][:2]==[1,2]
    assert state['known_generated_tokens']==4 and state['tokens_in_missing_responses_unknown']
    assert state['missing_cost_receipts']==['validation_b1_s000','validation_b1_s001']


def test_second_transient_failure_exhausts_only_its_identical_cell(tmp_path):
    value,ids=manifest();segment(tmp_path,value,0,[0],[]);segment(tmp_path,value,1,[0],[])
    state=m.scan(tmp_path,value,ids,'snapshot')
    assert state['attempts'][0]==2 and 0 not in state['pending_indexes'] and state['pending_indexes'][0]==1
    segment(tmp_path,value,2,[0],[])
    with pytest.raises(ValueError,match='scheduled again'):m.scan(tmp_path,value,ids,'snapshot')


def test_timeout_is_not_reclassified_as_a_retryable_kill(tmp_path):
    value,ids=manifest();folder=segment(tmp_path,value,0,[0],[],error='TimeoutError')
    path=folder/'dispatch/result.json';closed=json.loads(path.read_text());closed['worker_exit_code']=-9;put(path,closed)
    state=m.scan(tmp_path,value,ids,'snapshot')
    assert 0 not in state['pending_indexes'] and state['attempts'][0]==1


def test_unclosed_stage_demands_reconciliation_without_launching_a_duplicate(tmp_path):
    value,ids=manifest();segment(tmp_path,value,0,[0],[],closed=False)
    state=m.scan(tmp_path,value,ids,'snapshot')
    assert state['status']=='RECOVERY_REQUIRED' and state['unfinished_stage']=='validation_b1_s000'


def test_completed_output_is_never_generated_again_and_success_must_be_complete(tmp_path):
    value,ids=manifest();segment(tmp_path,value,0,[0],[0],status='RUNTIME_EXITED_ZERO')
    segment(tmp_path,value,1,[0],[0],status='RUNTIME_EXITED_ZERO')
    with pytest.raises(ValueError,match='scheduled again'):m.scan(tmp_path,value,ids,'snapshot')
    other=tmp_path/'other';segment(other,value,0,[0],[],status='RUNTIME_EXITED_ZERO')
    with pytest.raises(ValueError,match='lacks declared responses'):m.scan(other,value,ids,'snapshot')

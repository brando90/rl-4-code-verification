"""Require physical independent audit evidence while preserving every reward-increasing mutation and missing cell."""
from pathlib import Path
import json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));sys.path.insert(0,str(Path(__file__).parent))
import audit_report as m
from audit_inputs import VARIANTS


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return {'path':str(path),'sha256':m.digest(path)}


def fixture(tmp_path):
    cells=[];rows=[];formal=[]
    for index in range(32):
        for variant in VARIANTS:
            directory=tmp_path/str(index)/variant;source=put(directory/'solution.lean',{'authored':True})
            cell={'cell_id':f'{index}/{variant}','audit_id':str(index),'task_id':f'authored_{index}','group_id':str(index),
                'split':'train','variant':variant,'source':source};cells.append(cell)
            parts={'status':'measured','source_sha256':source['sha256'],'compile':True,'strict':0,
                'e':1,'n_examples':1,'raw_vacuity_hits':[],'d':{'numerator':1,'denominator':2},'t':1,'p':{'numerator':1,'denominator':2}}
            if variant=='padding':parts.update(d={'numerator':9,'denominator':10},p={'numerator':9,'denominator':10})
            strict=put(directory/'strict.json',parts);hidden=put(directory/'hidden.json',{'status':'measured','fully_applicable':True,'hidden_pass_rate':.5})
            rows.append({**cell,'strict_status':'measured','strict':0,'compile':True,'components':parts,'strict_receipt':strict,
                'hidden_status':'measured','hidden_test_coverage':.5,'hidden_receipt':hidden,'cleanup_verified':True})
            formal.append({**cell,'compile':True,'formal_specification_coverage':.5 if variant=='original' else .4})
    inputs={'condition':'v2-S2','declared_tasks':32,'cells':cells}
    cpu={'stage':'TRAIN_AUDIT_CPU','condition':'v2-S2','status':'ACCOUNTED','declared':128,'accounted':128,'rows':rows,'cleanup_unresolved':0}
    hosted={'stage':'TRAIN_AUDIT_HOSTED','condition':'v2-S2','declared':128,'rows':formal,'declared_ratings':768,
            'actual_bundle_verified':True,'requested_identity_verified':True}
    controls={k:{'status':'PASS','condition':'v2-S2'} for k in ('hidden','formal')}
    cleanup={'registered_processes_exited':True,'port_free':True,'owned_remote_entries_removed':[{'operation':k,'exit_code':0} for k in ('service','auth_secret')]}
    return inputs,cpu,hosted,controls,cleanup


def test_full_audit_preserves_all_reward_increases_and_verifies_independent_routes(tmp_path):
    inputs,cpu,hosted,controls,cleanup=fixture(tmp_path);train=[f'authored_{i}' for i in range(32)]
    value=m.assemble(inputs,cpu,hosted,controls,cleanup,train=train,C_weights={t:[1/3]*3 for t in train})
    assert value['independent_checks_functioning'] and not value['learning_admitted']
    assert value['accounted']==128 and value['accounted_mutation_comparisons']==96 and len(value['reward_increasing_mutations'])==64


def test_claimed_hidden_score_must_match_its_actual_independent_receipt(tmp_path):
    args=fixture(tmp_path);args[1]['rows'][0]['hidden_test_coverage']=1
    with pytest.raises(ValueError,match='hidden score differs'):m.assemble(*args,train=[f'authored_{i}' for i in range(32)])


def test_fully_unavailable_hidden_route_does_not_admit_learning(tmp_path):
    args=fixture(tmp_path)
    for row in args[1]['rows']:
        row['hidden_test_coverage']=None;row['hidden_status']='not_applicable'
        row['hidden_receipt']=put(Path(row['hidden_receipt']['path']),{'status':'not_applicable','fully_applicable':False,'hidden_pass_rate':None})
    value=m.assemble(*args,train=[f'authored_{i}' for i in range(32)])
    assert value['independent_coverage_known']['hidden']==0 and not value['independent_checks_functioning']
    assert value['by_variant']['original']['hidden_test_coverage']['missing']==32


def test_unresolved_hosted_cleanup_cannot_be_called_functioning(tmp_path):
    args=fixture(tmp_path);args[4]['port_free']=False
    value=m.assemble(*args,train=[f'authored_{i}' for i in range(32)])
    assert value['status']=='CLEANUP_REQUIRED' and not value['independent_checks_functioning']


def test_wrong_hosted_compile_gate_is_not_treated_as_independent_evidence(tmp_path):
    args=fixture(tmp_path);args[2]['rows'][0]['compile']=False
    with pytest.raises(ValueError,match='compile gate differs'):m.assemble(*args,train=[f'authored_{i}' for i in range(32)])


def test_zero_rating_pack_requires_explicit_no_service_receipt():
    assert m.cleanup_verified({'declared_ratings':0},{'status':'NO_SERVICE_REQUIRED','model_calls':0})
    assert not m.cleanup_verified({'declared_ratings':0},{})

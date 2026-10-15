"""Freeze the final A-pilot feasibility decision and token budget without reopening a completed gate."""
from pathlib import Path
import importlib.util,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_t5_driver',PHASE/'t5_driver.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return {'path':str(path),'sha256':m.digest(path)}


def fixture(tmp_path,monkeypatch,horizon=30):
    monkeypatch.setattr(m,'HERE',PHASE)
    states={str(seed):put(tmp_path/f'{seed}.json',{'condition':'v2-S2','arm':'A','run_seed':seed,'phase':'pilot',
        'status':'WAIT_FOR_T5','completed_updates':horizon,'execution_sha256':'pilot'}) for seed in (1301,1302)}
    inputs=put(tmp_path/'inputs.json',{'states':states,'updates':[]})
    pilot={'gate':'LEARNING_PILOT','condition':'v2-S2','status':'FROZEN','LP_sha256':'lp',
        'bindings':[{'path':str(p),'sha256':m.digest(p)} for p in (Path(m.__file__).resolve(),PHASE/'technical_measurements.py',PHASE/'schedule.py')]}
    lock={'gate':'T5_INPUTS','condition':'v2-S2','status':'FROZEN','pilot_execution_lock':{'name':'pilot','sha256':'pilot'},
        'configuration':{'root':str(tmp_path/'result'),'horizon':horizon,'inputs':inputs},'bindings':[inputs,*states.values()]}
    values={'lock':lock,'pilot':pilot,'prior':{'gate':'T5','status':'EXTEND_TO_60','horizon':30,'pilot_execution_sha256':'pilot'}}
    if horizon==60:lock['extension_admission']={'name':'prior'}
    monkeypatch.setattr(m,'published',lambda ref,_:values[ref['name']])
    rows=[{'arm':'A','seed':seed,'update':i,'split':'train','declared':256,'measured':256,
           'strict_successes':8 if i>horizon-10 else 0} for seed in (1301,1302) for i in range(1,horizon+1)]
    monkeypatch.setattr(m,'validate_updates',lambda *_:(rows,[2048]*(horizon*2*256)))
    return {'repository':'authored','lock':{'name':'lock','sha256':'inputs-lock'}},values


def test_t5_is_final_and_uses_all_fixed_slots_for_the_protocol_token_budget(tmp_path,monkeypatch):
    plan,values=fixture(tmp_path,monkeypatch)
    result=m.run(plan)
    assert result['status']=='PASS' and result['pilot_slots']==15360
    assert result['token_budget']['T']==25600*2048 and result['token_budget']['pilot_slots']==15360
    assert result['pilot_execution_sha256']=='pilot'
    monkeypatch.setattr(m,'t5',lambda *a,**kw:pytest.fail('gate recomputed'))
    with pytest.raises(FileExistsError):m.run(plan)


def test_second_horizon_requires_the_published_extension_decision(tmp_path,monkeypatch):
    plan,values=fixture(tmp_path,monkeypatch,60);values['prior']['status']='FAIL'
    with pytest.raises(ValueError,match='extension was not admitted'):m.run(plan)
    assert not (tmp_path/'result/evaluation_attempt.json').exists()


def test_prelearning_method_and_paused_states_are_bound(tmp_path,monkeypatch):
    plan,values=fixture(tmp_path,monkeypatch);values['pilot']['bindings'][0]['sha256']='changed'
    with pytest.raises(ValueError,match='before learning'):m.run(plan)
    assert not (tmp_path/'result').exists()


def test_missing_opportunity_is_rejected_before_any_gate_statistic():
    with pytest.raises(ValueError,match='complete fixed A pilot'):m.validate_updates([],30)


def test_every_fixed_response_is_joined_to_its_score_and_clean_device_stages(monkeypatch):
    monkeypatch.setattr(m,'read',lambda reference:reference['value'])
    entries=[]
    for seed in (1301,1302):
        for update in range(1,31):
            cells=[];files=[]
            for index in range(256):
                identity={'cell_id':f'{seed}/{update}/{index}','task_id':f'authored_{index//8}',
                    'sample':index%8,'group_index':index//8,'split':'train','arm':'A','run_seed':seed,'update':update}
                cells.append({**identity,'status':'measured','strict':0,'cleanup_verified':True})
                files.append({'value':{**identity,'output_token_ids':[1,2]}})
            scoring={'value':{'rows':cells}}
            entry={'seed':seed,'update':update,'scoring':scoring,'generation_files':files,
                'summary':{'value':{'arm':'A','seed':seed,'update':update,'split':'train','declared':256,
                    'status':'ACCOUNTED','measured':256,'strict_successes':0,'generated_tokens':512,'scoring':scoring}},
                'generation':{'value':{'status':'COMPLETE','completed':256,'generated_tokens':512}},
                'opportunity':{'value':{'status':'ACCOUNTED','arm':'A','run_seed':seed,'update':update,'optimizer_updates':1}},
                'closed_stages':{stage:{'value':{'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True,
                    'arm':'A','run_seed':seed,'update':update}} for stage in ('generate','update','export')}}
            entries.append(entry)
    rows,lengths=m.validate_updates(entries,30)
    assert len(rows)==60 and len(lengths)==15360 and sum(lengths)==30720
    entries[-1]['closed_stages']['export']['value']['cleanup_verified']=False
    with pytest.raises(ValueError,match='not cleanly closed'):m.validate_updates(entries,30)
    entries[-1]['closed_stages']['export']['value']['cleanup_verified']=True
    entries[0]['generation_files'][0]['value']['sample']=7
    with pytest.raises(ValueError,match='identity differ'):m.validate_updates(entries,30)

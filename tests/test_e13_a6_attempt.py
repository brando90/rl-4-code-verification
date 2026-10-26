"""Keep A6 infrastructure successors within three attempts and reject any measured predecessor."""
import copy,json,sys
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
from a6_attempt import check_predecessors,digest


def fixture(tmp_path):
    root=tmp_path/'first';root.mkdir()
    result=root/'result.json';result.write_text(json.dumps({'status':'INCOMPLETE','cleanup_verified':True,'released':{'status':'RELEASED'}}))
    return {'configuration':{'root':str(tmp_path/'second'),'scoring':{'root':str(tmp_path/'scoring')}},
        'infrastructure_attempt':{'number':2,'maximum_attempts':3,'cumulative_device_hours':2.,
            'previous':[{'number':1,'root':str(root),'evidence':{'result.json':digest(result)}}]}}


def test_clean_infrastructure_failure_can_have_successor(tmp_path):
    check_predecessors(fixture(tmp_path))


def test_any_response_or_scoring_prevents_successor(tmp_path):
    lock=fixture(tmp_path);root=Path(lock['infrastructure_attempt']['previous'][0]['root'])
    response=root/'00000.generation.json';response.write_text('{}')
    with pytest.raises(ValueError,match='generated'):check_predecessors(lock)
    response.unlink();Path(lock['configuration']['scoring']['root']).mkdir()
    with pytest.raises(ValueError,match='scoring'):check_predecessors(lock)


def test_attempt_cap_changed_budget_and_changed_receipt_rejected(tmp_path):
    lock=fixture(tmp_path)
    for key,value in [('number',4),('maximum_attempts',4),('cumulative_device_hours',2.1)]:
        changed=copy.deepcopy(lock);changed['infrastructure_attempt'][key]=value
        with pytest.raises(ValueError):check_predecessors(changed)
    Path(lock['infrastructure_attempt']['previous'][0]['root'],'result.json').write_text('{}')
    with pytest.raises(ValueError,match='evidence changed'):check_predecessors(lock)

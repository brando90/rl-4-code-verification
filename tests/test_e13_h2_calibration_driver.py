"""Exercise independent forecast bounds, publication fences and immutable calibration execution."""
from pathlib import Path
import sys,json,itertools
import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(HERE))
import h2


def panel(labels):
    tasks=[f'fixture_h2_{i}' for i in range(len(labels))];rows=[]
    for task,label in zip(tasks,labels):
        for s in range(8):
            rows.append({'task_id':task,'sample_idx':s,'split':'train','batch':'full2','policy':'sft_4B_f1p0',
                'cell_id':f'full2/{task}/{s}','status':'unresolved_measurement' if label is None else 'measured',
                'strict':int(label==1 and s==0)})
    return rows,tasks


def test_partial_groups_can_be_known_mixed_but_never_assumed_constant():
    rows,tasks=panel([0,1,None]);rows[0]['status']='unresolved_measurement'
    rows[10]['status']='unresolved_measurement'
    labels,counts=h2.mixed_labels(rows,tasks)
    np.testing.assert_array_equal(labels,[np.nan,1,np.nan])
    assert counts['measured_responses']==14 and counts['declared_responses']==24
    assert counts['identified_mixed_labels']==1


@pytest.mark.parametrize('defect',['test','duplicate','missing','identity','cleanup'])
def test_h2_rejects_changed_manifest_or_integrity_defect(defect):
    rows,tasks=panel([0,1])
    if defect=='test':rows[0]['split']='test'
    if defect=='duplicate':rows.append(rows[0])
    if defect=='missing':rows.pop()
    if defect=='identity':rows[0]['cell_id']='wrong'
    if defect=='cleanup':rows[0]['status']='unresolved_cleanup'
    with pytest.raises(ValueError):h2.mixed_labels(rows,tasks)


def test_h2_complete_pass_fail_and_one_class_inconclusive():
    rows,tasks=panel([0,0,1,1]);p=np.array([.1,.2,.8,.9])
    result=h2.evaluate(rows,tasks,p,tasks,forecast_admitted=True,draws=100)
    assert result['status']=='PASS' and result['auc']['minimum']==result['auc']['maximum']==1
    assert result['auc']['bootstrap_bounds_exact'] and result['counts']['declared_responses']==32
    assert result['diagnostics']['mean_bias']['minimum']==pytest.approx(0)
    assert result['F2_observed_minus_forecast_bounds']==[.25,.25]
    assert h2.evaluate(rows,tasks,1-p,tasks,forecast_admitted=True,draws=100)['status']=='FAIL'
    assert h2.evaluate(rows,tasks,p,tasks,forecast_admitted=False,draws=100)['status']=='INCONCLUSIVE'
    rows,tasks=panel([0,0,0,0])
    assert h2.evaluate(rows,tasks,p,tasks,forecast_admitted=True,draws=100)['status']=='INCONCLUSIVE'


def test_h2_missing_auc_bounds_equal_exhaustive_completions():
    rows,tasks=panel([0,None,1,None]);p=[.1,.3,.6,.9]
    result=h2.evaluate(rows,tasks,p,tasks,forecast_admitted=True,draws=100)
    aucs=[]
    for a,b in itertools.product((0,1),repeat=2):
        complete,_=panel([0,a,1,b]);r=h2.evaluate(complete,tasks,p,tasks,forecast_admitted=True,draws=10)
        aucs.append(r['auc']['minimum'])
    assert result['auc']['minimum']==min(aucs) and result['auc']['maximum']==max(aucs)
    assert result['status']=='INCONCLUSIVE' and result['counts']['unknown_mixed_labels']==2
    assert not result['auc']['bootstrap_bounds_exact']


def test_no_fit_or_substitute_when_strict_forecast_unavailable():
    rows,tasks=panel([0,1])
    result=h2.evaluate(rows,tasks,None,tasks,forecast_admitted=False)
    assert result['status']=='INCONCLUSIVE' and 'auc' not in result


def test_h2_publication_failure_precedes_data_access(tmp_path,monkeypatch):
    plan=tmp_path/'plan.json';plan.write_text('{}')
    def reject(_):raise ValueError('unpublished H2 inputs')
    monkeypatch.setattr(h2,'verify',reject)
    monkeypatch.setattr(h2,'evaluate',lambda *a,**k:pytest.fail('evaluation before publication'))
    with pytest.raises(ValueError,match='unpublished'):h2.run(plan)
    assert sorted(p.name for p in tmp_path.iterdir())==['plan.json']


def test_successful_calibration_freezes_f2_and_items_before_batch2(tmp_path,monkeypatch):
    import calibration
    from test_e13_calibration_inputs_controls import rows
    from calibration_inputs import anchor_arrays
    from rl4cv.forecast import verify_forecast
    data,tasks=rows();arrays=anchor_arrays(data,tasks);arrays['groups']=tasks
    root=tmp_path/'run';binding=tmp_path/'binding.json';binding.write_text('{}')
    plan=tmp_path/'plan.json';plan.write_text(json.dumps({'root':str(root),'method_lock':str(binding),
        'input_lock':str(binding),'method_revision':'fixture'}))
    monkeypatch.setattr(calibration,'verify',lambda _:({'g1_lock':str(binding),'B_reward_source':'fixture'},{}))
    monkeypatch.setattr(calibration,'load_arrays',lambda _:arrays)
    monkeypatch.setattr(calibration,'placebo',lambda *a:{'values':[0.],'measured':1,'declared':40})
    monkeypatch.setattr(calibration,'fit_marginals',lambda *a:({},dict(d={'admitted':False}),{'status':'FAIL'}))
    monkeypatch.setattr(calibration,'fit_strict_forecast',lambda *a:{'probabilities':np.full(5,.25),'admitted':False})
    monkeypatch.setattr(calibration,'reward_variance',lambda *a:{'status':'INCONCLUSIVE'})
    result=calibration.run(plan)
    assert result['status']=='FROZEN' and not result['C_calibration_admitted']
    assert result['placebo_measured']==1 and result['placebo_declared']==40
    assert verify_forecast(root/'forecast/F2_S2.json')
    f2=json.loads((root/'forecast/F2_S2.json').read_text())
    assert f2['prediction']==.75 and 'full2 not generated or scored' in f2['observed_information']
    prediction=json.loads((root/'H2_predictions.json').read_text())
    np.testing.assert_allclose(prediction['mixed_group_probability'],1-.25**8-.75**8)
    assert any(b['path'].endswith('item_parameters.json') for b in result['artifacts'])
    with pytest.raises(FileExistsError):calibration.run(plan)

"""Verify missing-cell isolation and actual-pattern controls before any real fit."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0, str(ROOT))


def load(name):
    spec = importlib.util.spec_from_file_location('test_e13_'+name, ROOT/(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_finite_gradient_and_likelihood_invariance_controls():
    result = load('fit_controls').numerical_controls()
    assert result['status'] == 'PASS'
    assert len(set(result['fixed_initializations'])) == 5


def test_actual_missingness_and_risk_sets_reach_recovery_unchanged(monkeypatch):
    m = load('fit_controls'); patterns = []
    monkeypatch.setattr(m, 'recover_pattern', lambda n: patterns.append(n.copy()) or {'status': 'PASS'})
    h = {'strict': [0, 0, 1, np.nan], 'q1': [0, 1, 1, np.nan],
         'compile': [0, 0, 1, np.nan], 'honest': [0, 0, 1, np.nan],
         'observed': [True, True, True, False], 'policy_index': [0,0,1,2], 'item_index': [0,1,1,2]}
    result = m.pattern_controls(h, (3,3))
    assert result['status'] == 'PASS' and result['missing_cells'] == 1
    assert [int(n.sum()) for n in patterns] == [3,3,2,1]
    assert all(n[2,2] == 0 for n in patterns)
    h['observed'][-1] = True
    with pytest.raises(ValueError, match='unmeasured'):
        m.pattern_controls(h, (3,3))


def test_failed_pattern_controls_block_admission(monkeypatch):
    m = load('fit_controls')
    monkeypatch.setattr(m, 'pattern_controls', lambda *args: {'status': 'FAIL'})
    monkeypatch.setattr(m, 'forecast_panel', lambda **kw: ({'M3': np.array([.5])}, {'M3': {'admitted': True}}))
    _, receipt = m.validated_forecast(history={}, policy_metadata=[1,2,3], item_features=[1,2,3])
    assert not receipt['M3']['admitted']


def test_unavailable_reward_predictor_does_not_suppress_strict_model(monkeypatch):
    m=load('forecast_a3');calls=[]
    def fitted(y,n,metadata,features,target_metadata,target_features,target_item_indices,prior_scale=1.):
        calls.append((y.copy(),n.copy()))
        return np.full((1,2),.4),{'admitted':True,'starts':[]}
    monkeypatch.setattr(m,'_fit_predict',fitted)
    h={'policy_index':[0,1,2,0,1,2],'item_index':[0,0,0,1,1,1],
       'strict':[0,1,0,1,0,1],'observed':[True]*6,'q1':[1]*6,'compile':[1]*6,'honest':[0,1,0,1,0,1]}
    predictions,receipts=m.forecast_a3(history=h,policy_metadata=np.zeros((3,2)),item_features=np.zeros((2,0)),
        target_metadata=np.zeros((1,2)),target_features=np.zeros((2,0)),target_item_indices=[0,1],
        earlier_successes=np.zeros((1,2)),earlier_trials=np.zeros((1,2)),earlier_reward=np.array([[np.nan,.5]]),
        calibration_x=[0.,1.],calibration_y=[0.,1.],calibration_trials=[1,1])
    assert predictions['M1'] is None and not receipts['M1']['admitted']
    assert np.all(predictions['M2']==.4) and receipts['M2']['admitted']
    assert len(calls)==21


def test_missing_labels_never_enter_fit_or_inner_selection(monkeypatch):
    m = load('nested_a3'); traces = []; evaluation_labels = []; frozen = []
    systems = [{'label': f'{size}-{f}', 'size': f'{size}B', 'fraction': f,
                'cumulative_assistant_tokens': int(f*100)}
               for size in (1.7,4,8) for f in (.25,.5,.75,1.)]
    tasks = [f't{i}' for i in range(100)]
    rows = [{'policy': s['label'], 'task_id': t, 'sample_idx': i, 'split': 'validation',
             'strict_status': 'scored', 'strict': i%2, 'q1': 1, 'compile': 1,
             'honest': i%2, 'factored_reward': .25+.75*(i%2)}
            for s in systems for t in tasks for i in range(8)]
    excluded = {f"{s['label']}/t0/0" for s in systems}
    for r in rows:
        if f"{r['policy']}/{r['task_id']}/{r['sample_idx']}" in excluded:
            for field in ('strict','q1','compile','honest','factored_reward'): r[field] = 'poison'
    def predict(**kw):
        h = kw['history']; observed = np.asarray(h['observed'])
        assert np.isfinite(np.asarray(h['strict'])[observed]).all()
        assert np.isnan(np.asarray(h['strict'])[~observed]).all()
        assert np.isfinite(kw['earlier_reward']).all()
        assert max(kw['policy_metadata'][:,1]) < np.log1p(100)
        traces.append(int((~observed).sum()))
        shape = (len(kw['target_metadata']), len(kw['target_features']))
        return {k: np.full(shape,.5) for k in ('M0','M1','M2','M3','M3e')}, {k: {'admitted': True} for k in ('M2','M3','M3e')}
    def selection(predictions, y, groups):
        assert np.isfinite(y).all() and len(y) == len(groups)
        assert all(len(p) == len(y) for p in predictions.values())
        return 'M3', {'M3': .7, 'M3e': .7}
    def assess(y, *args, **kwargs):
        assert len(frozen)==len(evaluation_labels)+1
        assert len(frozen[-1]['cell_ids'])==len(y)
        evaluation_labels.append(y); return {'status': 'INCONCLUSIVE'}
    monkeypatch.setattr(m, 'validated_forecast', predict)
    monkeypatch.setattr(m, 'select_candidate', selection)
    monkeypatch.setattr(m, 'assess_g1_a3', assess)
    m.run_forecast(rows, systems, {t:[1.,2.] for t in tasks}, {t:t for t in tasks}, excluded_ids=excluded,
                   draws=1,forecast_sink=frozen.append)
    assert sum(traces) > 0
    assert all(np.isnan(y).sum() == 3 for y in evaluation_labels)
    assert len(evaluation_labels) == 2
    assert all(len(f['inner_folds'])==3 for x in frozen for f in x['folds'])

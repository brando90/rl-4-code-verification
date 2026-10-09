"""Check the statistical estimands on small synthetic data, without reading experiment outcomes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import numpy as np
from analyze_e12 import auc,agreement,pooled_stats,interval,scsc,p1


def test_auc_ties_and_degenerate_labels():
    assert auc([.1,.2,.3,.4],[0,0,1,1])==1
    assert auc([1,1,1,1],[0,0,1,1])==.5
    assert np.isnan(auc([1,2],[1,1]))


def test_absolute_agreement_detects_constant_offset():
    r=agreement(np.array([.2,.4,.6]),np.array([.1,.3,.5]))
    assert np.isclose(r['spearman'],1) and np.isclose(r['pearson'],1)
    assert np.isclose(r['bias_score_minus_hidden'],.1)
    assert np.isclose(r['mean_absolute_difference'],.1)


def test_missing_fsc_stays_missing_unless_product_zero():
    assert scsc({'IC_tests':.5,'IC_proofs':.5,'FSC':None}) is None
    assert scsc({'IC_tests':0,'IC_proofs':.5,'FSC':None})==0
    assert scsc({'IC_tests':None,'IC_proofs':0,'FSC':1}) is None


def test_within_system_ranks_remove_system_score_scale():
    rows=[]
    for system,xs in [('a',[.01,.02,.03]),('b',[.7,.8,.9])]:
        for i,x in enumerate(xs):
            rows.append({'system':system,'IC_tests':x,'IC_proofs':x,'FSC':x,'hidden_all_pass':int(i>0),'hidden_pass_rate':i/2})
    r=pooled_stats(rows)
    assert r['auc']==1 and np.isclose(r['spearman_within_system'],1)
    assert r['n_cells']==6 and r['n_pass']==4


def test_interval_retains_undefined_draw_denominator():
    r=interval([0,1,None,float('nan')])
    assert r['n_defined']==2 and r['n_requested']==4


def test_p1_uses_common_factor_cells_and_excludes_hidden_missing_only_from_hidden_mean():
    rows=[]
    for i,system in enumerate(['a','b','c']):
        for j in range(3):
            x=(i+1)/4
            rows.append({'system':system,'task_id':str(j),'subset':'Core614','source_status':'measured',
                         'IC_tests':x,'IC_proofs':x,'FSC':x,'hidden_all_pass':None if j==2 else i/2,
                         'hidden_pass_rate':None if j==2 else i/2,'status':'not_applicable' if j==2 else 'evaluated'})
    result=p1(rows,np.random.default_rng(1),draws=5)
    assert np.isclose(result['spearman'],1)
    assert all(r['n_factor']==3 and r['n_hidden']==2 for r in result['per_system'])

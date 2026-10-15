"""Preserve current/boundary/incomplete tensors while retiring only obsolete authored checkpoint files."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_checkpoint_retention',PHASE/'checkpoint_retention.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def tensors(path,kind):
    path.mkdir(parents=True);(path/'tensor.bin').write_bytes(b'authored tiny tensors')
    receipt={'status':'COMPLETE','condition':'v2-S2','bindings':m.file_bindings(path)}
    name='receipt.json' if kind=='native' else 'export_receipt.json'
    (path/name).write_text(json.dumps(receipt));return path


def fixture(tmp_path):
    root=tmp_path/'run';root.mkdir()
    state={'phase':'main','arm':'B','run_seed':13011,'execution_sha256':'execution',
           'completed_updates':3,'model':str(root/'update_00003/export/output'),
           'checkpoint':str(root/'update_00003/update/output/after')}
    (root/'controller.lock').touch()
    (root/'admission.json').write_text(json.dumps({**state,'execution_lock_sha256':'execution'}))
    for i in range(1,5):
        update=root/f'update_{i:05d}'
        for relative,kind in [('update/output/before','native'),('update/output/after','native'),('export/output','export')]:
            tensors(update/relative,kind)
        (update/'raw_rollout.json').write_text('retained raw')
        for stage in ('generate','update','export'):
            dispatch=update/stage/'dispatch';dispatch.mkdir(parents=True)
            (dispatch/'result.json').write_text(json.dumps({'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True}))
        score=update/'score/cells';score.mkdir(parents=True)
        (score/'result.json').write_text(json.dumps({'rows':[{'cleanup_verified':True}]}))
        if i<4:(update/'opportunity.json').write_text(json.dumps({'condition':'v2-S2','status':'ACCOUNTED','update':i,
                                                             'state_after':state}))
    # Update 2 reuses the model from update 1 at a token boundary.
    (root/'update_00002/boundary.json').write_text(json.dumps({'model':str(root/'update_00001/export/output')}))
    return root,state


def test_later_boundary_reference_keeps_earlier_export_and_latest_incomplete_roots(tmp_path):
    root,state=fixture(tmp_path);result=m.candidates(root,state)
    paths={r['path'] for r in result['candidates']}
    assert str(root/'update_00001/export/output') not in paths
    assert str(root/'update_00002/export/output') in paths and len(paths)==5
    assert all('update_00003' not in p and 'update_00004' not in p for p in paths)


def test_removal_is_preceded_by_immutable_inventory_and_never_touches_raws(tmp_path):
    root,state=fixture(tmp_path);path=root/'retention/after_00003.json'
    result=m.retire(root,state,path,controller_fence=(root/'controller.lock').open('a'))
    assert result['status']=='COMPLETE' and len(result['removed'])==5
    assert json.loads(path.read_text())['status']=='PREPARED' and result['plan_sha256']==m.digest(path)
    assert (root/'update_00001/export/output/tensor.bin').exists()
    assert (root/'update_00003/update/output/after/tensor.bin').exists()
    assert (root/'update_00004/update/output/after/tensor.bin').exists()
    assert len(list(root.glob('update_*/raw_rollout.json')))==4
    with pytest.raises(FileExistsError):m.retire(root,state,path,controller_fence=(root/'controller.lock').open('a'))


def test_cross_run_and_changed_tensor_evidence_refuse_deletion(tmp_path):
    root,state=fixture(tmp_path);wrong={**state,'run_seed':13012}
    with pytest.raises(ValueError,match='identity'):m.candidates(root,wrong)
    (root/'update_00001/update/output/before/tensor.bin').write_bytes(b'changed')
    with pytest.raises(ValueError,match='file changed'):m.retire(root,state,root/'retention/attempt.json',controller_fence=(root/'controller.lock').open('a'))
    assert not (root/'retention/attempt.json').exists()


def test_unresolved_child_or_scorer_cleanup_preserves_all_tensors(tmp_path):
    root,state=fixture(tmp_path)
    dispatch=root/'update_00003/update/dispatch/result.json'
    dispatch.write_text(json.dumps({'status':'RUNTIME_EXITED_ZERO','cleanup_verified':False}))
    with pytest.raises(ValueError,match='child cleanup'):m.candidates(root,state)
    dispatch.write_text(json.dumps({'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True}))
    (root/'update_00001/score/cells/result.json').write_text(json.dumps({'rows':[{'cleanup_verified':False}]}))
    with pytest.raises(ValueError,match='scorer cleanup'):m.candidates(root,state)
    assert len(list(root.glob('update_*/update/output/*/tensor.bin')))==8

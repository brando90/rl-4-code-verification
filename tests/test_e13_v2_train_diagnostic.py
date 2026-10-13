"""Check train-only selection and R0 admission without opening any historical source."""
import csv
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2'


def selector():
    spec=importlib.util.spec_from_file_location('e13v2_train_selection_test', V2/'R1_attempt_1/r1_diagnostic_v2.py')
    module=importlib.util.module_from_spec(spec)
    before=list(sys.path)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:]=before
    return module


def test_unaccepted_r0_cannot_touch_sealed_metadata(tmp_path):
    (tmp_path/'R0_attempt_2').mkdir()
    (tmp_path/'R0_attempt_2/receipt.json').write_text('{"status":"FAIL"}')
    with pytest.raises(ValueError,match='R0 has not passed'):
        selector().prepare(root=tmp_path,split_path=tmp_path/'absent.csv',sealed_dir=tmp_path/'absent')
    assert not (tmp_path/'R1_attempt_1').exists()


def test_selection_excludes_test_and_validation_before_sampling(tmp_path,monkeypatch):
    module=selector()
    (tmp_path/'R0_attempt_2').mkdir()
    (tmp_path/'R0_attempt_2/receipt.json').write_text('{"status":"PASS"}')
    split_path=tmp_path/'split.csv'
    with split_path.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=['task_id','group_id','split']);writer.writeheader()
        writer.writerows({'task_id':f't{i}','group_id':f'g{i}','split':'train'} for i in range(539))
        writer.writerows({'task_id':x,'group_id':x,'split':x} for x in ['validation','test'])
    sealed=tmp_path/'sealed';sealed.mkdir()
    rows=[{'cell_id':f'm{m}/t{i}/{s}','task_id':f't{i}','group_id':f'g{i}','split':'train','source_path':'/nonexistent/train/source'}
          for i in range(539) for m in range(3) for s in range(8)]
    rows += [{'cell_id':x,'task_id':x,'group_id':x,'split':x,'source_path':'/never-open-heldout/source'} for x in ['test','validation']]
    (sealed/'sealed_manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (sealed/'sealed_results.jsonl').write_text(''.join(json.dumps({'cell_id':r['cell_id'],'status':'unmeasured' if i<9000 else 'measured','failure_class':'source_or_pinned_probe_rejected'})+'\n' for i,r in enumerate(rows)))
    real_digest=module.digest
    monkeypatch.setattr(module,'digest',lambda p: {'sealed_manifest.jsonl':'06fcbcda0d7406156f99754d69814a699fe4dbf29fee40e377fa190ccd03f1b6','sealed_results.jsonl':'8b5914819a098a749293494ee8db74ecbefca5c8ea0eebd493a6980a84edd85c'}.get(p.name) or real_digest(p))
    lock=module.prepare(root=tmp_path,split_path=split_path,sealed_dir=sealed)
    sample=json.loads((tmp_path/'R1_attempt_1/sample.json').read_text())
    allow=json.loads((tmp_path/'R1_attempt_1/train_allowlist.json').read_text())
    assert len(sample)==400 and len(allow)==12936
    assert all(r['split']=='train' and r['cell_id'] in allow for r in sample)
    assert not {'test','validation'} & set(allow)
    assert lock['sample_counts']=={'rejected':300,'measured':100}
    assert lock['population_counts']=={'rejected':9000,'measured':3936}


def test_selector_rejects_changed_sealed_manifest_before_source_access(tmp_path):
    module=selector()
    (tmp_path/'R0_attempt_2').mkdir();(tmp_path/'R0_attempt_2/receipt.json').write_text('{"status":"PASS"}')
    split_path=tmp_path/'split.csv'
    split_path.write_text('task_id,group_id,split\n'+''.join(f't{i},g{i},train\n' for i in range(539)))
    sealed=tmp_path/'sealed';sealed.mkdir();(sealed/'sealed_manifest.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='frozen base manifest mismatch'):
        module.prepare(root=tmp_path,split_path=split_path,sealed_dir=sealed)
    assert not (tmp_path/'R1_attempt_1').exists()

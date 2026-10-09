"""Verify bounded infrastructure retry classification and recovery of an interrupted outcome-log write."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from evaluate_e12 import infra_failure,recover_jsonl


def test_retry_only_signaled_infrastructure_failure():
    assert infra_failure({'compile':{'status':'error','returncode':-9}})
    assert infra_failure({'diagnostics':[{'compiler':{'status':'error','returncode':137}}]})
    assert not infra_failure({'compile':{'status':'error','returncode':1}})
    assert not infra_failure({'compile':{'status':'timeout','returncode':-9}})


def test_partial_tail_is_archived_and_committed_records_survive(tmp_path):
    path=tmp_path/'outcomes.jsonl';path.write_bytes(b'{"cell":1}\n{"cell":')
    assert recover_jsonl(path)==[{'cell':1}]
    assert path.read_bytes()==b'{"cell":1}\n'
    assert next(tmp_path.glob('*.partial_tail.*')).read_bytes()==b'{"cell":'
    with path.open('a') as stream:stream.write(json.dumps({'cell':2})+'\n')
    assert recover_jsonl(path)==[{'cell':1},{'cell':2}]

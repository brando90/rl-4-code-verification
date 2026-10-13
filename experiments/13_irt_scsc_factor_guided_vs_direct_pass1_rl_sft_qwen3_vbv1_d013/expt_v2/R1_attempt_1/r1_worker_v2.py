#!/usr/bin/env python3
"""Measure one locked train diagnostic through both complete paths and record process-tree memory."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import threading
import time

import psutil

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE.parent/'R0_attempt_2'))
sys.path.insert(0,str(HERE))
from declaration_adapter_v2 import inspect_source
from r1_diagnostic_v2 import observe_v1
import watchdog_e13v2 as watchdog


def cause(old):
    if old['result']['status']=='measured':return 'measured'
    errors=old['exceptions']
    text='\n'.join(e['message'] for e in errors)
    for fragment,label in [
        ('unparseable theorem type','vacuity_unparseable_type'),
        ('theorem counts inconsistent','vacuity_count_overflow'),
        ('malformed source','parser_parse_error'),('non-JSON','parser_non_json'),
        ('parser probe failed','parser_exit_failure'),('invalid command span','identity_invalid_span'),
        ('duplicate fully qualified','identity_duplicate'),('identities disagree','identity_kernel_disagreement'),
        ('compiled proof fraction disagrees','partial_credit_compiled_fraction'),
        ('source hash mismatch','integrity_source_hash'),('cannot load pinned module','module_loading')]:
        if fragment in text:return label
    return 'untyped_exception'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ordinal',type=int,required=True);a=ap.parse_args()
    wr=Path(os.environ['WR']);root=wr/'R1_attempt_1'
    rows=json.loads((root/'sample.json').read_text());row=rows[a.ordinal]
    allow=set(json.loads((root/'train_allowlist.json').read_text()))
    if row['split']!='train' or row['cell_id'] not in allow:raise ValueError('cell outside train allowlist')
    output=root/'cells'/f'{a.ordinal:04d}';output.mkdir(parents=True,exist_ok=False)
    with watchdog.locked(wr/'watchdog'):
        db=watchdog.database(wr/'watchdog');watchdog.register(db,'e13v2_a1','r1_cell',os.getpid());db.close()
    stop=threading.Event();peak=[0];samples=[0]
    process=psutil.Process()

    def monitor():
        while not stop.is_set():
            total=0
            for p in [process,*process.children(recursive=True)]:
                try:total+=p.memory_info().rss
                except psutil.Error:pass
            peak[0]=max(peak[0],total);samples[0]+=1
            stop.wait(.1)
    thread=threading.Thread(target=monitor,daemon=True);thread.start();start=time.monotonic()
    result={'cell_id':row['cell_id'],'original_category':row['original_category'],'status':'unresolved_measurement'}
    try:
        old=observe_v1(row,output=output/'v1',lake_dir=Path(os.environ['E13_LAKE_DIR']),scorer_root=Path(os.environ['E13_SCORER_ROOT']))
        result['v1_cause']=cause(old)
        result['v1_status']=old['result']['status']
        new=inspect_source(Path(row['source_path']),lake_dir=Path(os.environ['E13_LAKE_DIR']),
            scorer_root=Path(os.environ['E13_SCORER_ROOT']),evidence=output/'v2',
            expected_sha256=row['source_sha256'],family='base',known=True,truncated=row['truncated'])
        result.update(status='measured',v2=new,oracle_equal=new['strict']==row['old_kernel_binary'] and new['strict_status']=='scored')
    except subprocess.TimeoutExpired as exc:
        result.update(status='deterministic_resource_limit',exception=type(exc).__name__,message=str(exc))
    except MemoryError as exc:
        result.update(status='deterministic_resource_limit',exception=type(exc).__name__,message=str(exc))
    except Exception as exc:
        result.update(exception=type(exc).__name__,message=str(exc))
    finally:
        stop.set();thread.join()
        result.update(wall_seconds=time.monotonic()-start,peak_tree_rss_bytes=peak[0],
                      child_max_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024,
                      rss_samples=samples[0],sampling_seconds=.1)
        (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())

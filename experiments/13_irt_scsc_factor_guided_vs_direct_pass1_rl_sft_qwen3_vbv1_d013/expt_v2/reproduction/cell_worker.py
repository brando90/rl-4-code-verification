#!/usr/bin/env python3
"""Measure one source-bound R2 cell, retaining private evidence and all source-specific oracle readbacks."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import threading
import time
import traceback
import struct
import psutil

HERE=Path(__file__).resolve().parent;V2=HERE.parent
sys.path.insert(0,str(V2));sys.path.insert(0,str(V2/'R0_attempt_2'))
from declaration_adapter_v2 import inspect_source, sha256
from historical_oracle_v2 import load, E08
import watchdog_e13v2 as watchdog


def ladder_readback(source,old,known,root):
    """Reuse the exact compiled scorer record, but invoke the actual pinned ladder reader."""
    module=load('e13v2_r2_ladder_readback',E08/'analyze_ladder.py');module.WORK=root
    scores=root/'ladder/train/scored';scores.mkdir(parents=True)
    target=root/'ladder/train/jobs/fixture_g8_s0/fixture/verifier';target.mkdir(parents=True)
    (target/'solution.lean').symlink_to(source)
    row={**old['scored_response'],'task_id':'fixture','sample_idx':0,'status':'scored' if known else 'unmeasured'}
    (scores/'scored_fixture_g8.jsonl').write_text(json.dumps(row)+'\n')
    cells,_=module.cells_for({'source':'e08','label':'fixture'},['fixture'],'train')
    value=cells[('fixture',0)]
    return {'value':value['kernel_binary'],'status':'scored' if value['known'] else 'unmeasured'}


def family_reward(parts,strict):
    if strict==1:return 1.
    if not parts['e'] or not parts['n_examples'] or not parts['p']['denominator'] or parts['raw_vacuity_hits']:return 0.
    d=parts['d']['numerator']/parts['d']['denominator'] if parts['d']['denominator'] else 0.
    p=parts['p']['numerator']/parts['p']['denominator']
    return (max(.01,d)*max(.01,parts['t'])*max(.01,p))**(1/3)


def family_consistency(parts,strict,old):
    maximum=bool(parts['e'] and parts['t'] and parts['d']['denominator'] and parts['p']['denominator'] and
                 parts['d']['numerator']==parts['d']['denominator'] and parts['p']['numerator']==parts['p']['denominator'])
    if strict==1 and not maximum:return 'untyped_strict_success_component_deficit'
    if strict==0 and maximum:
        if parts['raw_vacuity_hits'] or old['vacuity']['unparseable']:return 'vacuity'
        if not old['kernel'].get('probe_ok',False):return 'kernel_probe_rejection'
        return 'untyped_maximum_components_strict_failure'
    return 'consistent'


def measure(row,evidence,route):
    if (row['split']=='test')!=(route=='opaque'):raise ValueError('sealed-route integrity defect')
    for path in [row['source_path'],*row['source_alias_paths']]:
        if sha256(path)!=row['source_sha256']:raise ValueError('source integrity defect')
    value=inspect_source(row['source_path'],lake_dir=Path(os.environ['E13_LAKE_DIR']),scorer_root=Path(os.environ['E13_SCORER_ROOT']),
                         evidence=evidence,expected_sha256=row['source_sha256'],family=row['family'],known=row['known'],truncated=row['truncated'])
    old=json.loads((evidence/'oracle/oracle.json').read_text());readbacks=[]
    for expectation in row['expectations']:
        actual={'value':value['strict'],'status':value['strict_status']} if expectation['family']==row['family'] else ladder_readback(Path(row['source_path']),old,expectation['status']=='scored',evidence/'alias_readback')
        readbacks.append({'policy':expectation['policy'],'family':expectation['family'],**actual,
                          'equal':actual['value']==expectation['value'] and actual['status']==expectation['status'],
                          'consistency':family_consistency(value,actual['value'],old),
                          'factored_reward':family_reward(value,actual['value'])})
    scored=old['scored_response'];raw_unparseable=bool(old['vacuity']['unparseable'])
    q1=bool(value['e'] and value['n_examples'] and value['p']['denominator'] and not value['raw_vacuity_hits'] and not raw_unparseable)
    honest=bool(scored['n_theorems_stated']>0 and scored['n_theorems_stated']==scored['n_theorems_proved'])
    return {'status':'measured','components':value,'readbacks':readbacks,'oracle_equal':all(r['equal'] for r in readbacks),
            'consistency':next((r['consistency'] for r in readbacks if r['consistency'].startswith('untyped')),value['consistency']),
            'q1':q1,'compile':old['compile'],'honest':honest}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--route',choices=['ordinary','opaque'],required=True);ap.add_argument('--ordinal',type=int,required=True);ap.add_argument('--attempt',type=int,required=True);args=ap.parse_args()
    root=Path(os.environ['WR'])/'R2';manifest=root/(args.route+'_manifest.jsonl')
    # Route-level coordinator verifies the complete manifest and implementation binding.
    with (root/(args.route+'_manifest.index')).open('rb') as index, manifest.open('rb') as handle:
        index.seek(args.ordinal*8);offset=struct.unpack('<Q',index.read(8))[0]
        handle.seek(offset);row=json.loads(handle.readline())
    if (row['split']=='test')!=(args.route=='opaque'):raise ValueError('source access denied by route')
    output=root/args.route/'cells'/f'{args.ordinal:05d}'/f'attempt_{args.attempt}';output.mkdir(parents=True,exist_ok=False)
    result={'cell_id':row['cell_id'],'ordinal':args.ordinal,'split':row['split'],'task_id':row['task_id'],
            'group_id':row['group_id'],'sample_idx':row['sample_idx'],'source_sha256':row['source_sha256'],'attempt':args.attempt}
    stop=threading.Event();peak=[0];proc=psutil.Process()
    def monitor():
        registered=set()
        while not stop.is_set():
            total=0
            for p in [proc,*proc.children(recursive=True)]:
                try:
                    total+=p.memory_info().rss
                    if p.pid!=proc.pid and p.pid not in registered:
                        with watchdog.locked(root.parent/'watchdog'):
                            db=watchdog.database(root.parent/'watchdog')
                            try:watchdog.register(db,'e13v2_a1','r2_descendant',p.pid);registered.add(p.pid)
                            except RuntimeError:pass
                            finally:db.close()
                except psutil.Error:pass
            peak[0]=max(peak[0],total);stop.wait(.25)
    thread=threading.Thread(target=monitor,daemon=True);thread.start();start=time.monotonic()
    try:result.update(measure(row,output/'evidence',args.route))
    except (subprocess.TimeoutExpired,MemoryError) as exc:
        result.update(status='deterministic_resource_limit',exception=type(exc).__name__)
        (output/'private_exception.txt').write_text(traceback.format_exc())
    except (OSError,UnicodeError,ValueError) as exc:
        result.update(status='integrity_defect',exception=type(exc).__name__)
        (output/'private_exception.txt').write_text(traceback.format_exc())
    except Exception as exc:
        result.update(status='unresolved_measurement',exception=type(exc).__name__)
        (output/'private_exception.txt').write_text(traceback.format_exc())
    finally:
        stop.set();thread.join();result.update(wall_seconds=time.monotonic()-start,peak_tree_rss_bytes=peak[0],child_max_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024)
        (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())

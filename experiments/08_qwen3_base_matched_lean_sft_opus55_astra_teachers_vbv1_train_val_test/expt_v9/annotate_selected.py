"""Regenerate comments only for changed selected proofs, preserving all unchanged version8 annotations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

import prefer_explicit as selection
from prefer_explicit import base

HERE=Path(__file__).resolve().parent
ROOT=selection.ROOT/'annotations'
base.ROOT=ROOT


def prepare():
    if (ROOT/'dispatch.json').exists():raise RuntimeError('annotation dispatch already frozen')
    rows=base.read_rows(selection.ROOT/'selection.jsonl')
    chosen=[r for r in rows if not r['baseline_annotation_issue'] and (r['changed'] or not (Path(r['baseline_comment_folder'])/'Solution.lean').exists())]
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/'manifest.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in chosen))
    batches=[chosen[i:i+64] for i in range(0,len(chosen),64)]
    schema=json.loads((selection.BASELINE/'workbook_annotations/schema.json').read_text())
    base.write(ROOT/'schema.json',schema)
    template=ROOT/'worker_template';template.mkdir()
    subprocess.run(['git','init','-q',str(template)],check=True)
    (template/'AGENTS.md').write_text('Explain the supplied selected proofs with accurate sketches and comments. Preserve all source bytes and return the requested JSON. The coordinator owns assembly and publication.\n')
    subprocess.run(['git','-C',str(template),'add','AGENTS.md'],check=True)
    subprocess.run(['git','-C',str(template),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize selected-proof annotation workers'],check=True)
    lanes=min(100,len(batches))
    config=(selection.RUN.parent/'rl4cv_tiny_curriculum/runtime/codex_profiles/natural_arithmetic/config.toml').read_text().replace('model_reasoning_effort = "high"','model_reasoning_effort = "medium"')
    for lane in range(lanes):
        work=ROOT/'workers'/f'lane_{lane:03d}'
        subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/f'lane_{lane:03d}';profile.mkdir(parents=True);(profile/'config.toml').write_text(config)
    for i,batch in enumerate(batches):
        folder=ROOT/'batches'/f'batch_{i:03d}'
        base.write(folder/'inputs.json',batch);base.write(folder/'status.json',dict(state='PENDING',declared=len(batch),attempts=0))
    base.write(ROOT/'dispatch.json',dict(rows=len(chosen),batches=len(batches),lanes=lanes,model=base.MODEL,effort=base.EFFORT,
        max_cli_attempts_per_batch=2,per_attempt_timeout_seconds=600,created_unix=time.time(),
        source_selection_sha256=base.sha((selection.ROOT/'selection.jsonl').read_bytes()),proof_change_by_annotator=False))
    print((ROOT/'dispatch.json').read_text(),flush=True)


def launch():
    dispatch=json.loads((ROOT/'dispatch.json').read_text());count=0
    for lane in range(dispatch['lanes']):
        name=f'codex-rl4cv-explicit-comments-{lane:03d}'
        if subprocess.run(['tmux','has-session','-t',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:continue
        command=f'python3 -u {HERE}/annotate_selected.py worker --lane {lane} >> {ROOT}/workers/lane_{lane:03d}/driver.log 2>&1'
        subprocess.run(['tmux','new-session','-d','-s',name,command],check=True);count+=1
    print(json.dumps(dict(launched=count)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','launch','worker','status']);parser.add_argument('--lane',type=int);args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='launch':launch()
    elif args.action=='worker':base.worker(args.lane)
    else:base.status()

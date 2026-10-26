"""Verify the frozen GX10 shard with native Lean, the identical inspector, and sixteen CPU slots."""
import os
from pathlib import Path
import bulk_verify as bulk

ENV=Path.home()/'workspace/rl4cv-gx10/lean-v4.22.0'
JOB=Path.home()/'workspace/rl4cv-gx10/verification-v10'

def main():
    import json,time
    while not (ENV/'setup_completion.json').exists():
        status=ENV/'setup_status.json'
        if status.exists() and json.loads(status.read_text()).get('state')=='FAILED':raise RuntimeError('Native environment setup failed; see setup log.')
        time.sleep(5)
    assert json.loads((ENV/'setup_completion.json').read_text())['state']=='DONE'
    lean=ENV/'lean-4.22.0-linux_aarch64/bin/lean'
    paths=[str(ENV/'mathlib4/.lake/build/lib/lean')]+[str(p) for p in (ENV/'mathlib4/.lake/packages').glob('*/.lake/build/lib/lean')]
    (JOB/'bin').mkdir(parents=True,exist_ok=True);(JOB/'grading').mkdir(exist_ok=True)
    wrapper=JOB/'bin/lake'
    wrapper.write_text('#!/usr/bin/python3\nimport os,sys\nassert sys.argv[1:3]==["env","lean"]\nenv=dict(os.environ,LEAN_PATH='+repr(':'.join(paths))+')\nos.execve('+repr(str(lean))+',['+repr(str(lean))+',"-j","1"]+sys.argv[3:],env)\n')
    wrapper.chmod(0o755)
    bulk.RUN=JOB;bulk.ROOT=JOB/'lean_corpus_v10';bulk.FROZEN=JOB/'frozen_kernel.py'
    bulk.run(16)

if __name__=='__main__':main()

"""Verify a small fixed public-source control set with the unchanged frozen Lean kernel inspector."""
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

FROZEN_SHA='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'
CONTROL_PATHS=('Mathlib/Data/Nat/Cast/WithTop.lean','Mathlib/Data/Int/Order/Lemmas.lean','Mathlib/Data/List/Prime.lean')


def sha(value):return hashlib.sha256(value).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--job-root',type=Path,required=True)
    p.add_argument('--mathlib-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    frozen=args.job_root/'frozen_kernel.py';assert sha(frozen.read_bytes())==FROZEN_SHA
    spec=importlib.util.spec_from_file_location('source_control_frozen_kernel',frozen)
    kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
    os.environ['PATH']=str(args.job_root/'bin')+':'+os.environ['PATH'];os.environ['CUDA_VISIBLE_DEVICES']=''
    rows=[]
    for relative in CONTROL_PATHS:
        source=(args.mathlib_root/relative).read_bytes();folder=args.output/Path(relative).stem;folder.mkdir(exist_ok=True)
        path=folder/'Solution.lean';path.write_bytes(source)
        report=asdict(kernel.check_file(str(path),str(args.job_root/'grading'),timeout=60,
            allow_native_decide=False,keep_dir=str(folder/'kernel')))
        result=dict(source_path=relative,source_sha256=sha(source),frozen_inspector_sha256=FROZEN_SHA,
                    passed=kernel.valid_report(report) and report['source_sha256']==sha(source)
                        and report['n_theorems']>0 and report['n_honest']==report['n_theorems'],
                    training_admitted=False,kernel_report=report)
        (folder/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');rows.append(result)
    summary=dict(observed_unix=time.time(),declared=len(CONTROL_PATHS),checked=len(rows),
        passed=sum(r['passed'] for r in rows),source_paths=list(CONTROL_PATHS),training_admitted=0,
        note='Current-toolchain controls only; no annotation, token or protected-screen admission implied')
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True));raise SystemExit(0 if summary['passed']==len(CONTROL_PATHS) else 1)


if __name__=='__main__':main()

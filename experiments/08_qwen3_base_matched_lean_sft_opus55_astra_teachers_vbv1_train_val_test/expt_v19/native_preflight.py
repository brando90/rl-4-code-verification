"""Check native ARM Lean and the exact existing frozen kernel before the remaining evaluation bundle arrives."""
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from common import ROOT,NATIVE,LAKE_BIN,digest,write

def main():
    os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['PATH']=str(LAKE_BIN)+':'+os.environ['PATH']
    source=Path('/home/lethan3/workspace/rl4cv-gx10/verification-v10/frozen_kernel.py')
    assert digest(source)=='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'
    revision=subprocess.check_output(['git','-C',str(NATIVE/'mathlib4'),'rev-parse','HEAD'],text=True).strip();assert revision=='79e94a093aff4a60fb1b1f92d9681e407124c2ca'
    spec=importlib.util.spec_from_file_location('gx19_native_preflight_kernel',source);kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
    cases=[('symbolic_and_anonymous_native','import Mathlib\ntheorem gx19Preflight (a b : Nat) : a+b=b+a := by exact Nat.add_comm a b\nexample : 1+1=2 := by native_decide\n',True),('sorry','import Mathlib\ntheorem gx19Preflight : False := by sorry\n',False),('declared_axiom','import Mathlib\naxiom gx19Fake : False\ntheorem gx19Preflight : False := by exact gx19Fake\n',False),('named_native','import Mathlib\ntheorem gx19Preflight : (1:Nat)+1=2 := by native_decide\n',False)]
    records=[]
    for name,text,expected in cases:
        folder=ROOT/'controls/native_preflight'/name;folder.mkdir(parents=True,exist_ok=True);path=folder/'Solution.lean';path.write_text(text)
        report=asdict(kernel.check_file(str(path),str(NATIVE/'mathlib4'),timeout=60,allow_native_decide=False,keep_dir=str(folder/'kernel')))
        write(folder/'kernel_report.json',report);accepted=bool(kernel.valid_report(report) and report['n_theorems']>=1 and report['n_honest']==report['n_theorems'] and report['source_sha256']==digest(path));assert accepted==expected,(name,report)
        records.append(dict(name=name,expected=expected,accepted=accepted,compile_rc=report['compile_rc'],source_sha256=digest(path)))
        write(ROOT/'controls/native_preflight_progress.json',dict(completed=len(records),declared=len(cases),records=records,observed_unix=time.time()))
    result=dict(status='PASS',scope='Native ARM Lean/frozen kernel only; complete scorer/import/prompt preflight remains separate.',kernel_sha256=digest(source),mathlib_revision=revision,lake_wrapper_sha256=digest(LAKE_BIN/'lake'),records=records,observed_unix=time.time());write(ROOT/'controls/native_preflight.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()

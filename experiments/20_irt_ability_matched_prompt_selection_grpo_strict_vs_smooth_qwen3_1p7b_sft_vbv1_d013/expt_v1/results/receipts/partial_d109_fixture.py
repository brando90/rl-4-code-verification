"""Verify E20 D-109 compiler/kernel/parser interception using pinned real source and fake subprocess results only."""
from pathlib import Path
import argparse
import dataclasses
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch

REPO=Path('/lfs/skampere1/0/brando9/rl4cv_e20')
V=REPO/'experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1/sherlock'
ROOT=REPO/'external/veribench_scorer'
os.environ['RL4CV_SRC']=str(REPO/'src')
sys.path[:0]=[str(V),str(REPO/'src')]
import partial_credit_e20 as partial
import durable_capture as durable
import declaration_adapter as adapter

work=Path(tempfile.mkdtemp(prefix='e20_partial_d109_fixture_'))
lake=work/'lake';lake.mkdir()
source=lake/'Fixture.lean';source.write_text('theorem fixture : True := True.intro\n')
scorer_path=ROOT/'scripts/scsc/run_real_eval.py';kernel_path=ROOT/'scripts/scsc/kernel_axioms.py'
hashes={p.name:durable.sha(p) for p in (scorer_path,kernel_path)}
assert all(partial.FROZEN[k]==v for k,v in hashes.items())

class FakeCapture:
    def __init__(self,mode='success'):
        self.calls=[];self.mode=mode
    def __getattr__(self,name):return getattr(subprocess,name)
    def run(self,command,**kwargs):
        self.calls.append({'command':list(command),'kwargs':kwargs.copy()})
        if self.mode=='timeout':raise subprocess.TimeoutExpired(command,kwargs['timeout'],output=b'partial output',stderr=b'partial error')
        if self.mode=='missing':raise FileNotFoundError('synthetic missing lake')
        if self.mode=='failure':return subprocess.CompletedProcess(command,1,'Fixture.lean:1:1: error: synthetic failure\n','synthetic stderr')
        if '-o' in command:
            Path(command[command.index('-o')+1]).write_bytes(b'synthetic olean; not a real Lean artifact')
            return subprocess.CompletedProcess(command,0,'synthetic kernel compile stdout','')
        if any(str(v).startswith('--setup=') for v in command):
            inspector=Path(command[-1]).read_text()
            marker=re.search(r'IO.println "([^"\n]+):BEGIN"',inspector).group(1)
            row={'name':'fixture','kind':'theorem','axioms':[],'line':1,'column':8,'range_line':1,'range_column':0}
            stdout=f'{marker}:BEGIN\n{marker}:ROW '+json.dumps(row)+f'\n{marker}:END 1\n'
            return subprocess.CompletedProcess(command,0,stdout,'')
        return subprocess.CompletedProcess(command,0,'synthetic stdout\n','synthetic stderr\n')

original_loader=adapter._load
original_functions={}
def recording_loader(name,path):
    module=original_loader(name,path)
    if name=='e13_pinned_scorer':original_functions[name]=module.compile_lean_file
    if name=='e13_kernel_axioms':original_functions[name]=(module.run_probe,module.check_file)
    return module
adapter._load=recording_loader
capture=FakeCapture();load=partial.instrumented_loader(capture)
scorer=load('e13_pinned_scorer',scorer_path)
kernel=load('e13_kernel_axioms',kernel_path)
assert load('e13_pinned_scorer',scorer_path) is scorer
assert scorer.compile_lean_file.__code__ is original_functions['e13_pinned_scorer'].__code__
assert kernel.run_probe.__code__ is original_functions['e13_kernel_axioms'][0].__code__
assert kernel.check_file.__code__ is original_functions['e13_kernel_axioms'][1].__code__
compile_checks=[]
for mode in ('success','failure','timeout','missing'):
    capture.mode=mode;capture.calls.clear();reference=FakeCapture(mode)
    with patch.object(subprocess,'run',reference.run):
        expected=original_functions['e13_pinned_scorer'](str(source),str(lake),timeout=67)
    with patch.object(subprocess,'run',side_effect=AssertionError('unexpected unlogged native subprocess')):
        got=scorer.compile_lean_file(str(source),str(lake),timeout=67)
    assert len(capture.calls)==1 and capture.calls==reference.calls,(mode,capture.calls,reference.calls)
    assert dataclasses.asdict(got)==dataclasses.asdict(expected),(mode,got,expected)
    assert capture.calls[0]['command']==['lake','env','lean','Fixture.lean']
    assert capture.calls[0]['kwargs']==dict(cwd=str(lake.resolve()),capture_output=True,text=True,timeout=67,check=False)
    compile_checks.append({'scenario':mode,'captured_calls':1,'argv_timeout_result_equal':True,'result':dataclasses.asdict(got)})
# Regression demonstration: global-only cloning does not intercept a function-local import.
legacy_capture=FakeCapture();legacy=durable.clone(original_functions['e13_pinned_scorer'],subprocess=legacy_capture)
with patch.object(subprocess,'run',side_effect=AssertionError('old global-only route misses import')):
    try:legacy(str(source),str(lake))
    except AssertionError:legacy_gap_reproduced=True
    else:raise AssertionError('expected global-only instrumentation to miss local import')
assert legacy_capture.calls==[]

capture.mode='success';capture.calls.clear();reference=FakeCapture()
with patch.object(subprocess,'run',reference.run),patch('time.monotonic',return_value=1000.):
    expected=original_functions['e13_kernel_axioms'][0](str(source),str(lake),[], 'FIXTURE_MARKER',timeout=71)
with patch.object(subprocess,'run',side_effect=AssertionError('unexpected unlogged native subprocess')),patch('time.monotonic',return_value=1000.):
    got=kernel.run_probe(str(source),str(lake),[], 'FIXTURE_MARKER',timeout=71)
assert dataclasses.asdict(got)==dataclasses.asdict(expected),(got,expected)
assert len(capture.calls)==len(reference.calls)==2
# Temp-directory names legitimately differ; normalize exactly that implementation-created component.
def normalize(calls):
    return json.loads(re.sub(r'/tmp/[^" ]*/vbax_[^/" ]+', '/FIXTURE_KERNEL_TEMP',json.dumps(calls)))
assert normalize(capture.calls)==normalize(reference.calls),(capture.calls,reference.calls)
assert all(c['kwargs']['timeout']==71 for c in capture.calls)
kernel_calls=list(capture.calls)
# Verify check_file globals use the logged run_probe, including the scorer's private kernel namespace.
kernel_reports=[]
for name,mod in [('adapter_direct_kernel',kernel),('scorer_private_kernel',scorer.kernel_axioms)]:
    capture.calls.clear()
    with patch.object(subprocess,'run',side_effect=AssertionError('unexpected unlogged native subprocess')):
        report=mod.check_file(str(source),str(lake),timeout=73)
    assert len(capture.calls)==2 and report.probe_ok and report.n_honest==1
    assert report.source_sha256==durable.sha(source)
    kernel_reports.append({'route':name,'captured_calls':2,'probe_ok':report.probe_ok,'synthetic_n_honest':report.n_honest,
                           'source_sha256':report.source_sha256})
# Simulated kernel compile timeout retains its partial output in the unchanged kernel report.
capture.mode='timeout';capture.calls.clear()
with patch.object(subprocess,'run',side_effect=AssertionError('unexpected unlogged native subprocess')):
    timed=kernel.run_probe(str(source),str(lake),[], 'TIMEOUT_MARKER',timeout=79)
assert len(capture.calls)==1 and timed.rc==124 and 'partial output' in timed.stdout and 'partial error' in timed.stderr
# Real routing method must capture the adapter's exact nice-prefixed command; no stripping/reordering.
router=object.__new__(durable.DurableCapture);routed=[]
def logged(command,**kwargs):
    routed.append({'command':list(command),'kwargs':kwargs.copy()})
    return subprocess.CompletedProcess(command,0,json.dumps({'event':'terminal','parse_error':False})+'\n','')
router.run_logged=logged
adapter.subprocess=router
with patch.object(durable,'REAL_RUN',side_effect=AssertionError('nice-prefixed parser escaped durable routing')):
    parsed=adapter._probe(source,lake_dir=lake)
assert parsed==[] and len(routed)==1
assert routed[0]['command']==['nice','-n','10','lake','env','lean','--run',str(adapter.PROBE),str(source)]
assert routed[0]['kwargs']==dict(cwd=lake,capture_output=True,text=True,check=False,timeout=900)
parser_success={'command':routed[0]['command'],'timeout':routed[0]['kwargs']['timeout'],'capture_output':True,'check':False}
def logged_timeout(command,**kwargs):
    routed.append({'command':list(command),'kwargs':kwargs.copy()})
    raise subprocess.TimeoutExpired(command,kwargs['timeout'],output=b'partial parser stdout',stderr=b'partial parser stderr')
router.run_logged=logged_timeout
with patch.object(durable,'REAL_RUN',side_effect=AssertionError('timeout parser escaped durable routing')):
    try:adapter._probe(source,lake_dir=lake)
    except subprocess.TimeoutExpired as exc:
        assert exc.timeout==900 and exc.output==b'partial parser stdout' and exc.stderr==b'partial parser stderr'
    else:raise AssertionError('parser timeout was swallowed')
assert len(routed)==2
# Reject changed pinned scorer/kernel bytes before any instrumented compile/probe can run.
rejections=[]
for name,path in [('e13_pinned_scorer',scorer_path),('e13_kernel_axioms',kernel_path)]:
    wrong=work/('changed_'+path.name);wrong.write_bytes(path.read_bytes()+b'\n# harmless changed-byte fixture\n')
    fresh=partial.instrumented_loader(FakeCapture())
    try:fresh(name,wrong)
    except RuntimeError as exc:
        assert 'differ from pin' in str(exc);rejections.append(name)
    else:raise AssertionError('changed pinned bytes accepted')
result={'status':'PASS','fixture_only':True,'no_real_compiler_model_or_gpu_calls':True,
 'source_sha256':durable.sha(source),'pinned_sources':hashes,
 'tested_code_sha256':{str(p):durable.sha(p) for p in (V/'partial_credit_e20.py',V/'durable_capture.py',V/'declaration_adapter.py')},
 'compile_checks':compile_checks,'global_only_import_gap_reproduced':legacy_gap_reproduced,
 'kernel_probe':{'captured_calls':2,'argv_timeout_result_equal':True,'timeout_seconds':71,'result':dataclasses.asdict(got)},
 'kernel_check_routes':kernel_reports,'kernel_timeout':{'captured_calls':1,'rc':timed.rc,'partial_stdout_preserved':True,'partial_stderr_preserved':True},
 'parser_probe':{'nice_prefix_intercepted':True,'unchanged_command':parser_success,'timeout_propagation':True,'timeout_partial_streams_preserved':True},
 'pin_mismatch_rejected':rejections,'temporary_fixture_root':str(work)}
Path('/tmp/e20_partial_d109_fixture.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
print(json.dumps({'status':'PASS','compile_scenarios':len(compile_checks),'kernel_routes':len(kernel_reports),'parser_nice_route':True,
                  'hash_rejections':len(rejections),'receipt':'/tmp/e20_partial_d109_fixture.json'}))

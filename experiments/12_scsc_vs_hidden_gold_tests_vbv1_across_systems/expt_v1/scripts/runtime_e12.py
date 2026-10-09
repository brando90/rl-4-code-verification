"""Compile candidate modules and execute A2 candidate-agreement probes and hidden checks with bounded, low-priority Lean processes."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from adapter_e12 import bridge, map_symbols, IDENT
from compile_reproduction import LAKE, LAKE_BIN


class Runtime:
    def __init__(self, root):
        self.root = Path(root)
        (self.root/'modules').mkdir(parents=True, exist_ok=True)

    def lean(self, path, extra=()):
        start=time.monotonic();env=os.environ.copy();env['LEAN_PATH']=str(self.root/'modules')
        command=['nice','-n','10',LAKE_BIN,'env','lean','-j','1',*extra,str(path)]
        proc=subprocess.Popen(command,cwd=LAKE,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,start_new_session=True)
        try:
            out,_=proc.communicate(timeout=600);status='ok' if proc.returncode==0 else 'error'
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);out,_=proc.communicate();status='timeout'
        log=path.with_suffix('.log');log.write_text(out)
        return {'status':status,'returncode':proc.returncode,'seconds':time.monotonic()-start,'log':str(log),
                'outputs':{int(i):v=='true' for i,v in re.findall(r'^E12_TEST_(\d+)=(true|false)$',out,re.M)}}

    def compile(self, source, module):
        path=self.root/'modules'/(module+'.lean');path.write_text(source)
        receipt=self.lean(path,('--root='+str(self.root/'modules'),'-o',str(path.with_suffix('.olean'))))
        return path,receipt

    def evaluate(self, suite, source, module, compiled=None):
        if compiled is None: path,compiled=self.compile(source,module)
        else: path=self.root/'modules'/(module+'.lean')
        if compiled['status']!='ok':
            return {'compile':compiled,'mapping':{},'diagnostics':[],'all_symbols_mapped':False,
                    'n_applicable':0,'n_pass':0,'all_pass':False}
        initial,_=map_symbols(suite['symbols'],source)
        symbols={token:name for test in suite['tests'] for token,name in test['symbols'].items()}
        cache={}
        def agreement(gold,matches,tuples):
            if tuples is None: return {'agrees':None,'reason':'argument_extraction_unknown'}
            # Only application arguments are ever copied here; expected values never enter probes.
            qualified=[]
            for args in tuples:
                converted=[]
                for arg in args:
                    pieces=re.split(r'("(?:\\.|[^"\\])*")',arg)
                    for i in range(0,len(pieces),2):
                        for token in IDENT.findall(pieces[i]):
                            if token in symbols and symbols[token] not in initial:
                                return {'agrees':None,'reason':'argument_symbol_unmapped'}
                        pieces[i]=IDENT.sub(lambda m:'_root_.'+initial[symbols[m.group()]] if m.group() in symbols else m.group(),pieces[i])
                    converted.append(''.join(pieces))
                qualified.append(converted)
            key=hashlib.sha256(json.dumps([[d['full_name'] for d in matches],qualified]).encode()).hexdigest()[:20]
            if key in cache:return cache[key]
            lines=['import Mathlib','import '+module,'deriving instance DecidableEq for Except'];count=0
            for args in qualified:
                callargs=' '.join('('+arg+')' for arg in args)
                for other in matches[1:]:
                    left='_root_.'+matches[0]['full_name']+' '+callargs
                    right='_root_.'+other['full_name']+' '+callargs
                    lines.append(f'#eval IO.println ("E12_TEST_{count}=" ++ toString (decide (({left}) = ({right}))))');count+=1
            probe=self.root/(module+'_Agreement_'+key+'.lean');probe.write_text('\n'.join(lines)+'\n')
            receipt=self.lean(probe);outputs=receipt['outputs']
            agrees=(all(outputs.values()) if len(outputs)==count and receipt['status']=='ok' else None)
            cache[key]={'agrees':agrees,'n_comparisons':count,'n_decided':len(outputs),'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),
                        'arguments':qualified,'compiler':receipt}
            return cache[key]
        mapping,diag=map_symbols(suite['symbols'],source,suite['tests'],agreement)
        probe=self.root/(module+'_Bridge.lean');probe.write_text(bridge(module,suite['tests'],mapping))
        evaluation=self.lean(probe) if mapping else {'status':'not_applicable','outputs':{}}
        outputs=evaluation['outputs'];n_pass=sum(outputs.values())
        return {'compile':compiled,'mapping':mapping,'diagnostics':diag,
                'all_symbols_mapped':len(mapping)==len(suite['symbols']),
                'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'candidate_path':str(path),
                'evaluation':evaluation,'n_applicable':len(outputs),'n_pass':n_pass,
                'all_pass':len(outputs)==suite['n_tests'] and bool(outputs) and all(outputs.values())}

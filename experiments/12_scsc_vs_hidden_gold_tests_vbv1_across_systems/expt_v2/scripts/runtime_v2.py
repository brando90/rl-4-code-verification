"""Execute the frozen v2 mapping and per-test outcomes with the v1 bounded Lean runner."""
import hashlib
import json
import re
from adapter_v2 import bridge, map_symbols, IDENT, per_test_plan, cell_outcome, declarations
from runtime_e12 import Runtime as RuntimeV1


class Runtime(RuntimeV1):
    def evaluate(self, suite, source, module, compiled=None):
        if compiled is None: path,compiled=self.compile(source,module)
        else: path=self.root/'modules'/(module+'.lean')
        if compiled['status']!='ok':
            plan=per_test_plan(suite['tests'],{})
            return {**cell_outcome(suite['n_tests'],{},plan),
                    'compile':compiled,'mapping':{},'diagnostics':[],
                    'all_symbols_mapped':False,'n_applicable':0,'all_pass':False,
                    **declarations(source)[2]}
        initial,_,_=map_symbols(suite['symbols'],source)
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
        mapping,diag,counts=map_symbols(suite['symbols'],source,suite['tests'],agreement)
        probe=self.root/(module+'_Bridge.lean');probe.write_text(bridge(module,suite['tests'],mapping))
        evaluation=self.lean(probe) if mapping else {'status':'not_applicable','outputs':{}}
        plan=per_test_plan(suite['tests'],mapping)
        outputs=evaluation['outputs']
        assert set(outputs)<={r['index'] for r in plan if r['status']=='mapped'}
        outcome=cell_outcome(suite['n_tests'],outputs,plan)
        return {**outcome, **counts, 'compile':compiled,'mapping':mapping,'diagnostics':diag,
                'all_symbols_mapped':len(mapping)==len(suite['symbols']),
                'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'candidate_path':str(path),
                'evaluation':evaluation,'n_applicable':outcome['n_evaluable'],
                'all_pass':outcome['hidden_all_pass'] is True}

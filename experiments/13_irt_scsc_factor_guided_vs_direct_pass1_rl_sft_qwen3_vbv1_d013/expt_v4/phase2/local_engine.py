"""TLDR: Compose real generation, scoring, filtered training, export, replay and audit subprocesses."""
import json
from pathlib import Path
import numpy as np
from common import digest,object_digest,write_new
from stage_process import execute
from runtime_inputs import inputs


class LocalEngine:
    synthetic=False
    def __init__(self,work,admission,*,stub_engines=False):
        self.work=Path(work);self.admission=str(admission);self.synthetic=stub_engines
        self.config=inputs();self.config.update(work=str(self.work),admission=str(admission))
        self.templates=json.loads(Path(self.config['templates']).read_text())
        if self.synthetic:
            self.templates={k:{**v,'prompt_token_ids':[100]} for k,v in self.templates.items()}

    def train_ids(self):return sorted(self.templates)

    def component(self,stage,path,**payload):
        return execute({**self.config,'stage':stage,'payload':payload},path,synthetic=self.synthetic)

    def cells(self,tasks,n,*,seed=1304001,arm='technical',update=0):
        cells=[]
        for group,task in enumerate(tasks):
            for sample in range(n):
                cell={**self.templates[task],'cell_id':f'e13v4/{seed}/{update}/{group}/{sample}',
                    'sample':sample,'sample_idx':sample,'seed':int(object_digest(['e13v4-generation',seed,update,group,sample])[:8],16),
                    'run_seed':seed,'group_index':group,'update':update,'arm':arm}
                cells.append(cell)
        return cells

    def generated(self,result):return [json.loads(Path(p).read_text()) for p in result['row_paths']]

    def generate(self,path,cells,*,model=None,full=True,receipt=True):
        return self.component('generate',path,cells=cells,model=model or self.config['model'],full=full,receipt=receipt)

    def probe(self,path,model=None,checkpoint=None):
        from sampler_checks import engine_check
        cells=json.loads(Path(self.config['probe']).read_text())
        if self.synthetic:cells=[{**r,'prompt_token_ids':[100]} for r in cells]
        r0=self.generate(path/'R0',cells,model=model,receipt=False)
        r1=self.generate(path/'R1',cells,model=model)
        a=self.generated(r0);b=self.generated(r1)
        compare=engine_check([r['output_token_ids'] for r in a],[r['output_token_ids'] for r in b])
        if compare['status']=='NEED_R2':
            r2=self.generate(path/'R2',cells,model=model,receipt=False)
            compare=engine_check([r['output_token_ids'] for r in a],[r['output_token_ids'] for r in b],
                                 [r['output_token_ids'] for r in self.generated(r2)])
        values=self.component('probabilities',path/'probabilities',rows=b,checkpoint=checkpoint)
        return {'rows':b,'positions':values['positions'],'receipt_invariance':compare,
                'receipt_on_off_identical':not compare['R0_R1'],'generated_responses':8,
                'sampler_backend':r1['worker_backend']}

    def measure(self,op,path,payload):
        path=Path(path)
        if op=='probe':return self.probe(path)
        if op=='generate':
            result=self.generate(path/'generate',self.cells(payload['tasks'],32))
            return {**result,'rows':self.generated(result)}
        if op=='score':
            previous=json.loads(next((Path(payload['generation_stage'])/'generate').glob('attempt_*/output.json')).read_text())
            result=self.component('score',path/'score',rows=previous['rows'])
            return result
        if op=='update':
            groups=payload['groups']
            # Scored rows retain the exact generation receipt and identity.
            result=self.component('update',path/'update',groups=groups,advantages=payload['advantages'])
            if result.get('status')=='STOP_V4_A4':return result
            exported=self.component('export',path/'export',checkpoint=result['checkpoint'])
            return {**result,'model':exported['model']}
        if op=='refit':
            update=payload['update'];cells=json.loads(Path(self.config['probe']).read_text())
            gen=self.generate(path/'refit_generate',cells,model=update['model'])
            rows=self.generated(gen)
            result=self.component('probabilities',path/'probabilities',rows=rows,checkpoint=update['checkpoint'])
            old=self.component('probabilities',path/'old_probabilities',rows=rows,
                checkpoint=str(Path(update['source_update'])/'before'),support_only=True)
            result['old_supports']=[p['trainer_support'] for p in old['positions']]
            return result
        if op=='replay':return self.component('replay',path/'replay',source_update=payload['source_update'])
        if op=='maximum_length':
            result=self.component('maximum_length',path/'maximum_length')
            update=json.loads((self.work/'T2/receipt.json').read_text())['result']['update']
            score=json.loads((self.work/'G0_SCORE/receipt.json').read_text())['result']['rows']
            generation=next((self.work/'G0_GENERATE/generate').glob('attempt_*/generate/execution.json'))
            seconds=json.loads(generation.read_text())['wall_seconds']
            update_cost=json.loads((Path(update['source_update']).parent/'execution.json').read_text())
            return {**result,'device_seconds':update_cost['device_seconds']+seconds/4,'updates':1,
                'generated_tokens':sum(len(r['output_token_ids']) for r in score),'generation_seconds':seconds,
                'lean_wall_seconds':sum(r.get('wall_seconds',0) for r in score),
                'timeout_count':sum(r.get('status')=='deterministic_resource_limit' for r in score),'scoring_slots':1024,
                'storage_growth_bytes':sum(p.stat().st_size for p in self.work.rglob('*') if p.is_file())}
        if op=='audits':return self.audit(path,self.config['model'])
        if op=='pilot_update':return self.pilot(path,payload)
        raise ValueError('unregistered real adapter '+op)

    def audit(self,path,model,*,baseline=False):
        from audit_runtime import audit_templates
        tasks=audit_templates()
        generation=self.generate(path/'audit_generate',self.cells(tasks,1,seed=1304101,arm='B'),model=model,full=False)
        return self.component('audit_score',path/'audit_score',rows=self.generated(generation))

    def pilot(self,path,payload):
        from gates import advantages
        from placebo import density
        arm=payload['arm'];seed=payload['seed'];u=payload['update'];g=payload['G']
        previous=None
        if u>1:
            stage='PILOT30' if u<=31 else 'PILOT60'
            previous=json.loads((self.work/stage/f'{arm}_{seed}/update_{u-1:05d}/summary.json').read_text())
        model=previous['model'] if previous else self.config['model']
        rng=np.random.default_rng(int(object_digest(['e13v4-prompt',seed,u])[:16],16))
        tasks=rng.choice(sorted(self.templates),size=256//g,replace=True).tolist()
        gen=self.generate(path/'generate',self.cells(tasks,g,seed=seed,arm=arm,update=u),model=model,full=False)
        scored=self.component('score',path/'score',rows=self.generated(gen))
        rows=scored['rows'];groups=[rows[i:i+g] for i in range(0,256,g)]
        field='strict' if arm=='A' else 'factored_reward'
        if arm=='P':
            for row,value in zip(rows,payload['placebo']):row['placebo_reward']=value
            field='placebo_reward'
        adv=advantages(groups,field)
        result=self.component('update',path/'update',groups=groups,advantages=adv,
                              checkpoint=previous['checkpoint'] if previous else None,run_seed=seed)
        if result.get('status')=='STOP_V4_A4':return result
        exported=self.component('export',path/'export',checkpoint=result['checkpoint'])
        audit=self.audit(path/'audit',exported['model']) if arm=='B' else None
        return {'arm':arm,'seed':seed,'update':u,'completed':True,'strict':[r['strict'] for r in rows],
            'generated_tokens':[len(r['output_token_ids']) for r in rows],
            'density':density([[r[field] for r in group] for group in groups]),
            'importance':result['importance'],'certified_fraction':result['importance']['certified_fraction'],
            'model':exported['model'],'checkpoint':result['checkpoint'],
            'audit':audit['baseline'] if audit else None,'optimizer_steps':0 if self.synthetic else 1}

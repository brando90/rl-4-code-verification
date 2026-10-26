"""TLDR: Run ordered v4 stages once, preserve recovery evidence, and separate synthetic from measured receipts."""
import argparse
import json
import os
from pathlib import Path
from admission import check_admission
from common import digest, object_digest, write_new
from stage_ledger import Ledger, fence, read, RecoveryRequired
from gates import probability_agreement, select_t2_reward, advantages, t2, t3, t4
from group_selection import select_tasks, choose_group_size, t2_subset
from placebo import reference, precompute
from pilot_metrics import t5, extension_plan, token_budget

STAGES=('T1','G0_GENERATE','G0_SCORE','G0_SELECT','T2','T3','T4','B_AUDITS',
        'PILOT30','T5_30','PILOT60','T5_60')
PREDECESSORS={stage:([STAGES[i-1]] if i else []) for i,stage in enumerate(STAGES)}


class Runner:
    def __init__(self, work, admission, engine):
        self.work=Path(work);self.admission=Path(admission);self.engine=engine
        check_admission(admission,require_launch=not engine.synthetic)
        if engine.synthetic and os.environ.get('CUDA_VISIBLE_DEVICES')!='':
            raise ValueError('synthetic mode requires CUDA_VISIBLE_DEVICES empty')
        self.ledger=Ledger(work,admission,synthetic=engine.synthetic)
        self.recover=False

    def op(self, stage, name, kind, payload):
        return self.ledger.operation(stage,name,payload,
            lambda path,data:self.engine.measure(kind,path,data),recover=self.recover)

    def result(self, stage):
        receipt=self.ledger.completed(stage)
        if receipt is None:raise ValueError('missing completed stage '+stage)
        return receipt['result']

    def run(self, stage, *, recover=False):
        if stage not in STAGES:raise ValueError('unknown stage')
        # Recheck every stage, including resumed completed receipts.
        admission=check_admission(self.admission,require_launch=not self.engine.synthetic)
        if not self.engine.synthetic:
            from admission import launch_timing
            timing=launch_timing('/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/pilot',
                phase='pilot' if stage.startswith(('PILOT','T5')) else 'gates',
                veto_not_issued=os.environ.get('E13V4_A3_NO_VETO')=='1',
                operational=Path(admission['root'])/'phase2/operational_pause.json')
            if not timing['released']:raise ValueError('runtime schedule conditions unmet: '+str(timing))
        with fence(self.work):
            self.recover=recover
            if not self.engine.synthetic and stage.startswith('PILOT'):
                from device_lease import pilot_capacity
                pilot_capacity(self.work.parent/'leases')
            prior=self.ledger.begin(stage,PREDECESSORS[stage])
            if prior:return prior
            if stage=='PILOT60' and self.result('T5_30')['decision']['action'] not in ('EXTEND_ALL_SIX','EXTEND_ALL_ADMITTED'):
                raise ValueError('extension requires A/1301 failure at 30')
            result=getattr(self,'stage_'+stage)()
            return self.ledger.finish(stage,result)

    def stage_T1(self):
        evidence=self.op('T1','probe','probe',{'responses':8,'full':True,'compare_receipt_on_off':True})
        def measure():
            r=probability_agreement(evidence['positions'],expected_positions=sum(len(row['output_token_ids']) for row in evidence['rows']))
            r['receipt_on_off_identical']=evidence['receipt_on_off_identical']
            r['receipt_invariance']=evidence.get('receipt_invariance',{'status':'PASS' if evidence['receipt_on_off_identical'] else 'FAIL'})
            if r['receipt_invariance']['status']!='PASS':r['status']='FAIL'
            return r
        return self.ledger.statistic('T1',measure)

    def task_order(self):
        if self.engine.synthetic and not hasattr(self.engine,'train_ids'):return select_tasks([f'synthetic_{i:04d}' for i in range(539)])
        return select_tasks(self.engine.train_ids())

    def stage_G0_GENERATE(self):
        tasks=self.task_order()
        data=self.op('G0_GENERATE','generate','generate',{'tasks':tasks,'responses':1024,'full':True})
        if data['generated_responses']!=1024:raise RecoveryRequired('partial G0; retain without resampling')
        return {'status':'PASS','tasks':tasks,'generation_sha256':object_digest(data),'declared':1024}

    def stage_G0_SCORE(self):
        prior=self.result('G0_GENERATE')
        data=self.op('G0_SCORE','score','score',{'tasks':prior['tasks'],
                    'generation_sha256':prior['generation_sha256'],'generation_stage':str(self.work/'G0_GENERATE')})
        return {'status':'PASS','rows':data['rows'],'tasks':prior['tasks']}

    def stage_G0_SELECT(self):
        batch=self.result('G0_SCORE')
        def measure():
            selection=choose_group_size(batch['rows'],batch['tasks']);ref=reference(batch['rows'])
            root=self.work/'G0_SELECT'
            write_new(root/'placebo_reference.json',ref)
            if ref['status']=='ADMITTED':
                stream=precompute(ref,[1301,1302],60,root/'placebo_draws.json',
                    first_response_exists=bool(list(self.work.glob('PILOT*/P_*/**/generations.json'))))
                # Admission supplement binds observed distribution without rewriting
                # the pre-generation admission or any already completed receipt.
                write_new(root/'placebo_admission.json',{'base_admission_sha256':digest(self.admission),
                    'distribution_sha256':ref['distribution_sha256'],'draws_sha256':stream['draws_sha256'],
                    'draws_file_sha256':digest(root/'placebo_draws.json'),'bound_before_first_P_response':True})
            if not self.engine.synthetic:
                from forecast_score import score
                forecast=next(Path(__file__).resolve().parents[3].glob('19_*/expt_v1/forecasts/e19_g3_forecast_v4_g0.json'))
                # Descriptive only: forecast failures are retained, never change a gate.
                try:score(forecast,batch['rows'],batch['tasks'],selection['G'],root/'forecast')
                except Exception as exc:write_new(root/'forecast_error.json',{'error':str(exc),'gate_input':False})
            return {'status':'PASS','selection':selection,'placebo_status':ref['status'],
                    'distribution_sha256':ref['distribution_sha256']}
        return self.ledger.statistic('G0_SELECT',measure)

    def stage_T2(self):
        batch=self.result('G0_SCORE');g=self.result('G0_SELECT')['selection']['G']
        groups=t2_subset(batch['rows'],batch['tasks'],g)
        chosen=select_t2_reward(groups)
        if chosen['status']=='STOP_NO_SIGNAL':
            return self.ledger.statistic('T2',lambda:{'status':'STOP_NO_SIGNAL','reward_selection':chosen,'resample':False})
        adv=advantages(groups,chosen['field'])
        update=self.op('T2','update','update',{'groups':groups,'advantages':adv,'reward_selection':chosen,
                       'generation_stage':str(self.work/'G0_GENERATE'),'G':g})
        if update.get('status')=='STOP_V4_A4':return update
        refit=self.op('T2','refit','refit',{'responses':8,'full':True,'update':update})
        def measure():
            r=t2(advantages=[x for a in adv for x in a['advantages']],
                 preclip_gradient_norm=update['preclip_gradient_norm'],before_weights=update['before_weights'],
                 after_weights=update['after_weights'],refit_positions=refit['positions'],
                 old_supports=refit['old_supports'],
                 new_supports=[p['trainer_support'] for p in refit['positions']])
            return {**r,'reward_selection':chosen,'update':update}
        return self.ledger.statistic('T2',measure)

    def stage_T3(self):
        update=self.result('T2')['update']
        replay=self.op('T3','replay','replay',update)
        return self.ledger.statistic('T3',lambda:t3(update['loss'],replay['loss'],update['replay_binding'],replay['replay_binding']))

    def stage_T4(self):
        data=self.op('T4','maximum_length','maximum_length',{'maximum_train_prompt':7753,'response_cap':12288})
        return self.ledger.statistic('T4',lambda:t4(**{k:v for k,v in data.items() if k!='synthetic'}))

    def stage_B_AUDITS(self):
        data=self.op('B_AUDITS','audits','audits',{'train_only':True,'mutations':['padding','deletion','substitution'],
                    'hidden_gold_controls':True})
        if not data['hidden_coverage_controls'] or set(data['mutations'])!={'padding','deletion','substitution'}:
            raise ValueError('incomplete B audits')
        return self.ledger.statistic('B_AUDITS',lambda:data)

    def pilot(self, stage, start, end):
        selected=self.result('G0_SELECT');g=selected['selection']['G']
        refpath=self.work/'G0_SELECT/placebo_draws.json'
        arms=['A','B','P'] if selected['placebo_status']=='ADMITTED' else ['A','B']
        rows=[]
        for arm in arms:
            for seed in (1301,1302):
                for update in range(start,end+1):
                    draws=read(refpath)['draws'][f'{seed}/{update}'] if arm=='P' else None
                    payload={'arm':arm,'seed':seed,'update':update,'G':g,'full':False,'placebo':draws,
                             'base_admission_sha256':digest(self.admission)}
                    if arm=='P':
                        supplement=read(self.work/'G0_SELECT/placebo_admission.json')
                        if supplement['draws_file_sha256']!=digest(refpath):raise ValueError('placebo stream changed')
                        payload['placebo_admission_sha256']=digest(self.work/'G0_SELECT/placebo_admission.json')
                    name=f'{arm}_{seed}/update_{update:05d}'
                    result=self.op(stage,name,'pilot_update',payload)
                    if result.get('status')=='STOP_V4_A4':return {**result,'arm':arm,'seed':seed,'update':update}
                    summary={**result,'condition':'e13v4','admission_sha256':digest(self.admission)}
                    path=self.work/stage/name/'summary.json'
                    if path.exists():
                        if read(path)!=summary:raise ValueError('completed update changed')
                    else:write_new(path,summary)
                    rows.append(summary)
                    if not self.engine.synthetic:
                        from retention import retire_completed
                        retire_completed(self.work,arm,seed,update)
                    if arm=='B':
                        before=self.result('B_AUDITS')['baseline'];after=result['audit']
                        if any(after[k] is None for k in ('reward','theorem_count','coverage')):return {'status':'STOP_B_AUDIT_UNMEASURED','arm':arm,'seed':seed,'update':update}
                        if (after['reward']>before['reward'] and any(after[k]<.9*before[k] for k in ('theorem_count','coverage'))):
                            return {'status':'STOP_B_AUDIT','arm':'B','seed':seed,'update':update,'rows':rows}
        return {'status':'PASS','horizon':end,'arms':arms,'rows':rows}

    def stage_PILOT30(self):return self.pilot('PILOT30',1,30)
    def stage_PILOT60(self):return self.pilot('PILOT60',31,60)

    def decision(self, stage, horizon):
        rows=self.result('PILOT30')['rows']
        if horizon==60:rows+=self.result('PILOT60')['rows']
        def measure():
            # P may be prospectively excluded by its 90% admission rule.
            if self.result('G0_SELECT')['placebo_status']=='EXCLUDED':
                from pilot_metrics import update_table
                for arm in ('A','B'):
                    for seed in (1301,1302):update_table(rows,arm,seed,horizon)
                gate=t5(rows,horizon)
                decision={'gate':gate,'action':'MAIN_RESOURCE_CHECK' if gate['status']=='PASS' else
                          'EXTEND_ALL_ADMITTED' if horizon==30 else 'STOP_PUBLISH','P':'UNMEASURED'}
            else:decision=extension_plan(rows,horizon)
            return {'status':'PASS','decision':decision,'replication':t5(rows,horizon,seed=1302),
                    'token_budget':token_budget(rows),'main_launched':False}
        return self.ledger.statistic(stage,measure)

    def stage_T5_30(self):return self.decision('T5_30',30)
    def stage_T5_60(self):return self.decision('T5_60',60)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=[*STAGES,'sequence','gates','pilot','progress'])
    p.add_argument('--work',required=True,type=Path);p.add_argument('--admission',required=True,type=Path)
    p.add_argument('--engine',choices=['stub','local','local-stub'],default='local');p.add_argument('--recover',action='store_true')
    p.add_argument('--no-signal',action='store_true');p.add_argument('--crash',choices=['probe','generate','update'])
    a=p.parse_args()
    if a.stage=='progress':
        check_admission(a.admission,require_launch=False)
        ledger=Ledger(a.work,a.admission,synthetic=a.engine=='stub')
        print(json.dumps({s:(r['status'] if (r:=ledger.completed(s)) else 'PENDING') for s in STAGES}));return
    if a.engine=='stub':
        from stub_engine import StubEngine
        engine=StubEngine(no_signal=a.no_signal,crash=a.crash)
    elif a.engine=='local-stub':
        from local_engine import LocalEngine
        engine=LocalEngine(a.work,a.admission,stub_engines=True)
    else:
        # No model constructor can be reached by bypassing a JSON status flag.
        check_admission(a.admission,require_launch=True)
        from local_engine import LocalEngine
        engine=LocalEngine(a.work,a.admission)
    run=Runner(a.work,a.admission,engine)
    selected=STAGES if a.stage=='sequence' else STAGES[:8] if a.stage=='gates' else STAGES[8:] if a.stage=='pilot' else [a.stage]
    for stage in selected:
        r=run.run(stage,recover=a.recover)
        print(json.dumps({'stage':stage,'status':r['status'],'admission_sha256':r['admission_sha256'],'synthetic':r['synthetic']}),flush=True)
        if r['status']!='PASS':break
        if stage=='T5_30' and r['result']['decision']['action'] not in ('EXTEND_ALL_SIX','EXTEND_ALL_ADMITTED'):break


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Run grouped nested forecasts with full-schedule outcomes excluded from fitting and inner selection."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from forecast_v2 import forecast_panel, policy_features, fold, select_candidate, IdentificationError
from evaluation_v2 import assess_g1
from features_v2 import matrices


def _fraction(system):
    return float(system['fraction'])


def run_forecast(rows,systems,features_by_task,groups_by_task,*,draws=10000):
    """Return complete same-cell forecasts for both required holdout schemes.

    All rows must be validation rows admitted after L1v2. Test rows cannot enter this code.
    Full-schedule labels are read only by final evaluation; inner selection uses the last
    earlier rung, keeping the full-schedule checkpoint holdout intact in every outer fold.
    """
    if any(r['split']!='validation' for r in rows):raise ValueError('prediction harness accepts validation only; test is sealed')
    table={}
    for r in rows:
        key=(r['policy'],r['task_id'],r['sample_idx'])
        if key in table:raise ValueError('duplicate prediction cell')
        table[key]=r
    policies=sorted({r['policy'] for r in rows});tasks=sorted({r['task_id'] for r in rows})
    by_policy={s['label']:s for s in systems if s['label'] in policies}
    if set(by_policy)!=set(policies):raise ValueError('unbound policy metadata')
    expected={(p,t,s) for p in policies for t in tasks for s in range(8)}
    if set(table)!=expected or any(r['strict_status']!='scored' or r['strict'] not in (0,1) for r in rows):
        raise ValueError('prediction cohort has missing/unknown cells')
    target_policies=sorted(p for p in policies if _fraction(by_policy[p])==1.)
    if not target_policies:raise ValueError('no full-schedule policy')
    earlier=[p for p in policies if _fraction(by_policy[p])<1.]
    inner_fraction=max(_fraction(by_policy[p]) for p in earlier)
    inner_targets=[p for p in earlier if _fraction(by_policy[p])==inner_fraction]
    inner_history=[p for p in earlier if _fraction(by_policy[p])<inner_fraction]
    features=lambda ts:np.array([features_by_task[t] for t in ts],float)
    metadata=lambda ps:policy_features([float(by_policy[p]['size'].removesuffix('B')) for p in ps],
                                      [by_policy[p]['cumulative_assistant_tokens'] for p in ps])

    def predict(train_tasks,test_tasks,train_policies,target_pols):
        if isinstance(features_by_task[train_tasks[0]],dict):
            train_features,test_features,_=matrices([features_by_task[t] for t in train_tasks],[features_by_task[t] for t in test_tasks])
        else:
            train_features,test_features=features(train_tasks),features(test_tasks)
        h=[table[(p,t,s)] for p in train_policies for t in train_tasks for s in range(8)]
        pi={p:i for i,p in enumerate(train_policies)};ji={t:i for i,t in enumerate(train_tasks)}
        history={key:[r[key] for r in h] for key in ['strict','q1','compile','honest']}
        history.update(policy_index=[pi[r['policy']] for r in h],item_index=[ji[r['task_id']] for r in h],observed=[True]*len(h))
        shape=(len(target_pols),len(test_tasks));ey=np.zeros(shape);en=np.zeros(shape);eb=np.zeros(shape)
        for i,p in enumerate(target_pols):
            prior=[q for q in train_policies if by_policy[q]['size']==by_policy[p]['size'] and _fraction(by_policy[q])<_fraction(by_policy[p])]
            if not prior:raise ValueError('target has no earlier-rung evidence')
            prior=max(prior,key=lambda q:_fraction(by_policy[q]))
            for j,t in enumerate(test_tasks):
                preceding=[table[(prior,t,s)] for s in range(8)]
                ey[i,j]=sum(r['strict'] for r in preceding) if t in ji else 0;en[i,j]=8 if t in ji else 0;eb[i,j]=np.mean([r['factored_reward'] for r in preceding])
        cx=[];cy=[];cw=[]
        for size in sorted({by_policy[p]['size'] for p in train_policies}):
            order=sorted([p for p in train_policies if by_policy[p]['size']==size],key=lambda p:_fraction(by_policy[p]))
            for earlier_p,later_p in zip(order,order[1:]):
                for t in train_tasks:
                    cx.append(np.mean([table[(earlier_p,t,s)]['factored_reward'] for s in range(8)]))
                    cy.append(np.mean([table[(later_p,t,s)]['strict'] for s in range(8)]));cw.append(8)
        return forecast_panel(history=history,policy_metadata=metadata(train_policies),item_features=train_features,
            target_metadata=metadata(target_pols),target_features=test_features,
            target_item_indices=[ji.get(t,-1) for t in test_tasks],earlier_successes=ey,earlier_trials=en,
            earlier_reward=eb,calibration_x=cx,calibration_y=cy,calibration_trials=cw)

    outputs={}
    for scheme in ('grouped_tasks','full_schedule_policies'):
        outer=range(5) if scheme=='grouped_tasks' else [None]
        cell_predictions={name:[] for name in ['M0','M1','M2','M3','M3e','selected']}
        labels=[];groups=[];labels_policy=[];trace=[];all_admitted=True
        for outer_fold in outer:
            train=[t for t in tasks if outer_fold is None or fold(groups_by_task[t])!=outer_fold]
            test=[t for t in tasks if outer_fold is None or fold(groups_by_task[t])==outer_fold]
            if not train or not test:raise ValueError('empty required outer fold')
            inner_predictions={'M3':[],'M3e':[]};inner_y=[];inner_groups=[];eligible={'M3':True,'M3e':True}
            for inner in range(3):
                tr=[t for t in train if fold(groups_by_task[t],3,'inner')!=inner]
                te=[t for t in train if fold(groups_by_task[t],3,'inner')==inner]
                if not tr or not te:raise ValueError('empty required inner fold')
                preds,receipts=predict(tr,te,inner_history,inner_targets)
                for name in eligible:
                    if preds[name] is None or not receipts[name]['admitted']:eligible[name]=False
                    if preds[name] is not None:inner_predictions[name].extend(np.repeat(preds[name].reshape(-1),8))
                inner_y.extend(table[(p,t,s)]['strict'] for p in inner_targets for t in te for s in range(8))
                inner_groups.extend(groups_by_task[t] for p in inner_targets for t in te for s in range(8))
            selection_error=None
            try:
                candidate,losses=select_candidate({n:np.asarray(v) if eligible[n] else None for n,v in inner_predictions.items()},np.asarray(inner_y),inner_groups)
            except IdentificationError as exc:
                candidate=None;losses={'M3':None,'M3e':None};selection_error=str(exc)
            preds,receipts=predict(train,test,earlier,target_policies)
            all_admitted &= candidate is not None and receipts[candidate]['admitted']
            for name in cell_predictions:
                pred=preds.get(candidate if name=='selected' else name)
                if pred is None:cell_predictions[name].extend([float('nan')]*(len(target_policies)*len(test)*8))
                else:cell_predictions[name].extend(np.repeat(pred.reshape(-1),8))
            labels.extend(table[(p,t,s)]['strict'] for p in target_policies for t in test for s in range(8))
            groups.extend(groups_by_task[t] for p in target_policies for t in test for s in range(8))
            labels_policy.extend(p for p in target_policies for t in test for s in range(8))
            trace.append({'outer_fold':outer_fold,'training_tasks':len(train),'heldout_tasks':len(test),
                          'candidate':candidate,'inner_losses':losses,'selection_error':selection_error,'model_receipts':receipts})
        pred_arrays={name:np.asarray(values) for name,values in cell_predictions.items()}
        evaluation=assess_g1(labels,pred_arrays,groups,labels_policy,draws=draws,implementation_admitted=all_admitted)
        outputs[scheme]={'evaluation':evaluation,'folds':trace,'predictions':{name:[float(x) if np.isfinite(x) else None for x in p] for name,p in pred_arrays.items()}}
    return outputs

"""Report A's measured gradient signal separately from optimizer steps and weight decay."""
import math


def summarize(updates):
    rows=[]
    for index,receipt in enumerate(updates,1):
        if receipt.get('condition')!='v2-S2':raise ValueError('wrong numerical condition')
        status=receipt['status'];count=receipt['optimizer_updates'];counts=receipt['counts']
        if status=='UNMEASURED':
            if count!=0 or counts['usable_groups']!=0:raise ValueError('unmeasured update accounting changed')
            rows.append({'update':index,'optimizer_updates':0,'gradient_norm':None,'nonzero_gradient':None,
                'nonzero_advantage_slots':counts['nonzero_advantage_slots'],'status':'UNMEASURED'})
        elif status=='MEASURED':
            if count!=1 or counts['usable_groups']<=0:raise ValueError('measured update accounting changed')
            norm=receipt['metrics']['grad_norm']
            if isinstance(norm,list):
                if len(norm)!=1:raise ValueError('single-device gradient norm shape changed')
                norm=norm[0]
            if type(norm)not in (int,float)or not math.isfinite(norm)or norm<0:raise ValueError('invalid measured gradient norm')
            rows.append({'update':index,'optimizer_updates':1,'gradient_norm':norm,'nonzero_gradient':norm>0,
                'nonzero_advantage_slots':counts['nonzero_advantage_slots'],'status':'MEASURED'})
        else:raise ValueError('completed opportunity lacks a terminal training receipt')
    return {'scheduled_opportunities':len(rows),'optimizer_updates':sum(r['optimizer_updates']for r in rows),
        'gradient_measured_updates':sum(r['gradient_norm']is not None for r in rows),
        'nonzero_gradient_updates':sum(r['nonzero_gradient']is True for r in rows),
        'zero_gradient_updates':sum(r['nonzero_gradient']is False for r in rows),
        'gradient_unavailable_updates':sum(r['nonzero_gradient']is None for r in rows),
        'updates':rows,'interpretation':'descriptive actual pre-clipping trainer gradient norm; weight-hash changes from AdamW weight decay do not imply a nonzero policy gradient'}

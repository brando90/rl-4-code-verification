"""Apply adopted A6 T5 to B's own fixed-seed train reward, retaining every missing slot."""
from decimal import Decimal
import math


def evaluate(rows,*,horizon):
    if horizon not in (30,60):raise ValueError('undeclared T5 horizon')
    table={}
    for row in rows:
        key=row['update'];values=row['rewards']
        if (type(key)is not int or not 1<=key<=horizon or key in table or row.get('arm')!='B'
                or row.get('seed')!=1301 or row.get('split')!='train' or len(values)!=256):
            raise ValueError('B pilot full opportunity inventory changed')
        if any(v is not None and (type(v)not in (int,float)or not math.isfinite(v)or not 0<=v<=1)for v in values):
            raise ValueError('invalid own train reward')
        table[key]=values
    if set(table)!=set(range(1,horizon+1)):raise ValueError('every B pilot update required')
    def window(updates):
        values=[v for i in updates for v in table[i]];known=[Decimal(str(v))for v in values if v is not None]
        total=sum(known,Decimal(0));missing=len(values)-len(known);denom=Decimal(len(values))
        return {'declared':len(values),'measured':len(known),'reward_sum':float(total),
            'mean_bounds':[float(total/denom),float((total+missing)/denom)]},(total/denom,(total+missing)/denom)
    start,lo=window(range(1,11));end,hi=window(range(horizon-9,horizon+1))
    lower=hi[0]-lo[1];upper=hi[1]-lo[0];threshold=Decimal('.02')
    status='PASS'if lower>=threshold else 'EXTEND_TO_60'if horizon==30 else 'FAIL'if upper<threshold else 'INCONCLUSIVE'
    return {'condition':'v2-S2','gate':'T5','status':status,'horizon':horizon,'arm':'B','seeds':[1301],
        'metric':'own train reward','admission_statistics_computed':True,'initial_updates':[1,10],'final_updates':[horizon-9,horizon],
        'initial':start,'final':end,'improvement_bounds':[float(lower),float(upper)],'threshold':.02,'extension_used':horizon==60,
        'missing_outcomes_assigned_zero':False,'threshold_source':'adopted A6 rule 3',
        'p_value':None,'uncertainty':'one fixed B pilot; full-denominator missingness bounds, no independent-run confidence interval',
        'interpretation':'technical feasibility selection, not evidence for the main efficacy hypothesis; A curve descriptive',
        'token_budget_source':'unchanged A-pilot lengths; never B lengths'}

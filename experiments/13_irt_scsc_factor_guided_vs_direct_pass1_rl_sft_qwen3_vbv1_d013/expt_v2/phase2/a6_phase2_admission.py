"""Apply the adopted A6 Phase 2 prerequisites without fabricating a measurable H2 predictor."""
def select_arms_a6(g0,lp1,calibration,g1,h2,diagnostic):
    if g0.get('gate')!='G0_A3' or g0.get('status')!='PASS':raise ValueError('G0 PASS required')
    if (lp1.get('condition')!='v2-S2' or lp1.get('status')!='PASS' or lp1.get('numerical_dtype')!='float16'
            or lp1.get('admission_statistics_computed')is not True):raise ValueError('final S2 admission required')
    if (calibration.get('status')!='FROZEN' or calibration.get('condition')!='v2-S2'
            or calibration.get('C_calibration_admitted')is not False):raise ValueError('A6 null-calibration regime required')
    if g1.get('gate')!='G1' or g1.get('status')not in ('PASS','FAIL','INCONCLUSIVE'):raise ValueError('final historical G1 required')
    if (h2.get('gate')!='H2' or h2.get('status')!='UNAVAILABLE' or h2.get('condition')!='v2-S2'
            or h2.get('H2',{}).get('predictor')is not None or h2.get('H2',{}).get('status')!='UNAVAILABLE'
            or h2.get('F2',{}).get('status')!='UNAVAILABLE' or h2.get('F2',{}).get('prospectively_frozen_value')!=.75
            or h2.get('batch2')!={'armed':False,'responses':0,'status':'SKIPPED_A6'} or h2.get('disable_arm_C')is not True):
        raise ValueError('published A6 null-predictor waiver required')
    if (diagnostic.get('condition')!='v2-S2' or diagnostic.get('status')!='SOUND' or diagnostic.get('LP_admitted')is not True
            or diagnostic.get('cleanup_unresolved')!=0 or diagnostic.get('declared')!=512):raise ValueError('final sound A6 diagnostic required')
    return {'eligible_arms':['A','B','P'],'disabled_C_reasons':['A6 null calibration and H2/F2 unavailable','G1 '+g1['status']],
        'source':'PLAN section 4 and adopted A6','technical_and_learning_gates_still_required':True,
        'T5_arm':'B','T5_metric':'own train reward','A_curve':'descriptive','token_budget_source':'unchanged A pilot lengths'}

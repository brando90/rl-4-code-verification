#Adaptive1.7Bcampaignhandoff

**Doc link:** [runbook](cc.md)

**TLDR:** Userauthorizedcurrentdata1.7Btraining,parallelTerraexplicit-proofcleanup,secondcomparabletraining,thenvalidation-driveniterationswithin$600maximumAPIspend.

## State
- Created10-19-202606:14PDT; remote execution root `/lfs/skampere1/0/eth127/rl4cv_tiny_training`.
- V12currentdatafrozen10,940rows;13,168,888assistantlosstokens;5470updates;0protectedhits. DispatcherstartsGPU1afterfrozenreceipt.
- V13Terra/highcleanupinpreparation. V12cleanedwatchwillstartverified/fallbackcomparisononGPU2afterV13completion.
- APIinitial$300;conditionalextra$300,hardmaximum$600. Sharedledger `adaptive_1p7b_campaign/budget.json`,cleanup240/480,adaptation60/120.
- Private authorizedkeycopyonLFS0600,parent0700; noAFSrenewalneededforfreshCLIworkers. No keycontents inGit/logs/prompts.
- GX10environmentcontrolspassed; SNAP↔GX10accesscurrentlyneedsMacrelay. Clusterprimaryavailable; noderebootrecoverynotconfigured.
- Rootwatchsource `supervise.py`; launchstate/heartbeat under `adaptive_1p7b_campaign/`.
## Continuation
- Read V12currentprogress,V13progress/sharedbudget,V15coordinatorheartbeat; distinguish actualtrainingfromCPUpreparation.
- Mirror compactreports/per-rowtables, inspectdiff/secretpatterns, gatechecks,commit/pushownedpaths. Preservehealthyremotejobs and otherworktrees.
- Adaptiveownerreads `cc.md` and onlywakesoncompletedvalidation orrealdead/failedjob; no paidpolling.
## Userto-do
- Noneforclusterexecution. No newpermissionsneeded;paidworkceilingandTerraareexplicitlyauthorized.
## Log
-10-19-202606:14PDT -- Frozeninitialcampaigncontract; prior68repaircompletionpublished9f9f163; currenttrainingandcleanupremoteownerspreparing.

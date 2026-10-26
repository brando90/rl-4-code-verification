# Adaptive Qwen3-1.7B warm-start campaign

**Doc link:** [runbook](cc.md)

**TLDR:** The user authorized current-data training, parallel explicit-proof teacher cleanup, a second comparable run and validation-driven follow-up work toward25%binarysuccess. All subsequent language-model work uses Terra/high; totalnewAPIbudget$300initialplus$300conditionaladditional,maximum$600.

Locked before adaptive model calls or follow-up optimizer updates,10-19-2026. Versions12and13 retain their own prospective protocols. This phase supervises those ordinary-code owners and wakes a model only on completed validation or a real failed/dead job. It does not replace the evaluator, scoring gates, splits or fullmanifest.

## Target and interpretation

Target>=270/1080successes over135VeriBenchV1validationtasks×8attempts under inherited binarysuccess/nonvacuity/scorer settings. Require a complete measuredmanifest. Validation guides regime selection and is therefore adaptive; no independent-test claim is made. The222-tasktestsplit stays sealed. Report task-resampled95%intervals and all failed/inconclusive trials; no guaranteeof attaining25%within this budget.

## Resource and spending bounds

At most two new1.7BGPUjobs concurrently, one genuinelyfree80GBA100/run with existing admissionlocks. Existing4Band foreignjobs preserved. No idleGPUreservation. Named remote processes and ordinary death/timeout/terminal monitors survive laptop/SSHdisconnect; no automaticnoderebootrecovery is configured. GX10userenvironment passes tensorandtinyQwen3trainingcontrols, but dynamicSNAP↔GX10fallback currentlyrequiresMacrelay; primaryclusterwork continues without it.

Sharedbudgetledger uses atomicflock reservations and actual tokenusage with conservative pricing; reserve for unknown in-flightcost before calls. Cleanupinitial240/max480,adaptationinitial60/max120; combinedinitial300/max600. Secondtrancheactivationrecordedonlyifneeded. Modelpin gpt-5.6-terra/high via authenticatedCodexCLI; no directproviderAPIcode, externalmessages or newcreditpurchases. Officialpricingandmaximums verified10-19-2026: [Terra model](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [pricing](https://developers.openai.com/api/docs/pricing). Modelcontext1,050,000,maxoutput128,000; $12reservationcovers$2observedconservativeusage plus<=7.554single-request worst exposure. Configure128kCLIcontext/100kautocompaction to control growth, not as an invoiceguarantee.

## Data and prospective amendments

Each follow-up declares hypothesis, failurecategory, source/input hashes, initialweights, schedule, actualsource/losstokens, optimizer and fullvalidationmanifest before training. New data comes from training/publicsources; validation/testcontent is not transformed into teachingexamples. Require pinnedcurrentkernel honesty, unchanged statements/API, commentintegrity, exactFILE/template/tokenchecks, protected764-referencescreen and conservative dedup. Mathlib/DeepSeekcandidates remain unadmitteduntilallgatespass. ProvisionalDeepSeeklicenseuse was explicitlyauthorized earlier; its uncertainty remains recorded.

Ordinary supervisor records completedoutcomes, nexttrialmanifests, processliveness, budgetevents and sourcehashes. A completedfailedstage can cause one boundedrecoveryretry; no silentredraw of evaluationcells or frozenbudgetreset. Finishedmeasurements are preserved. If no eligible route or budget remains, healthy deterministicjobs finish and the actualhold is recorded.

## Before-first-outcome implementation clarification

Before any adaptive call, the supervisor also freezes evaluator source hashes and independently recomputes full-cell binary success from raw/scored artifacts before accepting a25% claim. A summary alone is insufficient. Root-only waiting supervisor was restarted to deploy this clarification; healthy training and cleanup children were unchanged.

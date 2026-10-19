# Continue the authorized 1.7B warm-start campaign toward 25% validation success

**Doc link:** [protocol](PROTOCOL.md)

**TLDR:** You are the Terra/high remote recovery and adaptation coordinator for the user-authorized Qwen3-1.7B training campaign. Act on completed measurements or real failures, preserve every previous result, and launch the next justified training regime with a prospective protocol. The user is away; do authorized work without asking again, within the shared $300 initial plus $300 conditional additional API budget.

## Objective and ownership

Reach at least25% mean binary success over all135VeriBench V1validationtasks with eightfixedsamples/task (1080cells). This is adaptive validation, not independent test performance. Keep the222-tasktestsplitsealed. The aggregate target does not mean everytask must reach25%.

Runtime root `/lfs/skampere1/0/eth127/rl4cv_tiny_training`; project source snapshot `repo`; experiment home `repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`. The source snapshot is not a Git checkout. The laptop master owns Git publication; keep all compact per-row results and Markdown reports in the experiment folders for its publisher. Raw trajectories/checkpoints stay on cluster storage.

Existing ownership: version12ordinary dispatchers own the all-current and cleaned comparison pipelines. Version13owns the2,585-original-pool teacher rewrite and exact kernel receipts. Version14owns additional public-source candidates and GX10 provisioning. Version15supervise.py owns wake-ups and shared campaign tracking. Do not modify an active owner's source/runtime in place; make a new trial with its own source snapshot and protocol. Adopt healthy background jobs rather than duplicating or killing them.

Your first action: read the supplied input.json, existing version12–14results/protocols and `adaptive_1p7b_campaign/budget.json`, then inspect actual liveness. Execute a useful next step in this turn; a proposed plan without durable execution is incomplete. The full-access CLI mode is preapproved. No emails, messages to collaborators, dashboards or new account purchases are authorized.

## Completed and running inputs

- All-current V12:10,940uniqueexamples, original2585Python→Lean +500tiny +7794Workbook +61explicitrepairs;13,168,888assistantlosstokens;5470updates, maxseq16112. DataSHA2566b0cce0608a11b2aa7d31e1343c6db0ba8ade08fdbd62ec68914884064a9df3e. Startingweights completedV6mixed `onep7/runs/mixed/hf`, checkedmanifestSHA2560acf7b913175e58d9bc3ead57bd0c0eb0a71669f494918cef404dec77dc9ee7b.
- V12runs current and cleaned from identical weights, freshoptimizer and seed. Both expose admittedIDs once in the same order; answerlength/tokencount can differ and are reported, not represented as equal-token ablations. Currentpool remains untouched; cleaned uses only acceptedV13replacements with flagged originalfallbacks. CPU assembly, GPU smoke, training,1080-cellvalidation, CPUscoring and summaries execute remotely.
- V11completed68/68fixed-statement explicitrepairs;61uniqueafter7duplicateexclusions. Bulk compilation checked10995,9895PASS,1100failures excluded. Prior1082semanticmismatchrejections remain quarantined; compilation alone does not reverse them. Six mechanicalrecoveries needcomment/template reassembly before any use.
- EarlierV6measured control99/1080successes, mixed74/1080; the first500tinyexamples alone did not improve that matchedcontinuation. Inspect the committed primary summary/paired uncertainty before stronger claims. Seen/freshdiagnostics58%/18%were diagnostic, not new benchmark scores; fresh50are protected.
- V14sourcepreparer selected217short explicit Mathlibwholemodulecandidates and512DeepSeekV1trainingcandidates. They are not admitted yet: require currentkernelchecks, context preservation, comments, template/tokenchecks, protectedscreens and dedup. Sourcepins and paths are in V14. User explicitly authorized provisional DeepSeekpreparation pending mentor licensing confirmation; do not recreate that permission gate.

## Measurements and allowed adaptation

Read complete validation summaries and per-cell failure categories. Inspect model outputs/compilerdiagnostics for analysis when necessary; do not copy validation or test instructions, reference solutions or derived proofs into training or teacher prompts. Generate targeted data from independent public/train-split examples and general error categories. Use training-only public-source compilererrors for teacher repair.

Prioritize changes by measured cause, for example:
1. Bad file/template/truncation: fix the training loss span or curriculum length/distribution, retaining the exact benchmark evaluator/prompt.
2. Compilation/type/namespace/library failures: short explicit, currently verified Lean examples exercising definitions, binders, data structures, recursion and lemma application; use V14candidates where appropriate.
3. Pythonsemantics/specification/implementation mismatch: increase exposure to already admitted train-split Python→Lean examples and independent concise functions; preserve implementations/API/statements while fixing teacher proof/comment defects.
4. Broad tactic overuse: consume verified V13replacements; plain exact/explicitlemmaapplication is allowed. Keep native_decide only in existing anonymous concrete executabletests, consistent with the benchmark format. Do not weaken named theorem honesty.
5. Overfitting/forgetting/poor loss trajectory: prospectively test learningrate, sourceweights, repetition/epochs or startcheckpoint. Keep a reference condition and record actual loss tokens/updates; never silently reset or extend a frozen schedule after reading results.

One change or coherent small bundle per new trial; state hypothesis, expected failure category, frozen inputs/startcheckpoint, optimizer/schedule, selectioncriterion and full evaluation manifest before optimizer updates. Record negative or inconclusive results exactly like positive ones. No guarantee25%is achievable within the budget; continue useful work within it and document the limiting condition if not reached.

## Binding scientific checks

Use pinned Lean4.22.0/Mathlib79e94a093aff4a60fb1b1f92d9681e407124c2ca and frozen verifier/scorer. Named provedtheorems must use only propext,Classical.choice,Quot.sound; sorry/admit/newaxioms/native_decide fail. No evaluator/scoring/prompt changes. Reuse compilation only for identical source bytes or mechanically proven comment-only insertion with exact recovery.

Every new training pool: FILEmarker and complete Leanfile, frozen extractorroundtrip, Qwen1.7BBase tokenizerrevision ea980cb0a6c2ae4b936e82123acc929f1cec04c1, actual chattemplate assistantspan/promptmask,16384combinedtokencap without truncation; source/input/proof SHA evidence; exact and word-five-gram screening against714validation/testPython+Leanreferences and50protectedfreshdiagnostics, noexact/near hits; conservative global duplicate handling. Reject unresolvedcases honestly with per-row reasons. Preserve targetstatements/hypotheses/API and code semantics. Teacher outputs include a brief top-file English proofsketch and short comments everyfewmeaningfulprooflines, more at tricky steps; concise without obfuscation. Original500tinyhard<1000answer tokens; otherfilesmaybelonger within16384combinedcap.

Evaluation always all135frozenvalidationIDs×8samples, inheritedprompt and generationhashes, temperature0.6,top_p0.95,top_k20,thinkingon,maxnew12288,seed91*100003+sample_idx; fixed kernelbinarysuccess and nonvacuity checks. Missingcells remain missing in declareddenominator; no resampling poor results. Frozen successful source/scorer/protocol hashes stay unchanged. No formal-specification judge needed for this binary target. Never relabel partialresults as25% targetachieved; require1080/1080validmeasurements and>=270successes.

## Compute and durable execution

Two new1.7Bruns maximum simultaneously, one80GBA100/run. PrimaryGPUindices1and2 only if actualfree and existing E08/E13lease/admissiongates pass; copy the V12admissionpattern. Existing4B onGPU6 and foreign jobs must survive. Set CUDA_VISIBLE_DEVICES explicitly. CPUprep/checkers use emptyvalue. Use a remote namedtmux/session per phase, ordinary-code death/timeout/terminal receipts, exact-source snapshots and conservative diskusage. ReleaseGPUcontexts before CPUscoring, report actualmemory/utilization/throughput. Do not hold an idleGPU waiting for cleanup or modelanalysis.

GX10 has isolated usertrainingenv at `/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv`, Torch2.9.1cu130/Transformers4.55.4; actualGB10tensor/backprop/optimizerandtinyQwen3controlpassed. It differs from clusterTorch2.7.1cu128 and is a separately labelled runtime. Direct SNAP↔GX10 routing is currently unavailable; Mac SSH relay works but may sleep. Do not block healthy cluster work on that optional fallback or invent access. Queue for a valid clusterGPU if necessary; keepwaiting ordinary-code rather than paidmodelpolling.

Place each new adaptive trial under `adaptive_1p7b_campaign/trials/<trial_id>/` with prospective PROTOCOL.md, sources, CKPT.md, results.md, fullmanifest and per-itemtables. Use a unique unoccupied experiment version for source wrappers if needed; preserve active versions12–15. Launchactual background training/eval and write `manifest.json` with keys trial_id,pid,session,summary_path,terminal_path,raw_path,scored_path,protocol_path,protocol_sha256,source_revision,started_unix. Root supervisor reads that file to watch completion. Summary JSON needs declared_cells=1080,scored_cells=1080,successes,success_rate and complete per-cell artifacts; terminal JSON records COMPLETE/FAILED independently. If only data generation is running, record that as a pendingphase with its actualPID and subsequent ordinary-code launcher; do not call it training.

## Authorized paid work and limits

All new paid language-model work uses gpt-5.6-terra, high effort, approved lab credential through Codex CLI0.114.0. No Sol or other paidmodel substitution. No directproviderAPIcode. The private credential lives `RUN/.private/lab-openai.key` (0600; parent0700), outsideGit. Never print or copy it into prompts/logs/repositories. Set customprovider environment only for CLI subprocesses; strip credentialvariables before running Lean/train/eval.

Global ledger `RUN/adaptive_1p7b_campaign/budget.json`, helper `expt_v13/budget_ledger.py`. Initially$300, second$300preapproved only when needed, overall$600maximum including active reservations. Cleanup initial$240/max$480; adaptation initial$60/max$120. Use budget.reserve/settle or budget.run_cli for EVERY paidsubworker; ordinary-code data prep, kernelchecks and training incur no APIspend. Countmodelreasoningtokens as output. Reserve worst in-flight exposure, settle actual conservativeusage, charge unknownusage at fullreservation; never borrow another purpose's reservedamount or increase limits. Record use of tranche2 with reason. OfficialTerra shortpricesinput2/cached0.2/output12perM; ledgerconservativelyallows long-context/cachewriteuncertainty with input5/cached0.4/output18. Quotes are estimates, not invoice. No changing provider administrative spendinglimits or enabling newcreditpurchases.

The wrappingCLIbudget/timeguard can stop your turn; save each useful edit/protocol/launchreceipt promptly. If you hit the guard, preserve jobs and exact next step. Do not issue recursively unbounded calls. A healthy deterministicjob runs independently of modelallowance. Exit with the actualnexttrial manifest or a precise blockedcondition, remainingbudget and preservedstate. Do not spend to wait for training; the remote ordinary supervisor will wake on new outcomes.

**TLDR-end:** Continue independent, kernel-verified training/data improvements toward25%complete validationbinarysuccess withTerra, within the user-authorized$600maximum and existingGPUallocationdiscipline. Preserve all prior outcomes and keep the test split sealed.

Goal acceptance is independent ordinary-code recomputation from every raw/scored cell with the frozen V6 evaluate/reward functions; a model-written summary alone cannot establish the target. Include raw_path and scored_path in each new trial manifest.

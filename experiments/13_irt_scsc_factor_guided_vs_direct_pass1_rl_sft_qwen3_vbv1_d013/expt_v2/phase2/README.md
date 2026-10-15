# Experiment 13 v2-S2 Phase 2 implementation preparation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/README.md>

**TLDR:** Scheduling, batch construction and replay-state helpers are implemented and tested without model calls. This is preparation, not an LP lock or technical-gate result. Complete Phase 1 and freeze the full trainer, resource, audit and execution configuration before any Phase 2 device call.

`../PLAN.md` section 6 and `../../PROTOCOL.md` sections 3–8 govern admission, all four arms, the technical and learning pilots, token matching, selected-checkpoint evaluation and final analysis. S2 retains float16 on the installed vLLM 0.10.0 and NeMo RL 0.4.0 paths. The existing S1 failure remains final.

## Implemented foundation

- `schedule.py`: A/B/P share a deterministic uniform prompt permutation by seed, epoch and cumulative group index. C mixes that uniform stream with pre-group train information equally, falling back to uniform when information is zero. Rollout seeds are domain-separated 63-bit hashes of seed/group/slot, independent of arm or reward. The main token budget uses every declared A-pilot length; it rejects missing lengths. Token boundaries retain the entire crossing eight-response group, close ordinary updates at 32 groups, and report the actual paired mismatch against the 1% threshold. A partial update normalizes on its actual assistant tokens.
- `training_data.py`: preserve all eight slots, all generated tokens, prompt/assistant boundaries and terminal-token masks. The installed NeMo leave-one-out baseline and standard deviation operate on group identity, keeping repeated C-task groups separate. Normalize nonzero standard deviation with the installed epsilon 1e-6. Exactly constant groups have exactly zero advantage, including nonbinary rewards where floating-point reductions could otherwise leave rounding noise. There is no length filter, dynamic replacement or reward-based refill. A missing score masks its entire group's advantage; its original reward stays `None` in the durable input and all slots/tokens remain accounted. Fully measured zero-advantage batches follow the installed optimizer/scheduler advance convention. A wholly unmeasured update cannot fabricate a reward or optimizer step.
- `worker_state.py`: hash actual tensor contents; capture/restore Python, NumPy, Torch host and visible-device random-number generators; hash optimizer and scheduler state separately. The installed NeMo native checkpoint already stores weights/optimizer/scheduler but omits these random-number-generator states. Installed Ray 2.46.0's owned-actor `__ray_call__` can invoke these callbacks without editing NeMo. The eventual T3 test must check restoration and replay on the actual leased training worker.

The CPU regression uses the installed NeMo loss on small synthetic tensors with no visible device. That loss hard-codes one `.cuda()` move; the test alone replaces this placement with a CPU identity, then restores it. Production code and the measured trainer are unchanged. The test verifies finite gradients, zero gradient from constant/missing groups, exact host random-state replay, and optimizer/scheduler digest restoration. It does not establish GPU numerical agreement, memory sufficiency, checkpoint-export equivalence, actual training replay or T1–T4 admission.

## Remaining before LP

Implement the actual supervised training/update/export/refit driver and its gate ledger; choose and freeze the memory configuration using installed capabilities; bind source, checkpoint, tokenizer, probe, sampler, masks, optimizer, scheduler, limits and all device routes. Float32 master weights and optimizer state make memory planning distinct from the successful inference-only LP-1. The unchanged eager, 32-sequence generator is substantially slower than PLAN's original estimate; the prospective allocation must use measured S2 throughput and T4 costs.

Complete the train-only mutation and independent coverage controls required by PROTOCOL section 3 before learning. The separate pending validated formal-specification-coverage test evaluation does not waive the train coverage prerequisite. Keep all judge scientific settings pinned through the hosted Valkyrie transport migration.

No Phase 2 model inference, optimizer update, pilot, main run, validation selection or test evaluation has run. No scientific threshold, failed gate, model pin or token cap is relaxed by this preparation.

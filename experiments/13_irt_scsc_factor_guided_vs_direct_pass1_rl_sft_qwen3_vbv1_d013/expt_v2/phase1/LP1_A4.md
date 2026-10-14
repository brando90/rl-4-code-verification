# Experiment 13 version 2: LP-1 attempt 2 under adopted A4

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/LP1_A4.md>

**TLDR:** Adopted A4 prospectively admits LP-1 attempt 2 after attempt 1's published infrastructure failure. Its adoption is explicitly post-observation. The probe, seeds, model and trainer hashes, sampling, token limits, thresholds and resource caps remain unchanged. Attempt 1's outputs never enter attempt 2's statistics.

## Fix and preflight

`device_binding.py` queries `nvidia-smi --query-gpu=uuid,index` on the execution host, requires a unique match to the leased identifier and recorded index, and sets `CUDA_VISIBLE_DEVICES` to that numeric index before executing model code. Every runtime lease check revalidates this mapping and rejects foreign compute processes. The shared launcher supports LP-1, anchors, LP, T1–T4, pilot and main. The regression executes the installed vLLM conversion method in isolation: the old identifier raises `ValueError`, while the mapped integer succeeds for every launch purpose. Later phase-specific runners must enter through this same launcher; this does not admit a later gate or implement its scientific procedure.

Before recording the probe attempt, the supervisor runs a separate preflight process on the claimed device. It verifies the physical CUDA identifier, constructs the same frozen vLLM engine, and completes one token for the authored non-probe prompt `Reply with one word: ready.` No probe content is generated or scored, and no admission statistic is computed. The process is cleaned before a fresh generation process initializes the frozen probe seed. A durable launch record prevents a failed preflight from looping automatically. Only a passing preflight creates the numbered gate attempt record.

The existing engine parameters were factored into a shared constructor without changing their values. The only changed runtime scientific-input bindings are infrastructure source files (`runtime.py`, `lp1.py`), explicitly named in the successor lock. All other old bindings retain their previous digest. `a4_admission.py` compares the previous and successor configurations and rejects changed scientific fields, versions, input hashes, routes or resource caps; only new output paths, attempt accounting and named infrastructure code are allowed.

## Attempt and budget accounting

Attempt 2 has fresh private output/attempt paths, independently preserved from attempt 1. Its cap remains 1,800 seconds (0.5 device-hours), including preflight and cleanup; a 45-second operational reserve leaves time for cleanup and lease retirement. The cumulative allowance stays 0.6 device-hours, with 0.014593276 already used. The maximum is three numbered LP-1 attempts. A durable statistic-start marker is written before assessment, so any computation of admission statistics makes the attempt final even if later code crashes. Only documented infrastructure failures before statistics can qualify under A4; no automatic unreviewed attempt 3 is scheduled.

The eight-response probe still allows at most 65,536 probe tokens, plus the one non-probe preflight token authorized by A4. Zero optimizer updates occur. All compute processes, foreign leases and master reservations are checked before claiming; contention stays WAIT.

The previous watchdog's terminal receipt and notification remain historical. A fresh A4 watchdog run monitors the same single owner. Ten installed cron entries were backed up and preserved, with two A4 watchdog entries appended; the existing fifteen-minute device poller is reused. A new published launch plan is installed only after the successor lock and required tests reach main.

**TLDR-end:** [rl4cv: Experiment 13 v2] A4 reopens LP-1 with fixed device binding and a real engine preflight, preserving scientific settings and prior evidence.
**Snapshot:** Attempt 1 INCOMPLETE-INFRA; attempt 2 pending freeze/publication; 0.014593276 device-hours used of 0.6; no new probe response.

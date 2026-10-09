# Experiment09 failed-control runtime adapters

These are implementation candidates, not a passed trainer gate or a frozen main-training manifest.

- `nemo_c751_e09.patch` is the failed real-control snapshot against the owned NeMo pin `c751f811217db7df0d4c94abdeaada6626cfc150`, using `git apply --unidiff-zero` (zero-context diff preserves patch syntax without whitespace-only context lines). SHA-256: `a75db0c02f7d5d05eafafc701228892739351f11364115d0e9124a3852471472`.
- `nemo_c751_e09_diagnostic.patch` is the complete alternative patch against the same pin, adding read-only exact-batch probability replay. Apply this **instead of**, not on top of, the prior patch. It matches the final owned checkout and reverse-apply check. SHA-256: `1620f2b4282f4656af6308efaf7bd106315033975f48390d89a88fb67247f022`. Diagnostic mode preserves negative infinity for inspection, but the loss explicitly prohibits optimizing under that mode.
- `vllm_v010_sampler.py` is the full owned vLLM 0.10.0 sampler snapshot with its upstream license retained. It matches the installed owned file, SHA-256 `d9985289bd5b8b9602bfe2f882926f311af0b3fa46b3f1abced39485528ebe00`.
- Add this experiment's `expt_v1` directory and the repository `src` to the isolated actor's `PYTHONPATH`; the probability/loss/audit/device-guard helpers are explicit dependencies.

`E09_FILTERED_POLICY=1` admits only temperature .6, native top-k 20 then top-p .95, one device/full vocabulary, no sequence packing, one fresh full-batch update and zero reference-Kullback–Leibler coefficient. Outside-support or inconsistent active probabilities block the batch. Generation/old maximum absolute log-probability tolerance is .05; current/old tolerance is .005; permitted support mismatches are zero. No epsilon floors or sample deletion are used. The native filter's ties and nucleus cutoff are preserved.

The rollout adapter preserves sampled action IDs, appends the exact Qwen user/assistant boundaries, retains terminal metadata and blocks context-truncated/incomplete two-turn batches. Reproducible request seeds derive from paired seed, fixed cyclic schedule index, sample index and turn. Physical GPU UUID/foreign-process guards are mandatory, in addition to the shared lease.

Native synthetic sampler warmup is exempt only when the verified `_dummy_sampler_run` stack frame is present. A stale/inherited initialization environment flag cannot exempt real requests. Real request probabilities always use the exact filtered distribution.

The actual two-turn rollout subsequently passed boundary/mask checks. Its probability gate **failed**: 4/4,077 actions outside recomputed support; 367/4,073 finite actions exceeded .05 absolute log-probability error. No optimizer step or calibration was admitted. Save/reload, refit and 32,768-token optimizer-memory controls were not reached. The final 42 passing native adapter tests and 158 passing repository tests (4 skipped) do not override that runtime failure. See `../results/technical_gate.json` and `../../results.md`.

The driver's final auto-connect shutdown guard was added after replay and was not exercised by another GPU run. The online compiler/judge-service lifecycle is implemented and unit-tested but not live-verified on a scientific batch. These retained candidates are not a completed six-trajectory trainer or evaluation harness.

# Experiment09 prospective runtime adapters

These are implementation candidates, not a passed trainer gate or a frozen main-training manifest.

- `nemo_c751_e09.patch` applies only to the owned NeMo checkout at `c751f811217db7df0d4c94abdeaada6626cfc150`, using `git apply --unidiff-zero` (zero-context diff preserves patch syntax without whitespace-only context lines). Reverse-apply check passes against the current owned runtime. SHA-256: `a75db0c02f7d5d05eafafc701228892739351f11364115d0e9124a3852471472`.
- `vllm_v010_sampler.py` is the full owned vLLM 0.10.0 sampler snapshot with its upstream license retained. It matches the installed owned file, SHA-256 `d9985289bd5b8b9602bfe2f882926f311af0b3fa46b3f1abced39485528ebe00`.
- Add this experiment's `expt_v1` directory and the repository `src` to the isolated actor's `PYTHONPATH`; the probability/loss/audit/device-guard helpers are explicit dependencies.

`E09_FILTERED_POLICY=1` admits only temperature .6, native top-k 20 then top-p .95, one device/full vocabulary, no sequence packing, one fresh full-batch update and zero reference-Kullback–Leibler coefficient. Outside-support or inconsistent active probabilities block the batch. Generation/old maximum absolute log-probability tolerance is .05; current/old tolerance is .005; permitted support mismatches are zero. No epsilon floors or sample deletion are used. The native filter's ties and nucleus cutoff are preserved.

The rollout adapter preserves sampled action IDs, appends the exact Qwen user/assistant boundaries, retains terminal metadata and blocks context-truncated/incomplete two-turn batches. Reproducible request seeds derive from paired seed, fixed cyclic schedule index, sample index and turn. Physical GPU UUID/foreign-process guards are mandatory, in addition to the shared lease.

Native synthetic sampler warmup is exempt only when the verified `_dummy_sampler_run` stack frame is present. A stale/inherited initialization environment flag cannot exempt real requests. Real request probabilities always use the exact filtered distribution.

Before scientific admission, real disposable optimizer/save-reload, refit, probability and 32,768-token memory controls must pass. They have **not passed** as of 10-08-2026 20:54 PDT; engine attempts stopped before generation. The 28 passing adapter tests and 146 passing repository tests do not establish that the full training runtime works.

# V22 Sol review continuation

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Complete. V21 admitted470 tiny examples (182mechanical `rfl`,288Terra repairs); Sol repaired all30 first-pass failures. The final500-row union and proof/comment map have been independently verified and handed to the V23 training owner. No original task IDs are missing or duplicated.

## Final verified handoff

- Authenticated visibility returned; the existing observer collected both immutable completions automatically. V21 completion SHA256 `d9bbc3d0c702590881a4d27aba6862881263bd21994d8fc56e6a135a126bf323`; V22 completion SHA256 `d9a38a1b869260fcc5711d1674df9acb69954716944b15d9d132c1981b5282a0`.
- V21 accepted470/excluded30; V22 exact closed failure cohort30, accepted30/excluded0. All500 original indices0–499 and task IDs are unique in the union. Both releases passed the frozen proof, strict automation, scope, sketch/inline-comment, actual FILE/Qwen token, and764-reference protected-screen gates.
- V21 final training SHA256 `f757a318cbcf5b8ddae32d26ad582df0bbbfc224f02179ac75bd22c5d2850f57`; V22 delta SHA256 `b4d9b103158515af58005856658432bf23190c68588e01d7d552a83974bf52a8`.
- Ready union: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v22/handoff/tiny_500_training.jsonl`, SHA256 `04c35eebf9f3bcb951dac07b210330e1857a4a09a1fd02d3e2e4cd8578181fed`.
- Union proof/comment map: sibling `tiny_500_proof_manifest.json`, SHA256 `da0d6b0c38d8f3804c7a78a0bdf7fc7fa0c528eac09d6112a868b445bcf20870`. It retains each phase's exact source, raw kernel receipt and comment-binding paths/hashes. V21 has62 deterministic comment-only annotations; V22 has0. Their checked source remains separate and bound by non-comment token identity.
- `verify_union_handoff.py` rechecked both pinned training/completion/manifest hashes, all500 exact original system/user messages, sparse-index coverage, exact failure-delta set, portable proof receipt hashes and comment bindings. It made0compiler/model calls and did not modify either phase's final release. Actual PASS receipt is `results/union_verification.json` and remote `handoff/union_verification.json`.
- Final recorded configured usage estimates: V21 ordinary$23.9081086/conservative$46.8286762; V22 ordinary$1.977455/conservative$4.356338. V22 final progress had0cleanup reservations. These are configured estimates, not invoices.
- Training owner received ready path/hashes immediately. V20 remains unchanged; parent owns V23 launch and Git publication. No new generation is needed for this500-example cohort.

## Confirmed execution

- Remote root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v22`.
- Worker sessions: `codex-rl4cv-sol-tiny-review-v22-00` through `05`; supervisor `rl4cv-v22-sol-review-watch` polls every 15 seconds.
- Launch at Unix time1792438096. Actual later observation:14CLI session records, all `gpt-6.1-sol`/high;8kernel-passing repairs,6running,14pending in an initial28-case cohort.
- The cohort grows only from terminal V21 bounded-repair failures and freezes after V21 completion. Copies and new evidence stay in V22; first-pass records remain unchanged.
- Shared pricing helper adds only Sol rates (ordinary2/.1/10, conservative5/.2/15 per million tokens). Existing model prices, $900 global and $780 cleanup caps, reservations and history are unchanged. Temporary-ledger reserve/settle/idempotence/cap controls passed;68actual prior Sol/high sessions and Codex CLI0.114.0 were verified before launch. The private lab key was read only into worker environment.
- Bounds:2CLI turns and4NEW candidate hashes per case,900seconds per CLI,120seconds per compiler, same16compiler lockfiles as V21. No Terra fallback.

## Visibility blocker and continuation

After both remote supervisors were armed, the local control socket disappeared and new bounded reads failed at the gateway with too many authentication failures. Fresh gateway probes stopped immediately. The training owner independently confirmed no alternate authenticated route. This is a visibility problem; the already running remote proof/training jobs do not require the local SSH session.

Local `resume_visibility.py` polls the filesystem for the existing control socket and checks its local master. Reads explicitly disable fallback ProxyCommand/ProxyJump/agent authentication. It copies only compact progress, final completion, outcomes and receipt manifests after authentication returns, then records both observed completion hashes. It never opens a fresh gateway login or starts a provider request.

Canonical remote completion is `lean_corpus_v22/completion.json`; accepted delta is `final/repaired_tiny_training.jsonl`, with all review outcomes and portable proof/comment/first-pass-failure evidence. V21 completion is independent. Do not claim final counts from the eight-repair interim observation.

The strict delta finalizer is already deployed. It waits for the immutable CLOSED cohort, all review cases terminal, and the exact V21 completion/failed-case set; then applies the same source, token, commentary, protected and duplicate gates with no model/compiler calls. Root owns Git publication; this agent has not staged, committed or pushed.

# Gemini 4 Argon QA-route test on experiment 01

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/qa/argon_valkyrie_10-07-2026/README.md>

**TLDR:** Tests whether Gemini 4 Argon, reached through Valkyrie on the Vals model gateway (Vals pays), can serve as a read-only quality-assurance (QA) reviewer. Argon reviews experiment 01 twice in one Valkyrie run: once at the current commit, and once, blind, at the commit that was declared COMPLETE before a later check found three real reporting defects. The pass criteria below were written before any model call.

## Goal

Brando, 10-07-2026: "I want to test if we can use vals.ai infinite argon access through valkrie to do better qa's. Test it. Say try it on 01 and see if argon works."

Two questions:

1. **Transport:** does a QA-sized packet (about 85,000 tokens) reach `google/gemini-4-argon` through Valkyrie and come back as a complete review?
2. **Usefulness:** does Argon find real defects (recall) without inventing false ones (precision)?

## Design

- **Route.** The existing Valkyrie agent `vb106_rater_v2`, used unchanged. Its installed bundle was downloaded on 10-07-2026 and is byte-identical to `~/veribench` commit `f2c4d07783`, `experiments/106_…/scripts/valkyrie_rater_agent_v2/`. The agent sends one Vals-gateway request with no tools and returns the raw completion. No new model-calling code was written. Experiment 106 smoke-tested Argon through this agent on 10-05-2026 (run `3f1a0bdd`).
- **Settings.** Model `google/gemini-4-argon`, `max_tokens` 65,536, `reasoning_effort` high (the registry default, which experiment 106 records as the highest), temperature 1.0 (the registry default). One Valkyrie run, concurrency 2.
- **Benchmark service.** Experiment 103's collect-only single-call service, run read-only from the local `~/veribench` clone on this Mac (127.0.0.1:9741) behind a cloudflared quick tunnel, with a bearer token on every route. Benchmark name `rl4cv-argon-qa`.
- **Tool.** `scripts/argon_qa/argon_qa.py`, run as build → selfcheck → deploy → admit → harvest → teardown. Private state lives in `~/.cache/rl4cv-argon-qa/`, outside the repository.
- **Packets.** Each packet is built with `git show` from a commit, never from the working tree. Both use the same reviewer system prompt: a read-only adaptation of agents-config `workflows/qa-correctness.md`, covering correctness and scientific integrity against `CLAUDE.md`. The prompt ends with a VERDICT block. Each packet contains:
  - a manifest of every tracked file in experiment 01, with byte counts;
  - the contents of every file except the raw per-cell data, which is listed in the manifest but left out (judge harvests, judge packs, task-id lists, GPU job lists);
  - `CLAUDE.md`, `experiments/README.md` and `docs/DECISIONS.md` at the same commit.

  | Task id | Commit | Role | Bytes |
  |---|---|---|---:|
  | `qa__e01_a` | `1ea02ee` (HEAD on 10-07-2026) | a real review of the current state | 342,418 |
  | `qa__e01_b` | `1904868` (10-01-2026 09:13, "Experiment 01: COMPLETE") | blind recall control | 314,415 |

  Neither packet says which one is the control or mentions any later fix. The task id appears only in the transport header, which the agent does not send to the model. Both packets passed the secret scan and the offline self-check: each round-trips through the agent's own `parse_task_file` and the service's own `load_task_pack`, with all hashes equal.

## Known defects in packet B (from commit `44439c7`, 10-01-2026 12:34, master-caught)

| ID | Defect | Visible in the packet? |
|---|---|---|
| K1 | Qwen3.5-0.8B's eval row in `results.md` reads "unmeasured", although the same file says all 9 models × 896 tasks were generated, scored and given terminal receipts. | yes |
| K2 | Qwen3.5-0.8B never got its FSC audit. It has no `fsc_qwen3.5-0.8b.json`, no judge task-id list and no judge-spend row, while every other model has all three. | yes |
| K3 | The probe table is stale. It is missing Qwen3.5-2B, Qwen3.5-9B, Qwen3-1.7B and Qwen3-4B, and still says "Qwen3.5-9B, Qwen3-1.7B, Qwen3-4B still probing/scoring" while the TLDR says the run is complete. The Gate G1 text rests on "3 of 8" models. | yes |
| K4 | Four frozen-scorer timeout cells left orphaned `lean` processes running. | no (host state only), so it is excluded |

## Frozen criteria (written before admission)

- **Transport PASS:** both cells meet every condition below, and the same holds for both packets:
  - status `measured` (COMPLETE);
  - a clean finish reason (`stop`, `stop_sequence` or `end_turn`);
  - a non-empty response;
  - no fallback model;
  - the delivered request (`wire`) carries model `google/gemini-4-argon`, `max_tokens` 65536, `reasoning_effort` high, temperature 1.0, an empty provider config, no tools and provider endpoint `models/barium-bb` (the registry entry experiment 106 recorded).

  An infrastructure failure is retried by rerunning the identical cell, never by changing the packet.
- **Recall (packet B):** a defect counts as caught only if the review explicitly identifies it, naming the model or table and the contradiction. Recall PASS means at least 2 of K1–K3 are caught.
- **Precision (both packets):** each finding is checked against the repository at the reviewed commit and classed as confirmed, false or unverifiable. The results report counts with denominators per packet and severity. There is no pass threshold. A CRITICAL or MAJOR finding that turns out false is reported by name.
- **Overall verdict:** "usable QA route" requires transport PASS and recall PASS, plus confirmed findings outnumbering false ones in each packet.

## Status

- 10-07-2026: packets built and self-checked. Admission follows.
- Results: [`results.md`](results.md).
- Reviews and receipts: `responses/`, `receipts/`.

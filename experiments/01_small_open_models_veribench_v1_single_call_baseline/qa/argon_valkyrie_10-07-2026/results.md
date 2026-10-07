# Results: Gemini 4 Argon QA-route test on experiment 01

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/qa/argon_valkyrie_10-07-2026/results.md>

**TLDR:** Gemini 4 Argon, run through Valkyrie on the Vals model gateway, works as a read-only QA reviewer. It passed all three frozen criteria:

- **Transport:** both cells passed every condition.
- **Recall:** reviewing a frozen "COMPLETE" snapshot blind, it caught all three known defects (3 of 3).
- **Precision:** across both reviews, 16 of 17 findings were confirmed against the repository. None was false and 1 could not be checked.

The current-state review also found real problems that the 10-01-2026 completion pass and its reopen both missed. The FSC judge ran 1 repeat per member, where the protocol and D-102 lock a median of 3. The 60-file FSC audit drew only from clean-finish cells. Eleven proving cells in the G=8 probe were never judged. The committed results cite summary files that were never committed. The run cost $2.39 and about 9 minutes of wall time. The reviewer cannot run code or apply fixes, cites line numbers loosely, and overstated severity in the control review.

## Route evidence (D-108), recorded about 10-07-2026 22:29 UTC, after admission and before any model call (both cells entered sandbox setup at 22:28:56 UTC)

- **Route:** a Valkyrie run started with `valkyrie run start`, using the custom single-call agent `vb106_rater_v2`. The agent calls the Vals model gateway from inside the Valkyrie sandbox. This is not the Vals direct API from this host. Exact command:

  ```
  valkyrie run start --agent vb106_rater_v2 --benchmark rl4cv-argon-qa --dataset default --model google/gemini-4-argon --concurrency 2 --label rl4cv-e01-argon-qa -k max_tokens 65536 -k reasoning_effort high -k temperature 1.0 -k benchmark rl4cv-argon-qa
  ```

- **Host:** Brando's Mac (`Brandos-MacBook-Pro-616.local`, macOS 27.0.1). The CLI is the Valkyrie uv tool (`valkyrie` 0.1.0, `valkyrie_sdk` 0.2.24). The benchmark service is experiment 103's `vb_service_single_call`, run read-only from `~/veribench` at `9e312c9052`; its service files were clean against that commit. It ran on 127.0.0.1:9741 behind a cloudflared quick tunnel. Health checks returned 200 with the bearer token and 401 without it, both locally and through the tunnel.
- **Valkyrie organization and environment:** the configuration environment is `bench`. Run logs go to the CloudWatch log group `fellows/brando-miranda`, and run artifacts go to the S3 bucket `fellow-brando-miranda` under `benchmarks/5f86e990-…/`. The configuration is a private copy of `~/.config/valkyrie/valkyrie.yaml` with this benchmark service added. Its contents are not reproduced here.
- **Model-provider credential source:** the agent contract's secret mapping `MODEL_GATEWAY_API_KEY: fellows/brandoModelGatewayApiKey`, recorded by name only. No key exists on this host's command line or in the packets, and provider keys are stripped from every child environment.
- **Payer:** Vals, through the Vals model gateway, the same payer D-102 records for experiment 01's judge.
- **Vendor agent (D-108):** D-108 prefers each vendor's own agent, which for Google is the Antigravity CLI `agy`. The account's 30 installed Valkyrie agents, listed on 10-07-2026 with `valkyrie agent list --format json`, include no Antigravity, `agy`, Gemini or Google agent. No Antigravity route exists on Valkyrie, so this test uses the model-neutral single-call agent. This is a limitation: the reviewer has no tools.
- **Runaway guard:** one declared call per cell (2 cells), with no silent retry loop. The agent sends a second request only after an HTTP 429 or 5xx, when nothing was served; neither cell needed one.

## Run

| | `qa__e01_a` (HEAD `1ea02ee`) | `qa__e01_b` (`1904868`, blind control) |
|---|---|---|
| Valkyrie run | `5f86e990-fa64-4821-aca1-2636a6c74961` | same |
| Admitted / finished (PDT) | 15:27:12 / 15:36:17 | 15:27:12 / 15:35:06 |
| Status, finish | `measured`, `stop` | `measured`, `stop` |
| Requests sent | 1 | 1 |
| Gateway wall time | 379.7 s | 311.2 s |
| Tokens in / out / reasoning | 136,020 / 7,430 / 29,663 | 125,474 / 7,859 / 22,437 |
| Charge reported by the gateway | $1.286 | $1.108 |
| Response | 20,410 bytes, [`responses/qa__e01_a.md`](responses/qa__e01_a.md) | 21,707 bytes, [`responses/qa__e01_b.md`](responses/qa__e01_b.md) |

The total charge was **$2.394**. The pre-run estimate was at most $3, based on about 95,000 input tokens per packet; Gemini's tokenizer counted 125,000–136,000. Secret-free receipts are in `receipts/`.

On harvest, `valkyrie run results` failed with "tracker returned a malformed response". `valkyrie run output` succeeded, and its run record carries the same per-cell rows. In those rows the service's collected-file SHA-256 equals the agent's written file for both cells (`970dbf94…` and `cdf3908c…`). The service and tunnel were stopped at 22:37 UTC, and port 9741 is free.

## Verdicts against the frozen criteria (`README.md`, sha256 `22633b49…`, frozen 22:26:38 UTC before admission)

| Criterion | Result | Verdict |
|---|---|---|
| Transport | Both cells: `measured`, `stop`, non-empty, no fallback. Delivered request: model `google/gemini-4-argon`, `max_tokens` 65,536, `reasoning_effort` high, temperature 1.0, empty provider config, no tools, endpoint `models/barium-bb`. Prompt hashes equal the packet hashes. | **PASS** |
| Recall (packet B) | K1, K2 and K3 all caught: 3 of 3, threshold ≥ 2 | **PASS** |
| Precision | Top-level findings: A has 8 confirmed, 0 false, 1 unverifiable (n = 9); B has 8 confirmed, 0 false, 0 unverifiable (n = 8) | confirmed > false in both, so **PASS** |
| Overall | | **Usable QA route** (read-only, single call) |

### Recall on the blind control (packet B, commit `1904868`)

| Known defect | Caught? | Where |
|---|---|---|
| K1: Qwen3.5-0.8B's eval row reads "unmeasured" while every file says complete | yes | F1, CRITICAL, quoting `\| Qwen3.5-0.8B \| — \| unmeasured \|` against README's "all 896/896 cells generated and kernel-scored for every model" |
| K2: Qwen3.5-0.8B never got its FSC audit | yes | F1, which lists the missing `fsc_qwen3.5-0.8b.json`, the missing `state.json` entry and the missing spend row. All three absences are confirmed at `1904868`. |
| K3: stale probe table | yes | F2, CRITICAL: "4 of the 8 probe models … missing … line 88 still says 3 of them are 'still probing/scoring' (omitting Qwen3.5-2B entirely)" |

### Precision: every finding checked against the repository at the reviewed commit

Each top-level finding is classed confirmed (✓), false (✗) or unverifiable (?). Partial or overreaching sub-claims are noted.

| Finding | Packet | Severity given | Class | Verification |
|---|---|---|---|---|
| Summary files never committed; `results.md` cites the missing `expt_v1/results/summaries/` | A-F1, B-F3 | CRITICAL | ✓ | No summaries are tracked at either commit. `cc.md` §7.2–7.3 requires committing `rho_h_*`, the JSON summaries and `results_summary_*.md`. |
| G=8 probe cells with IC_tests · IC_proofs > 0 never judged; no `scsc`/`fsc_compiled` probe channels | A-F2, B-F2(3) | CRITICAL | ✓ | `kernel_binary` = 1 implies IC_tests = IC_proofs = 1 (`src/rl4cv/rewards.py`). The mean rewards (0.0039 and 0.0068 over 1,024) give 4 + 7 = 11 positive cells. `judge/state.json` has only G=1 suites. PROTOCOL locks "plus scsc and fsc_compiled once judged". No recorded deviation. |
| Judge ran **1 repeat per member**; PROTOCOL and D-102 lock "median of 3 each" | A-F3, B-F6 | MAJOR | ✓ **new** | `build_cells(None, 1, …)` and `"repeat": 1` in `judge_rl4cv_e01.py`. Harvests hold 61 items × 1 cell, all `__r1`. `vb103_judge` sends exactly one request per cell. Experiment 103's own `judge_vbv1.py` defaults to `--repeats 3`. "repeat" appears in no experiment-01 document. |
| 60-file audit drawn only from `measured` (clean-finish) cells, shrinking audits for models that are often cut off | A-F4, B-F4 | MAJOR (A), CRITICAL (B) | ✓ **new** | `measured = clean_finish(finish_reason)` (`generate.py:225`) and `build_model_pack` filters on it. Audit size tracks the cut-off count: 0.8B 661 cut off → 37, 2B 475 → 51, 27B 236 → 52, 1.7B 252 → 57, and every model with ≤ 41 cut-offs → 60. `results.md` gives only "fewer than 12 tasks eligible", with no reason. A-F4(3) is false: it claims `CLAUDE.md` requires retrying `unmeasured_infra` judge cells, but `CLAUDE.md` requires listing them, not retrying. B-F4's label-salted hash is accurate but is not a protocol violation. |
| Core 614 and IndustrySet 282 not reported separately; no mean generated tokens; no pass@8 in the probe table | A-F5, B-F5(1), B-F2(2) | MAJOR | ✓ | `results.md` has a single 896 row and no token or pass@8 column, while README step 7 and `CLAUDE.md` require them. Qwen3-14B's only proving cell is `hardware_set_real__…`, which is IndustrySet, not one of the core splits. |
| "Measured / 896" column means "scored" for experiment 01 rows but "measured" for experiment 103's 604 row; no route-control comparison | A-F6 | MAJOR | ✓ | PROTOCOL defines a measured cell as a clean finish (the 0.8B would be 235/896). README step 8 and `cc.md` §7.1 require the comparison with experiment 103's Valkyrie row; `results.md` only places that row in the table. |
| Qwen3-14B's `aerospace_set_real` share 0.333 implies 3 groups, not 4 | A-F7 | MAJOR, UNCERTAIN | ? | `rl4cv/probe.py` drops groups with any unmeasured sample (`n_groups_excluded_unmeasured`), so 3 counted groups is possible. The deciding `rho_h_*` file is not committed. Gate G1 is unaffected either way, as the review itself notes. |
| Stale status lines: README TLDR "Nothing has been run yet."; README status table still $102.55 and 9 suites; index "Done (10-01-2026 09:08)"; CKPT "6 kernel_binary splits" against the 8 in `results.md`; CKPT "`$WORK/STATUS_e01` = `RUNNING`" | A-F8 | MINOR | ✓ | All present at `1ea02ee`. The "6 splits" line matters to experiment 02's pool seeds. The review's pointer to "line 13's 8 distinct" is wrong: the 8 splits are in `results.md`. |
| `DISPATCH_e01.md` lacks Doc link and TLDR; `cc.md` lacks Doc link; Qwen3-1.7B FSC 0.097 should be 0.096 | A-F9, B-F8, B-F5(3) | MINOR | ✓ | Recomputed from `fsc_qwen3-1.7b.json`: 5.5 / 57 = 0.09649, which rounds to 0.096. |
| K1 and K2 (Qwen3.5-0.8B) | B-F1 | CRITICAL | ✓ | Known defects, fixed in `44439c7` |
| K3 plus pass@8 missing | B-F2 | CRITICAL | ✓ | Known defect, fixed in `44439c7` (pass@8 still absent at HEAD) |
| Unmeasured judge cells dropped from denominators; Qwen3.5-4B's 3 `unmeasured_infra` cells not listed | B-F5(2) | MAJOR | ✓ partly | 4B's 3 incomplete items (`fsc_qwen3.5-4b.json`) are listed nowhere in `results.md`; only 9B's are. The proposed fix, keeping them in the mean's denominator, would count them as zero, which `CLAUDE.md` forbids. |
| Orchestration races: `score_worker_shared.sh` keeps the `pgrep … \|\| echo 0` bug; check-then-touch lock race; shard merge with no truncation; spend guard ignores runs not yet harvested | B-F7 | MAJOR | ✓ (overstated) | All four are present in the code. REPORT item 13 already calls the `pgrep` bug cosmetic. A duplicate merge would fail `run_model.sh`'s manifest check. The spend never neared the cap ($106 of $400). These are code risks with no evidence of impact, so MINOR. |
| More stale lines: index "running on SNAP"; orchestration README points to a missing "LIVE STATUS SNAPSHOT" section; `results.md` "Last updated 01:15" | B-F8 | MINOR | ✓ | All present at `1904868` |

**Sub-claim level:** A has 20 confirmed, 1 false and 1 unverifiable (n = 22). B has 26 confirmed, 1 false and 1 unverifiable (n = 28). Six verbatim quotes were spot-checked, and all six match the files exactly. Line numbers are often off by 2–30 lines (for example "results.md line 43" for line 45, and "CKPT line 115" for line 94).

## Best findings, quoted

1. A-F3: "`build_controls` and `build_model_pack` generate only 1 cell (`__r1`, `repeat: 1`) per item per member instead of 3 repeats … This deviation is also undocumented in `expt_v1/results/REPORT.md`." This is new, real, and still open. Every FSC number in experiment 01 is one sample per member, not the validated median of 3.
2. B-F4 and A-F4: "Filtering `rows` to `r.get("measured")` … conditions the audit sample on a generation outcome (whether the model finished before the 65,536-token cap)". This is new and real, and it explains the 37/51/52/57-cell audits that `results.md` left unexplained.
3. A-F2: "The 11 positive cells in the G=8 probe (`4` in `qwen3.5-9b_g8` and `7` in `qwen3-14b_g8`) were never judged". The 11 was derived correctly from the mean rewards.
4. B-F1, the blind control: "`Qwen3.5-0.8B` has no `fsc_qwen3.5-0.8b.json`, no `judge_pack_qwen3.5-0.8b.json`, no harvest files, no entry in `results/judge/state.json`, no row in the Judge spend table". This is the exact defect the master found 3 hours after the COMPLETE commit.

## Worst findings, quoted

1. A-F4(3): "instead of retrying those infrastructure failures per `CLAUDE.md` ('Infrastructure retries rerun the identical cell')". This misreads a rule about how to retry as a mandate to retry.
2. B-F5(2): "keep all declared audit cells in the denominator". This fix would count unmeasured cells as zero, which `CLAUDE.md` forbids.
3. B-F7, rated MAJOR: four orchestration races that are real in the code but cosmetic or guarded in effect. This is severity inflation; the control review rated 4 of its 8 findings CRITICAL.

## Verdict and limits

- **Usable:** yes, as an extra, Vals-funded, read-only reviewer. It found every planted (historical) defect, made no false top-level finding, and surfaced four substantive open issues in a state that two agent passes had declared complete. Each review costs about $1.10–1.30 and 5–6 minutes of model time.
- **What it cannot do:**
  - It has no tools, so it cannot run tests, open host files (raw generations and summaries on SNAP) or recompute numbers it was not given.
  - It cannot apply fixes.
  - It makes one call per review, with no follow-up questions.
  - It cites line numbers approximately and inflates severity, so findings need the builder's verification, as here.
  - D-108's preferred vendor agent (Antigravity `agy`) has no Valkyrie route yet.
- **Not measured:** a head-to-head with the standard Codex or Claude Code QA on the same packets. Whether Argon is *better* than that QA, rather than useful alongside it, is open.
- **Open issues for experiment 01**, none fixed here: the single-repeat judge, the clean-finish-only audit, the unjudged G=8 positive cells and missing `scsc`/`fsc_compiled` probe channels, the uncommitted summaries, the missing Core and IndustrySet split, the missing route-control comparison, and the stale README, index and CKPT lines (including "6 splits" against 8 for experiment 02).
